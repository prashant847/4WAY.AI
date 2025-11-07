"""
Gemini AI Integration for Smart Traffic Management
Provides intelligent analysis and recommendations
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv
from loguru import logger
import json
from datetime import datetime
import time
import hashlib

# Load environment variables
load_dotenv()

class GeminiAI:
    """Gemini AI Integration for Traffic Analysis"""
    
    def __init__(self):
        """Initializes the Gemini AI model and logger."""
        self.configure_genai()
        self.model = self.get_available_model()
        self.logger = logger
        self.last_api_call_time = 0
        self.api_cooldown = 15  # seconds
        self.cache = {}
        self.cache_expiry = 60 # seconds

    def configure_genai(self):
        """Configures the Gemini AI with API key and model selection"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        # 🔧 GEMINI API: Use stable model names without 'models/' prefix
        # The SDK automatically handles the model path internally
        self.model_name = os.getenv('GEMINI_MODEL')  # allow override in env
        
        # Try to get available models
        try:
            logger.info("🔍 Fetching available Gemini models...")
            available_models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.replace('models/', '')  # Remove prefix
                    available_models.append(model_name)
                    logger.info(f"   ✓ {model_name}")
            
            if available_models:
                # Use first available model
                self.model_name = available_models[0]
                logger.success(f"✅ Selected model: {self.model_name}")
            else:
                # Fallback to known stable model
                self.model_name = 'gemini-pro'
                logger.warning(f"⚠️ No models found, using fallback: {self.model_name}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not list models: {e}. Using fallback.")
            # Fallback to most stable model
            self.model_name = self.model_name or 'gemini-pro'
            logger.info(f"Using fallback model: {self.model_name}")

        # Do not pre-instantiate a model object
        self.model = None
        logger.success(f"🤖 Gemini AI initialized with model: {self.model_name}")

    def get_available_model(self):
        """Gets the available model, handling any errors"""
        try:
            logger.info("🔍 Fetching available Gemini models...")
            available_models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.replace('models/', '')  # Remove prefix
                    available_models.append(model_name)
                    logger.info(f"   ✓ {model_name}")
            
            if available_models:
                # Use first available model
                model_name = available_models[0]
                logger.success(f"✅ Selected model: {model_name}")
                return model_name
            else:
                # Fallback to known stable model
                fallback_model = 'gemini-pro'
                logger.warning(f"⚠️ No models found, using fallback: {fallback_model}")
                return fallback_model
                
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return None

    def analyze_traffic_decision(self, vehicle_data, frame_width, frame_height):
        """
        Analyzes traffic data to make intelligent decisions, with caching and rate limiting.
        """
        # Create a hash of the vehicle data for caching
        vehicle_data_str = json.dumps(vehicle_data, sort_keys=True)
        data_hash = hashlib.md5(vehicle_data_str.encode()).hexdigest()

        # Check cache first
        if data_hash in self.cache:
            cached_data = self.cache[data_hash]
            if time.time() - cached_data['timestamp'] < self.cache_expiry:
                self.logger.info("Returning cached AI decision.")
                return cached_data['response']

        # Rate limiting
        current_time = time.time()
        if current_time - self.last_api_call_time < self.api_cooldown:
            self.logger.warning("API cooldown active. Skipping Gemini AI call.")
            return self._create_fallback_response(traffic_data=vehicle_data, error_message="Cooldown active, using fallback.", status="WAIT")

        if not self.model:
            self.logger.error("No model available for analysis.")
            return self._create_fallback_response(traffic_data=vehicle_data, error_message="AI model not available.", status="ERROR")

        prompt = self._create_prompt(vehicle_data, frame_width, frame_height)
        
        try:
            self.logger.info("Requesting decision from Gemini AI...")
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            
            self.last_api_call_time = time.time() # Update timestamp after successful call

            cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
            decision = json.loads(cleaned_response_text)
            
            # Cache the new response
            self.cache[data_hash] = {
                'timestamp': time.time(),
                'response': decision
            }
            
            self.logger.success("Successfully received and parsed AI decision.")
            return decision

        except Exception as e:
            self.logger.error(f"Error during Gemini AI analysis: {e}")
            return self._create_fallback_response(traffic_data=vehicle_data, error_message=f"AI analysis failed: {e}", status="ERROR")

    def _create_prompt(self, vehicle_data, frame_width, frame_height):
        """
        Creates the prompt for Gemini AI based on vehicle data and frame dimensions.
        """
        try:
            # Basic prompt structure
            prompt = f"""You are an expert traffic management AI. Analyze the following traffic data and provide a detailed decision.

**Traffic Data:**
{json.dumps(vehicle_data, indent=2)}

**Frame Dimensions:**
Width: {frame_width}, Height: {frame_height}

**Current Time:**
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Your Task:**
1. Identify the most congested lane
2. Recommend optimal signal timing
3. Predict impact of your decision
4. Provide confidence score (0-100)
5. Give detailed reasoning

**Response Format (JSON only, no markdown):**
{{
  "action": "Clear, actionable decision (e.g., 'Prioritize West Lane - Extend GREEN +30s')",
  "reason": "Brief explanation of why this decision is optimal",
  "detailed_analysis": "Deep analysis considering time of day, congestion patterns, and traffic flow",
  "impact_prediction": "Expected outcome (e.g., '25% delay reduction, 15 vehicles cleared in 45 seconds')",
  "confidence": 85,
  "priority_level": "CRITICAL/HIGH/MEDIUM/LOW",
  "alternative_action": "Backup recommendation if primary fails",
  "risk_factors": "Potential issues to watch for"
}}

**Important:** Return ONLY valid JSON, no explanations, no markdown formatting."""

            return prompt
        except Exception as e:
            self.logger.error(f"Error creating prompt: {e}")
            raise

    def _create_fallback_response(self, traffic_data=None, error_message=None, status="ERROR"):
        """Create a rule-based fallback when AI fails"""
        # Handle error cases where traffic_data is not provided
        if traffic_data is None or not isinstance(traffic_data, dict):
            return {
                'action': 'Normal Operation',
                'reason': error_message or 'No traffic data available',
                'detailed_analysis': f'System operating in fallback mode. Status: {status}',
                'impact_prediction': 'Minimal impact',
                'confidence': 50,
                'priority_level': 'LOW',
                'alternative_action': 'Continue monitoring',
                'risk_factors': 'Limited data available',
                'ai_powered': False,
                'timestamp': datetime.now().strftime("%I:%M %p")
            }
        
        lanes = traffic_data.get('lanes', [])
        
        if not lanes:
            return {
                'action': 'Normal Operation',
                'reason': error_message or 'No traffic data available',
                'detailed_analysis': 'System operating in fallback mode',
                'impact_prediction': 'Minimal impact',
                'confidence': 50,
                'priority_level': 'LOW',
                'alternative_action': 'Continue monitoring',
                'risk_factors': 'Limited data available',
                'ai_powered': False,
                'timestamp': datetime.now().strftime("%I:%M %p")
            }
        
        # Find most congested lane
        max_lane = max(lanes, key=lambda x: x.get('current_vehicles', 0))
        vehicles = max_lane.get('current_vehicles', 0)
        lane_name = max_lane.get('name', 'Unknown')
        
        if vehicles > 25:
            priority = 'CRITICAL'
            action = f'Prioritize {lane_name} - Extend GREEN +35s'
            impact = f'{int(vehicles * 0.25)} vehicles cleared in 60 seconds'
        elif vehicles > 15:
            priority = 'HIGH'
            action = f'Extend {lane_name} Signal +20s'
            impact = f'{int(vehicles * 0.20)} vehicles cleared in 45 seconds'
        else:
            priority = 'MEDIUM'
            action = f'Maintain {lane_name} Standard Timing'
            impact = 'Normal flow maintained'
        
        return {
            'action': action,
            'reason': f'{priority} congestion detected ({vehicles} vehicles)',
            'detailed_analysis': f'Rule-based analysis: {lane_name} requires attention',
            'impact_prediction': impact,
            'confidence': 70,
            'priority_level': priority,
            'alternative_action': 'Monitor and adjust dynamically',
            'risk_factors': 'Operating without AI - using fallback logic',
            'ai_powered': False,
            'timestamp': datetime.now().strftime("%I:%M %p")
        }
    
    def get_traffic_insights(self, historical_data):
        """
        Analyze historical patterns and provide insights
        
        Args:
            historical_data (list): Past traffic data points
            
        Returns:
            dict: Pattern analysis and predictions
        """
        try:
            prompt = f"""Analyze this traffic pattern data and provide insights:

**Historical Data (last 30 minutes):**
{json.dumps(historical_data, indent=2)}

**Provide:**
1. Trend analysis (increasing/decreasing/stable)
2. Pattern recognition (rush hour, normal, low traffic)
3. Next 15-minute prediction
4. Recommendations for optimization

**Response Format (JSON only):**
{{
  "trend": "increasing/decreasing/stable",
  "pattern_type": "rush_hour/normal/low_traffic",
  "prediction_next_15min": "Detailed prediction",
  "optimization_tips": ["tip1", "tip2", "tip3"]
}}"""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            insights = json.loads(response_text.strip())
            return insights
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return {
                'trend': 'stable',
                'pattern_type': 'normal',
                'prediction_next_15min': 'Steady traffic expected',
                'optimization_tips': ['Monitor closely', 'Adjust signals as needed']
            }

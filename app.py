"""
Main Flask Application
Advanced Traffic Management System Backend
"""
import os
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from pathlib import Path
import cv2
from datetime import datetime
from loguru import logger
import sys

from config import Config
from vehicle_detector import VehicleDetector
from traffic_analyzer import TrafficAnalyzer
from signal_controller import TrafficSignalController
from ai_gemini import GeminiAI

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    Config.LOGS_DIR / "traffic_system_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# 🎯 MEMORY OPTIMIZATION: Set max content length to prevent memory errors
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

CORS(app)

# Initialize components with error handling
detector = None
analyzer = None
signal_controller = None
gemini_ai = None

try:
    logger.info("Initializing YOLOv8 Vehicle Detector...")
    detector = VehicleDetector()
    logger.info("✅ Detector initialized successfully!")
except Exception as e:
    logger.error(f"❌ Detector initialization failed: {e}. Detection features disabled.")
    detector = None

try:
    analyzer = TrafficAnalyzer()
    signal_controller = TrafficSignalController()
    logger.info("✅ Traffic analyzer and signal controller ready!")
except Exception as e:
    logger.error(f"❌ Analyzer/Controller initialization failed: {e}")

# Initialize Gemini AI
try:
    gemini_ai = GeminiAI()
    logger.info("🤖 Gemini AI ready for smart decisions!")
except Exception as e:
    logger.warning(f"⚠️ Gemini AI initialization failed: {e}. Using fallback logic.")
    gemini_ai = None

# Global state
processing_status = {
    'is_processing': False,
    'current_phase': '',
    'progress': 0,
    'lane_results': [],
    'analysis_result': None
}


@app.route('/', methods=['GET'])
def home():
    """Serve the frontend dashboard"""
    return send_file('index.html')


@app.route('/styles.css', methods=['GET'])
def serve_css():
    """Serve CSS file"""
    return send_file('styles.css')


@app.route('/script.js', methods=['GET'])
def serve_js():
    """Serve JavaScript file"""
    return send_file('script.js')


@app.route('/videos/<filename>', methods=['GET'])
def serve_video(filename):
    """Serve video files"""
    import os
    video_path = os.path.join('videos', filename)
    if os.path.exists(video_path):
        return send_file(video_path, mimetype='video/mp4')
    else:
        return jsonify({'error': 'Video not found'}), 404


@app.route('/api/video-feed/<int:lane_id>', methods=['GET'])
def video_feed(lane_id):
    """Stream video feed with detection overlays for a specific lane"""
    def generate_frames(lane_id):
        """Generate frames with detection boxes"""
        video_path = Config.VIDEO_DIR / f"lane_{lane_id}.mp4"
        
        if not video_path.exists():
            return
        
        cap = cv2.VideoCapture(str(video_path))
        frame_count = 0
        last_detections = []
        lane_name = Config.LANE_NAMES[lane_id]  # Get lane name for tracker
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    # Loop video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0
                    continue
                
                frame_count += 1
                
                # Detect every 5th frame for better performance and memory
                if frame_count % 5 == 0:
                    try:
                        # Pass lane_name to maintain separate tracker state
                        last_detections = detector.detect_vehicles(frame, lane_id=lane_name)
                    except Exception as e:
                        logger.error(f"Detection error in video feed: {e}")
                        last_detections = []
                
                # Draw bounding boxes from last detection
                for det in last_detections:
                    x1, y1, x2, y2 = map(int, det[:4])
                    conf = det[4]
                    
                    # Draw box
                    color = (0, 255, 0)  # Green
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw label
                    label = f'Vehicle {conf:.2f}'
                    cv2.putText(frame, label, (x1, y1 - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Add lane info overlay
                cv2.putText(frame, f'Lane {lane_id} - {len(last_detections)} vehicles', 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 🎯 MEMORY OPTIMIZATION: Resize frame before encoding to reduce memory usage
                height, width = frame.shape[:2]
                if width > 640:
                    scale = 640 / width
                    new_width = 640
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                
                # Encode frame to JPEG with reduced quality for memory optimization
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                if not ret:
                    continue
                    
                frame_bytes = buffer.tobytes()
                
                # 🎯 Clear buffer to free memory
                del buffer
                
                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        except GeneratorExit:
            # Client disconnected, cleanup resources
            logger.info(f"Video feed {lane_id} client disconnected, cleaning up...")
        finally:
            # Always cleanup
            cap.release()
            logger.info(f"Video feed {lane_id} resources released")
    
    return Response(generate_frames(lane_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/process-videos', methods=['POST'])
def process_videos():
    """
    Process 4 traffic videos and perform complete analysis
    
    Expected request format:
    - Form data with 4 video files: video_0, video_1, video_2, video_3
    OR
    - JSON with video paths: {"videos": ["path1", "path2", "path3", "path4"]}
    """
    global detector, processing_status
    
    try:
        processing_status['is_processing'] = True
        processing_status['current_phase'] = 'Initializing'
        processing_status['progress'] = 0
        
        # Initialize detector if not already done
        if detector is None:
            logger.info("Initializing vehicle detector...")
            detector = VehicleDetector()
        
        # Get video sources
        video_paths = []
        
        # Check if videos are uploaded as files
        if request.files:
            logger.info("Processing uploaded video files")
            for i in range(4):
                file_key = f'video_{i}'
                if file_key in request.files:
                    file = request.files[file_key]
                    # Save uploaded file
                    filepath = Config.VIDEO_DIR / f"lane_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    file.save(str(filepath))
                    video_paths.append(str(filepath))
                    logger.info(f"Saved video {i} to {filepath}")
        
        # Check if video paths are provided in JSON
        elif request.json and 'videos' in request.json:
            video_paths = request.json['videos']
            logger.info(f"Using provided video paths: {video_paths}")
        
        else:
            # Look for videos in the videos directory
            video_files = list(Config.VIDEO_DIR.glob('*.mp4')) + list(Config.VIDEO_DIR.glob('*.avi'))
            if len(video_files) >= 4:
                video_paths = [str(f) for f in video_files[:4]]
                logger.info(f"Using videos from directory: {video_paths}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'Please provide 4 video files or paths',
                    'hint': 'Upload files as video_0, video_1, video_2, video_3 or provide paths in JSON'
                }), 400
        
        if len(video_paths) < 4:
            return jsonify({
                'success': False,
                'error': f'Need 4 videos, got {len(video_paths)}'
            }), 400
        
        # Process each video
        lane_results = []
        
        for idx, video_path in enumerate(video_paths[:4]):
            processing_status['current_phase'] = f'Processing Lane {idx} ({Config.LANE_NAMES[idx]})'
            processing_status['progress'] = int((idx / 4) * 80)
            
            logger.info(f"Processing video {idx}: {video_path}")
            
            if not os.path.exists(video_path):
                logger.error(f"Video not found: {video_path}")
                continue
            
            # Detect vehicles
            result = detector.process_video(video_path, lane_id=idx)
            
            if result:
                lane_results.append(result)
                logger.success(f"Lane {idx} processed successfully")
        
        if len(lane_results) < 4:
            return jsonify({
                'success': False,
                'error': f'Could not process all videos. Processed: {len(lane_results)}/4'
            }), 500
        
        # Analyze traffic
        processing_status['current_phase'] = 'Analyzing Traffic Patterns'
        processing_status['progress'] = 85
        
        analysis_result = analyzer.analyze_all_lanes(lane_results)
        
        # Update signal controller
        processing_status['current_phase'] = 'Updating Traffic Signals'
        processing_status['progress'] = 95
        
        signal_status = signal_controller.update_signals(analysis_result)
        
        # Store results
        processing_status['lane_results'] = lane_results
        processing_status['analysis_result'] = analysis_result
        processing_status['progress'] = 100
        processing_status['current_phase'] = 'Completed'
        
        logger.success("Video processing completed successfully")
        
        # Prepare response
        response = {
            'success': True,
            'message': 'Videos processed successfully',
            'timestamp': datetime.now().isoformat(),
            'lane_results': lane_results,
            'analysis': analysis_result,
            'signal_status': signal_status,
            'visualization': signal_controller.visualize_signals()
        }
        
        processing_status['is_processing'] = False
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing videos: {str(e)}")
        processing_status['is_processing'] = False
        processing_status['current_phase'] = 'Error'
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current processing status"""
    return jsonify({
        'success': True,
        'status': processing_status
    })


@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get current traffic signal states"""
    signal_status = signal_controller._get_signal_status()
    visualization = signal_controller.visualize_signals()
    
    return jsonify({
        'success': True,
        'signals': signal_status,
        'visualization': visualization,
        'statistics': signal_controller.get_statistics()
    })


@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """Get latest traffic analysis results"""
    if processing_status['analysis_result'] is None:
        # Return default/demo data instead of 404
        default_analysis = {
            'priority_ranking': [
                {
                    'rank': 1,
                    'lane_id': 1,
                    'lane_name': 'South',
                    'total_vehicles': 0,
                    'max_vehicles': 0,
                    'avg_vehicles': 0,
                    'congestion_score': 0,
                    'congestion_level': 'low',
                    'priority_score': 0,
                    'recommended_green_time': 15
                },
                {
                    'rank': 2,
                    'lane_id': 0,
                    'lane_name': 'North',
                    'total_vehicles': 0,
                    'max_vehicles': 0,
                    'avg_vehicles': 0,
                    'congestion_score': 0,
                    'congestion_level': 'low',
                    'priority_score': 0,
                    'recommended_green_time': 15
                },
                {
                    'rank': 3,
                    'lane_id': 2,
                    'lane_name': 'East',
                    'total_vehicles': 0,
                    'max_vehicles': 0,
                    'avg_vehicles': 0,
                    'congestion_score': 0,
                    'congestion_level': 'low',
                    'priority_score': 0,
                    'recommended_green_time': 15
                },
                {
                    'rank': 4,
                    'lane_id': 3,
                    'lane_name': 'West',
                    'total_vehicles': 0,
                    'max_vehicles': 0,
                    'avg_vehicles': 0,
                    'congestion_score': 0,
                    'congestion_level': 'low',
                    'priority_score': 0,
                    'recommended_green_time': 15
                }
            ],
            'signal_assignment': {
                0: 'RED',
                1: 'GREEN',
                2: 'RED',
                3: 'RED'
            },
            'recommendations': [
                'System ready - Waiting for video processing',
                'Use /api/process-videos to start detection'
            ]
        }
        
        return jsonify({
            'success': True,
            'analysis': default_analysis,
            'lane_results': [],
            'message': 'Default data - Process videos to get real analysis'
        })
    
    return jsonify({
        'success': True,
        'analysis': processing_status['analysis_result'],
        'lane_results': processing_status['lane_results']
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get signal change history"""
    limit = request.args.get('limit', 10, type=int)
    history = signal_controller.get_signal_history(limit)
    
    return jsonify({
        'success': True,
        'history': history,
        'total_records': len(signal_controller.signal_history)
    })


@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset the entire system"""
    global processing_status
    
    signal_controller.reset()
    processing_status = {
        'is_processing': False,
        'current_phase': '',
        'progress': 0,
        'lane_results': [],
        'analysis_result': None
    }
    
    logger.info("System reset completed")
    
    return jsonify({
        'success': True,
        'message': 'System reset successfully'
    })


@app.route('/api/lane/<int:lane_id>', methods=['GET'])
def get_lane_info(lane_id):
    """Get detailed information for a specific lane"""
    if lane_id < 0 or lane_id >= 4:
        return jsonify({
            'success': False,
            'error': 'Invalid lane ID. Must be 0-3'
        }), 400
    
    lane_results = processing_status.get('lane_results', [])
    
    lane_data = None
    for result in lane_results:
        if result['lane_id'] == lane_id:
            lane_data = result
            break
    
    if lane_data is None:
        return jsonify({
            'success': False,
            'message': f'No data available for lane {lane_id}'
        }), 404
    
    return jsonify({
        'success': True,
        'lane_id': lane_id,
        'lane_name': Config.LANE_NAMES[lane_id],
        'data': lane_data,
        'current_signal': signal_controller.get_lane_signal(lane_id)
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'video_dir': str(Config.VIDEO_DIR),
        'model': Config.MODEL_NAME,
        'detector_ready': detector is not None,
        'analyzer_ready': analyzer is not None,
        'gemini_ai_ready': gemini_ai is not None
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@app.route('/api/start-live-detection', methods=['POST'])
def start_live_detection():
    """Start continuous live detection from video files"""
    global detector, processing_status
    
    try:
        if processing_status['is_processing']:
            return jsonify({
                'success': False,
                'message': 'Detection already running'
            }), 400
        
        processing_status['is_processing'] = True
        processing_status['current_phase'] = 'Initializing Live Detection'
        
        # Initialize detector if not already done
        if detector is None:
            logger.info("Initializing YOLOv8 detector...")
            try:
                detector = VehicleDetector()
            except Exception as e:
                logger.error(f"Failed to initialize detector: {e}")
                processing_status['is_processing'] = False
                return jsonify({
                    'success': False,
                    'message': f'Failed to initialize detector: {str(e)}'
                }), 500
        
        # Start background thread for continuous processing
        import threading
        
        def process_videos_continuously():
            """Process videos in loop and update global state"""
            global processing_status
            
            logger.info("🎬 Background detection thread STARTED!")
            
            video_paths = [
                Config.VIDEO_DIR / "lane_0.mp4",
                Config.VIDEO_DIR / "lane_1.mp4",
                Config.VIDEO_DIR / "lane_2.mp4",
                Config.VIDEO_DIR / "lane_3.mp4"
            ]
            
            logger.info(f"📹 Opening video captures from: {Config.VIDEO_DIR}")
            
            # Open all video captures
            caps = [cv2.VideoCapture(str(path)) for path in video_paths]
            
            # 🔍 DEBUG: Check if all captures opened successfully
            for i, cap in enumerate(caps):
                if cap.isOpened():
                    logger.info(f"✅ Lane {i} video opened: {video_paths[i].name}")
                else:
                    logger.error(f"❌ Lane {i} video FAILED to open: {video_paths[i]}")
            
            frame_count = 0
            lane_vehicle_counts = [[] for _ in range(4)]
            skip_frames = 3  # Process every 3rd frame for faster updates
            
            logger.info(f"🔄 Starting detection loop with skip_frames={skip_frames}")
            logger.info("⚡ FAST MODE: Processing frames every 3rd frame for quick updates!")
            
            while processing_status['is_processing']:
                frames = []
                all_ended = True
                
                # Read one frame from each video
                for cap in caps:
                    ret, frame = cap.read()
                    if ret:
                        all_ended = False
                        frames.append(frame)
                    else:
                        # Loop video if it ends
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        frames.append(frame if ret else None)
                
                frame_count += 1
                
                # ⚡ SKIP FRAMES FOR SPEED - Only process every 3rd frame
                if frame_count % skip_frames != 0:
                    import time
                    time.sleep(0.01)  # Minimal delay
                    continue
                
                # Process detections for this frame
                current_vehicles = []
                
                for i, frame in enumerate(frames):
                    if frame is not None:
                        # Pass lane_id to maintain separate tracking state per lane
                        lane_name = Config.LANE_NAMES[i]
                        detections = detector.detect_vehicles(frame, lane_id=lane_name)
                        vehicle_count = len(detections)
                        lane_vehicle_counts[i].append(vehicle_count)
                        
                        # Log detection result every 10th processed frame
                        if frame_count % 30 == 0:
                            logger.info(f"Lane {Config.LANE_NAMES[i]}: Detected {vehicle_count} vehicles (frame {frame_count})")
                        
                        current_vehicles.append({
                            'lane_id': i,
                            'count': vehicle_count,
                            'detections': detections
                        })
                    else:
                        current_vehicles.append({'lane_id': i, 'count': 0, 'detections': []})
                
                # Keep only last 30 frames of data
                for i in range(4):
                    if len(lane_vehicle_counts[i]) > 30:
                        lane_vehicle_counts[i].pop(0)
                
                # Update lane results
                lane_results = []
                for i in range(4):
                    if lane_vehicle_counts[i]:
                        counts = lane_vehicle_counts[i]
                        total = sum(counts)
                        avg = total / len(counts)
                        max_vehicles = max(counts)
                        current_count = counts[-1] if counts else 0
                        
                        # ✅ IMPROVED: Realistic congestion score calculation
                        # Use current count as primary metric (realistic traffic measure)
                        # Formula: current_vehicles + (avg * 2) + (max * 0.5)
                        congestion_score = current_count + (avg * 2) + (max_vehicles * 0.5)
                        
                        result = {
                            'lane_id': i,
                            'lane_name': Config.LANE_NAMES[i],
                            'total_vehicles': total,
                            'current_vehicles': current_count,
                            'avg_vehicles_per_frame': round(avg, 2),
                            'max_vehicles_in_frame': max_vehicles,
                            'congestion_score': round(congestion_score, 2),
                            'vehicle_counts': {'car': 0}  # Simplified
                        }
                        lane_results.append(result)
                
                # Analyze and update signals
                if lane_results:
                    analysis = analyzer.analyze_all_lanes(lane_results)
                    signal_status = signal_controller.update_signals(analysis)
                    
                    # Store in global state
                    processing_status['lane_results'] = lane_results
                    processing_status['analysis_result'] = analysis
                    processing_status['signal_status'] = signal_status
                
                # ⚡ Optimized delay - 0.2 second for faster response
                import time
                time.sleep(0.2)
            
            # Cleanup
            for cap in caps:
                cap.release()
            
            logger.info("Live detection stopped")
        
        # Start background thread
        detection_thread = threading.Thread(target=process_videos_continuously, daemon=True)
        detection_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Live detection started',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error starting live detection: {str(e)}")
        processing_status['is_processing'] = False
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stop-live-detection', methods=['POST'])
def stop_live_detection():
    """Stop continuous live detection"""
    global processing_status
    
    processing_status['is_processing'] = False
    processing_status['current_phase'] = 'Stopped'
    
    return jsonify({
        'success': True,
        'message': 'Live detection stopped'
    })


@app.route('/api/emergency-mode', methods=['POST'])
def emergency_mode():
    """Activate emergency mode for specific lane"""
    try:
        data = request.get_json()
        lane_id = data.get('lane_id')
        
        if lane_id is None or lane_id not in [0, 1, 2, 3]:
            return jsonify({
                'success': False,
                'error': 'Invalid lane_id. Must be 0-3'
            }), 400
        
        # Force emergency signal override
        emergency_signals = {}
        lane_names = ['North', 'South', 'East', 'West']
        
        for i, name in enumerate(lane_names):
            if i == lane_id:
                emergency_signals[name] = {
                    'state': 'GREEN',
                    'time_remaining': 999,
                    'emergency': True
                }
            else:
                emergency_signals[name] = {
                    'state': 'RED',
                    'time_remaining': 999,
                    'emergency': True
                }
        
        logger.warning(f"🚨 EMERGENCY MODE: Lane {lane_names[lane_id]} set to GREEN")
        
        return jsonify({
            'success': True,
            'message': f'Emergency mode activated for {lane_names[lane_id]} lane',
            'signals': emergency_signals
        })
        
    except Exception as e:
        logger.error(f"Emergency mode error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/manual-mode', methods=['POST'])
def manual_mode():
    """Switch to manual cyclic mode"""
    try:
        # Stop AI detection
        global processing_status
        processing_status['is_processing'] = False
        
        logger.info("⚙️ Manual mode activated - Cyclic signal control")
        
        return jsonify({
            'success': True,
            'message': 'Manual mode activated',
            'mode': 'manual'
        })
        
    except Exception as e:
        logger.error(f"Manual mode error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/live-data', methods=['GET'])
def get_live_data():
    """Get current live detection data"""
    
    if not processing_status['lane_results']:
        # Return empty state
        return jsonify({
            'success': True,
            'is_running': processing_status['is_processing'],
            'lanes': [
                {'lane_id': 0, 'lane_name': 'North', 'current_vehicles': 0, 'wait_time': 0, 'density': 0, 'signal': 'RED'},
                {'lane_id': 1, 'lane_name': 'South', 'current_vehicles': 0, 'wait_time': 0, 'density': 0, 'signal': 'GREEN'},
                {'lane_id': 2, 'lane_name': 'East', 'current_vehicles': 0, 'wait_time': 0, 'density': 0, 'signal': 'RED'},
                {'lane_id': 3, 'lane_name': 'West', 'current_vehicles': 0, 'wait_time': 0, 'density': 0, 'signal': 'RED'}
            ]
        })
    
    # Get current signal status
    signal_status = signal_controller._get_signal_status()
    signals = signal_status.get('signals', {})
    
    # Prepare live data for each lane
    lanes_data = []
    for lane_result in processing_status['lane_results']:
        lane_id = lane_result['lane_id']
        lane_name = lane_result['lane_name']
        
        # Get signal info
        signal_info = signals.get(lane_name, {})
        signal_state = signal_info.get('state', 'RED')
        time_remaining = signal_info.get('time_remaining', 0)
        
        # ✅ IMPROVED: Realistic density percentage based on vehicle count
        # Low: 0-15 vehicles (0-25%), Medium: 16-35 (25-60%), High: 36-60 (60-85%), Critical: 60+ (85-100%)
        current_vehicles = lane_result.get('current_vehicles', 0)
        
        # 🔍 DEBUG: Log vehicle count
        logger.debug(f"Lane {lane_name}: {current_vehicles} vehicles detected")
        
        if current_vehicles <= Config.LOW_CONGESTION:
            density_percent = int((current_vehicles / Config.LOW_CONGESTION) * 25)
        elif current_vehicles <= Config.MEDIUM_CONGESTION:
            density_percent = 25 + int(((current_vehicles - Config.LOW_CONGESTION) / 
                                        (Config.MEDIUM_CONGESTION - Config.LOW_CONGESTION)) * 35)
        elif current_vehicles <= Config.HIGH_CONGESTION:
            density_percent = 60 + int(((current_vehicles - Config.MEDIUM_CONGESTION) / 
                                        (Config.HIGH_CONGESTION - Config.MEDIUM_CONGESTION)) * 25)
        else:
            density_percent = min(100, 85 + int(((current_vehicles - Config.HIGH_CONGESTION) / 40) * 15))
        
        lanes_data.append({
            'lane_id': lane_id,
            'lane_name': lane_name,
            'current_vehicles': current_vehicles,
            'wait_time': int(time_remaining),
            'density': density_percent,
            'signal': signal_state,
            'congestion_level': 'high' if density_percent > 60 else 'medium' if density_percent > 25 else 'low'
        })
    
    return jsonify({
        'success': True,
        'is_running': processing_status['is_processing'],
        'lanes': lanes_data,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/ai-decisions', methods=['GET'])
def get_ai_decisions():
    """Get AI decision engine recommendations powered by Gemini AI"""
    
    if not processing_status['lane_results']:
        # Default state when no processing
        return jsonify({
            'success': True,
            'decision': {
                'action': 'Monitoring traffic conditions',
                'reason': 'System ready - waiting for data',
                'detailed_analysis': 'Traffic detection system initializing. Cameras active and monitoring all lanes.',
                'impact_prediction': 'N/A - No active traffic',
                'confidence': 0,
                'priority_level': 'LOW',
                'alternative_action': 'Continue monitoring all lanes',
                'risk_factors': 'None - System in standby mode',
                'ai_powered': False
            },
            'timestamp': datetime.now().isoformat()
        })
    
    # Prepare traffic data for Gemini AI
    lanes = processing_status['lane_results']
    signal_status = signal_controller._get_signal_status()
    signals = signal_status.get('signals', {})
    
    # Format data for AI
    traffic_data = {
        'current_time': datetime.now().strftime('%I:%M %p'),
        'lanes': [],
        'total_vehicles': 0
    }
    
    for lane in lanes:
        lane_name = lane.get('lane_name', 'Unknown')
        vehicles = lane.get('current_vehicles', 0)
        signal_info = signals.get(lane_name, {})
        
        traffic_data['lanes'].append({
            'name': lane_name,
            'current_vehicles': vehicles,
            'signal_state': signal_info.get('state', 'RED'),
            'time_remaining': signal_info.get('time_remaining', 0),
            'congestion_level': lane.get('congestion_level', 'unknown')
        })
        traffic_data['total_vehicles'] += vehicles
    
    # Use Gemini AI if available, otherwise fallback
    if gemini_ai:
        try:
            # FIX: Added frame_width and frame_height arguments
            frame_width, frame_height = 640, 480  # Standard dimensions
            ai_decision = gemini_ai.analyze_traffic_decision(traffic_data, frame_width, frame_height)
            logger.info(f"🤖 Gemini AI: {ai_decision.get('action')}")
        except Exception as e:
            logger.error(f"Gemini AI failed: {e}. Using fallback.")
            ai_decision = _fallback_decision_logic(traffic_data, lanes, signals)
    else:
        ai_decision = _fallback_decision_logic(traffic_data, lanes, signals)
    
    return jsonify({
        'success': True,
        'decision': ai_decision,
        'timestamp': datetime.now().isoformat()
    })


def _fallback_decision_logic(traffic_data, lanes, signals):
    """Fallback rule-based logic when AI is unavailable"""
    # Find lane with highest congestion
    max_vehicles = 0
    critical_lane = None
    for lane in lanes:
        if lane.get('current_vehicles', 0) > max_vehicles:
            max_vehicles = lane.get('current_vehicles', 0)
            critical_lane = lane
    
    if not critical_lane:
        return {
            'action': 'Normal operation',
            'reason': 'Traffic levels optimal',
            'detailed_analysis': 'All lanes showing balanced traffic distribution. No intervention required.',
            'impact_prediction': 'Minimal delay across all lanes',
            'confidence': 85,
            'priority_level': 'LOW',
            'alternative_action': 'Continue standard signal timing',
            'risk_factors': 'None detected',
            'ai_powered': False
        }
    
    lane_name = critical_lane.get('lane_name', 'Unknown')
    current_vehicles = critical_lane.get('current_vehicles', 0)
    
    # Calculate density percentage
    if current_vehicles <= Config.LOW_CONGESTION:
        density_percent = int((current_vehicles / Config.LOW_CONGESTION) * 25)
        congestion_level = "low"
    elif current_vehicles <= Config.MEDIUM_CONGESTION:
        density_percent = 25 + int(((current_vehicles - Config.LOW_CONGESTION) / 
                                    (Config.MEDIUM_CONGESTION - Config.LOW_CONGESTION)) * 35)
        congestion_level = "medium"
    elif current_vehicles <= Config.HIGH_CONGESTION:
        density_percent = 60 + int(((current_vehicles - Config.MEDIUM_CONGESTION) / 
                                    (Config.HIGH_CONGESTION - Config.MEDIUM_CONGESTION)) * 25)
        congestion_level = "high"
    else:
        density_percent = min(100, 85 + int(((current_vehicles - Config.HIGH_CONGESTION) / 40) * 15))
        congestion_level = "critical"
    
    # Get current signal state for this lane
    lane_signal_info = signals.get(lane_name, {})
    current_signal = lane_signal_info.get('state', 'RED')
    time_remaining = lane_signal_info.get('time_remaining', 0)
    
    # Enhanced decision logic
    if congestion_level == "critical" and current_signal == "RED":
        action = f"🚨 CRITICAL: Prioritize {lane_name} - Immediate GREEN Signal"
        reason = f"Critical congestion detected: {current_vehicles} vehicles ({density_percent}% density)"
        detailed_analysis = f"{lane_name} lane experiencing severe congestion. Current wait time estimated at {int(current_vehicles * 2.5)} seconds. Immediate intervention required to prevent gridlock."
        impact_prediction = f"Expected to clear {int(current_vehicles * 0.40)} vehicles in 60 seconds. Delay reduction: {min(45, int(density_percent * 0.5))}%"
        confidence = min(95, 75 + int(density_percent / 5))
        priority = "CRITICAL"
        alternative = f"If immediate GREEN not possible, extend next cycle by 45 seconds for {lane_name}"
        risks = f"Risk of spillover to adjacent lanes if not addressed within 90 seconds. Monitor {lane_name} closely."
        
    elif congestion_level == "high" and current_signal == "GREEN":
        extension_time = 25 if current_vehicles > 50 else 15
        action = f"⚠️ Extend {lane_name} GREEN Signal +{extension_time}s"
        reason = f"High density: {current_vehicles} vehicles ({density_percent}% capacity)"
        detailed_analysis = f"{lane_name} currently processing traffic but requires additional time. Extension will optimize throughput and prevent secondary congestion."
        impact_prediction = f"Additional {int(current_vehicles * 0.35)} vehicles cleared. Total delay reduction: {min(35, int(density_percent * 0.35))}%"
        confidence = min(92, 70 + int(density_percent / 4))
        priority = "HIGH"
        alternative = f"Alternative: Maintain current timing and queue for extended next cycle"
        risks = "Moderate risk of residual congestion if cut short. Extension recommended."
        
    elif congestion_level == "high" and current_signal == "RED":
        action = f"📋 Queue {lane_name} for Priority GREEN Cycle"
        reason = f"High vehicle count detected: {current_vehicles} vehicles ({density_percent}%)"
        detailed_analysis = f"{lane_name} showing significant buildup while on RED. Queuing for next available GREEN cycle with extended duration to clear backlog efficiently."
        impact_prediction = f"Expected clearance: {int(current_vehicles * 0.30)} vehicles in next cycle. Delay reduction: {min(30, int(density_percent * 0.3))}%"
        confidence = min(88, 65 + int(density_percent / 3))
        priority = "HIGH"
        alternative = f"Monitor for critical threshold. If exceeds {Config.HIGH_CONGESTION + 10} vehicles, escalate to immediate priority."
        risks = f"Wait time currently at {time_remaining}s. Risk increases if other lanes also congest."
        
    elif congestion_level == "medium" and current_signal == "GREEN":
        action = f"✅ Maintain {lane_name} Standard Timing"
        reason = f"Moderate traffic flow: {current_vehicles} vehicles ({density_percent}%)"
        detailed_analysis = f"{lane_name} operating within normal parameters. Current GREEN signal efficiently processing traffic. No intervention required."
        impact_prediction = f"Steady clearance rate: {int(current_vehicles * 0.25)} vehicles per cycle. Delay reduction: 15%"
        confidence = 78
        priority = "MEDIUM"
        alternative = "Continue monitoring. Ready to extend if density increases above 70%."
        risks = "Low risk. Traffic flow stable and predictable."
        
    else:
        action = f"🟢 Normal Operation - {lane_name} Balanced"
        reason = f"Optimal traffic density: {current_vehicles} vehicles ({density_percent}%)"
        detailed_analysis = f"All lanes showing balanced distribution. {lane_name} currently has highest count but well within optimal range. Standard signal timing is effective."
        impact_prediction = f"Minimal delay expected. Current throughput: {int(current_vehicles * 0.20)} vehicles per cycle."
        confidence = 85
        priority = "LOW"
        alternative = "Maintain current pattern. System operating at peak efficiency."
        risks = "None. Traffic conditions optimal for current time period."
    
    return {
        'action': action,
        'reason': reason,
        'detailed_analysis': detailed_analysis,
        'impact_prediction': impact_prediction,
        'confidence': confidence,
        'priority_level': priority,
        'alternative_action': alternative,
        'risk_factors': risks,
        'ai_powered': False,
        'lane': lane_name,
        'vehicles': current_vehicles,
        'density': density_percent
    }


@app.route('/api/traffic-prediction', methods=['GET'])
def get_traffic_prediction():
    """Get 30-minute traffic flow prediction based on historical data"""
    from datetime import timedelta
    
    if not processing_status['lane_results']:
        # Default prediction data
        now = datetime.now()
        default_predictions = []
        for i in range(7):
            default_predictions.append({
                'time': (now + timedelta(minutes=i*5)).strftime('%H:%M'),
                'vehicles': 0,
                'prediction': 0
            })
        
        return jsonify({
            'success': True,
            'predictions': default_predictions,
            'trend': 'stable',
            'peak_time': 'N/A',
            'message': 'Waiting for historical data'
        })
    
    # Get historical data from signal controller
    history = signal_controller.get_signal_history(limit=30)
    
    # Calculate average vehicles across all lanes over time
    now = datetime.now()
    predictions = []
    
    # Get current average
    current_avg = sum(lane.get('current_vehicles', 0) for lane in processing_status['lane_results']) / len(processing_status['lane_results'])
    
    # Generate predictions for next 30 minutes (7 data points, every 5 min)
    for i in range(7):
        future_time = now + timedelta(minutes=i*5)
        
        # Simple prediction model:
        # - Current traffic as base
        # - Add slight variation based on time of day
        # - Simulate realistic traffic patterns
        
        hour = future_time.hour
        minute = future_time.minute
        
        # Peak hours: 8-10 AM, 5-7 PM (higher traffic)
        # Off-peak: 12-2 PM, 10 PM - 6 AM (lower traffic)
        if (8 <= hour < 10) or (17 <= hour < 19):
            # Peak hour - increase traffic
            multiplier = 1.2 + (i * 0.05)  # Gradual increase
        elif (12 <= hour < 14) or (22 <= hour or hour < 6):
            # Off-peak - decrease traffic
            multiplier = 0.8 - (i * 0.03)  # Gradual decrease
        else:
            # Normal hours - stable with slight variation
            multiplier = 1.0 + (i * 0.02)
        
        predicted_vehicles = int(current_avg * multiplier)
        predicted_vehicles = max(5, min(100, predicted_vehicles))  # Keep realistic (5-100)
        
        predictions.append({
            'time': future_time.strftime('%I:%M %p'),  # 12-hour format
            'vehicles': int(current_avg) if i == 0 else predicted_vehicles,
            'prediction': predicted_vehicles
        })
    
    # Determine trend
    if predictions[-1]['prediction'] > predictions[0]['vehicles'] * 1.15:
        trend = 'increasing'
    elif predictions[-1]['prediction'] < predictions[0]['vehicles'] * 0.85:
        trend = 'decreasing'
    else:
        trend = 'stable'
    
    # Find peak time
    peak_idx = max(range(len(predictions)), key=lambda i: predictions[i]['prediction'])
    peak_time = predictions[peak_idx]['time']
    
    return jsonify({
        'success': True,
        'predictions': predictions,
        'trend': trend,
        'peak_time': peak_time,
        'current_avg': int(current_avg),
        'timestamp': datetime.now().isoformat()
    })
# ============================================
# Gunicorn Entry Point
# This runs when the app is imported by Gunicorn
# ============================================
# Initialize startup message when app is loaded
logger.info("="*60)
logger.info("🚦 Advanced Traffic Management System Backend")
logger.info("="*60)
logger.info(f"Video Directory: {Config.VIDEO_DIR}")
logger.info(f"Output Directory: {Config.OUTPUT_DIR}")
logger.info(f"Model: {Config.MODEL_NAME}")
logger.info(f"Confidence Threshold: {Config.CONFIDENCE_THRESHOLD}")
logger.info("="*60)
logger.info("✅ Flask app ready for Gunicorn")


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚦 Advanced Traffic Management System Backend")
    logger.info("="*60)
    logger.info(f"Video Directory: {Config.VIDEO_DIR}")
    logger.info(f"Output Directory: {Config.OUTPUT_DIR}")
    logger.info(f"Model: {Config.MODEL_NAME}")
    logger.info(f"Confidence Threshold: {Config.CONFIDENCE_THRESHOLD}")
    logger.info("="*60)
    
    # 🚀 AUTO-START LIVE DETECTION
    import threading
    def auto_start_detection():
        """Auto-start detection after 2 seconds"""
        import time
        time.sleep(2)
        logger.info("🔥 AUTO-STARTING LIVE DETECTION...")
        processing_status['is_processing'] = True
        
        # Start detection thread
        def process_videos_continuously():
            """Process videos in loop and update global state"""
            global processing_status
            
            logger.info("🎬 AUTO-DETECTION thread STARTED!")
            
            video_paths = [
                Config.VIDEO_DIR / "lane_0.mp4",
                Config.VIDEO_DIR / "lane_1.mp4",
                Config.VIDEO_DIR / "lane_2.mp4",
                Config.VIDEO_DIR / "lane_3.mp4"
            ]
            
            logger.info(f"📹 Opening video captures from: {Config.VIDEO_DIR}")
            
            # Open all video captures
            caps = [cv2.VideoCapture(str(path)) for path in video_paths]
            
            for i, cap in enumerate(caps):
                if cap.isOpened():
                    logger.info(f"✅ Lane {i} video opened: {video_paths[i].name}")
                else:
                    logger.error(f"❌ Lane {i} video FAILED to open: {video_paths[i]}")
            
            frame_count = 0
            lane_vehicle_counts = [[] for _ in range(4)]
            skip_frames = 3
            
            logger.info(f"🔄 Starting detection loop with skip_frames={skip_frames}")
            logger.info("⚡ FAST MODE: Processing every 3rd frame!")
            
            while processing_status['is_processing']:
                frames = []
                
                for cap in caps:
                    ret, frame = cap.read()
                    if ret:
                        frames.append(frame)
                    else:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        frames.append(frame if ret else None)
                
                frame_count += 1
                
                if frame_count % skip_frames != 0:
                    import time
                    time.sleep(0.01)
                    continue
                
                current_vehicles = []
                
                for i, frame in enumerate(frames):
                    if frame is not None:
                        lane_name = Config.LANE_NAMES[i]
                        detections = detector.detect_vehicles(frame, lane_id=lane_name)
                        vehicle_count = len(detections)
                        lane_vehicle_counts[i].append(vehicle_count)
                        
                        if frame_count % 30 == 0:
                            logger.info(f"Lane {Config.LANE_NAMES[i]}: Detected {vehicle_count} vehicles (frame {frame_count})")
                        
                        current_vehicles.append({
                            'lane_id': i,
                            'count': vehicle_count,
                            'detections': detections
                        })
                    else:
                        current_vehicles.append({'lane_id': i, 'count': 0, 'detections': []})
                
                for i in range(4):
                    if len(lane_vehicle_counts[i]) > 30:
                        lane_vehicle_counts[i].pop(0)
                
                lane_results = []
                for i in range(4):
                    if lane_vehicle_counts[i]:
                        counts = lane_vehicle_counts[i]
                        total = sum(counts)
                        avg = total / len(counts)
                        max_vehicles = max(counts)
                        current_count = counts[-1] if counts else 0
                        
                        congestion_score = current_count + (avg * 2) + (max_vehicles * 0.5)
                        
                        result = {
                            'lane_id': i,
                            'lane_name': Config.LANE_NAMES[i],
                            'total_vehicles': total,
                            'current_vehicles': current_count,
                            'avg_vehicles_per_frame': round(avg, 2),
                            'max_vehicles_in_frame': max_vehicles,
                            'congestion_score': round(congestion_score, 2),
                            'vehicle_counts': {'car': 0}
                        }
                        lane_results.append(result)
                
                if lane_results:
                    analysis = analyzer.analyze_all_lanes(lane_results)
                    signal_status = signal_controller.update_signals(analysis)
                    
                    processing_status['lane_results'] = lane_results
                    processing_status['analysis_result'] = analysis
                    processing_status['signal_status'] = signal_status
                
                import time
                time.sleep(0.2)
            
            for cap in caps:
                cap.release()
            
            logger.info("Auto-detection stopped")
        
        detection_thread = threading.Thread(target=process_videos_continuously, daemon=True)
        detection_thread.start()
        logger.success("✅ LIVE DETECTION AUTO-STARTED!")
    
    auto_thread = threading.Thread(target=auto_start_detection, daemon=True)
    auto_thread.start()
    
    # 🎯 OPTIMIZED SERVER CONFIG: Better memory handling
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True,  # Enable threading for better concurrent request handling
        request_handler=None  # Use default handler with automatic cleanup
    )

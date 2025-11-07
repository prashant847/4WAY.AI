"""
Traffic Analyzer Module
Analyzes traffic density and determines optimal signal timing
"""
import numpy as np
from typing import List, Dict, Tuple
from loguru import logger
from config import Config


class TrafficAnalyzer:
    """Analyzes traffic patterns and congestion across multiple lanes"""
    
    def __init__(self):
        """Initialize traffic analyzer"""
        self.lane_data = {}
        self.history = []
        
    def analyze_all_lanes(self, lane_results: List[Dict]) -> Dict:
        """
        Analyze traffic across all lanes and determine priorities
        
        Args:
            lane_results: List of detection results from all lanes
            
        Returns:
            Analysis results with lane priorities and recommendations
        """
        if not lane_results or len(lane_results) == 0:
            logger.warning("No lane data provided for analysis")
            return None
        
        logger.info(f"Analyzing traffic for {len(lane_results)} lanes")
        
        # Store lane data
        for result in lane_results:
            lane_id = result['lane_id']
            self.lane_data[lane_id] = result
        
        # Calculate priority scores
        priority_scores = self._calculate_priorities(lane_results)
        
        # Determine signal assignments
        signal_assignment = self._assign_signals(priority_scores)
        
        # Calculate recommended green time
        green_times = self._calculate_green_times(priority_scores)
        
        # Generate analysis report
        analysis = {
            'timestamp': self._get_timestamp(),
            'total_lanes': len(lane_results),
            'lane_statistics': self._generate_lane_statistics(lane_results),
            'priority_ranking': priority_scores,
            'signal_assignment': signal_assignment,
            'recommended_green_times': green_times,
            'congestion_summary': self._generate_congestion_summary(lane_results),
            'recommendations': self._generate_recommendations(lane_results, priority_scores)
        }
        
        # Store in history
        self.history.append(analysis)
        
        logger.success("Traffic analysis completed")
        
        return analysis
    
    def _calculate_priorities(self, lane_results: List[Dict]) -> List[Dict]:
        """
        Calculate priority scores for each lane
        
        Args:
            lane_results: Results from all lanes
            
        Returns:
            Sorted list of lanes by priority
        """
        priorities = []
        
        for result in lane_results:
            # Multiple factors for priority calculation
            congestion_score = result.get('congestion_score', 0)
            total_vehicles = result.get('total_vehicles', 0)
            max_vehicles = result.get('max_vehicles_in_frame', 0)
            avg_vehicles = result.get('avg_vehicles_per_frame', 0)
            
            # Heavy vehicle count (buses and trucks get more weight)
            vehicle_counts = result.get('vehicle_counts', {})
            heavy_vehicles = vehicle_counts.get('bus', 0) + vehicle_counts.get('truck', 0)
            
            # Calculate composite priority score
            # 50% congestion, 20% total vehicles, 15% max vehicles, 10% heavy vehicles, 5% average
            priority_score = (
                congestion_score * 0.50 +
                min(total_vehicles / 10, 20) * 0.20 +
                max_vehicles * 2 * 0.15 +
                heavy_vehicles * 1.5 * 0.10 +
                avg_vehicles * 5 * 0.05
            )
            
            priorities.append({
                'lane_id': result['lane_id'],
                'lane_name': result['lane_name'],
                'priority_score': round(priority_score, 2),
                'congestion_score': congestion_score,
                'total_vehicles': total_vehicles,
                'max_vehicles_in_frame': max_vehicles,
                'heavy_vehicles': heavy_vehicles,
                'congestion_level': self._get_congestion_level(congestion_score)
            })
        
        # Sort by priority score (highest first)
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Add rank
        for idx, priority in enumerate(priorities):
            priority['rank'] = idx + 1
        
        return priorities
    
    def _assign_signals(self, priorities: List[Dict]) -> Dict[int, str]:
        """
        Assign traffic signals based on priorities
        Highest priority gets GREEN, others get RED
        
        Args:
            priorities: Sorted priority list
            
        Returns:
            Dictionary mapping lane_id to signal color
        """
        signals = {}
        
        if not priorities:
            return signals
        
        # Assign GREEN to highest priority lane
        highest_priority = priorities[0]
        signals[highest_priority['lane_id']] = 'GREEN'
        
        # All others get RED
        for priority in priorities[1:]:
            signals[priority['lane_id']] = 'RED'
        
        logger.info(f"Signal assignment: Lane {highest_priority['lane_name']} -> GREEN")
        
        return signals
    
    def _calculate_green_times(self, priorities: List[Dict]) -> Dict[int, int]:
        """
        Calculate recommended green light duration for each lane
        
        Args:
            priorities: Priority scores for lanes
            
        Returns:
            Dictionary mapping lane_id to recommended green time (seconds)
        """
        green_times = {}
        
        for priority in priorities:
            lane_id = priority['lane_id']
            score = priority['priority_score']
            
            # Scale green time based on priority score
            # Higher score = longer green time
            if score >= 50:
                green_time = Config.MAX_GREEN_TIME
            elif score >= 30:
                green_time = int(Config.MAX_GREEN_TIME * 0.75)
            elif score >= 15:
                green_time = int(Config.MAX_GREEN_TIME * 0.50)
            else:
                green_time = Config.MIN_GREEN_TIME
            
            green_times[lane_id] = green_time
        
        return green_times
    
    def _generate_lane_statistics(self, lane_results: List[Dict]) -> Dict:
        """Generate comprehensive statistics for all lanes"""
        total_vehicles_all_lanes = sum(r.get('total_vehicles', 0) for r in lane_results)
        avg_congestion = np.mean([r.get('congestion_score', 0) for r in lane_results])
        
        # Vehicle type distribution across all lanes
        all_vehicle_counts = {}
        for result in lane_results:
            for vtype, count in result.get('vehicle_counts', {}).items():
                all_vehicle_counts[vtype] = all_vehicle_counts.get(vtype, 0) + count
        
        return {
            'total_vehicles_all_lanes': total_vehicles_all_lanes,
            'average_congestion_score': round(avg_congestion, 2),
            'vehicle_type_distribution': all_vehicle_counts,
            'most_congested_lane': max(lane_results, key=lambda x: x.get('congestion_score', 0))['lane_name'],
            'least_congested_lane': min(lane_results, key=lambda x: x.get('congestion_score', 0))['lane_name']
        }
    
    def _generate_congestion_summary(self, lane_results: List[Dict]) -> Dict:
        """Generate congestion level summary"""
        levels = {'VERY_LOW': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        
        for result in lane_results:
            level = self._get_congestion_level(result.get('congestion_score', 0))
            levels[level] += 1
        
        return levels
    
    def _get_congestion_level(self, score: float) -> str:
        """Convert congestion score to level with realistic thresholds"""
        if score >= Config.CRITICAL_CONGESTION:
            return 'CRITICAL'
        elif score >= Config.HIGH_CONGESTION:
            return 'HIGH'
        elif score >= Config.MEDIUM_CONGESTION:
            return 'MEDIUM'
        elif score >= Config.LOW_CONGESTION:
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    def _generate_recommendations(self, lane_results: List[Dict], priorities: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check for critical congestion
        critical_lanes = [p for p in priorities if p['congestion_level'] == 'CRITICAL']
        if critical_lanes:
            recommendations.append(
                f"⚠️ CRITICAL: {len(critical_lanes)} lane(s) with critical congestion - "
                f"Consider extended green times or traffic rerouting"
            )
        
        # Check for imbalanced traffic
        scores = [p['priority_score'] for p in priorities]
        if len(scores) > 1:
            score_diff = max(scores) - min(scores)
            if score_diff > 40:
                recommendations.append(
                    f"⚠️ High traffic imbalance detected (score difference: {score_diff:.1f}) - "
                    f"Implement adaptive signal timing"
                )
        
        # Check for heavy vehicle presence
        total_heavy = sum(p['heavy_vehicles'] for p in priorities)
        if total_heavy > 10:
            recommendations.append(
                f"🚛 {total_heavy} heavy vehicles detected - "
                f"Consider dedicated lanes or priority signals"
            )
        
        # General recommendation
        highest_lane = priorities[0]['lane_name']
        recommendations.append(
            f"✅ Prioritize {highest_lane} lane with GREEN signal "
            f"(Score: {priorities[0]['priority_score']:.1f})"
        )
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_signal_cycle_plan(self, lane_results: List[Dict]) -> List[Dict]:
        """
        Generate a complete signal cycle plan for all lanes
        
        Args:
            lane_results: Detection results for all lanes
            
        Returns:
            List of signal phases with timing
        """
        priorities = self._calculate_priorities(lane_results)
        green_times = self._calculate_green_times(priorities)
        
        cycle_plan = []
        
        for priority in priorities:
            lane_id = priority['lane_id']
            lane_name = priority['lane_name']
            
            phase = {
                'lane_id': lane_id,
                'lane_name': lane_name,
                'rank': priority['rank'],
                'green_time': green_times[lane_id],
                'yellow_time': Config.YELLOW_TIME,
                'all_red_time': Config.ALL_RED_TIME,
                'total_phase_time': green_times[lane_id] + Config.YELLOW_TIME + Config.ALL_RED_TIME,
                'congestion_level': priority['congestion_level'],
                'priority_score': priority['priority_score']
            }
            
            cycle_plan.append(phase)
        
        # Calculate total cycle time
        total_cycle_time = sum(phase['total_phase_time'] for phase in cycle_plan)
        
        logger.info(f"Generated signal cycle plan: {len(cycle_plan)} phases, "
                   f"total cycle time: {total_cycle_time}s")
        
        return cycle_plan

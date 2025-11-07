"""
Traffic Signal Controller
Manages traffic light states and timing based on real-time analysis
"""
import time
from typing import Dict, List
from enum import Enum
from datetime import datetime, timedelta
from loguru import logger
from config import Config


class SignalState(Enum):
    """Traffic signal states"""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    ALL_RED = "ALL_RED"


class TrafficSignalController:
    """Controls traffic signals based on real-time traffic analysis"""
    
    def __init__(self):
        """Initialize traffic signal controller"""
        self.num_lanes = 4
        self.current_signals = {i: SignalState.RED for i in range(self.num_lanes)}
        self.current_green_lane = None
        self.signal_history = []
        self.cycle_count = 0
        self.start_time = None
        self.phase_start_time = None
        
        logger.info("Traffic Signal Controller initialized")
    
    def update_signals(self, analysis_result: Dict) -> Dict:
        """
        Update signal states based on traffic analysis
        
        Args:
            analysis_result: Analysis results from TrafficAnalyzer
            
        Returns:
            Current signal states and timing information
        """
        if not analysis_result:
            logger.warning("No analysis result provided")
            return self._get_signal_status()
        
        signal_assignment = analysis_result.get('signal_assignment', {})
        priorities = analysis_result.get('priority_ranking', [])
        
        if not priorities:
            logger.warning("No priority ranking available")
            return self._get_signal_status()
        
        # Get highest priority lane
        highest_priority_lane = priorities[0]['lane_id']
        
        # Update signals
        self._transition_to_lane(highest_priority_lane, signal_assignment)
        
        # Get recommended green time
        green_times = analysis_result.get('recommended_green_times', {})
        current_green_time = green_times.get(highest_priority_lane, Config.MIN_GREEN_TIME)
        
        # Record signal change
        signal_record = {
            'timestamp': datetime.now().isoformat(),
            'cycle': self.cycle_count,
            'green_lane': highest_priority_lane,
            'green_lane_name': Config.LANE_NAMES[highest_priority_lane],
            'green_duration': current_green_time,
            'priority_score': priorities[0]['priority_score'],
            'congestion_level': priorities[0]['congestion_level'],
            'signals': dict(self.current_signals)
        }
        
        self.signal_history.append(signal_record)
        self.cycle_count += 1
        
        logger.info(f"Signals updated: {Config.LANE_NAMES[highest_priority_lane]} -> GREEN "
                   f"for {current_green_time}s")
        
        return self._get_signal_status()
    
    def _transition_to_lane(self, target_lane: int, signal_assignment: Dict):
        """
        Safely transition signals to give green to target lane
        
        Args:
            target_lane: Lane ID to give green signal
            signal_assignment: Signal assignments for all lanes
        """
        # If there's currently a green lane, transition it properly
        if self.current_green_lane is not None and self.current_green_lane != target_lane:
            # Current green -> Yellow
            self.current_signals[self.current_green_lane] = SignalState.YELLOW
            logger.debug(f"Lane {self.current_green_lane} -> YELLOW")
            
            # Simulate yellow time
            time.sleep(0.1)  # Symbolic delay
            
            # Yellow -> Red
            self.current_signals[self.current_green_lane] = SignalState.RED
            logger.debug(f"Lane {self.current_green_lane} -> RED")
            
            # All red phase (safety clearance)
            all_red_start = time.time()
            logger.debug("All RED phase for safety clearance")
        
        # Set target lane to green
        self.current_signals[target_lane] = SignalState.GREEN
        self.current_green_lane = target_lane
        
        # Ensure all other lanes are red
        for lane_id in range(self.num_lanes):
            if lane_id != target_lane:
                self.current_signals[lane_id] = SignalState.RED
        
        self.phase_start_time = datetime.now()
    
    def _get_signal_status(self) -> Dict:
        """Get current signal status for all lanes with countdown"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'cycle': self.cycle_count,
            'signals': {}
        }
        
        for lane_id in range(self.num_lanes):
            lane_name = Config.LANE_NAMES[lane_id] if lane_id < len(Config.LANE_NAMES) else f'Lane {lane_id}'
            
            # Calculate time remaining for green signal
            time_remaining = 0
            if lane_id == self.current_green_lane and self.phase_start_time:
                elapsed = (datetime.now() - self.phase_start_time).total_seconds()
                time_remaining = max(0, Config.MIN_GREEN_TIME - elapsed)
            
            status['signals'][lane_name] = {
                'lane_id': lane_id,
                'state': self.current_signals[lane_id].value,
                'is_green': self.current_signals[lane_id] == SignalState.GREEN,
                'time_remaining': time_remaining
            }
        
        if self.current_green_lane is not None:
            status['current_green_lane'] = Config.LANE_NAMES[self.current_green_lane]
            
            if self.phase_start_time:
                elapsed = (datetime.now() - self.phase_start_time).total_seconds()
                status['phase_elapsed_time'] = round(elapsed, 1)
        
        return status
    
    def get_signal_status(self) -> Dict:
        """Public method to get signal status"""
        return self._get_signal_status()
    
    def get_signal_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent signal change history
        
        Args:
            limit: Number of recent records to return
            
        Returns:
            List of signal change records
        """
        return self.signal_history[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get controller statistics"""
        if not self.signal_history:
            return {
                'total_cycles': 0,
                'lanes_served': {},
                'average_cycle_time': 0
            }
        
        # Count how many times each lane got green
        lane_green_counts = {i: 0 for i in range(self.num_lanes)}
        for record in self.signal_history:
            lane_id = record.get('green_lane')
            if lane_id is not None:
                lane_green_counts[lane_id] += 1
        
        # Convert to lane names
        lanes_served = {
            Config.LANE_NAMES[lane_id]: count 
            for lane_id, count in lane_green_counts.items()
        }
        
        return {
            'total_cycles': self.cycle_count,
            'lanes_served': lanes_served,
            'total_signal_changes': len(self.signal_history)
        }
    
    def reset(self):
        """Reset controller to initial state"""
        self.current_signals = {i: SignalState.RED for i in range(self.num_lanes)}
        self.current_green_lane = None
        self.signal_history = []
        self.cycle_count = 0
        self.start_time = None
        self.phase_start_time = None
        logger.info("Traffic Signal Controller reset")
    
    def emergency_all_red(self):
        """Set all signals to RED (emergency situation)"""
        for lane_id in range(self.num_lanes):
            self.current_signals[lane_id] = SignalState.RED
        self.current_green_lane = None
        logger.warning("EMERGENCY: All signals set to RED")
    
    def get_lane_signal(self, lane_id: int) -> str:
        """Get current signal state for a specific lane"""
        if 0 <= lane_id < self.num_lanes:
            return self.current_signals[lane_id].value
        return "UNKNOWN"
    
    def visualize_signals(self) -> str:
        """
        Create a text visualization of current signal states
        
        Returns:
            String representation of signals
        """
        signal_icons = {
            'RED': '🔴',
            'YELLOW': '🟡',
            'GREEN': '🟢',
            'ALL_RED': '🔴'
        }
        
        lines = ["\n" + "="*50]
        lines.append("        TRAFFIC SIGNAL STATUS")
        lines.append("="*50)
        
        for lane_id in range(self.num_lanes):
            lane_name = Config.LANE_NAMES[lane_id]
            signal = self.current_signals[lane_id].value
            icon = signal_icons.get(signal, '⚪')
            
            status_line = f"  {lane_name:10s} [{icon}] {signal:8s}"
            
            if self.current_green_lane == lane_id and self.phase_start_time:
                elapsed = (datetime.now() - self.phase_start_time).total_seconds()
                status_line += f"  ({elapsed:.1f}s elapsed)"
            
            lines.append(status_line)
        
        lines.append("="*50 + "\n")
        
        return "\n".join(lines)

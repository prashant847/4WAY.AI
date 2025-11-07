"""
Video Processor with Visualization
Processes videos and creates annotated outputs
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict
from loguru import logger
from config import Config
from vehicle_detector import VehicleDetector


class VideoProcessor:
    """Process videos and create annotated outputs with detection visualization"""
    
    def __init__(self, detector: VehicleDetector):
        """
        Initialize video processor
        
        Args:
            detector: Initialized VehicleDetector instance
        """
        self.detector = detector
        
    def process_and_save(
        self,
        video_path: str,
        lane_id: int,
        output_path: str = None,
        show_preview: bool = False
    ) -> Dict:
        """
        Process video with detection and save annotated output
        
        Args:
            video_path: Input video path
            lane_id: Lane identifier
            output_path: Output video path (optional)
            show_preview: Show live preview window
            
        Returns:
            Processing results with statistics
        """
        logger.info(f"Processing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return None
        
        # Video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Setup output video writer
        if output_path is None:
            output_path = Config.OUTPUT_DIR / f"lane_{lane_id}_annotated.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        frame_idx = 0
        detections_per_frame = []
        
        logger.info(f"Processing {total_frames} frames at {fps} FPS")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect vehicles
            if frame_idx % Config.DETECTION_INTERVAL == 0:
                detections = self.detector.detect_vehicles(frame)
                detections_per_frame.append(len(detections))
                
                # Draw detections
                annotated_frame = self.detector.draw_detections(frame, detections)
                
                # Add info overlay
                annotated_frame = self._add_info_overlay(
                    annotated_frame,
                    lane_id,
                    frame_idx,
                    total_frames,
                    detections
                )
            else:
                annotated_frame = frame.copy()
            
            # Write frame
            out.write(annotated_frame)
            
            # Show preview
            if show_preview:
                cv2.imshow(f'Lane {lane_id} - Processing', annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            frame_idx += 1
            
            if frame_idx % 100 == 0:
                progress = (frame_idx / total_frames) * 100
                logger.debug(f"Progress: {progress:.1f}%")
        
        cap.release()
        out.release()
        
        if show_preview:
            cv2.destroyAllWindows()
        
        logger.success(f"Video saved to: {output_path}")
        
        return {
            'output_path': str(output_path),
            'frames_processed': frame_idx,
            'detections_per_frame': detections_per_frame,
            'avg_detections': np.mean(detections_per_frame) if detections_per_frame else 0
        }
    
    def _add_info_overlay(
        self,
        frame: np.ndarray,
        lane_id: int,
        frame_idx: int,
        total_frames: int,
        detections: List[Dict]
    ) -> np.ndarray:
        """Add informational overlay to frame"""
        overlay = frame.copy()
        
        # Semi-transparent background for text
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # Lane info
        lane_name = Config.LANE_NAMES[lane_id]
        cv2.putText(frame, f"Lane: {lane_name}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Frame info
        cv2.putText(frame, f"Frame: {frame_idx}/{total_frames}", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Vehicle count
        vehicle_count = len(detections)
        cv2.putText(frame, f"Vehicles: {vehicle_count}", (20, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Vehicle breakdown
        vehicle_types = {}
        for det in detections:
            vtype = det['class_name']
            vehicle_types[vtype] = vehicle_types.get(vtype, 0) + 1
        
        type_text = ", ".join([f"{k}:{v}" for k, v in vehicle_types.items()])
        cv2.putText(frame, type_text, (20, 130),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return frame
    
    def create_comparison_view(
        self,
        video_paths: List[str],
        output_path: str = None
    ) -> str:
        """
        Create a 2x2 grid comparison view of all 4 lanes
        
        Args:
            video_paths: List of 4 video paths
            output_path: Output path for comparison video
            
        Returns:
            Path to saved comparison video
        """
        if len(video_paths) != 4:
            logger.error("Need exactly 4 videos for comparison")
            return None
        
        # Open all videos
        caps = [cv2.VideoCapture(path) for path in video_paths]
        
        # Check all opened successfully
        if not all(cap.isOpened() for cap in caps):
            logger.error("Failed to open one or more videos")
            for cap in caps:
                cap.release()
            return None
        
        # Get properties from first video
        fps = int(caps[0].get(cv2.CAP_PROP_FPS))
        width = int(caps[0].get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(caps[0].get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Output will be 2x2 grid
        out_width = width * 2
        out_height = height * 2
        
        if output_path is None:
            output_path = Config.OUTPUT_DIR / "comparison_all_lanes.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (out_width, out_height))
        
        logger.info("Creating comparison video...")
        
        frame_idx = 0
        
        while True:
            frames = []
            
            # Read frame from each video
            for cap in caps:
                ret, frame = cap.read()
                if not ret:
                    frames.append(None)
                else:
                    frames.append(frame)
            
            # If any video ended, stop
            if None in frames:
                break
            
            # Process frames
            processed_frames = []
            for i, frame in enumerate(frames):
                detections = self.detector.detect_vehicles(frame)
                annotated = self.detector.draw_detections(frame, detections)
                
                # Add lane label
                cv2.putText(annotated, Config.LANE_NAMES[i], (20, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                
                processed_frames.append(annotated)
            
            # Create 2x2 grid
            top_row = np.hstack([processed_frames[0], processed_frames[1]])
            bottom_row = np.hstack([processed_frames[2], processed_frames[3]])
            grid = np.vstack([top_row, bottom_row])
            
            out.write(grid)
            
            frame_idx += 1
            
            if frame_idx % 30 == 0:
                logger.debug(f"Processed {frame_idx} frames")
        
        # Cleanup
        for cap in caps:
            cap.release()
        out.release()
        
        logger.success(f"Comparison video saved to: {output_path}")
        
        return str(output_path)

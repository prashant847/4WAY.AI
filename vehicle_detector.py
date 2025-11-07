"""
Advanced Vehicle Detection Module using YOLOv8
Handles real-time vehicle detection with multiple vehicle types
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple
from pathlib import Path
import torch
from loguru import logger
import supervision as sv
from config import Config


class VehicleDetector:
    """Advanced vehicle detection using YOLOv8"""
    
    def __init__(self, model_path: str = None, confidence: float = None):
        """
        Initialize the vehicle detector with optimizations
        
        Args:
            model_path: Path to YOLO model weights
            confidence: Confidence threshold for detections
        """
        self.confidence = confidence or Config.CONFIDENCE_THRESHOLD
        self.iou_threshold = Config.IOU_THRESHOLD
        self.vehicle_classes = Config.VEHICLE_CLASSES
        
        # Check if CUDA is available
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        
        # Load YOLO model with optimizations
        try:
            if model_path is None:
                model_path = Config.MODEL_DIR / Config.MODEL_NAME
            
            self.model = YOLO(str(model_path))
            
            # Enable FP16 for faster inference on GPU
            if self.device == 'cuda':
                self.model.to(self.device)
                # Warmup the model for GPU
                logger.info("Warming up GPU model...")
                dummy = torch.zeros(1, 3, 640, 640).to(self.device)
                try:
                    self.model(dummy, verbose=False, half=True)
                except Exception as e:
                    logger.warning(f"GPU warmup failed: {e}")
            
            logger.success(f"Model loaded successfully from {model_path}")
            logger.info(f"GPU Optimization: {'Enabled (FP16)' if self.device == 'cuda' else 'Disabled (CPU)'}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
        
        # Detection statistics
        self.total_detections = 0
        self.frame_count = 0
        
        # Performance tracking
        self.inference_times = []
        self.fps = 0
        
        # 🚀 NO TRACKING - Direct YOLOv8 detection for maximum speed and accuracy
        # ByteTrack removed for faster processing
        logger.info("🚀 Direct YOLOv8 detection mode (no tracking) for maximum performance")
        
    def detect_vehicles(self, frame: np.ndarray, lane_id: str = 'default') -> List[Dict]:
        """
        Detect vehicles in a single frame with optimized inference
        FAST MODE: Direct YOLOv8 detection without tracking for maximum performance
        
        Args:
            frame: Input video frame (BGR format)
            lane_id: Lane identifier (kept for API compatibility but not used)
            
        Returns:
            List of detected vehicles with bounding boxes and metadata
        """
        import time
        start_time = time.time()
        
        self.frame_count += 1
        detections = []
        
        try:
            # ⚡ IMPROVED PREPROCESSING: Better quality for detection
            height, width = frame.shape[:2]
            original_shape = (width, height)
            
            # 🎯 MINIMAL RESIZE: Keep higher resolution for better detection
            # Only resize if very large (>1280px width)
            if width > 1280:
                scale = 1280 / width
                frame = cv2.resize(frame, (1280, int(height * scale)), interpolation=cv2.INTER_LINEAR)
            elif width > 960:
                scale = 960 / width  
                frame = cv2.resize(frame, (960, int(height * scale)), interpolation=cv2.INTER_LINEAR)
            
            # 🎯 IMAGE ENHANCEMENT: Improve contrast and brightness for better detection
            # Convert to LAB color space
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge back and convert to BGR
            enhanced_lab = cv2.merge([l, a, b])
            frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            
            # Run optimized inference with IMPROVED DETECTION
            # Only use FP16 on CUDA GPU, not on CPU
            use_half = self.device == 'cuda'
            
            results = self.model(
                frame,
                conf=self.confidence,
                iou=self.iou_threshold,
                verbose=False,
                device=self.device,
                half=use_half,  # FP16 only on GPU
                agnostic_nms=False,  # 🎯 CLASS-AWARE NMS for better vehicle detection
                max_det=300,  # 🎯 INCREASED: More detections allowed (was 150)
                imgsz=960  # 🎯 INCREASED: Larger image size for better detection (was 640)
            )
            
            # Process results
            for result in results:
                boxes = result.boxes
                
                # 🔍 DEBUG: Log raw detections BEFORE filtering
                total_raw = len(boxes) if boxes is not None else 0
                logger.info(f"🎯 RAW YOLO detections (before filtering): {total_raw}")
                
                if total_raw == 0:
                    logger.warning("⚠️ YOLOv8 returned 0 detections!")
                
                # Convert to supervision format for tracking
                detections_sv = sv.Detections(
                    xyxy=boxes.xyxy.cpu().numpy(),
                    confidence=boxes.conf.cpu().numpy(),
                    class_id=boxes.cls.cpu().numpy().astype(int)
                )
                
                logger.info(f"📦 After Supervision conversion: {len(detections_sv)} detections")
                
                # 🚀 DIRECT DETECTION - No ByteTrack for maximum speed
                # Process all detections directly without tracking overhead
                logger.info(f"✅ Processing {len(detections_sv)} detections directly (no tracking)")
                
                # Filter and format detections
                for i in range(len(detections_sv)):
                    class_id = int(detections_sv.class_id[i])
                    
                    # Only process vehicle classes
                    if class_id in self.vehicle_classes:
                        x1, y1, x2, y2 = detections_sv.xyxy[i]
                        confidence = float(detections_sv.confidence[i])
                        
                        detection = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': round(confidence, 3),
                            'class_id': class_id,
                            'class_name': self.vehicle_classes[class_id],
                            'center': (int((x1 + x2) / 2), int((y1 + y2) / 2)),
                            'area': int((x2 - x1) * (y2 - y1)),
                            'track_id': -1  # No tracking in fast mode
                        }
                        
                        detections.append(detection)
                        self.total_detections += 1
            
            # Track inference time and FPS
            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)
            if len(self.inference_times) > 30:  # Keep last 30 frames
                self.inference_times.pop(0)
            
            # Calculate FPS
            if len(self.inference_times) > 0:
                avg_time = sum(self.inference_times) / len(self.inference_times)
                self.fps = 1.0 / avg_time if avg_time > 0 else 0
            
        except Exception as e:
            logger.error(f"Error during detection: {e}")
        
        return detections
    
    def process_video(self, video_path: str, lane_id: int = 0) -> Dict:
        """
        Process entire video and return aggregated statistics
        
        Args:
            video_path: Path to video file
            lane_id: ID of the lane (0-3 for North, South, East, West)
            
        Returns:
            Dictionary with vehicle counts and statistics
        """
        logger.info(f"Processing video: {video_path} for Lane {lane_id}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return None
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Video properties: {width}x{height}, {fps} FPS, {total_frames} frames")
        
        # Statistics tracking
        vehicle_counts = {vtype: 0 for vtype in self.vehicle_classes.values()}
        max_vehicles_in_frame = 0
        total_vehicles_detected = 0
        frames_processed = 0
        all_detections = []
        
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every Nth frame for efficiency
            if frame_idx % Config.DETECTION_INTERVAL == 0:
                detections = self.detect_vehicles(frame)
                all_detections.append(detections)
                
                # Update statistics
                frame_vehicle_count = len(detections)
                max_vehicles_in_frame = max(max_vehicles_in_frame, frame_vehicle_count)
                
                for detection in detections:
                    vehicle_counts[detection['class_name']] += 1
                
                frames_processed += 1
                
                if frames_processed % 30 == 0:
                    logger.debug(f"Processed {frames_processed} frames, detected {len(detections)} vehicles")
            
            frame_idx += 1
        
        cap.release()
        
        # Calculate average vehicles per frame
        total_vehicles_detected = sum(vehicle_counts.values())
        avg_vehicles_per_frame = total_vehicles_detected / frames_processed if frames_processed > 0 else 0
        
        # Calculate congestion score (weighted metric)
        congestion_score = self._calculate_congestion_score(
            vehicle_counts, 
            max_vehicles_in_frame, 
            avg_vehicles_per_frame
        )
        
        result = {
            'lane_id': lane_id,
            'lane_name': Config.LANE_NAMES[lane_id] if lane_id < len(Config.LANE_NAMES) else f'Lane {lane_id}',
            'total_vehicles': total_vehicles_detected,
            'vehicle_counts': vehicle_counts,
            'max_vehicles_in_frame': max_vehicles_in_frame,
            'avg_vehicles_per_frame': round(avg_vehicles_per_frame, 2),
            'frames_processed': frames_processed,
            'congestion_score': round(congestion_score, 2),
            'video_info': {
                'width': width,
                'height': height,
                'fps': fps,
                'total_frames': total_frames
            }
        }
        
        logger.success(f"Lane {lane_id} processed: {total_vehicles_detected} vehicles, Congestion: {congestion_score}")
        
        return result
    
    def _calculate_congestion_score(
        self, 
        vehicle_counts: Dict[str, int], 
        max_vehicles: int, 
        avg_vehicles: float
    ) -> float:
        """
        Calculate advanced congestion score
        
        Args:
            vehicle_counts: Dictionary of vehicle type counts
            max_vehicles: Maximum vehicles in a single frame
            avg_vehicles: Average vehicles per frame
            
        Returns:
            Congestion score (0-100)
        """
        # Weight different vehicle types
        vehicle_weights = {
            'car': 1.0,
            'motorcycle': 0.5,
            'bicycle': 0.3,
            'bus': 2.0,
            'truck': 2.0
        }
        
        # Calculate weighted vehicle count
        weighted_count = sum(
            vehicle_counts.get(vtype, 0) * vehicle_weights.get(vtype, 1.0)
            for vtype in vehicle_counts
        )
        
        # Combine multiple factors
        # 40% based on weighted count, 30% on max vehicles, 30% on average
        score = (
            (weighted_count * 0.4) +
            (max_vehicles * 3 * 0.3) +
            (avg_vehicles * 10 * 0.3)
        )
        
        # Normalize to 0-100 scale
        normalized_score = min(100, score)
        
        return normalized_score
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        # Color map for different vehicle types
        color_map = {
            'car': (0, 255, 0),       # Green
            'motorcycle': (255, 0, 0),  # Blue
            'bicycle': (0, 255, 255),   # Yellow
            'bus': (0, 0, 255),        # Red
            'truck': (255, 0, 255)     # Magenta
        }
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            color = color_map.get(class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - label_height - 10), (x1 + label_width, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated

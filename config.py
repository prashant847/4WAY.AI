"""
Advanced Traffic Management System Configuration
"""
import os
from pathlib import Path

class Config:
    # Base Directories
    BASE_DIR = Path(__file__).parent
    VIDEO_DIR = BASE_DIR / 'videos'
    OUTPUT_DIR = BASE_DIR / 'output'
    MODEL_DIR = BASE_DIR / 'models'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Create directories if they don't exist
    for directory in [VIDEO_DIR, OUTPUT_DIR, MODEL_DIR, LOGS_DIR]:
        directory.mkdir(exist_ok=True)
    
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # YOLO Model Configuration
    MODEL_NAME = 'yolov8n.pt'  # Options: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.15))  # 🎯 LOWERED: Better detection (15% threshold)
    IOU_THRESHOLD = float(os.getenv('IOU_THRESHOLD', 0.35))  # 🎯 LOWERED: Better overlap detection
    
    # Vehicle Classes (COCO dataset) - EXPANDED for better detection
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle', 
        5: 'bus',
        7: 'truck',
        1: 'bicycle',
        4: 'motorbike',  # Alternative motorcycle class
        6: 'train',      # For rail crossings
        8: 'boat'        # For waterway traffic (if applicable)
    }
    
    # Detection Settings
    DETECTION_INTERVAL = int(os.getenv('DETECTION_INTERVAL', 2))  # Process every N frames
    FRAME_SKIP = 1  # For faster processing
    
    # Traffic Signal Timing (seconds)
    MIN_GREEN_TIME = int(os.getenv('MIN_GREEN_TIME', 15))
    MAX_GREEN_TIME = int(os.getenv('MAX_GREEN_TIME', 120))
    YELLOW_TIME = int(os.getenv('YELLOW_TIME', 3))
    ALL_RED_TIME = int(os.getenv('ALL_RED_TIME', 2))
    
    # Lane Configuration
    LANE_NAMES = ['North', 'South', 'East', 'West']
    
    # Congestion Thresholds (REALISTIC TRAFFIC VALUES)
    LOW_CONGESTION = 15      # 0-15 vehicles = LOW (Green light not urgent)
    MEDIUM_CONGESTION = 35   # 16-35 vehicles = MEDIUM (Normal traffic)
    HIGH_CONGESTION = 60     # 36-60 vehicles = HIGH (Priority signal)
    CRITICAL_CONGESTION = 100  # 60+ vehicles = CRITICAL (Emergency priority)
    
    # Advanced Features
    ENABLE_TRACKING = True
    ENABLE_SPEED_ESTIMATION = False
    ENABLE_VEHICLE_COUNTING = True
    SAVE_ANNOTATED_VIDEOS = True

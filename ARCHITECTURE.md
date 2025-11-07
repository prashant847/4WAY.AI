
# System Architecture & Technical Documentation

## 🏗️ System Architecture

### Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Client/User Interface                    │
│  (API Calls, Web Interface, Command Line)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask REST API Server                    │
│                        (app.py)                             │
├─────────────────────────────────────────────────────────────┤
│  Routes:                                                    │
│  - POST /api/process-videos                                 │
│  - GET  /api/status                                         │
│  - GET  /api/signals                                        │
│  - GET  /api/analysis                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Vehicle    │ │   Traffic    │ │   Signal     │
│   Detector   │ │   Analyzer   │ │  Controller  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       │ YOLOv8        │ Congestion     │ Signal
       │ Detection     │ Scoring        │ Logic
       │                │                │
       └────────────────┴────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Video Files   │
              │  (4 Lanes)     │
              └────────────────┘
```

## 📦 Component Details

### 1. Vehicle Detector (`vehicle_detector.py`)

**Purpose**: Advanced vehicle detection using YOLOv8

**Key Features**:
- Multi-class vehicle detection (car, bus, truck, motorcycle, bicycle)
- GPU acceleration support
- Configurable confidence thresholds
- Frame-by-frame or batch processing
- Bounding box extraction
- Vehicle tracking and counting

**Main Class**: `VehicleDetector`

**Key Methods**:
```python
detect_vehicles(frame)           # Detect vehicles in single frame
process_video(video_path)        # Process entire video
draw_detections(frame, dets)     # Visualize detections
_calculate_congestion_score()    # Calculate congestion metric
```

**Detection Pipeline**:
```
Input Frame → YOLOv8 Inference → Non-Max Suppression → 
Filter Vehicle Classes → Extract Bounding Boxes → 
Calculate Metadata → Return Detections
```

**Output Format**:
```python
{
    'lane_id': 0,
    'lane_name': 'North',
    'total_vehicles': 45,
    'vehicle_counts': {
        'car': 30,
        'bus': 5,
        'truck': 8,
        'motorcycle': 2
    },
    'max_vehicles_in_frame': 12,
    'avg_vehicles_per_frame': 8.5,
    'congestion_score': 65.4
}
```

### 2. Traffic Analyzer (`traffic_analyzer.py`)

**Purpose**: Analyze traffic patterns and determine priorities

**Key Features**:
- Multi-factor congestion analysis
- Priority score calculation
- Lane ranking
- Intelligent recommendations
- Historical data tracking

**Main Class**: `TrafficAnalyzer`

**Key Methods**:
```python
analyze_all_lanes(lane_results)    # Analyze all 4 lanes
_calculate_priorities()            # Calculate priority scores
_assign_signals()                  # Assign traffic signals
_calculate_green_times()           # Calculate optimal timing
get_signal_cycle_plan()           # Generate complete cycle plan
```

**Priority Score Algorithm**:
```
Priority Score = (Congestion Score × 0.50) +
                 (Total Vehicles / 10 × 0.20) +
                 (Max Vehicles × 2 × 0.15) +
                 (Heavy Vehicles × 1.5 × 0.10) +
                 (Avg Vehicles × 5 × 0.05)
```

**Congestion Levels**:
- **LOW**: Score < 15 (Green zone)
- **MEDIUM**: Score 15-35 (Yellow zone)
- **HIGH**: Score 35-60 (Orange zone)
- **CRITICAL**: Score > 60 (Red zone)

### 3. Signal Controller (`signal_controller.py`)

**Purpose**: Manage traffic signal states and transitions

**Key Features**:
- Safe signal transitions (Green → Yellow → Red)
- All-red clearance phase
- Signal state tracking
- History logging
- Emergency all-red mode

**Main Class**: `TrafficSignalController`

**Signal States**:
- `RED`: Stop
- `YELLOW`: Prepare to stop
- `GREEN`: Go
- `ALL_RED`: Clearance phase

**State Transition Diagram**:
```
GREEN → YELLOW → RED → (All Red Phase) → GREEN (Next Lane)
         3s      Nx    2s
```

**Key Methods**:
```python
update_signals(analysis)          # Update based on analysis
_transition_to_lane(lane_id)     # Safe transition
get_signal_status()               # Current state
visualize_signals()               # Text visualization
```

### 4. Video Processor (`video_processor.py`)

**Purpose**: Process videos and create visualizations

**Key Features**:
- Annotated video generation
- Multi-lane comparison view
- Information overlays
- Real-time preview

**Main Class**: `VideoProcessor`

**Key Methods**:
```python
process_and_save(video_path)      # Process with visualization
create_comparison_view(videos)    # 2×2 grid view
_add_info_overlay(frame)          # Add statistics overlay
```

### 5. Flask API Server (`app.py`)

**Purpose**: REST API for system interaction

**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| POST | `/api/process-videos` | Process 4 videos |
| GET | `/api/status` | Processing status |
| GET | `/api/signals` | Signal states |
| GET | `/api/analysis` | Analysis results |
| GET | `/api/history` | Signal history |
| POST | `/api/reset` | Reset system |
| GET | `/api/lane/{id}` | Lane details |
| GET | `/api/health` | Health check |

## 🔄 Data Flow

### Complete Processing Flow:

```
1. User uploads/provides 4 videos
        ↓
2. Flask API receives request
        ↓
3. VehicleDetector processes each video
   - Detects vehicles frame-by-frame
   - Counts and categorizes vehicles
   - Calculates congestion scores
        ↓
4. TrafficAnalyzer analyzes all lanes
   - Calculates priority scores
   - Ranks lanes by urgency
   - Generates recommendations
        ↓
5. SignalController updates signals
   - Assigns GREEN to highest priority
   - Sets others to RED
   - Logs state changes
        ↓
6. Response sent to user
   - Lane results
   - Analysis data
   - Signal states
   - Recommendations
```

## 🧮 Algorithms

### Congestion Score Calculation

```python
# Weighted vehicle count
weighted_count = Σ(vehicle_count × vehicle_weight)

# Vehicle weights
weights = {
    'car': 1.0,
    'motorcycle': 0.5,
    'bicycle': 0.3,
    'bus': 2.0,
    'truck': 2.0
}

# Final score (0-100)
score = (weighted_count × 0.4) +
        (max_vehicles × 3 × 0.3) +
        (avg_vehicles × 10 × 0.3)

# Normalize
score = min(100, score)
```

### Green Time Calculation

```python
if priority_score >= 50:
    green_time = MAX_GREEN_TIME  # 120s
elif priority_score >= 30:
    green_time = MAX_GREEN_TIME × 0.75  # 90s
elif priority_score >= 15:
    green_time = MAX_GREEN_TIME × 0.50  # 60s
else:
    green_time = MIN_GREEN_TIME  # 15s
```

## 📊 Performance Metrics

### Detection Performance
- **Accuracy**: 90%+ (YOLOv8 on COCO dataset)
- **Speed**: 
  - GPU: ~30 FPS (RTX 3060)
  - CPU: ~5 FPS (Intel i7)
- **Processing Time**: 
  - 30s video: ~10-15s (GPU)
  - 30s video: ~60-90s (CPU)

### System Capacity
- **Concurrent Requests**: Limited to sequential processing
- **Video Size**: Up to 4K resolution supported
- **Storage**: ~50MB per minute of annotated output

## 🔧 Configuration Options

### Detection Configuration
```python
CONFIDENCE_THRESHOLD = 0.45    # Lower = more detections
IOU_THRESHOLD = 0.4           # Overlap threshold
DETECTION_INTERVAL = 2        # Process every Nth frame
```

### Signal Timing
```python
MIN_GREEN_TIME = 15    # Minimum green duration
MAX_GREEN_TIME = 120   # Maximum green duration
YELLOW_TIME = 3        # Yellow light duration
ALL_RED_TIME = 2       # Safety clearance
```

### Model Selection
```python
# Trade-off: Speed vs Accuracy
yolov8n.pt  # Fastest (6.3M params)
yolov8s.pt  # Fast (11.2M params)
yolov8m.pt  # Balanced (25.9M params)
yolov8l.pt  # Accurate (43.7M params)
yolov8x.pt  # Most accurate (68.2M params)
```

## 🚀 Optimization Tips

### For Speed
1. Use `yolov8n.pt` model
2. Increase `DETECTION_INTERVAL`
3. Lower video resolution
4. Use GPU

### For Accuracy
1. Use `yolov8x.pt` model
2. Decrease `DETECTION_INTERVAL` to 1
3. Lower `CONFIDENCE_THRESHOLD` to 0.3
4. Process at original resolution

## 🔒 Security Considerations

1. **Input Validation**: Validate video formats and sizes
2. **Rate Limiting**: Implement rate limiting for API
3. **Authentication**: Add API key authentication for production
4. **File Upload**: Restrict file types and sizes
5. **CORS**: Configure CORS for specific origins

## 📈 Scalability

### Current Limitations
- Sequential video processing (one at a time)
- Single-threaded analysis
- In-memory state storage

### Scaling Strategies
1. **Horizontal Scaling**: Deploy multiple instances
2. **Queue System**: Use Celery for background processing
3. **Database**: Store results in PostgreSQL/MongoDB
4. **Caching**: Use Redis for real-time data
5. **Load Balancing**: NGINX for multiple instances

## 🐛 Error Handling

### Common Errors
1. **Video Not Found**: Check file paths
2. **Model Load Failed**: Download YOLOv8 weights
3. **CUDA Out of Memory**: Use smaller model or CPU
4. **API Timeout**: Increase timeout for large videos

### Logging
- **Console**: INFO level messages
- **File**: DEBUG level with rotation
- **Location**: `logs/traffic_system_*.log`

## 📚 Dependencies

### Core Libraries
- **ultralytics**: YOLOv8 implementation
- **torch**: Deep learning framework
- **opencv-python**: Video processing
- **flask**: Web framework
- **numpy**: Numerical operations

### Optional Dependencies
- **CUDA**: GPU acceleration (10x faster)
- **matplotlib**: Chart generation
- **loguru**: Advanced logging

## 🎓 Best Practices

1. **Video Quality**: Use clear, high-quality videos
2. **Camera Angle**: Top-down or elevated angle works best
3. **Lighting**: Good lighting improves detection
4. **Video Length**: 30-60 seconds ideal for testing
5. **Frame Rate**: 25-30 FPS recommended

---

**For implementation details, see source code comments.**

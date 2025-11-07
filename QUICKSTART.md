# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Add Your Videos
Place 4 traffic videos in the `videos/` folder:
- `lane_0.mp4` - North direction
- `lane_1.mp4` - South direction  
- `lane_2.mp4` - East direction
- `lane_3.mp4` - West direction

### Step 3: Run the System

#### Option A: Test Script (Quickest)
```powershell
python test_system.py
```

#### Option B: Flask API Server
```powershell
# Terminal 1: Start server
python app.py

# Terminal 2: Test API
python api_client_example.py
```

### Step 4: Check Results
Results will be saved in the `output/` folder:
- `results_*.json` - Analysis data
- `*_annotated.mp4` - Videos with detections
- `congestion_chart_*.png` - Visual charts
- `traffic_report_*.txt` - Detailed report

## 📊 Expected Output

### Console Output
```
🚦 Processing North lane...
   Total Vehicles: 45
   Congestion Score: 65.4
   
🚦 Processing South lane...
   Total Vehicles: 23
   Congestion Score: 32.1

SIGNAL ASSIGNMENT:
🟢 North: GREEN (highest priority)
🔴 South: RED
🔴 East: RED
🔴 West: RED
```

### API Response
```json
{
  "success": true,
  "lane_results": [...],
  "analysis": {
    "priority_ranking": [
      {
        "rank": 1,
        "lane_name": "North",
        "priority_score": 65.4,
        "congestion_level": "HIGH"
      }
    ]
  }
}
```

## 🎯 Key Features You'll See

1. **Vehicle Detection**: Detects cars, buses, trucks, motorcycles, bicycles
2. **Congestion Analysis**: Calculates weighted congestion scores
3. **Smart Signals**: Automatically assigns GREEN to most congested lane
4. **Real-time Status**: Monitor via REST API
5. **Visualizations**: Annotated videos and charts

## 🔧 Common Issues

**Issue**: No videos found
**Fix**: Make sure videos are in `videos/` folder with .mp4 or .avi extension

**Issue**: Slow processing
**Fix**: Increase `DETECTION_INTERVAL` in `config.py` to 5 or 10

**Issue**: Import errors
**Fix**: Run `pip install -r requirements.txt` again

## 📝 Next Steps

- Read full `README.md` for detailed documentation
- Customize settings in `config.py`
- Explore API endpoints in `app.py`
- Check `output/` folder for results

## 💡 Tips

- Use shorter videos (30-60 seconds) for testing
- GPU makes processing 10x faster
- Lower `CONFIDENCE_THRESHOLD` to detect more vehicles
- Check `logs/` folder if something goes wrong

---
Need help? Check the logs in `logs/` directory!

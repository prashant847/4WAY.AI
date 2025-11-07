"""
QUICK VIDEO PROCESSOR - Creates videos with bounding boxes
Dekho videos mein cars, trucks ke around boxes!
"""
import cv2
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from vehicle_detector import VehicleDetector

print("\n" + "="*70)
print("🚗 QUICK VIDEO PROCESSOR - Creating Annotated Videos")
print("="*70 + "\n")

# Initialize detector
print("🔧 Loading AI model (YOLOv8)...")
detector = VehicleDetector()
print("✅ Model loaded!\n")

# Find videos
videos = list(Config.VIDEO_DIR.glob("*.mp4"))

if not videos:
    print("❌ No videos found in videos/ folder!")
    print("Please add your videos to: d:\\4-traffic backend\\videos\\")
    input("\nPress Enter to exit...")
    sys.exit(1)

print(f"📹 Found {len(videos)} video(s):\n")
for i, v in enumerate(videos, 1):
    print(f"  {i}. {v.name}")

print(f"\n{'='*70}")
print("Processing videos... This will take a few minutes.")
print(f"{'='*70}\n")

# Process each video
for idx, video_path in enumerate(videos[:4]):  # Max 4 videos
    lane_name = Config.LANE_NAMES[idx] if idx < 4 else f"Video {idx}"
    output_name = f"{lane_name}_WITH_BOXES.mp4"
    output_path = Config.OUTPUT_DIR / output_name
    
    print(f"\n🎬 Processing: {video_path.name} ({lane_name})")
    print(f"💾 Output: {output_name}")
    print("-" * 70)
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Resolution: {width}x{height}, FPS: {fps}, Frames: {total_frames}")
    
    # Create output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    frame_count = 0
    vehicle_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect vehicles
        detections = detector.detect_vehicles(frame)
        
        # Draw boxes around vehicles
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            label = det['class_name']
            conf = det['confidence']
            
            # Color based on vehicle type
            colors = {
                'car': (0, 255, 0),      # Green
                'bus': (0, 0, 255),      # Red
                'truck': (255, 0, 255),  # Magenta
                'motorcycle': (255, 0, 0),  # Blue
                'bicycle': (0, 255, 255)    # Yellow
            }
            color = colors.get(label, (255, 255, 255))
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label_text = f"{label} {conf:.2f}"
            (w, h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1-h-10), (x1+w, y1), color, -1)
            cv2.putText(frame, label_text, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        
        # Add info overlay
        cv2.rectangle(frame, (10, 10), (350, 80), (0, 0, 0), -1)
        cv2.putText(frame, f"Lane: {lane_name}", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Vehicles: {len(detections)}", (20, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        out.write(frame)
        
        frame_count += 1
        vehicle_count += len(detections)
        
        # Progress
        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"⏳ {progress:.0f}% | Frame {frame_count}/{total_frames} | "
                  f"Vehicles: {len(detections)}", end='\r')
    
    cap.release()
    out.release()
    
    print(f"\n✅ Done! Detected {vehicle_count} vehicles total")
    print(f"📁 Saved: {output_path}")

# Final summary
print(f"\n{'='*70}")
print("🎉 ALL VIDEOS PROCESSED!")
print(f"{'='*70}\n")

print("📂 Your annotated videos are in:")
print(f"   {Config.OUTPUT_DIR}\n")

print("🎬 Files created:")
for video in Config.OUTPUT_DIR.glob("*_WITH_BOXES.mp4"):
    print(f"   ✓ {video.name}")

print(f"\n{'='*70}")
print("💡 Open the 'output' folder and play the videos!")
print("   You'll see colored boxes around detected vehicles")
print(f"{'='*70}\n")

input("Press Enter to exit...")

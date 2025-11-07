"""
Simple Video Player with Detection
Press 'q' to quit, 'p' to pause, SPACE to resume
"""
import cv2
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from vehicle_detector import VehicleDetector
from config import Config

print("\n" + "="*70)
print("🚗 LIVE VIDEO DETECTION - Press 'q' to quit, 'p' to pause")
print("="*70 + "\n")

# Initialize detector
print("Loading AI model...")
detector = VehicleDetector()
print("✓ Model loaded!\n")

# Video paths
video_paths = [
    Config.VIDEO_DIR / "lane_0.mp4",
    Config.VIDEO_DIR / "lane_1.mp4",
    Config.VIDEO_DIR / "lane_2.mp4",
    Config.VIDEO_DIR / "lane_3.mp4"
]

# Open all videos
caps = []
lane_names = ['North', 'South', 'East', 'West']

print("Opening videos...")
for i, path in enumerate(video_paths):
    cap = cv2.VideoCapture(str(path))
    if cap.isOpened():
        caps.append(cap)
        print(f"✓ {lane_names[i]} lane video loaded")
    else:
        print(f"✗ Could not open {path}")

if len(caps) == 0:
    print("\n❌ No videos found! Please check videos folder.")
    sys.exit(1)

print(f"\n✓ Loaded {len(caps)} videos")
print("\nStarting detection... (This may take a moment)\n")

frame_count = 0
paused = False

while True:
    if not paused:
        frames = []
        all_ended = True
        
        # Read frames from all videos
        for cap in caps:
            ret, frame = cap.read()
            if ret:
                all_ended = False
                frames.append(frame)
            else:
                frames.append(None)
        
        if all_ended:
            print("\n✓ All videos finished!")
            break
        
        # Process each valid frame
        for i, frame in enumerate(frames):
            if frame is not None:
                # Detect vehicles
                detections = detector.detect_vehicles(frame)
                
                # Draw detections
                annotated = detector.draw_detections(frame, detections)
                
                # Add info overlay
                # Lane name
                cv2.rectangle(annotated, (10, 10), (350, 90), (0, 0, 0), -1)
                cv2.putText(
                    annotated,
                    f"{lane_names[i]} Lane",
                    (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 0),
                    2
                )
                
                # Vehicle count
                cv2.putText(
                    annotated,
                    f"Vehicles: {len(detections)}",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2
                )
                
                # Show window
                cv2.imshow(f'{lane_names[i]} Lane - Detection', annotated)
        
        frame_count += 1
        
        # Print progress
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")
    
    # Handle keyboard input
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        print("\nStopping...")
        break
    elif key == ord('p'):
        paused = True
        print("⏸ Paused (press SPACE to resume)")
    elif key == ord(' '):
        paused = False
        print("▶ Resumed")

# Cleanup
for cap in caps:
    cap.release()
cv2.destroyAllWindows()

print("\n" + "="*70)
print("✓ Detection complete!")
print(f"Total frames processed: {frame_count}")
print("="*70 + "\n")

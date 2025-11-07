"""
Process videos and create annotated outputs with bounding boxes
Run this to see detected vehicles with boxes around them!
"""
import sys
from pathlib import Path
import cv2
from loguru import logger

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO")

from config import Config
from vehicle_detector import VehicleDetector

def process_video_with_visualization(video_path, lane_id, output_path=None):
    """
    Process video and create annotated version with bounding boxes
    
    Args:
        video_path: Path to input video
        lane_id: Lane identifier (0-3)
        output_path: Where to save annotated video
    """
    logger.info(f"🎬 Processing {Config.LANE_NAMES[lane_id]} lane: {video_path}")
    
    # Initialize detector
    detector = VehicleDetector()
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Failed to open video: {video_path}")
        return None
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logger.info(f"📹 Video: {width}x{height} @ {fps} FPS, {total_frames} frames")
    
    # Setup output
    if output_path is None:
        output_path = Config.OUTPUT_DIR / f"{Config.LANE_NAMES[lane_id]}_annotated.mp4"
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    frame_idx = 0
    total_vehicles = 0
    
    logger.info(f"🚗 Starting detection... This may take a few minutes...")
    logger.info(f"💾 Output will be saved to: {output_path}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect vehicles in this frame
        detections = detector.detect_vehicles(frame)
        
        # Draw bounding boxes
        annotated_frame = detector.draw_detections(frame, detections)
        
        # Add lane info overlay
        cv2.rectangle(annotated_frame, (10, 10), (400, 100), (0, 0, 0), -1)
        cv2.putText(annotated_frame, f"Lane: {Config.LANE_NAMES[lane_id]}", 
                   (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Frame: {frame_idx}/{total_frames}", 
                   (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(annotated_frame, f"Vehicles: {len(detections)}", 
                   (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Write frame
        out.write(annotated_frame)
        
        frame_idx += 1
        total_vehicles += len(detections)
        
        # Progress update
        if frame_idx % 30 == 0:
            progress = (frame_idx / total_frames) * 100
            logger.info(f"⏳ Progress: {progress:.1f}% ({frame_idx}/{total_frames} frames)")
    
    cap.release()
    out.release()
    
    logger.success(f"✅ Done! Processed {frame_idx} frames, detected {total_vehicles} vehicles")
    logger.success(f"📁 Annotated video saved: {output_path}")
    
    return str(output_path)


def main():
    """Process all 4 lane videos"""
    print("\n" + "="*80)
    print("🚦 TRAFFIC VIDEO PROCESSOR - WITH BOUNDING BOXES")
    print("="*80 + "\n")
    
    # Find videos
    video_files = [
        Config.VIDEO_DIR / "lane_0.mp4",
        Config.VIDEO_DIR / "lane_1.mp4",
        Config.VIDEO_DIR / "lane_2.mp4",
        Config.VIDEO_DIR / "lane_3.mp4"
    ]
    
    # Check which videos exist
    available_videos = [v for v in video_files if v.exists()]
    
    if not available_videos:
        logger.error("❌ No videos found in videos/ folder!")
        logger.info("Please add videos: lane_0.mp4, lane_1.mp4, lane_2.mp4, lane_3.mp4")
        return
    
    logger.info(f"📹 Found {len(available_videos)} videos to process")
    print()
    
    # Process each video
    output_files = []
    for idx, video_path in enumerate(available_videos):
        lane_id = int(video_path.stem.split('_')[1])
        
        print("\n" + "-"*80)
        output_path = process_video_with_visualization(video_path, lane_id)
        if output_path:
            output_files.append(output_path)
        print("-"*80)
    
    # Summary
    print("\n" + "="*80)
    print("🎉 ALL VIDEOS PROCESSED!")
    print("="*80)
    print("\n📁 Annotated videos saved in output/ folder:\n")
    
    for i, output_file in enumerate(output_files, 1):
        print(f"  {i}. {output_file}")
    
    print("\n" + "="*80)
    print("💡 Open the output/ folder to watch videos with bounding boxes!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

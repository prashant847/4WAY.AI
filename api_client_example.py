"""
Example client script to interact with the Traffic Management API
"""
import requests
import json
from pathlib import Path


class TrafficAPIClient:
    """Client to interact with Traffic Management API"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def health_check(self):
        """Check if API is running"""
        response = requests.get(f"{self.base_url}/api/health")
        return response.json()
    
    def process_videos_with_paths(self, video_paths):
        """
        Process videos by providing file paths
        
        Args:
            video_paths: List of 4 video file paths
        """
        data = {"videos": video_paths}
        response = requests.post(
            f"{self.base_url}/api/process-videos",
            json=data
        )
        return response.json()
    
    def process_videos_with_upload(self, video_files):
        """
        Process videos by uploading files
        
        Args:
            video_files: List of 4 video file paths to upload
        """
        files = {}
        for i, video_path in enumerate(video_files[:4]):
            with open(video_path, 'rb') as f:
                files[f'video_{i}'] = (Path(video_path).name, f, 'video/mp4')
        
        response = requests.post(
            f"{self.base_url}/api/process-videos",
            files=files
        )
        return response.json()
    
    def get_status(self):
        """Get current processing status"""
        response = requests.get(f"{self.base_url}/api/status")
        return response.json()
    
    def get_signals(self):
        """Get current traffic signal states"""
        response = requests.get(f"{self.base_url}/api/signals")
        return response.json()
    
    def get_analysis(self):
        """Get latest traffic analysis"""
        response = requests.get(f"{self.base_url}/api/analysis")
        return response.json()
    
    def get_history(self, limit=10):
        """Get signal change history"""
        response = requests.get(f"{self.base_url}/api/history?limit={limit}")
        return response.json()
    
    def reset_system(self):
        """Reset the system"""
        response = requests.post(f"{self.base_url}/api/reset")
        return response.json()
    
    def get_lane_info(self, lane_id):
        """Get information for specific lane"""
        response = requests.get(f"{self.base_url}/api/lane/{lane_id}")
        return response.json()


def example_usage():
    """Example usage of the API client"""
    
    # Initialize client
    client = TrafficAPIClient("http://localhost:5000")
    
    print("=" * 80)
    print("Traffic Management API - Example Usage")
    print("=" * 80 + "\n")
    
    # 1. Health check
    print("1. Checking API health...")
    health = client.health_check()
    print(f"   Status: {health.get('status')}")
    print(f"   System Ready: {health.get('system_ready')}\n")
    
    # 2. Process videos with paths
    print("2. Processing videos...")
    video_paths = [
        "d:/4-traffic backend/videos/lane_0.mp4",
        "d:/4-traffic backend/videos/lane_1.mp4",
        "d:/4-traffic backend/videos/lane_2.mp4",
        "d:/4-traffic backend/videos/lane_3.mp4"
    ]
    
    try:
        result = client.process_videos_with_paths(video_paths)
        
        if result.get('success'):
            print("   ✓ Videos processed successfully!\n")
            
            # 3. Get analysis results
            print("3. Traffic Analysis Results:")
            print("-" * 80)
            
            analysis = result.get('analysis', {})
            priorities = analysis.get('priority_ranking', [])
            
            for priority in priorities:
                print(f"   {priority['rank']}. {priority['lane_name']}")
                print(f"      Score: {priority['priority_score']:.2f}")
                print(f"      Level: {priority['congestion_level']}")
                print(f"      Vehicles: {priority['total_vehicles']}\n")
            
            # 4. Get signal states
            print("4. Current Signal States:")
            print("-" * 80)
            signal_data = result.get('signal_status', {})
            for lane_name, info in signal_data.get('signals', {}).items():
                state = info['state']
                icon = '🟢' if state == 'GREEN' else '🔴'
                print(f"   {icon} {lane_name}: {state}")
            
            print("\n" + "=" * 80)
            print("Example completed successfully!")
            print("=" * 80)
        else:
            print(f"   ✗ Error: {result.get('error')}")
    
    except requests.exceptions.ConnectionError:
        print("   ✗ Error: Could not connect to API")
        print("   Make sure the Flask server is running: python app.py")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")


if __name__ == "__main__":
    example_usage()

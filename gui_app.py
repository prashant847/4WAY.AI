"""
GUI Application for Traffic Management System
Shows videos with real-time detection boxes
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import threading
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time

from config import Config
from vehicle_detector import VehicleDetector
from traffic_analyzer import TrafficAnalyzer
from signal_controller import TrafficSignalController


class TrafficManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚦 Traffic Management System - GUI")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize components
        self.detector = None
        self.analyzer = TrafficAnalyzer()
        self.controller = TrafficSignalController()
        
        # Video paths
        self.video_paths = [
            str(Config.VIDEO_DIR / "lane_0.mp4"),
            str(Config.VIDEO_DIR / "lane_1.mp4"),
            str(Config.VIDEO_DIR / "lane_2.mp4"),
            str(Config.VIDEO_DIR / "lane_3.mp4")
        ]
        
        # State
        self.is_processing = False
        self.current_frame_labels = [None, None, None, None]
        self.lane_results = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the GUI layout"""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#1e1e1e', height=80)
        title_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="🚦 Advanced Traffic Management System",
            font=('Arial', 24, 'bold'),
            bg='#1e1e1e',
            fg='#00ff00'
        )
        title_label.pack(pady=20)
        
        # Main container
        main_container = tk.Frame(self.root, bg='#2b2b2b')
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left side - Video feeds (2x2 grid)
        video_frame = tk.LabelFrame(
            main_container,
            text="📹 Live Detection (4 Lanes)",
            font=('Arial', 14, 'bold'),
            bg='#2b2b2b',
            fg='white',
            bd=2
        )
        video_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # Create 2x2 grid for videos
        video_grid = tk.Frame(video_frame, bg='#2b2b2b')
        video_grid.pack(fill='both', expand=True, padx=10, pady=10)
        
        lane_names = ['North', 'South', 'East', 'West']
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#ffa07a']
        
        for i in range(4):
            row = i // 2
            col = i % 2
            
            lane_frame = tk.Frame(video_grid, bg='#1e1e1e', bd=2, relief='solid')
            lane_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # Lane title
            lane_title = tk.Label(
                lane_frame,
                text=f"{lane_names[i]} Lane",
                font=('Arial', 12, 'bold'),
                bg=colors[i],
                fg='white'
            )
            lane_title.pack(fill='x')
            
            # Video display
            video_label = tk.Label(lane_frame, bg='black')
            video_label.pack(fill='both', expand=True, padx=2, pady=2)
            self.current_frame_labels[i] = video_label
        
        # Configure grid weights
        video_grid.grid_rowconfigure(0, weight=1)
        video_grid.grid_rowconfigure(1, weight=1)
        video_grid.grid_columnconfigure(0, weight=1)
        video_grid.grid_columnconfigure(1, weight=1)
        
        # Right side - Control panel and results
        right_panel = tk.Frame(main_container, bg='#2b2b2b', width=400)
        right_panel.pack(side='right', fill='both', padx=5)
        
        # Control buttons
        control_frame = tk.LabelFrame(
            right_panel,
            text="⚙️ Controls",
            font=('Arial', 12, 'bold'),
            bg='#2b2b2b',
            fg='white'
        )
        control_frame.pack(fill='x', pady=5)
        
        btn_style = {
            'font': ('Arial', 11, 'bold'),
            'width': 20,
            'height': 2,
            'bd': 0,
            'cursor': 'hand2'
        }
        
        self.start_btn = tk.Button(
            control_frame,
            text="▶️ Start Processing",
            bg='#4caf50',
            fg='white',
            command=self.start_processing,
            **btn_style
        )
        self.start_btn.pack(pady=10, padx=10)
        
        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ Stop",
            bg='#f44336',
            fg='white',
            command=self.stop_processing,
            state='disabled',
            **btn_style
        )
        self.stop_btn.pack(pady=5, padx=10)
        
        # Traffic Signals Display
        signal_frame = tk.LabelFrame(
            right_panel,
            text="🚦 Traffic Signals",
            font=('Arial', 12, 'bold'),
            bg='#2b2b2b',
            fg='white'
        )
        signal_frame.pack(fill='x', pady=10)
        
        self.signal_labels = []
        self.countdown_labels = []
        for i, name in enumerate(lane_names):
            signal_row = tk.Frame(signal_frame, bg='#1e1e1e')
            signal_row.pack(fill='x', padx=10, pady=5)
            
            name_label = tk.Label(
                signal_row,
                text=name,
                font=('Arial', 10, 'bold'),
                bg='#1e1e1e',
                fg='white',
                width=8,
                anchor='w'
            )
            name_label.pack(side='left', padx=5)
            
            signal_label = tk.Label(
                signal_row,
                text="●",
                font=('Arial', 24),
                bg='#1e1e1e',
                fg='gray'
            )
            signal_label.pack(side='left', padx=10)
            
            # Add countdown timer label
            countdown_label = tk.Label(
                signal_row,
                text="--",
                font=('Arial', 12, 'bold'),
                bg='#1e1e1e',
                fg='#00ff00',
                width=4
            )
            countdown_label.pack(side='right', padx=5)
            
            self.signal_labels.append(signal_label)
            self.countdown_labels.append(countdown_label)
        
        # Statistics Display
        stats_frame = tk.LabelFrame(
            right_panel,
            text="📊 Statistics",
            font=('Arial', 12, 'bold'),
            bg='#2b2b2b',
            fg='white'
        )
        stats_frame.pack(fill='both', expand=True, pady=5)
        
        self.stats_text = tk.Text(
            stats_frame,
            bg='#1e1e1e',
            fg='#00ff00',
            font=('Consolas', 9),
            wrap='word',
            height=15
        )
        self.stats_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg='#1e1e1e', height=30)
        status_frame.pack(fill='x', side='bottom')
        
        # FPS counter
        self.fps_label = tk.Label(
            status_frame,
            text="FPS: 0.0",
            font=('Arial', 9, 'bold'),
            bg='#1e1e1e',
            fg='#ffcc00',
            anchor='e',
            width=15
        )
        self.fps_label.pack(side='right', padx=10, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to process videos",
            font=('Arial', 9),
            bg='#1e1e1e',
            fg='#00ff00',
            anchor='w'
        )
        self.status_label.pack(fill='x', padx=10, pady=5)
    
    def start_processing(self):
        """Start video processing in a separate thread"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.update_status("Initializing detector...")
        
        # Start processing thread
        thread = threading.Thread(target=self.process_videos, daemon=True)
        thread.start()
    
    def stop_processing(self):
        """Stop video processing"""
        self.is_processing = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.update_status("Processing stopped")
    
    def process_videos(self):
        """Process all 4 videos simultaneously with detection and multi-threading"""
        try:
            # Initialize detector
            self.update_status("Loading AI model...")
            self.detector = VehicleDetector()
            
            # Open all video captures
            caps = []
            for video_path in self.video_paths:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    self.update_status(f"Error: Could not open {video_path}")
                    return
                caps.append(cap)
            
            self.update_status("Processing videos with real-time detection...")
            
            frame_count = 0
            lane_vehicle_counts = [[] for _ in range(4)]
            
            # Create thread pool for parallel processing
            with ThreadPoolExecutor(max_workers=4) as executor:
                while self.is_processing:
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
                        break
                    
                    # Process frames in parallel
                    futures = []
                    for i, frame in enumerate(frames):
                        if frame is not None:
                            future = executor.submit(self.process_single_frame, frame, i)
                            futures.append((i, future))
                    
                    # Collect results
                    for i, future in futures:
                        annotated, num_detections = future.result()
                        lane_vehicle_counts[i].append(num_detections)
                        self.display_frame(annotated, i)
                    
                    frame_count += 1
                    
                    if frame_count % 30 == 0:
                        self.update_status(f"Processed {frame_count} frames...")
            
            # Release captures
            for cap in caps:
                cap.release()
            
            # Analyze results
            self.analyze_results(lane_vehicle_counts)
            
            self.update_status("Processing complete! Check statistics panel.")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
        
        finally:
            self.is_processing = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def process_single_frame(self, frame, lane_id):
        """Process a single frame with detection (for parallel execution)"""
        # Detect vehicles
        detections = self.detector.detect_vehicles(frame)
        
        # Draw detections
        annotated = self.detector.draw_detections(frame, detections)
        
        # Add lane info
        cv2.putText(
            annotated,
            f"{Config.LANE_NAMES[lane_id]} Lane",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        
        cv2.putText(
            annotated,
            f"Vehicles: {len(detections)}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )
        
        # Add FPS counter
        if hasattr(self.detector, 'fps'):
            cv2.putText(
                annotated,
                f"FPS: {self.detector.fps:.1f}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )
        
        return annotated, len(detections)
    
    def display_frame(self, frame, lane_id):
        """Display frame in the corresponding lane panel"""
        # Resize for display
        height, width = frame.shape[:2]
        display_width = 350
        display_height = int(height * (display_width / width))
        
        frame_resized = cv2.resize(frame, (display_width, display_height))
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        # Convert to PhotoImage
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        
            # Update label
        if self.current_frame_labels[lane_id]:
            self.current_frame_labels[lane_id].imgtk = imgtk
            self.current_frame_labels[lane_id].configure(image=imgtk)
        
        # Update FPS display
        if hasattr(self.detector, 'fps'):
            self.fps_label.config(text=f"FPS: {self.detector.fps:.1f}")
    
    def analyze_results(self, lane_vehicle_counts):
        """Analyze and display results"""
        lane_results = []
        
        for i, counts in enumerate(lane_vehicle_counts):
            if counts:
                total = sum(counts)
                avg = total / len(counts)
                max_vehicles = max(counts)
                
                result = {
                    'lane_id': i,
                    'lane_name': Config.LANE_NAMES[i],
                    'total_vehicles': total,
                    'avg_vehicles_per_frame': avg,
                    'max_vehicles_in_frame': max_vehicles,
                    'congestion_score': avg * 10 + max_vehicles * 3,
                    'vehicle_counts': {'car': 0}  # Simplified
                }
                lane_results.append(result)
        
        # Analyze traffic
        if lane_results:
            analysis = self.analyzer.analyze_all_lanes(lane_results)
            signal_status = self.controller.update_signals(analysis)
            
            # Update signals display
            self.update_signals(signal_status)
            
            # Update statistics
            self.update_statistics(analysis)
    
    def update_signals(self, signal_status):
        """Update traffic signal display with countdown"""
        signals = signal_status.get('signals', {})
        
        for i, (lane_name, info) in enumerate(signals.items()):
            state = info['state']
            if state == 'GREEN':
                color = '#00ff00'
            elif state == 'YELLOW':
                color = '#ffff00'
            else:
                color = '#ff0000'
            
            self.signal_labels[i].config(fg=color)
            
            # Update countdown timer
            remaining = info.get('time_remaining', 0)
            if remaining > 0:
                self.countdown_labels[i].config(text=f"{int(remaining)}s")
            else:
                self.countdown_labels[i].config(text="--")
        
        # Schedule next update
        if self.is_processing:
            self.root.after(500, lambda: self.update_countdown_timers())
    
    def update_statistics(self, analysis):
        """Update statistics display"""
        self.stats_text.delete(1.0, tk.END)
        
        text = "="*40 + "\n"
        text += "TRAFFIC ANALYSIS RESULTS\n"
        text += "="*40 + "\n\n"
        
        priorities = analysis.get('priority_ranking', [])
        
        text += "PRIORITY RANKING:\n"
        text += "-"*40 + "\n"
        for p in priorities:
            text += f"{p['rank']}. {p['lane_name']}\n"
            text += f"   Score: {p['priority_score']:.2f}\n"
            text += f"   Level: {p['congestion_level']}\n"
            text += f"   Vehicles: {p['total_vehicles']}\n\n"
        
        text += "\nSIGNAL ASSIGNMENT:\n"
        text += "-"*40 + "\n"
        signals = analysis.get('signal_assignment', {})
        for lane_id, signal in signals.items():
            lane_name = Config.LANE_NAMES[lane_id]
            icon = '🟢' if signal == 'GREEN' else '🔴'
            text += f"{icon} {lane_name}: {signal}\n"
        
        text += "\n\nRECOMMENDATIONS:\n"
        text += "-"*40 + "\n"
        for rec in analysis.get('recommendations', []):
            text += f"• {rec}\n"
        
        self.stats_text.insert(1.0, text)
    
    def update_countdown_timers(self):
        """Continuously update countdown timers"""
        if not self.is_processing:
            return
        
        signal_status = self.controller.get_signal_status()
        signals = signal_status.get('signals', {})
        
        for i, (lane_name, info) in enumerate(signals.items()):
            remaining = info.get('time_remaining', 0)
            if remaining > 0:
                self.countdown_labels[i].config(text=f"{int(remaining)}s")
            else:
                self.countdown_labels[i].config(text="--")
        
        # Schedule next update
        self.root.after(500, self.update_countdown_timers)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=f"Status: {message}")
        self.root.update()


def main():
    """Launch the GUI application"""
    root = tk.Tk()
    app = TrafficManagementGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

"""
ESP32-CAM Fire Detection - Color-Based (Temporary Solution)
===========================================================
Simple fire detection menggunakan color range sebagai temporary solution
sementara menunggu training model custom.

PERINGATAN: 
- Metode ini kurang akurat dibanding YOLOv8
- Banyak false positive (object merah akan terdeteksi)
- Gunakan hanya untuk testing atau temporary

Untuk production, HARUS train custom YOLOv8 model!

Author: AI Assistant
Date: 2025
"""

import cv2
import numpy as np
import requests
from datetime import datetime
import os
import json
import time
import winsound
from pathlib import Path
import threading


class ColorBasedFireDetection:
    def __init__(self, config_path="config.json"):
        """Initialize color-based fire detection"""
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Setup directories
        self.setup_directories()
        
        # Detection parameters
        self.confidence_threshold = 0.6  # Fixed for color-based
        self.fire_detected = False
        self.detection_count = 0
        self.last_alert_time = 0
        self.alert_cooldown = self.config['alert_cooldown']
        
        # Video recording
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        print("⚠️  Using COLOR-BASED fire detection (temporary solution)")
        print("⚠️  For better accuracy, train custom YOLOv8 model!")
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            default_config = {
                "esp32_cam_url": "http://192.168.2.100:81/stream",
                "alert_cooldown": 5,
                "enable_sound_alert": True,
                "enable_video_recording": True,
                "max_recording_duration": 60,
                "log_dir": "logs",
                "recordings_dir": "recordings",
                "display_window": True,
                "save_detection_images": True
            }
            return default_config
    
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config['log_dir'],
            self.config['recordings_dir'],
            'detections'
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def connect_to_stream(self):
        """Connect to ESP32-CAM MJPEG stream"""
        url = self.config['esp32_cam_url']
        print(f"🔌 Connecting to ESP32-CAM: {url}")
        
        try:
            stream = requests.get(url, stream=True, timeout=5)
            if stream.status_code == 200:
                print("✅ Connected to ESP32-CAM stream")
                return stream
            else:
                print(f"❌ Failed to connect: Status {stream.status_code}")
                return None
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return None
    
    def parse_mjpeg_stream(self, stream):
        """Parse MJPEG stream and yield frames"""
        bytes_data = b''
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                # Decode JPEG
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    yield frame
    
    def detect_fire(self, frame):
        """Detect fire using color-based method"""
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define fire color range in HSV
        # Fire is typically: Red-Orange-Yellow
        lower_fire1 = np.array([0, 100, 100])      # Red-Orange
        upper_fire1 = np.array([30, 255, 255])
        
        lower_fire2 = np.array([160, 100, 100])    # Red (wrap around)
        upper_fire2 = np.array([180, 255, 255])
        
        # Create masks
        mask1 = cv2.inRange(hsv, lower_fire1, upper_fire1)
        mask2 = cv2.inRange(hsv, lower_fire2, upper_fire2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area (minimum size)
            if area > 1000:  # Adjust threshold as needed
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate confidence based on area and color intensity
                confidence = min(0.9, area / 10000.0)
                
                detections.append({
                    'bbox': (x, y, x+w, y+h),
                    'confidence': confidence,
                    'class': 'fire (color)',
                    'area': area
                })
        
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on frame"""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            
            # Draw bounding box
            color = (0, 165, 255)  # Orange for fire
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"FIRE: {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def draw_info(self, frame, detections):
        """Draw information overlay on frame"""
        h, w = frame.shape[:2]
        
        # Status panel
        panel_height = 140
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Title
        cv2.putText(frame, "ESP32-CAM FIRE DETECTION (COLOR-BASED)", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Warning
        cv2.putText(frame, "WARNING: Color-based detection - Less accurate!", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
        
        # Status
        status_text = "🔥 FIRE DETECTED!" if len(detections) > 0 else "✓ Monitoring..."
        status_color = (0, 0, 255) if len(detections) > 0 else (0, 255, 0)
        cv2.putText(frame, status_text, (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Detection info
        info_text = f"Detections: {len(detections)} | FPS: {self.fps:.1f} | Total: {self.detection_count}"
        cv2.putText(frame, info_text, (10, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 130),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Recording indicator
        if self.is_recording:
            cv2.circle(frame, (w - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (w - 60, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame
    
    def log_detection(self, detections, frame):
        """Log fire detection to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.config['log_dir'], f"fire_detection_color_{log_date}.log")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"🔥 FIRE DETECTED (COLOR-BASED)!\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Number of detections: {len(detections)}\n")
            f.write(f"{'='*60}\n")
            
            for i, det in enumerate(detections, 1):
                f.write(f"\nDetection #{i}:\n")
                f.write(f"  Method: Color-based\n")
                f.write(f"  Confidence: {det['confidence']:.4f}\n")
                f.write(f"  Bounding Box: {det['bbox']}\n")
                f.write(f"  Area: {det.get('area', 0):.0f} pixels\n")
            
            f.write(f"\n{'='*60}\n\n")
        
        # Save detection image
        if self.config['save_detection_images']:
            img_filename = f"fire_color_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            img_path = os.path.join('detections', img_filename)
            cv2.imwrite(img_path, frame)
            print(f"💾 Saved detection image: {img_path}")
        
        print(f"📝 Logged detection to: {log_file}")
    
    def play_alert(self):
        """Play sound alert"""
        if self.config['enable_sound_alert']:
            current_time = time.time()
            if current_time - self.last_alert_time > self.alert_cooldown:
                threading.Thread(target=self._beep_sound, daemon=True).start()
                self.last_alert_time = current_time
    
    def _beep_sound(self):
        """Play beep sound in separate thread"""
        try:
            for _ in range(3):
                winsound.Beep(1000, 200)
                time.sleep(0.1)
        except:
            pass
    
    def start_recording(self, frame):
        """Start video recording"""
        if not self.config['enable_video_recording'] or self.is_recording:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fire_color_{timestamp}.avi"
        filepath = os.path.join(self.config['recordings_dir'], filename)
        
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(filepath, fourcc, 20.0, (w, h))
        
        self.is_recording = True
        self.recording_start_time = time.time()
        print(f"🎥 Started recording: {filepath}")
    
    def stop_recording(self):
        """Stop video recording"""
        if self.is_recording and self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            self.is_recording = False
            self.recording_start_time = None
            print("⏹️  Stopped recording")
    
    def update_recording(self, frame, detections):
        """Update video recording"""
        if len(detections) > 0:
            if not self.is_recording:
                self.start_recording(frame)
            elif self.is_recording:
                duration = time.time() - self.recording_start_time
                if duration > self.config['max_recording_duration']:
                    self.stop_recording()
                    self.start_recording(frame)
        else:
            if self.is_recording:
                duration = time.time() - self.recording_start_time
                if duration > 5:
                    self.stop_recording()
        
        if self.is_recording and self.video_writer is not None:
            self.video_writer.write(frame)
    
    def calculate_fps(self):
        """Calculate current FPS"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self):
        """Main detection loop"""
        print("\n" + "="*60)
        print("🔥 ESP32-CAM FIRE DETECTION (COLOR-BASED)")
        print("="*60)
        print(f"📍 ESP32-CAM URL: {self.config['esp32_cam_url']}")
        print(f"⚠️  Method: Color-based (Temporary)")
        print(f"⚠️  For better accuracy, train YOLOv8 model!")
        print("="*60)
        print("Press 'q' to quit, 's' to save screenshot, 'r' to toggle recording\n")
        
        # Connect to stream
        stream = self.connect_to_stream()
        if stream is None:
            print("❌ Failed to connect to ESP32-CAM. Exiting...")
            return
        
        try:
            for frame in self.parse_mjpeg_stream(stream):
                # Run fire detection
                detections = self.detect_fire(frame)
                
                # Handle detections
                if len(detections) > 0:
                    self.detection_count += len(detections)
                    self.log_detection(detections, frame)
                    self.play_alert()
                
                # Draw visualizations
                frame = self.draw_detections(frame, detections)
                frame = self.draw_info(frame, detections)
                
                # Update recording
                self.update_recording(frame, detections)
                
                # Calculate FPS
                self.calculate_fps()
                
                # Display frame
                if self.config['display_window']:
                    cv2.imshow('Fire Detection (Color-Based) - ESP32-CAM', frame)
                    
                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n👋 Quitting...")
                        break
                    elif key == ord('s'):
                        screenshot_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        cv2.imwrite(screenshot_name, frame)
                        print(f"📸 Screenshot saved: {screenshot_name}")
                    elif key == ord('r'):
                        if self.is_recording:
                            self.stop_recording()
                        else:
                            self.start_recording(frame)
        
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.stop_recording()
            cv2.destroyAllWindows()
            print("\n✅ System shutdown complete")


def main():
    """Main entry point"""
    print("\n⚠️  WARNING: This uses COLOR-BASED fire detection")
    print("⚠️  Less accurate than YOLOv8 - many false positives!")
    print("⚠️  For production, train custom YOLOv8 model")
    print("\nRead USE_FIRE_MODEL.md for instructions\n")
    
    response = input("Continue with color-based detection? (y/n) [y]: ").strip().lower()
    if response not in ['', 'y', 'yes']:
        print("Exiting...")
        return
    
    # Create detector
    detector = ColorBasedFireDetection()
    
    # Run detection
    detector.run()


if __name__ == "__main__":
    main()

"""
ESP32-CAM Fire Detection System with YOLOv8
============================================
Real-time fire detection menggunakan ESP32-CAM stream dan YOLOv8.
Fitur:
- Deteksi api real-time
- Logging otomatis saat deteksi
- Visualisasi dengan bounding box
- Alert system
- FPS counter
- Rekam video saat deteksi

Author: AI Assistant
Date: 2025
"""

import cv2
import numpy as np
from ultralytics import YOLO
import requests
from datetime import datetime
import os
import json
import time
import winsound
from pathlib import Path
import threading


class FireDetectionSystem:
    def __init__(self, config_path="config.json"):
        """Initialize fire detection system"""
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Setup directories
        self.setup_directories()
        
        # Check if model exists
        model_path = self.config['model_path']
        if not os.path.exists(model_path):
            print(f"\n❌ Model file not found: {model_path}")
            print("\n💡 Download model terlebih dahulu:")
            print("   Option 1 (Manual): python download_model_manual.py")
            print("   Option 2 (Auto):   python download_fire_model.py")
            print("\n   Atau jalankan manual:")
            print("   >>> from ultralytics import YOLO")
            print("   >>> model = YOLO('yolov8n.pt')  # Auto-download")
            print()
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        # Load YOLOv8 model
        print("📦 Loading YOLOv8 model...")
        try:
            self.model = YOLO(model_path)
            print(f"✅ Model loaded: {model_path}")
        except Exception as e:
            print(f"\n❌ Failed to load model: {e}")
            print("\n💡 Model mungkin corrupt. Download ulang:")
            print(f"   1. Hapus file: {model_path}")
            print("   2. Run: python download_model_manual.py")
            raise
        
        # Detection parameters
        self.confidence_threshold = self.config['confidence_threshold']
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
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            default_config = {
                "esp32_cam_url": "http://192.168.2.100:81/stream",
                "model_path": "models/yolov8n.pt",
                "confidence_threshold": 0.7,
                "alert_cooldown": 5,
                "enable_sound_alert": True,
                "enable_video_recording": True,
                "max_recording_duration": 60,
                "log_dir": "logs",
                "recordings_dir": "recordings",
                "display_window": True,
                "save_detection_images": True
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"⚙️  Created default config: {config_path}")
            return default_config
    
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config['log_dir'],
            self.config['recordings_dir'],
            'models',
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
        """Run fire detection on frame"""
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                
                # STRICT FILTER: Only detect if class name contains 'fire'
                # Note: YOLOv8n standard doesn't have 'fire' class!
                # You need to train custom model or use fire-specific model
                if 'fire' in class_name.lower():
                    # Additional size filter to reduce false positives
                    width = int(x2 - x1)
                    height = int(y2 - y1)
                    
                    # Skip very small detections (likely noise)
                    if width < 30 or height < 30:
                        continue
                    
                    detections.append({
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                        'confidence': confidence,
                        'class': class_name,
                        'class_id': class_id
                    })
        
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on frame"""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            class_name = det['class']
            
            # Draw bounding box
            color = (0, 0, 255)  # Red for fire
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{class_name}: {confidence:.2f}"
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
        panel_height = 120
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Title
        cv2.putText(frame, "ESP32-CAM FIRE DETECTION SYSTEM", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Status
        status_text = "🔥 FIRE DETECTED!" if len(detections) > 0 else "✓ Monitoring..."
        status_color = (0, 0, 255) if len(detections) > 0 else (0, 255, 0)
        cv2.putText(frame, status_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Detection info
        info_text = f"Detections: {len(detections)} | FPS: {self.fps:.1f} | Total: {self.detection_count}"
        cv2.putText(frame, info_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 110),
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
        log_file = os.path.join(self.config['log_dir'], f"fire_detection_{log_date}.log")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"🔥 FIRE DETECTED!\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Number of detections: {len(detections)}\n")
            f.write(f"{'='*60}\n")
            
            for i, det in enumerate(detections, 1):
                f.write(f"\nDetection #{i}:\n")
                f.write(f"  Class: {det['class']}\n")
                f.write(f"  Confidence: {det['confidence']:.4f}\n")
                f.write(f"  Bounding Box: {det['bbox']}\n")
            
            f.write(f"\n{'='*60}\n\n")
        
        # Save detection image
        if self.config['save_detection_images']:
            img_filename = f"fire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            img_path = os.path.join('detections', img_filename)
            cv2.imwrite(img_path, frame)
            print(f"💾 Saved detection image: {img_path}")
        
        print(f"📝 Logged detection to: {log_file}")
    
    def play_alert(self):
        """Play sound alert for fire detection"""
        if self.config['enable_sound_alert']:
            current_time = time.time()
            if current_time - self.last_alert_time > self.alert_cooldown:
                # Play Windows beep sound
                threading.Thread(target=self._beep_sound, daemon=True).start()
                self.last_alert_time = current_time
    
    def _beep_sound(self):
        """Play beep sound in separate thread"""
        try:
            for _ in range(3):
                winsound.Beep(1000, 200)  # 1000 Hz for 200ms
                time.sleep(0.1)
        except:
            pass
    
    def start_recording(self, frame):
        """Start video recording"""
        if not self.config['enable_video_recording'] or self.is_recording:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fire_recording_{timestamp}.avi"
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
        """Update video recording based on fire detection"""
        if len(detections) > 0:
            if not self.is_recording:
                self.start_recording(frame)
            elif self.is_recording:
                # Check max recording duration
                duration = time.time() - self.recording_start_time
                if duration > self.config['max_recording_duration']:
                    self.stop_recording()
                    self.start_recording(frame)  # Start new recording
        else:
            # Stop recording after 5 seconds of no detection
            if self.is_recording:
                duration = time.time() - self.recording_start_time
                if duration > 5:
                    self.stop_recording()
        
        # Write frame if recording
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
        print("🔥 ESP32-CAM FIRE DETECTION SYSTEM")
        print("="*60)
        print(f"📍 ESP32-CAM URL: {self.config['esp32_cam_url']}")
        print(f"🎯 Confidence Threshold: {self.confidence_threshold}")
        print(f"📁 Logs Directory: {self.config['log_dir']}")
        print(f"🎥 Recordings Directory: {self.config['recordings_dir']}")
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
                    cv2.imshow('Fire Detection - ESP32-CAM', frame)
                    
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
            # Cleanup
            self.stop_recording()
            cv2.destroyAllWindows()
            print("\n✅ System shutdown complete")


def main():
    """Main entry point"""
    # Create fire detection system
    detector = FireDetectionSystem()
    
    # Run detection
    detector.run()


if __name__ == "__main__":
    main()

"""
ESP32-CAM Fire Detection with YOLOv10
======================================
Advanced fire detection menggunakan YOLOv10 custom model dengan:
- Fire color enhancement (HSV boost)
- Verification system (color + area analysis)
- Multi-threshold confidence levels
- Morphological noise reduction
- Real-time logging dan recording

Inspired by: https://github.com/Nexuszzz/Pblyoloiot
Adapted for: ESP32-CAM streaming system

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


class YOLOv10FireDetection:
    def __init__(self, config_path="config_yolov10.json"):
        """Initialize YOLOv10 fire detection system"""
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Setup directories
        self.setup_directories()
        
        # Check if model exists
        model_path = self.config['model_path']
        if not os.path.exists(model_path):
            print(f"\n❌ Model file not found: {model_path}")
            print("\n💡 Download fire.pt model:")
            print("   1. Clone repo: git clone https://github.com/Nexuszzz/Pblyoloiot")
            print("   2. Copy fire.pt ke folder models/")
            print("   3. Or download dari trained model source")
            print()
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        # Load YOLOv10 model
        print("📦 Loading YOLOv10 fire detection model...")
        try:
            self.model = YOLO(model_path)
            print(f"✅ Model loaded: {model_path}")
            print(f"   Classes: {self.model.names}")
        except Exception as e:
            print(f"\n❌ Failed to load model: {e}")
            raise
        
        # Detection parameters
        self.conf_threshold = self.config['conf_threshold']
        self.high_conf_threshold = self.config['high_conf_threshold']
        self.min_fire_area = self.config['min_fire_area']
        self.max_fire_area = self.config['max_fire_area']
        self.fire_pixel_ratio_threshold = self.config['fire_pixel_ratio_threshold']
        
        # Enhancement parameters
        self.saturation_boost = self.config['saturation_boost']
        self.brightness_boost = self.config['brightness_boost']
        self.enable_fire_enhancement = self.config['enable_fire_enhancement']
        
        # System state
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
                "model_path": "models/fire.pt",
                "conf_threshold": 0.25,
                "high_conf_threshold": 0.45,
                "min_fire_area": 20,
                "max_fire_area": 100000,
                "fire_pixel_ratio_threshold": 0.10,
                "saturation_boost": 2.0,
                "brightness_boost": 1.5,
                "enable_fire_enhancement": True,
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
    
    def enhance_fire_visibility(self, frame):
        """Enhance the visibility of fire in the frame using HSV color boost"""
        if not self.enable_fire_enhancement:
            return frame
        
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define fire color ranges (red, orange, and yellow hues)
        lower_red1 = np.array([0, 30, 50])      # Expanded red range
        upper_red1 = np.array([20, 255, 255])   # Include more orange
        lower_red2 = np.array([160, 30, 50])    # Expanded red range
        upper_red2 = np.array([180, 255, 255])  # Include brighter reds
        
        # Create masks for fire colors
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        fire_mask = cv2.bitwise_or(mask1, mask2)
        
        # Enhance saturation and brightness in fire regions
        hsv_enhanced = hsv.copy()
        hsv_enhanced[:,:,1] = np.clip(hsv[:,:,1] * self.saturation_boost, 0, 255).astype(np.uint8)
        hsv_enhanced[:,:,2] = np.clip(hsv[:,:,2] * self.brightness_boost, 0, 255).astype(np.uint8)
        
        # Apply enhancement only to fire-colored regions
        hsv_enhanced = cv2.bitwise_and(hsv_enhanced, hsv_enhanced, mask=fire_mask)
        hsv = cv2.bitwise_and(hsv, hsv, mask=~fire_mask)
        hsv = cv2.add(hsv, hsv_enhanced)
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return enhanced
    
    def verify_fire_detection(self, frame, box):
        """Additional verification for fire detection using color analysis"""
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        area = (x2 - x1) * (y2 - y1)
        
        # Check if detection area is within reasonable bounds
        if area < self.min_fire_area or area > self.max_fire_area:
            return False, 0, area
        
        # Extract the region of interest
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False, 0, area
        
        # Convert to HSV for color analysis
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Define fire color ranges
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        # Calculate percentage of fire-colored pixels
        mask1 = cv2.inRange(hsv_roi, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv_roi, lower_red2, upper_red2)
        fire_mask = cv2.bitwise_or(mask1, mask2)
        
        # Add morphological operations to reduce noise
        kernel = np.ones((3,3), np.uint8)
        fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_OPEN, kernel)
        fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)
        
        fire_pixel_ratio = np.count_nonzero(fire_mask) / fire_mask.size
        
        # Verify fire pixel ratio
        is_fire = fire_pixel_ratio > self.fire_pixel_ratio_threshold
        
        return is_fire, fire_pixel_ratio, area
    
    def detect_fire(self, frame):
        """Run fire detection with enhancement and verification"""
        # Enhance frame to make fire more visible
        enhanced_frame = self.enhance_fire_visibility(frame)
        
        # Run YOLO detection
        results = self.model(enhanced_frame, conf=self.conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                
                # Verify fire detection
                is_verified, fire_ratio, area = self.verify_fire_detection(frame, box)
                
                if is_verified:
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': confidence,
                        'class': class_name,
                        'class_id': class_id,
                        'area': area,
                        'fire_ratio': fire_ratio,
                        'high_confidence': confidence > self.high_conf_threshold
                    })
        
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on frame"""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            class_name = det['class']
            area = det['area']
            fire_ratio = det['fire_ratio']
            
            # Color based on confidence
            if det['high_confidence']:
                color = (0, 0, 255)  # Red for high confidence
                thickness = 3
                conf_level = "HIGH"
            else:
                color = (0, 165, 255)  # Orange for lower confidence
                thickness = 2
                conf_level = "MED"
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label with confidence
            label = f"{class_name} {confidence:.2f} [{conf_level}]"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Background for label
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw area and fire ratio info
            info_text = f"Area: {area}px | Fire: {fire_ratio*100:.1f}%"
            cv2.putText(frame, info_text, (x1, y2 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
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
        cv2.putText(frame, "ESP32-CAM FIRE DETECTION - YOLOv10", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Model info
        cv2.putText(frame, f"Model: {os.path.basename(self.config['model_path'])}", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Status
        if len(detections) > 0:
            high_conf_count = sum(1 for d in detections if d['high_confidence'])
            status_text = f"🔥 FIRE DETECTED! ({high_conf_count} HIGH CONF)"
            status_color = (0, 0, 255)
        else:
            status_text = "✓ Monitoring..."
            status_color = (0, 255, 0)
        
        cv2.putText(frame, status_text, (10, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Detection info
        info_text = f"Detections: {len(detections)} | FPS: {self.fps:.1f} | Total: {self.detection_count}"
        cv2.putText(frame, info_text, (10, 110),
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
        log_file = os.path.join(self.config['log_dir'], f"fire_yolov10_{log_date}.log")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"🔥 FIRE DETECTED (YOLOv10)!\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Number of detections: {len(detections)}\n")
            f.write(f"{'='*70}\n")
            
            for i, det in enumerate(detections, 1):
                f.write(f"\nDetection #{i}:\n")
                f.write(f"  Class: {det['class']}\n")
                f.write(f"  Confidence: {det['confidence']:.4f}\n")
                f.write(f"  Confidence Level: {'HIGH' if det['high_confidence'] else 'MEDIUM'}\n")
                f.write(f"  Bounding Box: {det['bbox']}\n")
                f.write(f"  Area: {det['area']} pixels\n")
                f.write(f"  Fire Pixel Ratio: {det['fire_ratio']*100:.2f}%\n")
            
            f.write(f"\n{'='*70}\n\n")
        
        # Save detection image
        if self.config['save_detection_images']:
            img_filename = f"fire_yolov10_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
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
        filename = f"fire_yolov10_{timestamp}.avi"
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
        print("\n" + "="*70)
        print("🔥 ESP32-CAM FIRE DETECTION SYSTEM - YOLOv10")
        print("="*70)
        print(f"📍 ESP32-CAM URL: {self.config['esp32_cam_url']}")
        print(f"🎯 Confidence Threshold: {self.conf_threshold} (High: {self.high_conf_threshold})")
        print(f"📊 Min Fire Area: {self.min_fire_area}px | Max: {self.max_fire_area}px")
        print(f"🎨 Fire Enhancement: {'Enabled' if self.enable_fire_enhancement else 'Disabled'}")
        print(f"📁 Logs: {self.config['log_dir']} | Recordings: {self.config['recordings_dir']}")
        print("="*70)
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
                    cv2.imshow('Fire Detection - YOLOv10 - ESP32-CAM', frame)
                    
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
            import traceback
            traceback.print_exc()
        finally:
            self.stop_recording()
            cv2.destroyAllWindows()
            print("\n✅ System shutdown complete")


def main():
    """Main entry point"""
    # Create fire detection system
    detector = YOLOv10FireDetection()
    
    # Run detection
    detector.run()


if __name__ == "__main__":
    main()

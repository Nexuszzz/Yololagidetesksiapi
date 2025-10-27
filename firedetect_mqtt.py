"""
ESP32-CAM Fire Detection with YOLOv10 + MQTT
============================================
- Baca stream MJPEG ESP32-CAM
- Deteksi api dengan YOLOv10 + verifikasi warna/area
- Publish MQTT alert ke lab/zaks/alert (agar ESP32 DevKit bereaksi)

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
import uuid
from pathlib import Path

# ============ MQTT ============
import paho.mqtt.client as mqtt


class YOLOv10FireDetectionMQTT:
    def __init__(self, config_path="config_yolov10.json"):
        """Initialize fire detection with MQTT"""
        print("\n" + "="*70)
        print("🔥 ESP32-CAM FIRE DETECTION - YOLOv10 + MQTT")
        print("="*70)
        
        self.config = self.load_config(config_path)
        self.setup_directories()
        
        # Load model
        model_path = self.config['model_path']
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"❌ Model not found: {model_path}\n"
                f"💡 Download with: python get_fire_model.py"
            )
        
        print(f"📦 Loading YOLOv10 model: {model_path}")
        self.model = YOLO(model_path)
        print(f"✅ Model loaded successfully!")
        
        # Detection parameters
        self.conf_threshold = self.config['conf_threshold']
        self.high_conf_threshold = self.config['high_conf_threshold']
        self.min_fire_area = self.config['min_fire_area']
        self.max_fire_area = self.config['max_fire_area']
        self.fire_pixel_ratio_threshold = self.config['fire_pixel_ratio_threshold']
        self.saturation_boost = self.config['saturation_boost']
        self.brightness_boost = self.config['brightness_boost']
        self.enable_fire_enhancement = self.config['enable_fire_enhancement']
        self.alert_cooldown = self.config['alert_cooldown']
        self.enable_video_recording = self.config['enable_video_recording']
        self.max_recording_duration = self.config['max_recording_duration']
        self.display_window = self.config['display_window']
        self.save_detection_images = self.config['save_detection_images']
        
        # State
        self.detection_count = 0
        self.last_alert_time = 0
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # MQTT
        self.mq = None
        self.mqtt_cfg = self.config.get("mqtt", {})
        self.client_id = f"yolo-fire-{uuid.getnode():x}"
        
        if self.mqtt_cfg:
            self.connect_mqtt()
        else:
            print("⚠️  MQTT config not found, running without MQTT")
    
    # ==================== CONFIG ====================
    def load_config(self, config_path):
        """Load or create config file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                cfg = json.load(f)
            
            # Add MQTT config if missing
            if "mqtt" not in cfg:
                cfg["mqtt"] = {
                    "host": "13.213.57.228",
                    "port": 1883,
                    "user": "zaks",
                    "password": "engganngodinginginmcu",
                    "topic_alert": "lab/zaks/alert",
                    "topic_event": "lab/zaks/event"
                }
                with open(config_path, 'w') as f:
                    json.dump(cfg, f, indent=4)
                print(f"⚙️  Updated config with MQTT settings")
        else:
            # Create default config
            cfg = {
                "esp32_cam_url": "http://10.75.111.90:81/stream",
                "model_path": "models/fire.pt",
                "conf_threshold": 0.25,
                "high_conf_threshold": 0.45,
                "min_fire_area": 20,
                "max_fire_area": 200000,
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
                "save_detection_images": True,
                "mqtt": {
                    "host": "13.213.57.228",
                    "port": 1883,
                    "user": "zaks",
                    "password": "engganngodinginginmcu",
                    "topic_alert": "lab/zaks/alert",
                    "topic_event": "lab/zaks/event"
                }
            }
            with open(config_path, 'w') as f:
                json.dump(cfg, f, indent=4)
            print(f"⚙️  Created default config: {config_path}")
        
        return cfg
    
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config['log_dir'],
            self.config['recordings_dir'],
            'models',
            'detections'
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
    
    # ==================== MQTT ====================
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mq = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
            
            if self.mqtt_cfg.get("user"):
                self.mq.username_pw_set(
                    self.mqtt_cfg["user"],
                    self.mqtt_cfg["password"]
                )
            
            self.mq.connect(
                self.mqtt_cfg["host"],
                int(self.mqtt_cfg["port"]),
                60
            )
            self.mq.loop_start()
            
            # Send online event
            self.publish_event({"event": "yolo_online"})
            print(f"📡 MQTT connected: {self.mqtt_cfg['host']}:{self.mqtt_cfg['port']}")
            
        except Exception as e:
            print(f"⚠️  MQTT connection failed: {e}")
            print(f"   Continuing without MQTT...")
            self.mq = None
    
    def publish_event(self, obj: dict):
        """Publish event to MQTT"""
        if not self.mq:
            return
        
        obj = {
            "id": self.client_id,
            **obj,
            "ts": int(time.time())
        }
        
        try:
            self.mq.publish(
                self.mqtt_cfg["topic_event"],
                json.dumps(obj),
                qos=0,
                retain=False
            )
        except Exception as e:
            print(f"⚠️  MQTT publish event error: {e}")
    
    def publish_alert(self, conf: float, bbox=None):
        """Publish fire alert to MQTT"""
        if not self.mq:
            return
        
        payload = {
            "id": self.client_id,
            "src": "yolo_fire",
            "alert": "flame_detected",
            "conf": float(conf),
            "bbox": [int(v) for v in bbox] if bbox is not None else None,
            "ts": int(time.time())
        }
        
        try:
            self.mq.publish(
                self.mqtt_cfg["topic_alert"],
                json.dumps(payload),
                qos=1,
                retain=False
            )
            print(f"📡 MQTT Alert sent: conf={conf:.2f} bbox={bbox}")
        except Exception as e:
            print(f"⚠️  MQTT publish alert error: {e}")
    
    # ==================== STREAM ====================
    def connect_to_stream(self):
        """Connect to ESP32-CAM MJPEG stream"""
        url = self.config['esp32_cam_url']
        print(f"\n🔌 Connecting to ESP32-CAM: {url}")
        
        try:
            r = requests.get(url, stream=True, timeout=5)
            if r.status_code == 200:
                print("✅ Stream connected successfully!")
                return r
        except Exception as e:
            print(f"❌ Stream connection error: {e}")
        
        return None
    
    def parse_mjpeg_stream(self, stream):
        """Parse MJPEG stream into frames"""
        bytes_data = b''
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                frame = cv2.imdecode(
                    np.frombuffer(jpg, dtype=np.uint8),
                    cv2.IMREAD_COLOR
                )
                
                if frame is not None:
                    yield frame
    
    def frames(self):
        """Generator for video frames"""
        stream = self.connect_to_stream()
        
        if stream is None:
            print("\n❌ Cannot connect to ESP32-CAM stream")
            print("💡 Check:")
            print("   1. ESP32-CAM is powered on")
            print("   2. WiFi connection is active")
            print("   3. IP address in config_yolov10.json is correct")
            print(f"   4. Try opening in browser: {self.config['esp32_cam_url']}")
            return
        
        yield from self.parse_mjpeg_stream(stream)
    
    # ==================== VISION ====================
    def enhance_fire_visibility(self, frame):
        """Enhance fire colors (HSV boost)"""
        if not self.enable_fire_enhancement:
            return frame
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Fire color range (red-orange-yellow)
        lower1 = np.array([0, 30, 50])
        upper1 = np.array([20, 255, 255])
        lower2 = np.array([160, 30, 50])
        upper2 = np.array([180, 255, 255])
        
        mask = cv2.bitwise_or(
            cv2.inRange(hsv, lower1, upper1),
            cv2.inRange(hsv, lower2, upper2)
        )
        
        # Boost saturation and brightness
        hsv_enhanced = hsv.copy()
        hsv_enhanced[:, :, 1] = np.clip(
            hsv[:, :, 1] * self.saturation_boost, 0, 255
        ).astype(np.uint8)
        hsv_enhanced[:, :, 2] = np.clip(
            hsv[:, :, 2] * self.brightness_boost, 0, 255
        ).astype(np.uint8)
        
        # Apply enhancement only to fire regions
        hsv = cv2.bitwise_and(hsv, hsv, mask=~mask)
        hsv = cv2.add(hsv, cv2.bitwise_and(hsv_enhanced, hsv_enhanced, mask=mask))
        
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def verify_fire(self, frame, box):
        """Verify fire detection with color analysis"""
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        area = (x2 - x1) * (y2 - y1)
        
        # Area check
        if area < self.min_fire_area or area > self.max_fire_area:
            return False, 0.0, area
        
        # Extract ROI
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False, 0.0, area
        
        # Color analysis
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        lower1 = np.array([0, 50, 50])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([170, 50, 50])
        upper2 = np.array([180, 255, 255])
        
        mask = cv2.bitwise_or(
            cv2.inRange(hsv, lower1, upper1),
            cv2.inRange(hsv, lower2, upper2)
        )
        
        # Morphological operations (noise reduction)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Calculate fire pixel ratio
        ratio = float(np.count_nonzero(mask)) / float(mask.size)
        
        return (ratio > self.fire_pixel_ratio_threshold), ratio, area
    
    def detect_fire(self, frame):
        """Detect fire in frame"""
        enhanced = self.enhance_fire_visibility(frame)
        results = self.model(enhanced, conf=self.conf_threshold, verbose=False)
        
        detections = []
        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.model.names.get(cls_id, str(cls_id))
                
                # Verify with color analysis
                is_fire, ratio, area = self.verify_fire(frame, box)
                
                if is_fire:
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    detections.append({
                        "bbox": (x1, y1, x2, y2),
                        "confidence": conf,
                        "class": cls_name,
                        "class_id": cls_id,
                        "area": area,
                        "fire_ratio": ratio,
                        "high_confidence": conf > self.high_conf_threshold
                    })
        
        return detections
    
    # ==================== UI/LOG ====================
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels"""
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            conf = d["confidence"]
            area = d["area"]
            ratio = d["fire_ratio"]
            
            # Color based on confidence
            color = (0, 0, 255) if d["high_confidence"] else (0, 165, 255)  # Red or Orange
            thick = 3 if d["high_confidence"] else 2
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thick)
            
            # Label
            label = f"{d['class']} {conf:.2f} [{'HIGH' if d['high_confidence'] else 'MED'}]"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 4),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Info
            info = f"Area:{area}px | Fire:{ratio*100:.1f}%"
            cv2.putText(frame, info, (x1, y2 + 18),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame
    
    def draw_info_panel(self, frame, detections):
        """Draw info panel on frame"""
        h, w = frame.shape[:2]
        panel_h = 120
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
        
        # Status
        status = "🔥 FIRE DETECTED!" if detections else "✓ Monitoring..."
        color = (0, 0, 255) if detections else (0, 255, 0)
        
        # Title
        cv2.putText(frame, "ESP32-CAM FIRE DETECTION - YOLOv10 + MQTT",
                   (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Status
        cv2.putText(frame, status, (10, 58),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Stats
        cv2.putText(frame, f"FPS: {self.fps:.1f} | Total Detections: {self.detection_count}",
                   (10, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        
        # Timestamp
        cv2.putText(frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   (10, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Recording indicator
        if self.is_recording:
            cv2.circle(frame, (w - 28, 26), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (w - 64, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        
        return frame
    
    def log_detection(self, detections, frame):
        """Log detection to file"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = os.path.join(
            self.config['log_dir'],
            f"fire_mqtt_{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"🔥 FIRE DETECTED @ {ts}\n")
            f.write(f"{'='*70}\n")
            for i, d in enumerate(detections, 1):
                f.write(
                    f"#{i} | {d['class']} | "
                    f"conf={d['confidence']:.3f} | "
                    f"area={d['area']}px | "
                    f"fire_ratio={d['fire_ratio']:.3f} | "
                    f"bbox={d['bbox']}\n"
                )
        
        # Save image
        if self.save_detection_images:
            out = os.path.join(
                'detections',
                f"fire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            cv2.imwrite(out, frame)
            print(f"💾 Detection saved: {out}")
    
    # ==================== RECORDING ====================
    def start_recording(self, frame):
        """Start video recording"""
        if not self.enable_video_recording or self.is_recording:
            return
        
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out_path = os.path.join(
            self.config['recordings_dir'],
            f"fire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        )
        
        self.video_writer = cv2.VideoWriter(out_path, fourcc, 20.0, (w, h))
        self.is_recording = True
        self.recording_start_time = time.time()
        print(f"🎥 Recording started: {out_path}")
    
    def stop_recording(self):
        """Stop video recording"""
        if self.is_recording and self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            print("⏹️  Recording stopped")
        
        self.is_recording = False
        self.recording_start_time = None
    
    def update_recording(self, frame, detections):
        """Update recording state"""
        if detections:
            # Start recording if fire detected
            if not self.is_recording:
                self.start_recording(frame)
            # Restart if max duration reached
            elif time.time() - self.recording_start_time > self.max_recording_duration:
                self.stop_recording()
                self.start_recording(frame)
        else:
            # Stop recording 5 seconds after last detection
            if self.is_recording and time.time() - self.recording_start_time > 5:
                self.stop_recording()
        
        # Write frame if recording
        if self.is_recording and self.video_writer is not None:
            self.video_writer.write(frame)
    
    # ==================== FPS ====================
    def update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
    
    # ==================== MAIN LOOP ====================
    def run(self):
        """Main detection loop"""
        print("\n" + "="*70)
        print(f"📍 Stream URL: {self.config['esp32_cam_url']}")
        print(f"🎯 Confidence: {self.conf_threshold} (High: {self.high_conf_threshold})")
        print(f"📡 MQTT: {'Enabled' if self.mq else 'Disabled'}")
        print("="*70)
        print("\n⌨️  Controls:")
        print("   q = Quit")
        print("   s = Save screenshot")
        print("   r = Toggle recording")
        print("\n")
        
        last_heartbeat = 0
        
        try:
            for frame in self.frames():
                # Detect fire
                detections = self.detect_fire(frame)
                
                # Handle detections
                if detections:
                    self.detection_count += len(detections)
                    
                    # MQTT alert (with cooldown)
                    now = time.time()
                    if now - self.last_alert_time > self.alert_cooldown:
                        best = max(detections, key=lambda d: d["confidence"])
                        self.publish_alert(best["confidence"], best["bbox"])
                        self.last_alert_time = now
                    
                    # Log
                    self.log_detection(detections, frame)
                
                # Draw UI
                frame = self.draw_detections(frame, detections)
                frame = self.draw_info_panel(frame, detections)
                
                # Recording
                self.update_recording(frame, detections)
                
                # FPS
                self.update_fps()
                
                # Display
                if self.display_window:
                    cv2.imshow("Fire Detection - YOLOv10 + MQTT", frame)
                    key = cv2.waitKey(1) & 0xFF
                    
                    if key == ord('q'):
                        break
                    elif key == ord('r'):
                        if self.is_recording:
                            self.stop_recording()
                        else:
                            self.start_recording(frame)
                    elif key == ord('s'):
                        out = os.path.join(
                            'detections',
                            f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        )
                        cv2.imwrite(out, frame)
                        print(f"📸 Screenshot: {out}")
                
                # MQTT heartbeat (every 30 seconds)
                if self.mq and (time.time() - last_heartbeat) > 30:
                    last_heartbeat = time.time()
                    self.publish_event({
                        "event": "heartbeat",
                        "fps": round(self.fps, 2),
                        "detections": self.detection_count
                    })
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
        
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            self.stop_recording()
            
            if self.mq:
                self.publish_event({"event": "yolo_offline"})
                self.mq.loop_stop()
                try:
                    self.mq.disconnect()
                except:
                    pass
            
            cv2.destroyAllWindows()
            print("\n✅ Shutdown complete")


def main():
    """Main entry point"""
    try:
        detector = YOLOv10FireDetectionMQTT()
        detector.run()
    except FileNotFoundError as e:
        print(f"\n{e}")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

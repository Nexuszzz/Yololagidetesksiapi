"""
Script untuk test koneksi ke ESP32-CAM stream
==============================================
Script sederhana untuk memastikan ESP32-CAM streaming dengan baik.

Author: AI Assistant
Date: 2025
"""

import cv2
import numpy as np
import requests
from datetime import datetime
import time


def test_esp32_stream(url="http://192.168.2.100:81/stream", duration=10):
    """
    Test ESP32-CAM MJPEG stream
    
    Args:
        url: URL ESP32-CAM stream
        duration: Durasi test dalam detik (0 untuk unlimited)
    """
    print("="*60)
    print("🎥 ESP32-CAM STREAM TEST")
    print("="*60)
    print(f"📍 URL: {url}")
    print(f"⏱️  Duration: {duration}s" if duration > 0 else "⏱️  Duration: Unlimited")
    print("="*60)
    print("\nPress 'q' to quit, 's' to save screenshot\n")
    
    # Try to connect
    print("🔌 Connecting to ESP32-CAM...")
    try:
        stream = requests.get(url, stream=True, timeout=5)
        if stream.status_code != 200:
            print(f"❌ Connection failed: Status {stream.status_code}")
            return False
        print("✅ Connected successfully!\n")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Pastikan ESP32-CAM sudah dinyalakan")
        print("   2. Cek IP address ESP32-CAM di Serial Monitor")
        print("   3. Pastikan PC dan ESP32-CAM dalam network yang sama")
        print("   4. Update URL di config.json jika IP berbeda")
        return False
    
    # Parse stream
    bytes_data = b''
    frame_count = 0
    start_time = time.time()
    fps_start = start_time
    fps_frames = 0
    current_fps = 0
    
    try:
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                # Decode frame
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    frame_count += 1
                    fps_frames += 1
                    
                    # Calculate FPS
                    elapsed = time.time() - fps_start
                    if elapsed > 1.0:
                        current_fps = fps_frames / elapsed
                        fps_frames = 0
                        fps_start = time.time()
                    
                    # Get frame info
                    h, w = frame.shape[:2]
                    
                    # Draw info overlay
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
                    
                    # Info text
                    cv2.putText(frame, "ESP32-CAM STREAM TEST", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"FPS: {current_fps:.1f} | Frames: {frame_count} | Size: {w}x{h}", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, 85),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                    
                    # Display
                    cv2.imshow('ESP32-CAM Stream Test', frame)
                    
                    # Handle keys
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n⏹️  Stopped by user")
                        break
                    elif key == ord('s'):
                        filename = f"esp32_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        cv2.imwrite(filename, frame)
                        print(f"📸 Screenshot saved: {filename}")
                    
                    # Check duration
                    if duration > 0 and (time.time() - start_time) > duration:
                        print(f"\n⏱️  Test duration completed ({duration}s)")
                        break
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        cv2.destroyAllWindows()
        
        # Statistics
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        
        print("\n" + "="*60)
        print("📊 TEST STATISTICS")
        print("="*60)
        print(f"⏱️  Total Duration: {total_time:.2f}s")
        print(f"🎞️  Total Frames: {frame_count}")
        print(f"📈 Average FPS: {avg_fps:.2f}")
        print(f"✅ Status: {'SUCCESS' if frame_count > 0 else 'FAILED'}")
        print("="*60)
        
        return frame_count > 0


def ping_esp32(ip="192.168.2.100"):
    """
    Ping ESP32-CAM untuk cek koneksi
    
    Args:
        ip: IP address ESP32-CAM
    """
    import subprocess
    import platform
    
    print(f"\n🏓 Pinging {ip}...")
    
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', ip]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ ESP32-CAM is reachable!")
            return True
        else:
            print("❌ ESP32-CAM is not reachable!")
            return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ESP32-CAM Stream')
    parser.add_argument('--url', type=str, default='http://192.168.2.100:81/stream',
                       help='ESP32-CAM stream URL')
    parser.add_argument('--duration', type=int, default=0,
                       help='Test duration in seconds (0 for unlimited)')
    parser.add_argument('--ping', action='store_true',
                       help='Ping ESP32-CAM before testing')
    
    args = parser.parse_args()
    
    # Extract IP from URL for ping
    if args.ping:
        try:
            ip = args.url.split('//')[1].split(':')[0]
            ping_esp32(ip)
            print()
        except:
            print("⚠️  Could not extract IP for ping\n")
    
    # Test stream
    success = test_esp32_stream(args.url, args.duration)
    
    if success:
        print("\n✅ Stream test PASSED!")
        print("💡 ESP32-CAM siap digunakan untuk fire detection!")
    else:
        print("\n❌ Stream test FAILED!")
        print("\n💡 Troubleshooting:")
        print("   1. Cek Serial Monitor ESP32-CAM untuk IP address")
        print("   2. Pastikan WiFi credentials benar")
        print("   3. Test ping ESP32-CAM: python test_esp32_stream.py --ping")
        print("   4. Buka browser dan akses: http://192.168.2.100:81/stream")


if __name__ == "__main__":
    main()

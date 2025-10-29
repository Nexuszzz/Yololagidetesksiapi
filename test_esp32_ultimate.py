"""
Quick Test for ESP32-CAM Stream
Test MJPEG stream before running full detector
"""

import cv2
import numpy as np
import requests
import time

ESP32_URL = "http://10.75.111.108:81/stream"

print("\n" + "="*70)
print("📹 ESP32-CAM STREAM TEST")
print("="*70)
print(f"URL: {ESP32_URL}\n")

# Test 1: HTTP Connection
print("Test 1: HTTP Connection...")
try:
    response = requests.get(ESP32_URL, stream=True, timeout=5)
    if response.status_code == 200:
        print("✅ HTTP connection OK (status 200)")
    else:
        print(f"❌ HTTP error: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n💡 Solutions:")
    print("   1. Check ESP32-CAM power ON")
    print("   2. Check WiFi connection")
    print("   3. Verify IP address: http://10.75.111.108:81/stream")
    print("   4. Try opening URL in browser")
    exit(1)

# Test 2: Frame Parsing
print("\nTest 2: Frame Parsing...")
bytes_buffer = b''
frame_count = 0
start_time = time.time()

try:
    for chunk in response.iter_content(chunk_size=4096):
        if not chunk:
            continue
        
        bytes_buffer += chunk
        
        # Limit buffer
        if len(bytes_buffer) > 5 * 1024 * 1024:  # 5MB
            bytes_buffer = bytes_buffer[-5*1024*1024:]
        
        # Find JPEG
        jpeg_start = bytes_buffer.find(b'\xff\xd8')
        jpeg_end = bytes_buffer.find(b'\xff\xd9')
        
        if jpeg_start != -1 and jpeg_end != -1 and jpeg_end > jpeg_start:
            jpg = bytes_buffer[jpeg_start:jpeg_end+2]
            bytes_buffer = bytes_buffer[jpeg_end+2:]
            
            # Decode
            img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            if img is not None and img.size > 0:
                frame_count += 1
                
                if frame_count == 1:
                    print(f"✅ First frame decoded! Size: {img.shape[1]}x{img.shape[0]}")
                
                # Draw info
                cv2.putText(img, f"Frame: {frame_count}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(img, "Press 'q' to quit", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow("ESP32-CAM Stream Test", img)
                
                if frame_count >= 10:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"✅ Received {frame_count} frames in {elapsed:.1f}s")
                    print(f"✅ FPS: {fps:.1f}")
                    print("\n🎉 ESP32-CAM stream is working!")
                    print("   You can now run: python fire_detect_ultimate.py")
                    break
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n⚠️  Test stopped by user")
                    break

except KeyboardInterrupt:
    print("\n⚠️  Test interrupted")
except Exception as e:
    print(f"\n❌ Stream error: {e}")
    print("\n💡 Solutions:")
    print("   1. Check ESP32-CAM not in use by other program")
    print("   2. Restart ESP32-CAM")
    print("   3. Check network stability")
finally:
    cv2.destroyAllWindows()
    
print("\n" + "="*70)
print("Test complete")
print("="*70)

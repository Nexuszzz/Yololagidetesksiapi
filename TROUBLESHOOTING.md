# 🔧 Troubleshooting Guide

Panduan lengkap untuk mengatasi masalah umum pada ESP32-CAM Fire Detection System.

---

## 📋 Quick Diagnostics

Jalankan diagnostics ini terlebih dahulu:

```bash
# 1. Check Python version
python --version

# 2. Check dependencies
pip list | findstr "ultralytics opencv torch"

# 3. Test ESP32 connection
python test_esp32_stream.py --ping

# 4. Test stream
python test_esp32_stream.py
```

---

## 🔴 ESP32-CAM Issues

### Problem: Cannot Upload to ESP32-CAM

**Symptoms:**
- "Failed to connect to ESP32"
- "A fatal error occurred"
- Stuck at "Connecting..."

**Solutions:**

1. **Check Wiring:**
   ```
   FTDI → ESP32-CAM
   5V   → 5V
   GND  → GND
   TX   → U0R
   RX   → U0T
   GND  → GPIO 0 (untuk upload!)
   ```

2. **Upload Procedure:**
   - Connect GPIO 0 to GND
   - Click Upload in Arduino IDE
   - Wait for "Connecting..."
   - Press and hold RESET button
   - Wait 2 seconds
   - Release RESET button
   - Upload should start

3. **Check Driver:**
   - Windows: Install CH340/CP2102 driver
   - Download from manufacturer website

4. **Try Different USB Port:**
   - Some USB ports provide insufficient power
   - Try USB 2.0 instead of USB 3.0

5. **Check Arduino IDE Settings:**
   ```
   Board: AI Thinker ESP32-CAM
   Upload Speed: 115200 (try 9600 if failed)
   Flash Frequency: 80MHz
   PSRAM: Enabled
   Partition: Huge APP (3MB No OTA)
   ```

---

### Problem: Brownout Detector Triggered

**Symptoms:**
- ESP32 keeps rebooting
- Serial Monitor shows: "Brownout detector was triggered"
- Camera works but reboots randomly

**Solutions:**

1. **Better Power Supply:**
   - Use 5V 2A power supply
   - Don't power from USB (insufficient current)
   - Use quality power adapter

2. **Add Capacitor:**
   - Add 220µF-470µF capacitor between 5V and GND
   - Place as close to ESP32-CAM as possible
   - Helps stabilize voltage

3. **Reduce Power Consumption:**
   ```cpp
   // Disable flash LED
   pinMode(4, OUTPUT);
   digitalWrite(4, LOW);
   
   // Lower camera frequency
   config.xclk_freq_hz = 10000000; // 10MHz instead of 20MHz
   
   // Reduce frame size
   config.frame_size = FRAMESIZE_QVGA;
   ```

4. **Check Connections:**
   - Loose wires can cause voltage drops
   - Use short, thick wires
   - Solder connections for production

---

### Problem: Camera Init Failed

**Symptoms:**
- "Camera init failed 0x20001" or similar error code
- Camera doesn't start

**Solutions:**

1. **Enable PSRAM:**
   - Tools → PSRAM: Enabled

2. **Check Partition Scheme:**
   - Tools → Partition Scheme: Huge APP (3MB No OTA)

3. **Reset Camera Module:**
   ```cpp
   // Add to setup() before esp_camera_init()
   pinMode(PWDN_GPIO_NUM, OUTPUT);
   digitalWrite(PWDN_GPIO_NUM, LOW);
   delay(100);
   digitalWrite(PWDN_GPIO_NUM, HIGH);
   delay(100);
   ```

4. **Check Camera Ribbon:**
   - Camera ribbon cable properly inserted
   - Blue side facing away from ESP32
   - Connection is secure

5. **Try Different Frame Size:**
   ```cpp
   config.frame_size = FRAMESIZE_SVGA;  // Try different sizes
   ```

---

### Problem: WiFi Connection Failed

**Symptoms:**
- Cannot connect to WiFi
- Timeout after dots
- Wrong IP or no IP

**Solutions:**

1. **Check Credentials:**
   ```cpp
   const char* WIFI_SSID = "YourSSID";      // Case-sensitive!
   const char* WIFI_PASS = "YourPassword";   // Check for typos
   ```

2. **WiFi Band:**
   - ESP32 only supports 2.4GHz
   - Check router settings
   - Disable 5GHz if auto-switching

3. **Signal Strength:**
   - Move closer to router
   - Check antenna connection
   - Avoid metal enclosures

4. **Router Settings:**
   - Enable 2.4GHz band
   - Check MAC filtering (disable or add ESP32)
   - Check maximum connected devices limit

5. **Add WiFi Diagnostics:**
   ```cpp
   WiFi.disconnect(true);
   delay(1000);
   WiFi.mode(WIFI_STA);
   WiFi.begin(WIFI_SSID, WIFI_PASS);
   
   int retries = 0;
   while (WiFi.status() != WL_CONNECTED && retries < 20) {
     delay(500);
     Serial.print(".");
     Serial.print(WiFi.status()); // Print status code
     retries++;
   }
   ```

   Status codes:
   - 0 = WL_IDLE_STATUS
   - 1 = WL_NO_SSID_AVAIL (SSID not found)
   - 3 = WL_CONNECTED
   - 4 = WL_CONNECT_FAILED (wrong password)
   - 6 = WL_DISCONNECTED

---

### Problem: Stream Not Accessible

**Symptoms:**
- ESP32 connected to WiFi but stream URL doesn't work
- Browser shows "Connection refused"

**Solutions:**

1. **Check IP Address:**
   - Note exact IP from Serial Monitor
   - Try: `http://IP_ADDRESS:81/stream`
   - Example: `http://192.168.1.100:81/stream`

2. **Firewall:**
   - Temporarily disable firewall
   - Add exception for port 81

3. **Same Network:**
   - Computer and ESP32 must be on same network
   - Check if computer on WiFi or ethernet
   - Try pinging ESP32: `ping 192.168.1.100`

4. **Port Conflict:**
   ```cpp
   // Try different port
   #define STREAM_PORT 8080  // Instead of 81
   ```

5. **Test with curl:**
   ```bash
   curl http://192.168.1.100:81/stream
   # Should show MJPEG data
   ```

---

## 🐍 Python Issues

### Problem: ModuleNotFoundError

**Symptoms:**
```
ModuleNotFoundError: No module named 'cv2'
ModuleNotFoundError: No module named 'ultralytics'
```

**Solutions:**

1. **Activate Virtual Environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Python Path:**
   ```bash
   which python  # Linux/Mac
   where python  # Windows
   
   # Should point to venv/bin/python or venv\Scripts\python.exe
   ```

4. **Reinstall Specific Package:**
   ```bash
   pip install opencv-python
   pip install ultralytics
   ```

---

### Problem: Cannot Connect to Stream (Python)

**Symptoms:**
```
❌ Connection error: HTTPConnectionPool...
❌ Failed to connect: Status 404
```

**Solutions:**

1. **Test Stream First:**
   ```bash
   python test_esp32_stream.py --ping
   ```

2. **Check URL in config.json:**
   ```json
   {
       "esp32_cam_url": "http://192.168.2.100:81/stream"
   }
   ```
   - Remove trailing slash
   - Include /stream endpoint
   - Correct IP address

3. **Test with Browser:**
   - Open browser
   - Go to: http://IP:81/stream
   - Should see video stream

4. **Check Network:**
   ```bash
   ping 192.168.2.100
   
   # Should get replies
   ```

5. **Try Different Network Interface:**
   ```python
   # If multiple network interfaces
   import socket
   print(socket.gethostbyname(socket.gethostname()))
   ```

---

### Problem: Low FPS / Laggy Detection

**Symptoms:**
- FPS < 5
- Detection very slow
- High latency

**Solutions:**

1. **Use Smaller Model:**
   ```json
   {
       "model_path": "models/yolov8n.pt"  // Nano = fastest
   }
   ```

2. **Reduce Frame Size (ESP32):**
   ```cpp
   #define DEFAULT_FRAMESIZE FRAMESIZE_QVGA  // 320x240
   ```

3. **Enable GPU:**
   ```bash
   # Check GPU availability
   python -c "import torch; print(torch.cuda.is_available())"
   
   # If True, YOLO will auto-use GPU
   ```

4. **Reduce Quality (ESP32):**
   ```cpp
   #define DEFAULT_JPEG_QUALITY 15  // Higher = lower quality = faster
   ```

5. **Close Other Apps:**
   - Close browser tabs
   - Close other CPU-intensive apps

6. **Optimize System:**
   ```python
   # In fire_detection.py, reduce confidence threshold
   self.confidence_threshold = 0.6  # Higher = faster
   ```

---

### Problem: CUDA Out of Memory

**Symptoms:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**

1. **Use Smaller Model:**
   ```json
   {
       "model_path": "models/yolov8n.pt"  // Instead of yolov8x.pt
   }
   ```

2. **Reduce Batch Size (Training):**
   ```bash
   python train_custom_model.py --batch-size 8  # Instead of 16
   ```

3. **Use CPU Instead:**
   ```python
   # Force CPU
   import torch
   torch.cuda.is_available = lambda: False
   ```

4. **Clear CUDA Cache:**
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

---

### Problem: Model Not Found

**Symptoms:**
```
FileNotFoundError: models/yolov8n.pt not found
```

**Solutions:**

1. **Download Model:**
   ```bash
   python download_fire_model.py
   ```

2. **Check Path:**
   ```bash
   dir models         # Windows
   ls models/         # Linux/Mac
   ```

3. **Manual Download:**
   ```python
   from ultralytics import YOLO
   model = YOLO('yolov8n.pt')  # Auto-downloads
   ```

---

### Problem: False Detections

**Symptoms:**
- Detecting fire when there's none
- Too many false positives

**Solutions:**

1. **Increase Confidence Threshold:**
   ```json
   {
       "confidence_threshold": 0.7  // Higher = fewer false positives
   }
   ```

2. **Train Custom Model:**
   - Use fire-specific dataset
   - More training epochs
   - Better quality images

3. **Improve Lighting:**
   - Better lighting conditions
   - Avoid backlight
   - Stable lighting (not flickering)

4. **Filter by Size:**
   ```python
   # In detect_fire(), add size filter
   width = x2 - x1
   height = y2 - y1
   if width < 20 or height < 20:
       continue  # Skip small detections
   ```

---

### Problem: Missing Detections

**Symptoms:**
- Fire present but not detected
- Low detection rate

**Solutions:**

1. **Lower Confidence Threshold:**
   ```json
   {
       "confidence_threshold": 0.3  // Lower = more sensitive
   }
   ```

2. **Better Camera Position:**
   - Clear view of area
   - Appropriate distance
   - Good angle

3. **Improve Lighting:**
   - Adequate lighting
   - Avoid shadows
   - Consistent lighting

4. **Use Better Model:**
   - Use yolov8m or yolov8l (more accurate)
   - Train on similar environment
   - More training data

5. **Increase Frame Size:**
   ```cpp
   #define DEFAULT_FRAMESIZE FRAMESIZE_VGA  // Better quality
   ```

---

## 🔧 Training Issues

### Problem: Training Very Slow

**Solutions:**

1. **Use GPU:**
   ```bash
   python train_custom_model.py --device 0  # Use GPU 0
   ```

2. **Reduce Batch Size:**
   ```bash
   python train_custom_model.py --batch-size 8
   ```

3. **Use Smaller Model:**
   ```bash
   python train_custom_model.py --model n  # Nano
   ```

4. **Reduce Image Size:**
   ```bash
   python train_custom_model.py --img-size 416  # Instead of 640
   ```

---

### Problem: Training Crashes

**Solutions:**

1. **Reduce Batch Size:**
   ```bash
   python train_custom_model.py --batch-size 4
   ```

2. **Check Dataset:**
   - All images readable?
   - Labels format correct?
   - No corrupted files?

3. **Increase RAM:**
   - Close other programs
   - Use --cache False

4. **Check Disk Space:**
   - Need space for checkpoints
   - Clean temp files

---

## 📊 Performance Optimization

### For Real-time Detection:

1. **Hardware:**
   - Use GPU if available
   - Minimum 8GB RAM
   - SSD for faster I/O

2. **Software:**
   ```json
   {
       "model_path": "models/yolov8n.pt",
       "confidence_threshold": 0.6,
       "enable_video_recording": false  // Disable if not needed
   }
   ```

3. **ESP32-CAM:**
   ```cpp
   #define DEFAULT_FRAMESIZE FRAMESIZE_QVGA
   #define DEFAULT_JPEG_QUALITY 12
   ```

4. **Network:**
   - Strong WiFi signal
   - Minimal interference
   - Quality router

---

## 🆘 Still Having Issues?

1. **Check Logs:**
   ```bash
   # Python logs
   cat logs/fire_detection_*.log
   
   # ESP32 logs
   # Check Serial Monitor
   ```

2. **Verbose Mode:**
   ```python
   # In fire_detection.py
   results = self.model(frame, conf=self.confidence_threshold, verbose=True)
   ```

3. **Create Issue:**
   - Describe problem
   - Include error messages
   - Include system info:
     ```bash
     python --version
     pip list
     ```
   - Include config.json (remove sensitive info)

4. **Community Help:**
   - Stack Overflow
   - ESP32 forums
   - YOLOv8 discussions

---

## 📝 Diagnostic Script

Save as `diagnose.py`:

```python
import sys
import platform

print("="*60)
print("SYSTEM DIAGNOSTICS")
print("="*60)

# Python version
print(f"\nPython: {sys.version}")
print(f"Platform: {platform.system()} {platform.release()}")

# Check imports
packages = ['cv2', 'numpy', 'ultralytics', 'torch', 'requests']
print("\nPackage Check:")
for pkg in packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', 'unknown')
        print(f"  ✓ {pkg}: {version}")
    except ImportError:
        print(f"  ✗ {pkg}: NOT INSTALLED")

# Check CUDA
try:
    import torch
    print(f"\nCUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
except:
    print("\nCUDA: Not available")

print("\n" + "="*60)
```

Run with:
```bash
python diagnose.py
```

---

**💡 Remember:** Most issues dapat diatasi dengan:
1. Proper power supply (ESP32-CAM)
2. Correct configuration (IP address, paths)
3. Virtual environment (Python packages)
4. Good network connection

---

Made with ❤️ | 2025

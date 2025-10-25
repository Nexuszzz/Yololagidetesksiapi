# 🚀 Setup Guide - ESP32-CAM Fire Detection

Panduan lengkap step-by-step untuk setup sistem fire detection.

---

## 📋 Prerequisites

Sebelum mulai, pastikan Anda punya:

### Hardware
- ✅ ESP32-CAM module (AI Thinker)
- ✅ FTDI programmer atau USB-to-Serial adapter
- ✅ Jumper wires
- ✅ Power supply 5V ≥ 1A
- ✅ MicroUSB cable
- ✅ Computer/Laptop

### Software
- ✅ Arduino IDE (v1.8.19 atau lebih baru)
- ✅ Python 3.8 atau lebih baru
- ✅ Git (optional)

---

## 🔧 Part 1: ESP32-CAM Setup

### Step 1: Install Arduino IDE

1. Download Arduino IDE dari: https://www.arduino.cc/en/software
2. Install dan jalankan Arduino IDE

### Step 2: Install ESP32 Board Support

1. Buka Arduino IDE
2. File → Preferences
3. Di "Additional Board Manager URLs", tambahkan:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click OK
5. Tools → Board → Boards Manager
6. Cari "esp32"
7. Install "esp32 by Espressif Systems"
8. Tunggu hingga selesai

### Step 3: Wiring ESP32-CAM to Programmer

#### Untuk Upload (Programming Mode):
```
FTDI/USB-Serial  →  ESP32-CAM
─────────────────────────────
5V               →  5V
GND              →  GND
TX               →  U0R (RX)
RX               →  U0T (TX)
GND              →  GPIO 0 (untuk upload)
```

⚠️ **PENTING**: 
- GPIO 0 harus terhubung ke GND saat upload
- Lepas GPIO 0 dari GND setelah upload selesai
- Gunakan power supply eksternal 5V jika kamera tidak stabil

#### Untuk Running (Normal Mode):
```
Power Supply  →  ESP32-CAM
───────────────────────────
5V            →  5V
GND           →  GND
```

### Step 4: Configure Arduino IDE

1. Tools → Board → ESP32 Arduino
2. Select "AI Thinker ESP32-CAM"
3. Set these parameters:
   - Upload Speed: 115200
   - Flash Frequency: 80MHz
   - Flash Mode: QIO
   - Partition Scheme: **Huge APP (3MB No OTA)**
   - Core Debug Level: None
   - PSRAM: **Enabled**

### Step 5: Upload Code

1. Buka file `esp32_cam_stream/esp32_cam_stream.ino`

2. Edit WiFi credentials:
   ```cpp
   const char* WIFI_SSID = "YourWiFiName";
   const char* WIFI_PASS = "YourPassword";
   ```

3. **IMPORTANT**: Hubungkan GPIO 0 ke GND

4. Click Upload button (atau Ctrl+U)

5. Tunggu hingga "Connecting....." muncul

6. Press RESET button pada ESP32-CAM

7. Upload akan mulai (progress bar akan muncul)

8. Setelah "Hard resetting via RTS pin..." muncul:
   - Lepas GPIO 0 dari GND
   - Press RESET button

9. Buka Serial Monitor (Tools → Serial Monitor)
   - Set baud rate: 115200

10. Anda akan melihat output seperti:
    ```
    Booting ESP32-CAM stream-only...
    Menghubungkan ke WiFi Server.......
    WiFi OK. IP: 192.168.2.100
    Stream siap: http://192.168.2.100:81/stream
    ```

11. **Catat IP address ini!** Anda akan membutuhkannya nanti.

### Step 6: Test ESP32-CAM Stream

1. Buka web browser
2. Akses: `http://192.168.2.100:81/stream` (ganti dengan IP Anda)
3. Anda akan melihat live stream dari kamera

---

## 🐍 Part 2: Python Environment Setup

### Step 1: Install Python

1. Download Python dari: https://www.python.org/downloads/
2. Install Python 3.8 atau lebih baru
3. ✅ Check "Add Python to PATH" saat install!

4. Verify installation:
   ```bash
   python --version
   # Output: Python 3.x.x
   ```

### Step 2: Clone/Download Project

```bash
# Option 1: Clone dengan Git
git clone <repository-url>
cd zakaiot

# Option 2: Download ZIP
# Extract ke folder zakaiot
cd zakaiot
```

### Step 3: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Anda akan melihat (venv) di prompt
```

### Step 4: Install Dependencies

#### Option A: Automatic Setup (Recommended)

```bash
python setup.py
```

Script ini akan:
- Check Python version
- Create directories
- Install packages
- Download YOLOv8 model
- Create config files

#### Option B: Manual Installation

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Download model
python download_fire_model.py
```

### Step 5: Configure System

1. Edit `config.json`:
   ```json
   {
       "esp32_cam_url": "http://192.168.2.100:81/stream",  // ← Update ini!
       "model_path": "models/yolov8n.pt",
       "confidence_threshold": 0.5
   }
   ```

2. Ganti IP address dengan IP ESP32-CAM Anda

### Step 6: Test Connection

```bash
# Test dengan ping
python test_esp32_stream.py --ping

# Test stream
python test_esp32_stream.py
```

Jika berhasil, Anda akan melihat:
- ✅ Ping successful
- ✅ Stream connected
- Live video window

---

## 🔥 Part 3: Run Fire Detection

### Step 1: Start Detection

```bash
python fire_detection.py
```

### Step 2: Test Detection

Untuk test sistem:
1. Tampilkan gambar api di layar HP/laptop
2. Arahkan ESP32-CAM ke gambar
3. System akan detect dan log

### Step 3: Check Logs

Logs tersimpan di `logs/fire_detection_YYYY-MM-DD.log`

```
============================================================
🔥 FIRE DETECTED!
Timestamp: 2025-10-25 12:30:45
Number of detections: 1
============================================================

Detection #1:
  Class: fire
  Confidence: 0.8542
  Bounding Box: (120, 85, 245, 210)
```

### Step 4: Check Recordings

Videos tersimpan di `recordings/fire_recording_*.avi`

---

## 🎯 Part 4: Training Custom Model (Optional)

Untuk akurasi lebih baik dengan dataset fire custom.

### Step 1: Get Dataset

Download fire detection dataset:
- **Roboflow**: https://universe.roboflow.com/fire-detection
- **Kaggle**: https://www.kaggle.com/datasets/phylake1337/fire-dataset

### Step 2: Prepare Dataset

Structure:
```
fire_dataset/
├── images/
│   ├── train/      # Put training images here
│   └── val/        # Put validation images here
├── labels/
│   ├── train/      # Put training labels here (.txt)
│   └── val/        # Put validation labels here (.txt)
└── data.yaml
```

### Step 3: Create data.yaml

```yaml
path: ./fire_dataset
train: images/train
val: images/val

names:
  0: fire

nc: 1
```

### Step 4: Train Model

```bash
# Basic training
python train_custom_model.py --data fire_dataset/data.yaml

# Advanced training
python train_custom_model.py \
    --data fire_dataset/data.yaml \
    --model m \
    --epochs 100 \
    --batch-size 16 \
    --device 0  # Use GPU
```

Training time:
- CPU: 2-4 hours
- GPU: 30-60 minutes

### Step 5: Use Trained Model

Update `config.json`:
```json
{
    "model_path": "fire_detection_training/fire_yolov8/weights/best.pt"
}
```

Run detection:
```bash
python fire_detection.py
```

---

## ✅ Verification Checklist

Sebelum production use, verify:

- [ ] ESP32-CAM streaming stabil
- [ ] Python environment setup complete
- [ ] All dependencies installed
- [ ] Model downloaded
- [ ] Config.json updated dengan IP yang benar
- [ ] Test stream successful
- [ ] Fire detection working
- [ ] Logs being created
- [ ] Recordings working (jika enabled)
- [ ] Alert sound working (jika enabled)

---

## 🐛 Common Issues

### Issue 1: ESP32-CAM tidak connect ke WiFi

**Solusi:**
```cpp
// Check WiFi credentials
const char* WIFI_SSID = "YourWiFiName";  // Correct?
const char* WIFI_PASS = "YourPassword";   // Correct?

// Try adding this before WiFi.begin():
WiFi.disconnect(true);
delay(1000);
```

### Issue 2: Brownout detector was triggered

**Solusi:**
- Use better power supply (2A recommended)
- Add 220µF capacitor between 5V and GND
- Don't use USB power for camera

### Issue 3: Camera init failed

**Solusi:**
- Enable PSRAM in Arduino IDE
- Select correct board: AI Thinker ESP32-CAM
- Check partition scheme: Huge APP
- Check all pin connections

### Issue 4: Cannot connect to stream (Python)

**Solusi:**
```bash
# Check IP
ping 192.168.2.100

# Test with browser
http://192.168.2.100:81/stream

# Update config.json with correct IP
```

### Issue 5: ModuleNotFoundError

**Solusi:**
```bash
# Activate virtual environment first
venv\Scripts\activate

# Then install
pip install -r requirements.txt
```

### Issue 6: Low FPS / Laggy

**Solusi:**
- Use YOLOv8n (nano) model
- Reduce frame size: FRAMESIZE_QVGA
- Enable GPU if available
- Close other applications

---

## 📊 Expected Performance

### With CPU (Intel i5/i7):
- FPS: 5-15
- Latency: 100-300ms
- Model: YOLOv8n

### With GPU (NVIDIA GTX 1060+):
- FPS: 20-30
- Latency: 30-50ms
- Model: YOLOv8n/s

### ESP32-CAM Stream:
- Resolution: VGA (640x480)
- FPS: 15-20
- Latency: 50-100ms

---

## 🎓 Tips for Success

1. **Start Simple**: Test dengan YOLOv8n dulu sebelum upgrade ke model besar

2. **Good Lighting**: Fire detection lebih baik dengan lighting yang cukup

3. **Camera Position**: Posisikan kamera dengan view yang clear

4. **Test First**: Selalu test dengan `test_esp32_stream.py` sebelum run detection

5. **Monitor Logs**: Check logs untuk tune confidence threshold

6. **Stable Power**: ESP32-CAM sangat sensitif dengan power quality

7. **Train Custom**: Untuk production, always train dengan dataset custom

8. **Regular Updates**: Update dependencies secara regular

---

## 🆘 Getting Help

Jika masih ada masalah:

1. Check README.md - Troubleshooting section
2. Check logs di `logs/` folder
3. Run dengan verbose mode
4. Create GitHub issue dengan:
   - Error message
   - Steps to reproduce
   - System info (Python version, OS, etc.)

---

## ✨ Next Steps

Setelah setup berhasil:

1. **Optimize**: Tune parameters untuk case Anda
2. **Train**: Train model custom untuk akurasi lebih baik
3. **Integrate**: Integrate dengan alarm/notification system
4. **Scale**: Add multiple cameras
5. **Deploy**: Deploy ke production environment

---

**🔥 Selamat! Setup Complete! 🔥**

Anda siap untuk detect fire dengan ESP32-CAM + YOLOv8!

---

Made with ❤️ | 2025

# 📹 QUICK SETUP - ESP32-CAM UNTUK ULTIMATE DETECTOR

## ✅ SUDAH DIKONFIGURASI!

Config `config_ultimate.json` sudah diset untuk **ESP32-CAM langsung**:

```json
{
  "use_esp32_cam": true,
  "esp32_cam_url": "http://10.75.111.108:81/stream"
}
```

---

## 🚀 CARA MENJALANKAN

### **Option 1: Quick Start**
```bash
python fire_detect_ultimate.py
```

### **Option 2: Batch File**
```bash
.\run_ultimate.bat
```

---

## 🔍 CEK ESP32-CAM SEBELUM MULAI

### **Test 1: Buka di Browser**
```
http://10.75.111.108:81/stream
```

Harus muncul video stream! Jika tidak:
1. Check ESP32-CAM power
2. Check WiFi connection
3. Check IP address correct

### **Test 2: Python Test Script**
```bash
python test_esp32_connection.py
```

Edit IP di script jika perlu.

---

## ⚙️ GANTI IP ESP32-CAM (JIKA BERBEDA)

### **Cara 1: Edit Config JSON**
```bash
notepad config_ultimate.json
```

Ubah baris:
```json
"esp32_cam_url": "http://YOUR_ESP32_IP:81/stream"
```

### **Cara 2: Cari IP ESP32-CAM**

**Di Serial Monitor Arduino:**
```
WiFi connected
IP address: 192.168.1.XXX
```

**Di Router:**
- Login ke router
- Cari device "ESP32-CAM"
- Lihat IP address

**Ping ESP32-CAM:**
```bash
ping 10.75.111.108
```

---

## 📊 EXPECTED OUTPUT

```
================================================================================
🔥 ULTIMATE FIRE DETECTION - ALL-IN-ONE SYSTEM
================================================================================

✅ Device: GPU - NVIDIA GeForce RTX 4060
📦 Loading: fire_yolov8s_ultra_best.pt
✅ Model loaded!

Configuration:
  Source: ESP32-CAM  ← ESP32-CAM ACTIVE!
  Multi-stage: ENABLED (90% accuracy)
  Gemini AI: DISABLED
  MQTT: DISABLED
  Device: GPU
================================================================================

🔌 ESP32-CAM: http://10.75.111.108:81/stream
✅ Source ready!
⌨️  Press 'q' to quit
```

---

## 🎯 ENABLE FITUR TAMBAHAN

### **Enable Gemini AI:**
```json
"gemini_enabled": true
```

### **Enable MQTT:**
```json
"mqtt_enabled": true
```

### **Enable Semua (ULTIMATE):**
```json
{
  "use_esp32_cam": true,
  "gemini_enabled": true,
  "mqtt_enabled": true
}
```

---

## 🐛 TROUBLESHOOTING

### **Error: "Stream connection error"**
✅ **Fix:**
1. Check ESP32-CAM power ON
2. Check WiFi connected
3. Test URL di browser: `http://10.75.111.108:81/stream`
4. Update IP di config jika berubah

### **Error: "Timeout"**
✅ **Fix:**
1. Check network same subnet
2. Ping ESP32-CAM: `ping 10.75.111.108`
3. Restart ESP32-CAM
4. Check firewall

### **Video terlalu lambat**
✅ **Fix:**
1. Lower ESP32-CAM resolution
2. Check WiFi signal strength
3. Reduce YOLO conf_threshold (faster)

### **Tidak ada deteksi**
✅ **Fix:**
1. Check model path correct
2. Lower conf_threshold (0.30)
3. Check lighting conditions
4. Test dengan api real (candle)

---

## 📝 QUICK REFERENCE

| Setting | Current Value | Change To |
|---------|---------------|-----------|
| **Source** | ESP32-CAM ✅ | Webcam: `"use_esp32_cam": false` |
| **ESP32 URL** | 10.75.111.108:81 | Your IP |
| **Gemini** | DISABLED | Enable: `"gemini_enabled": true` |
| **MQTT** | DISABLED | Enable: `"mqtt_enabled": true` |
| **Confidence** | 0.45 | Lower: 0.30 (more detections) |

---

## 🎨 DISPLAY INFO

Saat running dengan ESP32-CAM, display akan show:

```
┌─────────────────────────────────────────────────┐
│ ULTIMATE FIRE DETECTION                         │
│                                                 │
│ Source: ESP32-CAM (10.75.111.108)              │
│ 🔥 FIRE x1                                      │
│ FPS: 15.3 Acc: 92.5%                           │
└─────────────────────────────────────────────────┘
```

**Note:** FPS dengan ESP32-CAM biasanya 12-18 (tergantung WiFi)

---

## 🚀 SEKARANG SIAP!

**Run dengan ESP32-CAM:**
```bash
python fire_detect_ultimate.py
```

**Sistem akan:**
1. ✅ Load YOLO model
2. ✅ Connect ke ESP32-CAM (10.75.111.108:81)
3. ✅ Start detection dengan multi-stage verification
4. ✅ Display real-time hasil

**Test dengan:**
- Nyalakan api (candle, lighter)
- Lihat detection dengan box warna
- Check stats di panel

---

## 💡 TIPS

### **Untuk Akurasi Terbaik:**
- ✅ Cahaya cukup (tidak terlalu gelap)
- ✅ Jarak 1-3 meter dari ESP32-CAM
- ✅ ESP32-CAM stabil (tidak goyang)
- ✅ WiFi signal kuat

### **Untuk Enable Gemini AI:**
```json
"gemini_enabled": true
```
Accuracy naik jadi 95%! (tapi lebih lambat)

### **Untuk Enable MQTT Alerts:**
```json
"mqtt_enabled": true
```
ESP32 DevKit akan dapat alert!

---

**🔥 READY TO DETECT FIRE WITH ESP32-CAM! 🔥**

**Run:** `python fire_detect_ultimate.py`

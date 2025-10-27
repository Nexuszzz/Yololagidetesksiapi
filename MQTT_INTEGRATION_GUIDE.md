# 🔥 MQTT Integration Guide - YOLO Fire Detection + ESP32 DevKit

Panduan integrasi lengkap antara fire detection YOLOv10 (PC/Laptop) dengan ESP32 DevKit untuk trigger buzzer alarm via MQTT.

---

## 📋 System Architecture

```
┌─────────────────┐                  ┌──────────────────┐
│   ESP32-CAM     │  MJPEG Stream    │  PC/Laptop       │
│  (Video Source) │ ───────────────> │  + Python YOLO   │
└─────────────────┘                  │  + OpenCV        │
                                     └──────────────────┘
                                              │
                                              │ MQTT Publish
                                              │ lab/zaks/alert
                                              ▼
                                     ┌──────────────────┐
                                     │  MQTT Broker     │
                                     │  13.213.57.228   │
                                     │  Port: 1883      │
                                     └──────────────────┘
                                              │
                                              │ MQTT Subscribe
                                              │ lab/zaks/alert
                                              ▼
                                     ┌──────────────────┐
                                     │  ESP32 DevKit    │
                                     │  + DHT11         │
                                     │  + Gas Sensor    │
                                     │  + Flame Sensor  │
                                     │  + Buzzer 🔊     │
                                     │  + LCD I2C       │
                                     └──────────────────┘
```

---

## 🔧 Changes Made to ESP32 DevKit Code

### **1. Subscribe to YOLO Alert Topic**

**Before:**
```cpp
mqtt.subscribe(TOPIC_SUB);  // Hanya command topic
```

**After:**
```cpp
mqtt.subscribe(TOPIC_SUB);    // Command topic
mqtt.subscribe(TOPIC_ALERT);  // ⭐ YOLO alert topic (PENTING!)
```

### **2. Handle YOLO Alert in Callback**

**Added:**
```cpp
void onMqttMsg(char* topic, byte* payload, unsigned int len) {
  // ... existing code ...
  
  // ⭐ HANDLE ALERT DARI YOLO
  if (strcmp(topic, TOPIC_ALERT) == 0) {
    Serial.println("[🔥 YOLO ALERT] Fire detected by camera!");
    forceAlarm = true;
    yoloAlarmTime = millis();  // Auto-off timer
    return;
  }
  
  // ... rest of code ...
}
```

### **3. Auto-off Timer (5 seconds)**

**Added in loop():**
```cpp
// Auto-off YOLO alarm setelah 5 detik
if (forceAlarm && yoloAlarmTime > 0) {
  if (millis() - yoloAlarmTime >= YOLO_ALARM_DURATION) {
    forceAlarm = false;
    yoloAlarmTime = 0;
    Serial.println("[YOLO ALARM] Auto-off after 5 seconds");
  }
}
```

### **4. LCD Shows Alarm Source**

**Updated:**
```cpp
const char* alarmSrc = "";
if (fire) {
  if (forceAlarm) alarmSrc = "YOL";  // YOLO alert
  else if (flameTrig) alarmSrc = "FLM";  // Flame sensor
  else alarmSrc = "GAS";  // Gas threshold
}
```

---

## 📡 MQTT Topics

| Topic | Publisher | Subscriber | Purpose |
|-------|-----------|------------|---------|
| `lab/zaks/alert` | **Python YOLO** | **ESP32 DevKit** | Fire alert from camera |
| `lab/zaks/alert` | **ESP32 DevKit** | - | Fire alert from flame sensor |
| `lab/zaks/event` | Both | - | System events (boot, heartbeat, etc) |
| `lab/zaks/log` | ESP32 DevKit | - | Telemetry data |
| `lab/zaks/status` | ESP32 DevKit | - | Online/offline status (LWT) |
| `nimak/deteksi-api/cmd` | - | ESP32 DevKit | Manual commands |
| `nimak/deteksi-api/telemetry` | ESP32 DevKit | - | Sensor data |

---

## 📦 MQTT Payload Format

### **From Python YOLO to ESP32 (lab/zaks/alert)**

```json
{
  "id": "yolo-fire-abcdef123456",
  "src": "yolo_fire",
  "alert": "flame_detected",
  "conf": 0.87,
  "bbox": [120, 85, 245, 210],
  "ts": 1730000000
}
```

### **From ESP32 Flame Sensor (lab/zaks/alert)**

```json
{
  "id": "1234567890AB",
  "src": "esp32_flame",
  "alert": "flame",
  "t": 28.5,
  "h": 65,
  "gasA": 1234,
  "gasMv": 1500
}
```

### **Heartbeat Event (lab/zaks/event)**

```json
{
  "id": "yolo-fire-abcdef123456",
  "event": "heartbeat",
  "fps": 18.5,
  "detections": 5,
  "ts": 1730000000
}
```

---

## 🚀 How to Deploy

### **Step 1: Upload ESP32 DevKit Code**

1. Open `esp32_devkit_mqtt/esp32_devkit_mqtt.ino` in Arduino IDE
2. Update WiFi credentials (if needed):
   ```cpp
   const char* WIFI_SSID = "YourWiFiName";
   const char* WIFI_PASS = "YourPassword";
   ```
3. Select board: **ESP32 Dev Module**
4. Upload code
5. Open Serial Monitor (115200 baud)
6. Verify output:
   ```
   WiFi OK, IP: 192.168.x.xxx
   MQTT OK
   ✅ Subscribed to:
      - nimak/deteksi-api/cmd (commands)
      - lab/zaks/alert (YOLO alerts)
   ✅ Setup complete!
   ```

### **Step 2: Run Python YOLO Fire Detection**

```bash
# Make sure paho-mqtt is installed
pip install paho-mqtt

# Run detection with MQTT
python firedetect_mqtt.py
```

Expected output:
```
======================================================================
🔥 ESP32-CAM FIRE DETECTION - YOLOv10 + MQTT
======================================================================
📦 Loading YOLOv10 model: models/fire.pt
✅ Model loaded successfully!
📡 MQTT connected: 13.213.57.228:1883
======================================================================
📍 Stream URL: http://10.75.111.90:81/stream
🎯 Confidence: 0.25 (High: 0.45)
📡 MQTT: Enabled
======================================================================
```

### **Step 3: Test Fire Detection**

1. **Test dengan lighter/candle** di depan ESP32-CAM
2. **Watch for:**
   - Python YOLO detects fire → Shows red/orange bounding box
   - Python publishes MQTT alert to `lab/zaks/alert`
   - ESP32 DevKit receives alert
   - ESP32 buzzer bunyi selama 5 detik
   - LCD shows: `ALRM YOL` (YOLO alarm)

---

## 🧪 Testing Scenarios

### **Test 1: YOLO Fire Detection**

**Steps:**
1. Run `python firedetect_mqtt.py`
2. Hold lighter in front of ESP32-CAM (20-30cm)
3. Wait for detection

**Expected:**
- ✅ Python: "📡 MQTT Alert sent: conf=0.45"
- ✅ ESP32 Serial: "[🔥 YOLO ALERT] Fire detected by camera!"
- ✅ ESP32 LCD: Shows `ALRM YOL`
- ✅ Buzzer: ON for 5 seconds
- ✅ Auto-off after 5 seconds

---

### **Test 2: Local Flame Sensor**

**Steps:**
1. Trigger flame sensor langsung (lighter near flame sensor)

**Expected:**
- ✅ ESP32 Serial: "[LOCAL ALERT] Flame detected!"
- ✅ ESP32 LCD: Shows `ALRM FLM`
- ✅ Buzzer: ON while flame detected
- ✅ MQTT publish to `lab/zaks/alert` with `"src":"esp32_flame"`

---

### **Test 3: Manual Command**

**Steps:**
1. Publish MQTT command:
   ```bash
   mosquitto_pub -h 13.213.57.228 -p 1883 \
     -u zaks -P engganngodinginginmcu \
     -t nimak/deteksi-api/cmd \
     -m "BUZZER_ON"
   ```

**Expected:**
- ✅ Buzzer: ON until BUZZER_OFF command
- ✅ ESP32 LCD: Shows `ALRM`

---

### **Test 4: Heartbeat & Status**

**Check MQTT messages:**
```bash
# Subscribe to all lab/zaks/* topics
mosquitto_sub -h 13.213.57.228 -p 1883 \
  -u zaks -P engganngodinginginmcu \
  -t "lab/zaks/#" -v
```

**Expected every 30 seconds:**
- ✅ Python: Heartbeat with FPS and detection count
- ✅ ESP32: Telemetry with sensor data

---

## 🔍 Troubleshooting

### **Problem: ESP32 Tidak Menerima Alert dari YOLO**

**Check:**
1. Serial Monitor ESP32, pastikan ada:
   ```
   ✅ Subscribed to:
      - lab/zaks/alert (YOLO alerts)
   ```

2. Check Python MQTT connection:
   ```
   📡 MQTT connected: 13.213.57.228:1883
   ```

3. Test MQTT manually:
   ```bash
   mosquitto_pub -h 13.213.57.228 -p 1883 \
     -u zaks -P engganngodinginginmcu \
     -t lab/zaks/alert \
     -m '{"alert":"test"}'
   ```

4. Check ESP32 Serial untuk incoming message

---

### **Problem: Buzzer Tidak Bunyi**

**Check:**
1. `BUZZER_PIN` wiring correct (Pin 25)
2. Buzzer polarity (active high/low)
3. Test buzzer dengan command:
   ```
   BUZZER_ON
   ```
4. Check Serial Monitor:
   ```
   [🔥 YOLO ALERT] Fire detected by camera!
   ```

---

### **Problem: YOLO Tidak Detect Api**

**Solutions:**
1. Lower confidence threshold:
   ```json
   "conf_threshold": 0.20
   ```

2. Test dengan api yang lebih besar (candle, bukan lighter)

3. Check model:
   ```bash
   dir models\fire.pt
   ```

4. Check enhancement enabled:
   ```json
   "enable_fire_enhancement": true
   ```

---

## 📊 System Behavior

### **Alarm Priority:**

1. **YOLO Alert** (forceAlarm via MQTT)
   - Duration: 5 seconds auto-off
   - LCD: `ALRM YOL`
   - Can be extended if fire still detected

2. **Local Flame Sensor**
   - Duration: While flame detected
   - LCD: `ALRM FLM`
   - Publishes own alert to MQTT

3. **Gas Threshold**
   - Duration: While gas > threshold
   - LCD: `ALRM GAS`
   - No MQTT alert (only in telemetry)

4. **Manual Command**
   - Duration: Until BUZZER_OFF
   - LCD: `ALRM`
   - Persists across reboots if not turned off

---

## ⚙️ Configuration Files

### **Python: config_yolov10.json**

```json
{
  "esp32_cam_url": "http://10.75.111.90:81/stream",
  "model_path": "models/fire.pt",
  "conf_threshold": 0.25,
  "high_conf_threshold": 0.45,
  "mqtt": {
    "host": "13.213.57.228",
    "port": 1883,
    "user": "zaks",
    "password": "engganngodinginginmcu",
    "topic_alert": "lab/zaks/alert",
    "topic_event": "lab/zaks/event"
  }
}
```

### **ESP32: WiFi & MQTT (hardcoded)**

```cpp
const char* WIFI_SSID = "RedmiNote13";
const char* WIFI_PASS = "naufal.453";
IPAddress MQTT_HOST_IP(13, 213, 57, 228);
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER = "zaks";
const char* MQTT_PASS = "engganngodinginginmcu";
```

---

## 🎯 Success Criteria

✅ **Python YOLO:**
- Connects to ESP32-CAM stream
- Detects fire with 90-95% accuracy
- Connects to MQTT broker
- Publishes alerts on fire detection
- Sends heartbeat every 30 seconds

✅ **ESP32 DevKit:**
- Connects to WiFi
- Connects to MQTT broker
- Subscribes to `lab/zaks/alert`
- Receives YOLO alerts
- Activates buzzer on alert
- Auto-off after 5 seconds
- Shows alarm source on LCD
- Publishes own flame sensor alerts

✅ **Integration:**
- End-to-end latency < 2 seconds
- No false positives from red objects
- Buzzer activates reliably
- System recovers from network issues

---

## 📝 Monitoring Commands

### **Monitor All MQTT Traffic:**
```bash
mosquitto_sub -h 13.213.57.228 -p 1883 \
  -u zaks -P engganngodinginginmcu \
  -t "#" -v
```

### **Monitor Only Alerts:**
```bash
mosquitto_sub -h 13.213.57.228 -p 1883 \
  -u zaks -P engganngodinginginmcu \
  -t "lab/zaks/alert" -v
```

### **Monitor Events:**
```bash
mosquitto_sub -h 13.213.57.228 -p 1883 \
  -u zaks -P engganngodinginginmcu \
  -t "lab/zaks/event" -v
```

---

## 🔄 System Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│ 1. ESP32-CAM streams video via MJPEG               │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ 2. Python YOLO receives frames & detects fire      │
│    - Fire enhancement (HSV boost)                   │
│    - YOLO inference                                 │
│    - Double verification (color + area)             │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼ (if fire detected)
┌─────────────────────────────────────────────────────┐
│ 3. Python publishes MQTT alert                      │
│    Topic: lab/zaks/alert                            │
│    Payload: {conf, bbox, timestamp}                 │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ 4. MQTT Broker forwards message                     │
│    Host: 13.213.57.228:1883                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ 5. ESP32 DevKit receives alert                      │
│    - Callback: onMqttMsg()                          │
│    - Sets: forceAlarm = true                        │
│    - Starts: 5-second timer                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ 6. ESP32 activates buzzer                           │
│    - digitalWrite(BUZZER_PIN, HIGH)                 │
│    - LCD shows: ALRM YOL                            │
│    - Publishes confirmation event                   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼ (after 5 seconds)
┌─────────────────────────────────────────────────────┐
│ 7. Auto-off if no local fire detected               │
│    - forceAlarm = false                             │
│    - Buzzer OFF                                     │
│    - Publishes auto-off event                       │
└─────────────────────────────────────────────────────┘
```

---

## 💡 Tips & Best Practices

1. **Network Stability:**
   - Use stable WiFi connection
   - Place ESP32 near router
   - Monitor RSSI in telemetry

2. **MQTT Reliability:**
   - Use QoS 1 for alerts (delivery guarantee)
   - Set proper keepalive (30 seconds)
   - Implement LWT (Last Will Testament)

3. **Fire Detection Tuning:**
   - Start with default thresholds
   - Adjust based on environment
   - Test with real fire scenarios
   - Monitor false positive rate

4. **Power Management:**
   - Use quality 5V power supply
   - Separate power for buzzer if needed
   - Monitor voltage drops

5. **Logging:**
   - Enable all log topics
   - Store logs for analysis
   - Monitor system health

---

## ✅ Checklist Before Deployment

- [ ] ESP32-CAM streaming reliably
- [ ] Python YOLO model (fire.pt) downloaded
- [ ] MQTT broker accessible
- [ ] ESP32 DevKit connected to WiFi
- [ ] ESP32 subscribed to lab/zaks/alert
- [ ] Buzzer tested manually (BUZZER_ON command)
- [ ] Test fire detection dengan lighter/candle
- [ ] Verify MQTT alert received by ESP32
- [ ] Verify buzzer activates on YOLO alert
- [ ] Test auto-off after 5 seconds
- [ ] Monitor MQTT traffic with mosquitto_sub
- [ ] Check LCD display shows correct info
- [ ] Verify heartbeat messages every 30s
- [ ] Test system recovery from disconnect

---

**🎉 System Ready for Deployment!**

For issues or questions, check `TROUBLESHOOTING.md` or Serial Monitor output.

Made with ❤️ | 2025

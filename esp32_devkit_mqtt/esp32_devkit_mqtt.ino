#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "DHT.h"

// ===== PIN =====
#define SDA_PIN        21
#define SCL_PIN        22
#define DHTPIN         23
#define DHTTYPE        DHT11        // ganti ke DHT22 jika sensornya DHT22
#define GAS_ANALOG     34           // ADC1
#define GAS_DIGITAL    27           // DO gas (aktif LOW)
#define FLAME_PIN      26           // DO flame (aktif LOW)
#define BUZZER_PIN     25

// ===== WiFi =====
const char* WIFI_SSID = "RedmiNote13";
const char* WIFI_PASS = "naufal.453";

// ===== MQTT =====
IPAddress MQTT_HOST_IP(13, 213, 57, 228);
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER = "zaks";
const char* MQTT_PASS = "engganngodinginginmcu";

// Topik lama (tetap dipakai)
const char* TOPIC_PUB = "nimak/deteksi-api/telemetry";
const char* TOPIC_SUB = "nimak/deteksi-api/cmd";

// Topik tambahan (baru)
const char* TOPIC_EVENT = "lab/zaks/event";
const char* TOPIC_LOG   = "lab/zaks/log";
const char* TOPIC_LWT   = "lab/zaks/status";
const char* TOPIC_ALERT = "lab/zaks/alert";  // ⭐ Alert dari YOLO

// ===== LCD & DHT =====
LiquidCrystal_I2C lcd(0x27, 16, 2);
DHT dht(DHTPIN, DHTTYPE);

// ===== MQTT client =====
WiFiClient net;
PubSubClient mqtt(net);

// ===== State =====
int  GAS_THRESHOLD = 4095;
bool forceAlarm    = false;     // Bisa dari command ATAU dari YOLO alert
bool prevFlame     = false;     // Deteksi edge OFF->ON

unsigned long lastPub  = 0;
const unsigned long PUB_MS = 30000;   // Publish tiap 30 detik
unsigned long lastLcd  = 0;

float lastT = NAN, lastH = NAN;       // Cache nilai sah terakhir
unsigned long lastDht = 0;
const unsigned long DHT_PERIOD_MS = (DHTTYPE == DHT11) ? 1000UL : 2000UL;

// Timer untuk auto-off buzzer dari YOLO alert
unsigned long yoloAlarmTime = 0;
const unsigned long YOLO_ALARM_DURATION = 5000;  // 5 detik

// ==== Util ====
String chipIdString() {
  uint64_t id = ESP.getEfuseMac();
  char buf[17];
  snprintf(buf, sizeof(buf), "%04X%08X", (uint16_t)(id>>32), (uint32_t)id);
  return String(buf);
}

void lcdPrint2(const char* l1, const char* l2) {
  char top[17], bot[17];
  snprintf(top, sizeof(top), "%-16s", l1);
  snprintf(bot, sizeof(bot), "%-16s", l2);
  lcd.setCursor(0,0); lcd.print(top);
  lcd.setCursor(0,1); lcd.print(bot);
}

void onMqttMsg(char* topic, byte* payload, unsigned int len) {
  String msg; msg.reserve(len);
  for (unsigned int i=0; i<len; i++) msg += (char)payload[i];
  Serial.printf("[MQTT] %s => %s\n", topic, msg.c_str());

  // ⭐ HANDLE ALERT DARI YOLO (lab/zaks/alert)
  if (strcmp(topic, TOPIC_ALERT) == 0) {
    Serial.println("[🔥 YOLO ALERT] Fire detected by camera! Activating buzzer...");
    forceAlarm = true;
    yoloAlarmTime = millis();  // Set timer untuk auto-off
    
    // Publish confirmation
    char conf[80];
    snprintf(conf, sizeof(conf), "{\"event\":\"yolo_alarm_received\",\"id\":\"%s\"}", 
             chipIdString().c_str());
    mqtt.publish(TOPIC_EVENT, conf, false);
    
    return;  // Exit early
  }

  // HANDLE COMMAND LAMA (nimak/deteksi-api/cmd)
  if (msg.equalsIgnoreCase("BUZZER_ON")) {
    forceAlarm = true;
    yoloAlarmTime = 0;  // Disable auto-off
  }
  else if (msg.equalsIgnoreCase("BUZZER_OFF")) {
    forceAlarm = false;
    yoloAlarmTime = 0;
  }
  else if (msg.startsWith("THR=")) {
    GAS_THRESHOLD = msg.substring(4).toInt();
    Serial.printf("[MQTT] THR -> %d\n", GAS_THRESHOLD);
    char ebuf[64];
    snprintf(ebuf, sizeof(ebuf), "{\"event\":\"thr_update\",\"thr\":%d}", GAS_THRESHOLD);
    mqtt.publish(TOPIC_EVENT, ebuf, false);
  }
}

void wifiConnect() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("WiFi connect to %s ...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { 
    delay(250); 
    Serial.print("."); 
  }
  Serial.printf("\nWiFi OK, IP: %s\n", WiFi.localIP().toString().c_str());
}

void mqttConnect() {
  mqtt.setServer(MQTT_HOST_IP, MQTT_PORT);
  mqtt.setCallback(onMqttMsg);
  mqtt.setKeepAlive(30);
  mqtt.setBufferSize(512);

  while (!mqtt.connected()) {
    String cid = "esp32-" + chipIdString();
    Serial.printf("MQTT connect %s ...\n", cid.c_str());
    const char* willTopic = TOPIC_LWT;
    const char* willMsg   = "{\"status\":\"offline\"}";
    
    if (mqtt.connect(cid.c_str(), MQTT_USER, MQTT_PASS, willTopic, 1, true, willMsg)) {
      Serial.println("MQTT OK");
      
      // ⭐ Subscribe ke semua topic yang diperlukan
      mqtt.subscribe(TOPIC_SUB);    // Command lama
      mqtt.subscribe(TOPIC_ALERT);  // ⭐ Alert dari YOLO (PENTING!)
      
      mqtt.publish(TOPIC_LWT, "{\"status\":\"online\"}", true);  // Retained
      mqtt.publish(TOPIC_EVENT, "{\"event\":\"boot\",\"status\":\"online\"}", false);
      
      Serial.println("✅ Subscribed to:");
      Serial.printf("   - %s (commands)\n", TOPIC_SUB);
      Serial.printf("   - %s (YOLO alerts)\n", TOPIC_ALERT);
    } else {
      Serial.printf("MQTT rc=%d, retry...\n", mqtt.state());
      delay(1000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n🔥 ESP32 DevKit Fire Detection + YOLO MQTT");
  Serial.println("============================================");

  // LCD I2C
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  lcd.init();
  lcd.backlight();
  lcdPrint2("Booting...", "WiFi init");

  // Sensor
  dht.begin();
  pinMode(GAS_DIGITAL, INPUT_PULLUP);  // Aktif LOW
  pinMode(FLAME_PIN,   INPUT_PULLUP);  // Aktif LOW
  pinMode(BUZZER_PIN,  OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  analogReadResolution(12);
  analogSetPinAttenuation(GAS_ANALOG, ADC_11db);

  // Net
  wifiConnect();
  mqttConnect();

  lcd.clear();
  lcdPrint2("WiFi+MQTT OK", WiFi.localIP().toString().c_str());
  delay(800);
  
  Serial.println("✅ Setup complete!");
  Serial.println("Waiting for fire detection...\n");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) wifiConnect();
  if (!mqtt.connected()) mqttConnect();
  mqtt.loop();

  // ==== Auto-off YOLO alarm setelah 5 detik ====
  if (forceAlarm && yoloAlarmTime > 0) {
    if (millis() - yoloAlarmTime >= YOLO_ALARM_DURATION) {
      forceAlarm = false;
      yoloAlarmTime = 0;
      Serial.println("[YOLO ALARM] Auto-off after 5 seconds");
      mqtt.publish(TOPIC_EVENT, "{\"event\":\"yolo_alarm_auto_off\"}", false);
    }
  }

  // ==== DHT (rate-limit + cache) ====
  if (millis() - lastDht >= DHT_PERIOD_MS) {
    lastDht = millis();
    float _h = dht.readHumidity();
    float _t = dht.readTemperature();
    if (!isnan(_h) && !isnan(_t)) { 
      lastH = _h; 
      lastT = _t; 
    } else { 
      Serial.println("[DHT] Read failed (keep last)"); 
    }
  }
  float h = lastH;
  float t = lastT;

  // ==== GAS & FLAME ====
  int   gasAnalog = analogRead(GAS_ANALOG);
  uint32_t gasMv  = analogReadMilliVolts(GAS_ANALOG);
  bool  gasTrig   = (digitalRead(GAS_DIGITAL) == LOW);
  bool  flameTrig = (digitalRead(FLAME_PIN)   == LOW);

  // ==== LOGIKA ALARM ====
  // Local fire: flame sensor OR gas threshold
  bool localFire = flameTrig || (gasAnalog >= GAS_THRESHOLD);
  
  // Total alarm: local fire OR force alarm (dari YOLO/command)
  bool fire = localFire || forceAlarm;
  
  digitalWrite(BUZZER_PIN, fire ? HIGH : LOW);

  // ==== ALERT sekali saat OFF -> ON (local flame) ====
  if (flameTrig && !prevFlame) {
    char abuf[220];
    char tbuf[8], hbuf[8];
    if (isnan(t)) snprintf(tbuf, sizeof(tbuf), "null"); 
    else dtostrf(t, 4, 1, tbuf);
    if (isnan(h)) snprintf(hbuf, sizeof(hbuf), "null"); 
    else dtostrf(h, 4, 1, hbuf);
    
    snprintf(abuf, sizeof(abuf),
      "{\"id\":\"%s\",\"src\":\"esp32_flame\",\"alert\":\"flame\",\"t\":%s,\"h\":%s,"
      "\"gasA\":%d,\"gasMv\":%lu}",
      chipIdString().c_str(), tbuf, hbuf, gasAnalog, (unsigned long)gasMv);
    
    mqtt.publish(TOPIC_ALERT, abuf, false);
    mqtt.publish(TOPIC_EVENT, "{\"event\":\"flame_on\"}", false);
    Serial.printf("[LOCAL ALERT] Flame detected!\n");
  }
  prevFlame = flameTrig;

  // ==== LCD (refresh tiap ~1 dtk) ====
  static unsigned long lastLcd = 0;
  if (millis() - lastLcd >= 1000) {
    lastLcd = millis();
    char l1[17], l2[17];
    
    if (isnan(t) || isnan(h)) 
      snprintf(l1, sizeof(l1), "T: --.-C H:--%%");
    else 
      snprintf(l1, sizeof(l1), "T:%4.1fC H:%2.0f%%", t, h);
    
    // Tampilkan sumber alarm
    const char* alarmSrc = "";
    if (fire) {
      if (forceAlarm) alarmSrc = "YOL";  // YOLO alert
      else if (flameTrig) alarmSrc = "FLM";  // Flame sensor
      else alarmSrc = "GAS";  // Gas threshold
    }
    
    snprintf(l2, sizeof(l2), "G:%4d F:%s %s%s",
             gasAnalog, 
             flameTrig ? "ON " : "OFF", 
             fire ? "ALRM" : "OK  ",
             fire ? alarmSrc : "");
    
    lcdPrint2(l1, l2);
  }

  // ==== Telemetry tiap 30 detik ====
  if (millis() - lastPub >= PUB_MS) {
    lastPub = millis();

    char tbuf[8], hbuf[8];
    if (isnan(t)) snprintf(tbuf, sizeof(tbuf), "null"); 
    else dtostrf(t, 4, 1, tbuf);
    if (isnan(h)) snprintf(hbuf, sizeof(hbuf), "null"); 
    else dtostrf(h, 4, 1, hbuf);

    char payload[280];
    snprintf(payload, sizeof(payload),
      "{\"id\":\"%s\",\"t\":%s,\"h\":%s,\"gasA\":%d,\"gasMv\":%lu,"
      "\"gasD\":%s,\"flame\":%s,\"alarm\":%s,\"forceAlarm\":%s}",
      chipIdString().c_str(),
      tbuf, hbuf,
      gasAnalog, (unsigned long)gasMv,
      gasTrig ? "true" : "false",
      flameTrig ? "true" : "false",
      fire ? "true" : "false",
      forceAlarm ? "true" : "false");

    mqtt.publish(TOPIC_PUB, payload);   // Telemetry utama
    mqtt.publish(TOPIC_LOG, payload);   // Duplikat ke log
    Serial.printf("[PUB] %s\n", payload);
  }

  delay(100);  // Tetap responsif untuk mqtt.loop()
}

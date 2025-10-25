/************ ESP32-CAM — MJPEG Stream Only (untuk YOLO/OpenCV) ************
 * Board   : AI Thinker ESP32-CAM (OV2640)
 * Endpoint: http://<IP-ESP32>:81/stream
 * Catatan : Pilih "AI Thinker ESP32-CAM" di Boards, PSRAM: Enabled,
 *           Partition: Huge APP (3MB No OTA). Pastikan suplai 5V ≥ 1A stabil.
 ****************************************************************************/

#include <Arduino.h>
#include <WiFi.h>
#include "esp_camera.h"
#include "esp_timer.h"
#include "img_converters.h"
#include "esp_http_server.h"

// ================== WiFi ==================
const char* WIFI_SSID = "Server";
const char* WIFI_PASS = "Asdcvbjkl1!";

// ================== Port Stream =============
#define STREAM_PORT 81

// ================== Pinout AI Thinker ==================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ================== Tuning Kamera ==================
// Ukuran frame: FRAMESIZE_QQVGA, QQVGA2, QVGA, CIF, VGA, SVGA, XGA, SXGA, UXGA
// Saran YOLO realtime: QVGA (320x240) atau VGA (640x480).
#define DEFAULT_FRAMESIZE  FRAMESIZE_VGA  // ganti ke FRAMESIZE_QVGA untuk latensi lebih rendah
#define DEFAULT_JPEG_QUALITY 12           // 10-15 bagus untuk stream; lebih kecil = lebih bagus (lebih berat)
#define DEFAULT_FB_COUNT    2             // 2 untuk streaming lancar

// ================== HTTP Stream Handler ==================
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=frame";
static const char* _STREAM_BOUNDARY     = "--frame";
static const char* _STREAM_PART         = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t *_jpg_buf = NULL;
  char part_buf[64];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;
  // Biarkan koneksi tetap hidup untuk stream
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Gagal ambil frame");
      res = ESP_FAIL;
      break;
    }

    if (fb->format != PIXFORMAT_JPEG) {
      bool jpeg_converted = frame2jpg(fb, DEFAULT_JPEG_QUALITY, &_jpg_buf, &_jpg_buf_len);
      esp_camera_fb_return(fb);
      fb = NULL;
      if (!jpeg_converted) {
        Serial.println("Konversi JPG gagal");
        res = ESP_FAIL;
        break;
      }
    } else {
      _jpg_buf = fb->buf;
      _jpg_buf_len = fb->len;
    }

    // Kirim boundary
    if (httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY)) != ESP_OK) {
      res = ESP_FAIL;
    } else if (httpd_resp_send_chunk(req, "\r\n", 2) != ESP_OK) {
      res = ESP_FAIL;
    } else {
      // Header part
      size_t hlen = snprintf(part_buf, sizeof(part_buf), _STREAM_PART, _jpg_buf_len);
      if (httpd_resp_send_chunk(req, part_buf, hlen) != ESP_OK) {
        res = ESP_FAIL;
      } else if (httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len) != ESP_OK) {
        res = ESP_FAIL;
      } else if (httpd_resp_send_chunk(req, "\r\n", 2) != ESP_OK) {
        res = ESP_FAIL;
      }
    }

    // Kembalikan buffer
    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if (_jpg_buf) {
      free(_jpg_buf);
      _jpg_buf = NULL;
    }

    if (res != ESP_OK) break;
    // (opsional) tambahkan delay kecil jika CPU terlalu tinggi
    // vTaskDelay(1); 
  }

  // Pastikan release resource di akhir
  if (fb) esp_camera_fb_return(fb);
  if (_jpg_buf) free(_jpg_buf);
  return res;
}

static httpd_handle_t startStreamServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = STREAM_PORT;
  config.ctrl_port = STREAM_PORT + 1; // port kontrol internal

  httpd_handle_t stream_httpd = NULL;
  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_uri_t stream_uri = {
      .uri       = "/stream",
      .method    = HTTP_GET,
      .handler   = stream_handler,
      .user_ctx  = NULL
    };
    httpd_register_uri_handler(stream_httpd, &stream_uri);
  }
  return stream_httpd;
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false);
  Serial.println();
  Serial.println("Booting ESP32-CAM stream-only...");

  // ===== Inisialisasi Kamera =====
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;                 // 20 MHz
  config.pixel_format = PIXFORMAT_JPEG;           // stream = JPEG

  if (psramFound()) {
    config.frame_size   = DEFAULT_FRAMESIZE;
    config.jpeg_quality = DEFAULT_JPEG_QUALITY;
    config.fb_count     = DEFAULT_FB_COUNT;
    config.fb_location  = CAMERA_FB_IN_PSRAM;
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY; // latensi rendah
  } else {
    // fallback tanpa PSRAM
    config.frame_size   = FRAMESIZE_QVGA;
    config.jpeg_quality = 15;
    config.fb_count     = 1;
    config.fb_location  = CAMERA_FB_IN_DRAM;
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  }

  esp_err_t cam_err = esp_camera_init(&config);
  if (cam_err != ESP_OK) {
    Serial.printf("Kamera init gagal 0x%x\n", cam_err);
    delay(2000);
    ESP.restart();
  }

  // Opsi tuning sensor (flip/mirror, brightness, dll)
  sensor_t *s = esp_camera_sensor_get();
  // s->set_vflip(s, 1);    // 1=flip vertical jika gambar terbalik
  // s->set_hmirror(s, 1);  // 1=mirror horizontal
  // s->set_brightness(s, 1); // -2..2
  // s->set_saturation(s, 0); // -2..2

  // ===== WiFi =====
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false); // kurangi latensi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.printf("Menghubungkan ke WiFi %s", WIFI_SSID);
  uint8_t tries = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (++tries > 60) { // ~30 detik
      Serial.println("\nWiFi gagal, restart...");
      ESP.restart();
    }
  }
  Serial.printf("\nWiFi OK. IP: %s\n", WiFi.localIP().toString().c_str());

  // ===== HTTP Stream Server =====
  if (startStreamServer() == NULL) {
    Serial.println("Gagal start stream server, restart...");
    delay(2000);
    ESP.restart();
  }
  Serial.printf("Stream siap: http://%s:%d/stream\n",
                WiFi.localIP().toString().c_str(), STREAM_PORT);
}

void loop() {
  // Tidak perlu apa-apa; streaming ditangani oleh HTTP server
}

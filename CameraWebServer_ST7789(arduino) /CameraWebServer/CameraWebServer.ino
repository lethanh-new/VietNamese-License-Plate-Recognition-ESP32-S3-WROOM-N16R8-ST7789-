#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>

// =========================================================
//  THƯ VIỆN ĐỒ HỌA & GIẢI MÃ JPEG
// =========================================================
#include <SPI.h>
#include <TFT_eSPI.h> 
#include <TJpg_Decoder.h> 

TFT_eSPI tft = TFT_eSPI(); 

WiFiServer tcpServer(88); 
String current_plate = "Cho xe...";
String current_province = "--";

// Cấu hình IP tĩnh tương thích với Hotspot iPhone
IPAddress local_IP(172, 20, 10, 8);
IPAddress gateway(172, 20, 10, 1); 
IPAddress subnet(255, 255, 255, 0);

// =========================================================
// Select camera model in board_config.h
// =========================================================
#include "board_config.h"

const char *ssid = "iPhone"; 
const char *password = "999999999"; 

void startCameraServer();
void setupLedFlash();

// Hàm callback của thư viện TJpg_Decoder để đẩy từng block ảnh ra màn hình
bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t* bitmap) {
  // GIỚI HẠN VÙNG VẼ: Chỉ cho phép giải mã và vẽ ảnh trong khoảng y từ 0 đến 160
  // Bất kỳ pixel nào có tọa độ y lớn hơn 160 (vùng của chữ) sẽ bị bỏ qua để tránh đè chữ
  if (y + h > 160) {
    if (y >= 160) return false; // Nằm hoàn toàn ở vùng dưới thì bỏ qua
    h = 160 - y; // Cắt bớt phần dư thừa nếu block ảnh bị chớm xuống vùng chữ
  }
  
  tft.pushImage(x, y, w, h, bitmap);
  return true;
}

// Hàm cập nhật chữ thông tin ở vùng dưới cố định (y=160 đến 240)
void update_tft_text() {
  // Chỉ xóa vùng chữ nhỏ (y=165 đến 240) để tránh lạm dụng làm nháy màn hình
  tft.fillRect(0, 160, 240, 80, TFT_BLACK); 
  
  tft.setTextSize(2);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK); // Vẽ chữ vàng trên nền đen
  tft.drawString("BS: " + current_plate, 10, 170);
  
  tft.setTextColor(TFT_CYAN, TFT_BLACK); // Vẽ chữ xanh cyan trên nền đen
  tft.drawString("Tinh: " + current_province, 10, 205);
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Khởi tạo màn hình TFT
  tft.init();
  tft.setRotation(0); 
  tft.fillScreen(TFT_BLACK);
  
  // Khởi tạo bộ giải mã JPEG
  TJpgDec.setJpgScale(1); 
  TJpgDec.setCallback(tft_output);
  TJpgDec.setSwapBytes(true); // Giữ nguyên đảo byte sửa lỗi loang màu

  tft.setTextSize(2);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.drawString("TFT & JPG OK!", 10, 50);

  // Cấu hình Camera ở độ phân giải 240x240
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  
  config.frame_size = FRAMESIZE_240X240;  
  config.pixel_format = PIXFORMAT_JPEG;  
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (psramFound()) {
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.fb_location = CAMERA_FB_IN_DRAM;
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // Khởi tạo camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    tft.setTextColor(TFT_RED, TFT_BLACK);
    tft.drawString("CAM INIT FAIL!", 10, 90);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  s->set_hmirror(s, 1);
  if (s->id.PID == OV3660_PID) {
    s->set_hmirror(s, 1);
    s->set_vflip(s, 1);        
    s->set_brightness(s, 1);   
    s->set_saturation(s, -2);  
  }
  
  s->set_framesize(s, FRAMESIZE_240X240);

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  // Cấu hình IP tĩnh kết nối mạng
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Loi IP Tinh!");
  }
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  startCameraServer();
  tcpServer.begin();

  // Tạo giao diện phân vùng rõ rệt ngay từ đầu
  tft.fillScreen(TFT_BLACK);
  
  // Vẽ một đường line màu xám mỏng phân chia giữa vùng ảnh và vùng chữ
  tft.drawFastHLine(0, 160, 240, TFT_DARKGREY); 
  
  update_tft_text();
}

void loop() {
  // 📸 LẤY KHUNG HÌNH TỪ CAMERA VÀ VẼ LÊN TFT
  camera_fb_t * fb = esp_camera_fb_get();
  if (fb) {
    // Vẽ ảnh từ tọa độ x=0, y=0. Hàm tft_output ở trên sẽ tự động chặn không cho vẽ đè xuống y > 160.
    TJpgDec.drawJpg(0, 0, fb->buf, fb->len);
    esp_camera_fb_return(fb); 
  }

  // 📡 KIỂM TRA DỮ LIỆU CHỮ TỪ PYTHON
  WiFiClient client = tcpServer.available();
  if (client) {
    String data = "";
    
    // đọc hết sạch bộ đệm kể cả khi Python đã ngắt kết nối
    while (client.connected() || client.available()) {
      if (client.available()) {
        char c = client.read();
        if (c == '\n') break; 
        data += c;
      }
    }
    client.stop(); // Giải phóng kết nối an toàn

    data.trim(); // Loại bỏ các ký tự xuống dòng thừa (\r, khoảng trắng)

    int sep_idx = data.indexOf('|');
    if (sep_idx != -1) {
      current_plate = data.substring(0, sep_idx);
      current_province = data.substring(sep_idx + 1);
      
      // Xóa khoảng trắng thừa của từng phần
      current_plate.trim();
      current_province.trim();
      
      // Cập nhật lại vùng chữ khi nhận đủ bộ dữ liệu mới
      update_tft_text(); 
    }
  }
  
  delay(1); 
}
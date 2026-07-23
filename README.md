# License Plate Recognition System
ESP32-S3 CAM + YOLOv5 + ST7789 TFT Display

---
# 0. Lỗi dễ gặp

## Lỗi `ModuleNotFoundError: No module named 'pandas'`

Nếu gặp lỗi:

```text
ModuleNotFoundError: No module named 'pandas'
```

Hãy cài đặt `pandas`:

```bash
python -m pip install pandas
```

Kiểm tra:

```bash
python -c "import pandas; print(pandas.__version__)"
```
Đảm bảo dự án đang chạy bằng **Python 3.12**.

```bash
python --version
```

Kết quả mong muốn:

```text
Python 3.12.x
```

Kiểm tra đường dẫn Python:

```bash
python -c "import sys; print(sys.executable)"
```


---
# 1. Yêu cầu

## Phần cứng

- ESP32-S3 CAM
- Camera OV2640
- TFT ST7789 1.54" 240x240 IPS LCD
- Cáp USB

---

## Phần mềm

- Arduino IDE
- Python 3.12
- Visual Studio Code (khuyến nghị)

---

# 2. Cài đặt thư viện Arduino

Cài đặt các thư viện sau trong Arduino IDE:

- TFT_eSPI
- TJpg_Decoder
- WiFi
- WebServer
- ESP32 Board Package

> **Lưu ý**

Vui lòng **copy thư mục `TFT_eSPI`** được cung cấp trong project để **ghi đè** thư viện TFT_eSPI cũ.

ở địa chỉ

```
...Arduino\libraries\
```

---

# 3. Cấu hình TFT ST7789

Trong file `User_Setup.h` của thư viện TFT_eSPI cần cấu hình:

```
Driver: ST7789

Resolution:
240 x 240
```

Các chân kết nối:

| TFT | ESP32-S3 |
|------|-----------|
| MOSI | GPIO2 |
| SCLK | GPIO1 |
| DC | GPIO21 |
| RST | GPIO47 |
| VCC | 3.3V |
| GND | GND |

---

# 4. Nạp chương trình cho ESP32-S3

Mở project Arduino.

Chọn:

```
Board
→ ESP32S3 Dev Module
```

Chọn đúng COM Port.

Nhấn

```
Upload
```

Sau khi nạp thành công, mở Serial Monitor để kiểm tra.

Nếu khởi động thành công sẽ hiển thị tương tự:

```
WiFi Connected

Camera Ready

HTTP Server Started

TCP Server Started

TFT Init OK
```

---

# 5. Cài đặt thư viện Python

Mở Command Prompt.

Cài đặt các thư viện:

```bash
python -m pip install torch torchvision torchaudio

python -m pip install opencv-python

python -m pip install numpy

python -m pip install pandas

python -m pip install pillow

python -m pip install matplotlib

python -m pip install requests
```

---

# 6. Chạy hệ thống nhận dạng thời gian thực

Mở Terminal.

Di chuyển tới thư mục project.

Chạy:

```bash
python webcam.py
```

Chương trình sẽ:

- Kết nối tới ESP32-S3 CAM
- Nhận hình ảnh qua HTTP
- Phát hiện biển số bằng YOLOv5
- Hiệu chỉnh góc nghiêng
- Nhận dạng ký tự
- Gửi kết quả về ESP32 bằng TCP Socket
- Hiển thị biển số và tỉnh trên màn hình TFT ST7789

---

# 7. Kiểm thử mô hình với ảnh

Đặt ảnh cần kiểm thử vào thư mục project.

Ví dụ:

```
test.jpg
```

Chạy:

```bash
python kiem_thu_mo_hinh.py --image test.jpg
```

Ví dụ khác:

```bash
python kiem_thu_mo_hinh.py --image images/car1.jpg
```

Kết quả:

- Hiển thị Bounding Box biển số
- Hiển thị biển số đã nhận dạng
- Không cần ESP32-S3 CAM

---

# 8. Kiểm tra kết nối

Đảm bảo:

- ESP32-S3 và máy tính cùng mạng Wi-Fi
- Đúng địa chỉ IP trong `webcam.py`

Ví dụ:

```python
ESP32_IP = "172.20.10.8"
```

Nếu thay đổi IP Wi-Fi, cần cập nhật lại địa chỉ này.

---

# 9. Mô hình AI

Thư mục:

```
model/
```

Bao gồm:

```
LP_detector_nano_61.pt

LP_ocr_nano_62.pt
```

Không đổi tên các file này.

---

# 10. Kết thúc

Nhấn:

```
q
```

để đóng chương trình `webcam.py`.

Đối với `kiem_thu_mo_hinh.py`, đóng cửa sổ OpenCV để kết thúc chương trình.
import torch
import sys
import socket
import urllib.request
import numpy as np
import cv2
import time
import re


orig_torch_load = torch.load
def universal_torch_load(*args, **kwargs):
    if 'weights_only' in kwargs:
        kwargs['weights_only'] = False
    else:
        kwargs.update(weights_only=False)
    return orig_torch_load(*args, **kwargs)
torch.load = universal_torch_load

# Import các thư viện phụ trợ xoay và đọc biển số từ dự án 
import function.chinh_goc_nghieng as chinh_goc_nghieng
import function.xu_ly_ki_tu as xu_ly_ki_tu

# =========================================================
#  CẤU HÌNH ĐỊA CHỈ IP VÀ PORT CỦA ESP32-S3
# =========================================================
ESP32_IP = "172.20.10.8"  
ESP32_PORT_TEXT = 88       # Cổng nhận kết quả chữ hiển thị TFT

# Đường dẫn gọi lệnh chụp ảnh đơn từ Web Server ESP32
esp32_capture_url = f"http://172.20.10.8/capture"

# =========================================================
# DANH SÁCH TRA CỨU MÃ BIỂN SỐ TỈNH THÀNH VIỆT NAM
# =========================================================
PROVINCE_MAP = {
    "11": "Cao Bang", "12": "Lang Son", "14": "Quang Ninh", "15": "Hai Phong", "16": "Hai Phong",
    "17": "Thai Binh", "18": "Nam Dinh", "19": "Phu Tho", "20": "Thai Nguyen", "21": "Yen Bai",
    "22": "Tuyen Quang", "23": "Ha Giang", "24": "Lao Cai", "25": "Lai Chau", "26": "Son La",
    "27": "Dien Bien", "28": "Hoa Binh", "29": "Ha Noi", "30": "Ha Noi", "31": "Ha Noi",
    "32": "Ha Noi", "33": "Ha Noi", "34": "Hai Duong", "35": "Ninh Binh", "36": "Thanh Hoa",
    "37": "Nghe An", "38": "Ha Tinh", "39": "Dong Nai", "43": "Da Nang", "47": "Dak Lak",
    "48": "Dak Nong", "49": "Lam Dong", "50": "TP.HCM", "51": "TP.HCM", "52": "TP.HCM",
    "53": "TP.HCM", "54": "TP.HCM", "55": "TP.HCM", "56": "TP.HCM", "57": "TP.HCM",
    "58": "TP.HCM", "59": "TP.HCM", "60": "Dong Nai", "61": "Binh Duong", "62": "Long An",
    "63": "Tien Giang", "64": "Vinh Long", "65": "Can Tho", "66": "Dong Thap", "67": "An Giang",
    "68": "Kien Giang", "69": "Ca Mau", "70": "Tay Ninh", "71": "Ben Tre", "72": "Ba Ria - Vung Tau",
    "73": "Quang Binh", "74": "Quang Tri", "75": "Thua Thien Hue", "76": "Quang Ngai", "77": "Binh Dinh",
    "78": "Phu Yen", "79": "Khanh Hoa", "81": "Gia Lai", "82": "Kon Tum", "83": "Soc Trang",
    "84": "Tra Vinh", "85": "Ninh Thuan", "86": "Binh Thuan", "88": "Vinh Phuc", "89": "Hung Yen",
    "90": "Ha Nam", "92": "Quang Nam", "93": "Binh Phuoc", "94": "Bac Lieu", "95": "Hau Giang",
    "97": "Bac Kan", "98": "Bac Giang", "99": "Bac Ninh"
}

def get_province(plate_str):
    clean_str = re.sub(r'[^a-zA-Z0-9]', '', plate_str)
    if len(clean_str) >= 2:
        code = clean_str[:2] 
        return PROVINCE_MAP.get(code, "Unknown")
    return "Unknown"

# =========================================================
# TẢI MÔ HÌNH AI YOLOv5
# =========================================================
print("Đang tải mô hình AI YOLOv5...")
yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector_nano_61.pt', force_reload=True, source='local')
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr_nano_62.pt', force_reload=True, source='local')
yolo_license_plate.conf = 0.60

print("\n[HỆ THỐNG SẴN SÀNG] Đang chạy chế độ đồng bộ màn hình 240x240...")

last_sent_plate = ""
last_sent_time = 0

# Tạo text hiển thị tĩnh ban đầu trên màn hình máy tính
display_text_pc = "Cho xe..."
province_text_pc = "--"

while True:
    try:
        # Gửi yêu cầu HTTP GET lấy ảnh từ ESP32-S3 CAM
        img_resp = urllib.request.urlopen(esp32_capture_url, timeout=0.8)
        img_np = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        raw_frame = cv2.imdecode(img_np, -1)
        
        if raw_frame is None:
            continue
            
        # 🟢 ĐỒNG BỘ KÍCH THƯỚC: Resize vùng live cam về đúng tỷ lệ 240x160 trước khi đưa vào AI
        frame_cam = cv2.resize(raw_frame, (240, 160))
        
        # Đưa ảnh vào Model phát hiện vị trí biển số xe
        plates = yolo_LP_detect(frame_cam, size=640)
        list_plates = plates.pandas().xyxy[0].values.tolist()
        
        for plate in list_plates:
            x, y = int(plate[0]), int(plate[1])
            w, h = int(plate[2] - plate[0]), int(plate[3] - plate[1])
            
            crop_img = frame_cam[y:y+h, x:x+w]
            cv2.rectangle(frame_cam, (x, y), (x+w, y+h), color=(0, 0, 255), thickness=2)
            
            lp = ""
            flag = 0
            for cc in range(0, 2):
                for ct in range(0, 2):
                    lp = xu_ly_ki_tu.read_plate(yolo_license_plate, chinh_goc_nghieng.deskew(crop_img, cc, ct))
                    if lp != "unknown":
                        province = get_province(lp)
                        
                        # Cập nhật thông tin hiển thị lên phần đen phía dưới trên máy tính
                        display_text_pc = f"BS: {lp}"
                        province_text_pc = f"Tinh: {province}"
                        
                        # === GỬI KẾT QUẢ XUỐNG ESP32 QUA WI-FI SOCKET (Hẹn giờ 5s) ===
                        current_time = time.time()
                        if lp != last_sent_plate or (current_time - last_sent_time > 5):
                            packet = f"{lp}|{province}\n"
                            try:
                                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                client_socket.settimeout(0.5)
                                client_socket.connect((ESP32_IP, ESP32_PORT_TEXT))
                                client_socket.sendall(packet.encode('utf-8'))
                                client_socket.close()
                                
                                last_sent_plate = lp
                                last_sent_time = current_time
                                print(f"🔥 Đã truyền lên TFT: {lp} | {province}")
                            except Exception as socket_error:
                                print(f"⚠️ Lỗi kết nối Wi-Fi: {socket_error}")
                                
                        flag = 1
                        break
                if flag == 1:
                    break
                    
        #  TẠO KHUNG HÌNH FULL 240x240 MÔ PHỎNG TFT:
        # Tạo một canvas đen hoàn toàn kích thước 240x240
        canvas = np.zeros((240, 240, 3), dtype=np.uint8)
        
        # Đè vùng Live Cam (240x160) vào nửa trên canvas
        canvas[0:160, 0:240] = frame_cam
        
        # Vẽ chữ biển số xe mô phỏng trực tiếp lên vùng đen (160 -> 240) của OpenCV máy tính
        cv2.putText(canvas, display_text_pc, (10, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, province_text_pc, (10, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1, cv2.LINE_AA)
        
        # Hiển thị cửa sổ mô phỏng chuẩn kích thước 240x240
        cv2.imshow('He thong kiem soat Bien so xe (240x240)', canvas)
        
    except urllib.error.URLError:
        pass
    except Exception as e:
        print(f"Loi he thong: {e}")
        
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
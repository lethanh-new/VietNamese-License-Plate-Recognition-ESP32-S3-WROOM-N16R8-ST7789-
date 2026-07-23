# Import thư viện tính toán ma trận
import numpy as np
# Import các hàm toán học
import math
# Import thư viện xử lý ảnh OpenCV
import cv2
# Tăng độ tương phản bằng CLAHE (Contrast Limited Adaptive Histogram Equalization) 
def changeContrast(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)

    # CLAHE giúp tăng độ tương phản cục bộ
    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    cl = clahe.apply(l_channel)
    limg = cv2.merge((cl, a, b))
    enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    return enhanced_img

# Xoay ảnh theo góc angle (độ)
def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1]) / 2)

    rot_mat = cv2.getRotationMatrix2D(
        image_center,
        angle,
        1.0
    )

    result = cv2.warpAffine(
        image,
        rot_mat,
        image.shape[1::-1],
        flags=cv2.INTER_LINEAR
    )
    return result
# Tính góc nghiêng của biển số
def compute_skew(src_img, center_thres):

    if len(src_img.shape) == 3:
        h, w, _ = src_img.shape
    elif len(src_img.shape) == 2:
        h, w = src_img.shape
    else:
        print("Unsupported image type")

    # Khử nhiễu
    img = cv2.medianBlur(src_img, 3)

    # Phát hiện cạnh
    edges = cv2.Canny(
        img,
        threshold1=30,
        threshold2=100,
        apertureSize=3,
        L2gradient=True
    )

    # Phát hiện các đường thẳng
    lines = cv2.HoughLinesP(
        edges,
        1,
        math.pi / 180,
        30,
        minLineLength=w / 1.5,
        maxLineGap=h / 3.0
    )

    if lines is None:
        return 1

    # Chọn đường nằm gần phía trên nhất
    min_line = 100
    min_line_pos = 0

    for i in range(len(lines)):
        for x1, y1, x2, y2 in lines[i]:

            center_point = [
                (x1 + x2) / 2,
                (y1 + y2) / 2
            ]

            if center_thres == 1:
                if center_point[1] < 7:
                    continue

            if center_point[1] < min_line:
                min_line = center_point[1]
                min_line_pos = i

    angle = 0.0
    cnt = 0

    for x1, y1, x2, y2 in lines[min_line_pos]:

        ang = np.arctan2(
            y2 - y1,
            x2 - x1
        )

        # Bỏ các góc quá lớn
        if math.fabs(ang) <= 30:
            angle += ang
            cnt += 1

    if cnt == 0:
        return 0.0

    return (angle / cnt) * 180 / math.pi


# Căn chỉnh biển số về nằm ngang
def deskew(src_img, change_cons, center_thres):

    if change_cons == 1:
        return rotate_image(
            src_img,
            compute_skew(
                changeContrast(src_img),
                center_thres
            )
        )

    return rotate_image(
        src_img,
        compute_skew(src_img, center_thres)
    )
import math
# Tính phương trình đường thẳng đi qua hai điểm
# y = ax + b
def linear_equation(x1, y1, x2, y2):
    b = y1 - (y2 - y1) * x1 / (x2 - x1)
    a = (y1 - b) / x1
    return a, b


# Kiểm tra một điểm có nằm gần đường thẳng hay không
# Sai số cho phép ±3 pixel
def check_point_linear(x, y, x1, y1, x2, y2):
    a, b = linear_equation(x1, y1, x2, y2)
    y_pred = a * x + b
    return math.isclose(y_pred, y, abs_tol=3)


# Nhận dạng chuỗi ký tự trên biển số
# Đồng thời phân loại biển số 1 hàng hoặc 2 hàng
def read_plate(yolo_license_plate, im):

    # Mặc định biển số 1 hàng
    LP_type = "1"

    # Chạy mô hình OCR YOLO
    results = yolo_license_plate(im)

    # Lấy danh sách các bounding box
    bb_list = results.pandas().xyxy[0].values.tolist()

    # Nếu số ký tự không hợp lệ thì bỏ qua
    if len(bb_list) == 0 or len(bb_list) < 7 or len(bb_list) > 10:
        return "unknown"

    center_list = []
    y_sum = 0

    # Tính tọa độ tâm của từng ký tự
    for bb in bb_list:

        x_c = (bb[0] + bb[2]) / 2
        y_c = (bb[1] + bb[3]) / 2

        y_sum += y_c

        # Lưu:
        # x tâm
        # y tâm
        # ký tự dự đoán
        center_list.append([x_c, y_c, bb[-1]])

    # Tìm ký tự ngoài cùng bên trái và bên phải
    l_point = center_list[0]
    r_point = center_list[0]

    for cp in center_list:

        if cp[0] < l_point[0]:
            l_point = cp

        if cp[0] > r_point[0]:
            r_point = cp

    # Kiểm tra tất cả ký tự có nằm trên cùng
    # một đường thẳng hay không
    # Nếu không -> biển số 2 hàng
    for ct in center_list:

        if l_point[0] != r_point[0]:

            if not check_point_linear(
                ct[0],
                ct[1],
                l_point[0],
                l_point[1],
                r_point[0],
                r_point[1]
            ):
                LP_type = "2"

    # Trung bình tọa độ y
    y_mean = int(y_sum / len(bb_list))

    # (Không sử dụng trong đoạn mã này)
    size = results.pandas().s

    # Ghép ký tự theo từng loại biển số
    line_1 = []
    line_2 = []
    license_plate = ""

    # Biển số 2 hàng
    if LP_type == "2":

        # Chia ký tự thành 2 dòng
        for c in center_list:

            if int(c[1]) > y_mean:
                line_2.append(c)
            else:
                line_1.append(c)

        # Sắp xếp từ trái sang phải
        for l1 in sorted(line_1, key=lambda x: x[0]):
            license_plate += str(l1[2])

        license_plate += "-"

        for l2 in sorted(line_2, key=lambda x: x[0]):
            license_plate += str(l2[2])

    # Biển số 1 hàng
    else:

        for l in sorted(center_list, key=lambda x: x[0]):
            license_plate += str(l[2])

    # Trả về chuỗi biển số
    return license_plate
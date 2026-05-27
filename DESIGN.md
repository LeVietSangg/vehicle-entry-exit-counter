# HỆ THỐNG ĐẾM XE RA/VÀO (VEHICLE ENTRY/EXIT COUNTER)

## 1. TỔNG QUAN DỰ ÁN

**Mục tiêu:** Xây dựng một script Python cho phép nhận vào một file video giao thông
khu vực cổng, hệ thống tự động bám vết xe, xác định hướng di chuyển qua vạch ảo
để đếm số lượng xe VÀO (Entry) và RA (Exit), trả về video kết quả và file Excel báo cáo.

**Công nghệ chủ đạo:**
- Ngôn ngữ: Python thuần
- AI Engine: Ultralytics (YOLOv8n) → Supervision (ByteTrack / LineZone)
- Thống kê: OpenCV (hiển thị màn hình video), Pandas (xuất file CSV/Excel)

---

## 2. CẤU TRÚC THƯ MỤC

```
vehicle-entry-exit-counter/
│
├── DESIGN.md                   # Tài liệu kiến trúc dự án
├── requirements.txt            # Danh sách thư viện
├── main.py                     # File chạy chính
│
├── processing/                 # Package xử lý logic
│   ├── __init__.py
│   ├── tracker.py              # YOLO + Tracking (ByteTrack)
│   └── counter.py              # Thuật toán đếm hướng Ra/Vào + Quản lý Log
│
├── data/                       # Chứa 3 video test mẫu
│   ├── video_easy.mp4
│   ├── video_medium.mp4
│   └── video_hard.mp4
│
├── outputs/                    # Chứa video kết quả + file excel kết quả
│   ├── result_<tên_video>.mp4
│   └── report_<tên_video>.xlsx
│
└── reports/                    # File báo cáo Word/Slide (nếu có)
```

---

## 3. KIẾN TRÚC DỮ LIỆU LOG XE RA/VÀO

### 3.1. Mục đích

Mỗi lần một xe cắt qua vạch ảo (LineZone), hệ thống sẽ ghi nhận một bản ghi
(log entry) vào một **mảng tạm thời trong bộ nhớ** (Python list). Mảng này được
dùng để:
- Hiển thị thống kê real-time trên video đầu ra.
- Xuất ra file Excel/CSV khi xử lý xong.

### 3.2. Các trường thông tin mỗi bản ghi (Log Entry)

Mỗi phần tử trong mảng log là một **dictionary** với các trường sau:

| # | Tên trường       | Kiểu dữ liệu | Ví dụ              | Mô tả                                                      |
|---|------------------|---------------|---------------------|-------------------------------------------------------------|
| 1 | `track_id`       | `int`         | `7`                 | ID duy nhất của xe, do ByteTrack gán khi bám vết            |
| 2 | `class_id`       | `int`         | `2`                 | Mã lớp COCO của đối tượng (2=car, 3=motorcycle, 5=bus, 7=truck) |
| 3 | `class_name`     | `str`         | `"car"`             | Tên loại phương tiện (chuyển từ class_id)                   |
| 4 | `direction`      | `str`         | `"Entry"`           | Hướng di chuyển: `"Entry"` (Vào) hoặc `"Exit"` (Ra)        |
| 5 | `frame_number`   | `int`         | `342`               | Số thứ tự frame video tại thời điểm xe cắt vạch            |
| 6 | `timestamp`      | `str`         | `"00:00:14"`        | Thời gian trong video (HH:MM:SS), tính từ frame_number + FPS |
| 7 | `confidence`     | `float`       | `0.87`              | Độ tin cậy nhận diện từ YOLO (0.0 → 1.0)                   |

### 3.3. Ví dụ mảng log trong bộ nhớ

```python
vehicle_log = [
    {
        "track_id": 1,
        "class_id": 2,
        "class_name": "car",
        "direction": "Entry",
        "frame_number": 120,
        "timestamp": "00:00:04",
        "confidence": 0.92
    },
    {
        "track_id": 3,
        "class_id": 3,
        "class_name": "motorcycle",
        "direction": "Exit",
        "frame_number": 456,
        "timestamp": "00:00:15",
        "confidence": 0.85
    },
    {
        "track_id": 7,
        "class_id": 5,
        "class_name": "bus",
        "direction": "Entry",
        "frame_number": 890,
        "timestamp": "00:00:30",
        "confidence": 0.78
    }
]
```

### 3.4. Bảng ánh xạ Class ID → Class Name

Hệ thống chỉ theo dõi các lớp phương tiện giao thông trong bộ COCO:

| Class ID (COCO) | Class Name     | Tiếng Việt     |
|------------------|---------------|----------------|
| 2                | `car`         | Ô tô con       |
| 3                | `motorcycle`  | Xe máy          |
| 5                | `bus`         | Xe buýt         |
| 7                | `truck`       | Xe tải          |

```python
VEHICLE_CLASS_MAP = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}
```

---

## 4. QUY TẮC SỐNG CÒN (Definition of Done)

- **Đếm đúng hướng:** Tuyệt đối không nhầm xe đi Vào thành Ra và ngược lại.
- **Định dạng file Excel xuất ra phải rõ ràng**, không bỏ sót bất kỳ đầu ra nào cho biết dữ liệu mỗi xe khớp chạy vạch nào.

---

## 5. ĐỊNH DẠNG FILE EXCEL ĐẦU RA

File `report_<tên_video>.xlsx` sẽ gồm **2 sheet**:

### Sheet 1: `Summary` — Tổng hợp

| Loại xe       | Số xe Vào (Entry) | Số xe Ra (Exit) | Tổng |
|---------------|--------------------|-----------------|------|
| car           | 5                  | 3               | 8    |
| motorcycle    | 2                  | 1               | 3    |
| bus           | 1                  | 0               | 1    |
| truck         | 0                  | 1               | 1    |
| **TỔNG CỘNG** | **8**              | **5**           | **13** |

### Sheet 2: `Detail` — Chi tiết từng lượt

| STT | Track ID | Loại xe    | Hướng  | Frame  | Thời gian  | Độ tin cậy |
|-----|----------|------------|--------|--------|------------|------------|
| 1   | 1        | car        | Entry  | 120    | 00:00:04   | 0.92       |
| 2   | 3        | motorcycle | Exit   | 456    | 00:00:15   | 0.85       |
| 3   | 7        | bus        | Entry  | 890    | 00:00:30   | 0.78       |

---

## 6. CÁCH LÀM VIỆC NHÓM

- **TV A:** Đảm nhiệm module tracking từ video đầu ra  → file `tracker.py`
- **TV B:** Đảm nhiệm module counter (đếm hướng, quản lý log) → file `counter.py`
- **TV C:** Đảm nhiệm việc kết nối file Excel và giao diện video chương trình → file `main.py`
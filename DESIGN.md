# HỆ THỐNG ĐẾM XE RA/VÀO (VEHICLE ENTRY/EXIT COUNTER)

## 1. Thành phần công nghệ áp dụng
- Ngôn ngữ: Python 3
- AI Model: YOLOv8n (Nhận diện phương tiện)
- Tracking: ByteTrack (Bám vết gán ID phương tiện)
- Đếm hướng: Thư viện Supervision (Dùng tính năng LineZone cắt vạch ảo)

## 2. Logic phân biệt hướng xe (Directional Logic)
- Vẽ vạch kiểm soát ảo chia không gian video làm 2 vùng: Vùng A (Phía Ngoài Cổng) và Vùng B (Phía Trong Cổng).
- **Entry (Đi Vào):** Xe di chuyển cắt vạch theo hướng từ Vùng A sang Vùng B.
- **Exit (Đi Ra):** Xe di chuyển cắt vạch theo hướng từ Vùng B sang Vùng A.

## 3. Cấu trúc dữ liệu Log xe (Output tạm thời)
- Thông tin mỗi lượt xe qua vạch được lưu tạm vào một mảng dạng:
  `{ "track_id": 1, "class": "car", "direction": "Entry", "time": "00:14" }`
# Vehicle Entry/Exit Counter 🚗🚙

Hệ thống giám sát và đếm lưu lượng phương tiện giao thông thông minh sử dụng Trí tuệ nhân tạo (AI). 
Dự án là sự kết hợp hoàn hảo giữa mô hình nhận diện **YOLOv8**, thuật toán tracking **ByteTrack**, xử lý ảnh **OpenCV** và giao diện người dùng **Tkinter**.

## 🌟 Tính năng Cốt lõi

1. **Giao diện trực quan (GUI)**: Cho phép tinh chỉnh mọi tham số (Video, Model, Confidence, Line ROI) trực tiếp mà không cần sửa code.
2. **Công cụ Pick Lines (Interactive ROI)**: Tích hợp công cụ trỏ chuột lên khung hình video để vẽ 2 vạch Entry (Vào) và Exit (Ra) một cách tự động.
3. **Quản lý đa luồng (Multi-threading)**: Giao diện mượt mà, cho phép Stop khẩn cấp giữa chừng mà không làm mất dữ liệu đếm.
4. **Kết xuất Báo cáo Đa tầng**: Tự động xuất biểu đồ trực quan (Matplotlib) và file báo cáo Excel (Pandas) chi tiết từng giây.
5. **Cơ sở dữ liệu Lịch sử (SQLite)**: Lưu vết tự động mọi phiên làm việc vào CSDL và tra cứu dễ dàng qua giao diện.

## ⚙️ Cài đặt & Khởi chạy

**Yêu cầu hệ thống:** Python 3.8 trở lên.

1. Cài đặt các thư viện phụ thuộc:
```bash
pip install ultralytics supervision opencv-python pandas openpyxl matplotlib
```

2. Khởi chạy phần mềm:
```bash
python app.py
```

## 📝 Hướng dẫn Test 

Để thấy được sức mạnh thực sự của hệ thống tracking và đếm xe, nhóm **đặc biệt khuyến nghị** người test nên tải và sử dụng các video có dạng **đường cao tốc 2 làn chạy ngược chiều nhau (một chiều đi lên, một chiều đi xuống)**.

- **Bước 1**: Bấm `Browse` để chọn video 2 chiều.![VIDEO NHƯ ẢNH](image.png)
- **Bước 2**: Bấm nút `🎯 Pick Lines`.
  - Click chuột lần 1 vào vạch làn đi LÊN (Màu xanh - Entry).
  - Click chuột lần 2 vào vạch làn đi XUỐNG (Màu đỏ - Exit).
- **Bước 3**: Bấm `Start Processing` và quan sát.

---
*Dự án hoàn thiện được thiết kế với mục tiêu triển khai thực tế tại các bãi đỗ xe thông minh, trạm thu phí và trạm quan trắc giao thông.*

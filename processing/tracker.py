import supervision as sv
from ultralytics import YOLO

def init_yolo(model_path: str = "yolov8n.pt") -> YOLO:
    """
    Khởi tạo và tải mô hình YOLOv8.
    
    Args:
        model_path: Đường dẫn tới file trọng số của mô hình YOLOv8 (mặc định yolov8n.pt).
        
    Returns:
        Đối tượng mô hình YOLO.
    """
    model = YOLO(model_path)
    return model


def init_tracker(track_thresh: float = 0.25, track_buffer: int = 120, match_thresh: float = 0.8, frame_rate: int = 30) -> sv.ByteTrack:
    """
    Khởi tạo thuật toán bám vết ByteTrack bằng thư viện supervision.
    Đảm bảo một chiếc xe khi đi từ đầu đến cuối video chỉ giữ duy nhất 1 ID định danh.
    
    Args:
        track_thresh: Ngưỡng confidence tối thiểu để duy trì bám vết.
        track_buffer: Số lượng frame tối đa giữ lại ID của phương tiện khi bị mất dấu (ví dụ do che khuất).
                      120 frames ở 30fps tương đương 4 giây, giúp bám vết mượt mà hơn và tránh nhảy ID.
        match_thresh: Ngưỡng IoU để ghép nối các bounding box.
        frame_rate: Tốc độ khung hình (FPS) của video.
        
    Returns:
        Đối tượng sv.ByteTrack.
    """
    tracker = sv.ByteTrack(
        track_thresh=track_thresh,
        track_buffer=track_buffer,
        match_thresh=match_thresh,
        frame_rate=frame_rate
    )
    return tracker

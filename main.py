"""Entry point cho hệ thống đếm xe ra/vào.

Đã tích hợp đầy đủ YOLOv8, ByteTrack, LineZone, OpenCV vẽ UI và xuất Excel.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import cv2
import supervision as sv
import numpy as np

from processing.counter import VEHICLE_CLASS_MAP, VehicleLogger
from processing.tracker import build_yolo_kwargs, init_tracker, init_yolo


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vehicle Entry/Exit Counter")
    parser.add_argument(
        "--source",
        type=str,
        default="data/video_easy.mp4",
        help="Duong dan video nguon",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Model YOLOv8 (vd: yolov8n.pt)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.01,
        help="Nguong confidence cho YOLO (lower to capture more detections)",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.2,
        help="Nguong IoU cho NMS (lower to allow overlapping boxes)",
    )
    parser.add_argument(
        "--track_thresh",
        type=float,
        default=0.25,
        help="ByteTrack track_thresh (lower to keep more tracks)",
    )
    parser.add_argument(
        "--track_buffer",
        type=int,
        default=120,
        help="ByteTrack track_buffer (frames to keep lost tracks)",
    )
    parser.add_argument(
        "--match_thresh",
        type=float,
        default=0.8,
        help="ByteTrack match_thresh (IoU for matching boxes)",
    )
    parser.add_argument(
        "--entry_line_y",
        type=int,
        default=288,
        help="Y coordinate of virtual counting line for ENTRY (default 288).",
    )
    parser.add_argument(
        "--exit_line_y",
        type=int,
        default=200,
        help="Y coordinate of virtual counting line for EXIT (default 200).",
    )
    # Existing args continue below
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Không tìm thấy video đầu vào tại: {source_path}")
        print("Vui lòng copy một video test vào thư mục data/ (ví dụ: data/video_easy.mp4)")
        return

    # Khởi tạo mô hình AI
    print("Đang khởi tạo YOLOv8 và ByteTrack...")
    model, class_ids = init_yolo(
        model_path=args.model,
        class_ids=VEHICLE_CLASS_MAP.keys(),
        conf=args.conf,
        iou=args.iou,
    )
    yolo_kwargs = build_yolo_kwargs(class_ids, conf=args.conf, iou=args.iou)

    cap = cv2.VideoCapture(str(source_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Chuẩn bị luồng ghi video đầu ra
    os.makedirs("outputs", exist_ok=True)
    out_video_path = f"outputs/result_{source_path.name}"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_video = cv2.VideoWriter(out_video_path, fourcc, fps, (width, height))

    # Khởi tạo tracker & logger
    tracker = init_tracker(
        track_thresh=args.track_thresh,
        track_buffer=args.track_buffer,
        match_thresh=args.match_thresh,
        frame_rate=int(fps),
    )
    logger = VehicleLogger(fps=fps)

    # Cấu hình 2 vạch ảo độc lập cho Entry và Exit
    START_ENTRY = sv.Point(0, args.entry_line_y)
    END_ENTRY = sv.Point(width, args.entry_line_y)
    line_zone_entry = sv.LineZone(start=START_ENTRY, end=END_ENTRY)

    START_EXIT = sv.Point(0, args.exit_line_y)
    END_EXIT = sv.Point(width, args.exit_line_y)
    line_zone_exit = sv.LineZone(start=START_EXIT, end=END_EXIT)

    # Khởi tạo các công cụ vẽ (Annotator) của supervision
    box_annotator = sv.BoundingBoxAnnotator(thickness=2)
    label_annotator = sv.LabelAnnotator(text_thickness=2, text_scale=0.5)
    line_zone_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=2, text_scale=1)

    frame_index = 0
    print(f"Bắt đầu xử lý video... Vạch Entry Y={args.entry_line_y}, Vạch Exit Y={args.exit_line_y}")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_index += 1

        # YOLOv8 nhận diện
        results = model.predict(frame, verbose=False, **yolo_kwargs)
        if not results:
            out_video.write(frame)
            continue
            
        detections = sv.Detections.from_ultralytics(results[0])
        
        # Cập nhật tracker (ByteTrack)
        detections = tracker.update_with_detections(detections)

        # Cập nhật LineZone và kiểm tra đếm hướng
        if len(detections) > 0:
            crossed_in_entry, _ = line_zone_entry.trigger(detections=detections)
            _, crossed_out_exit = line_zone_exit.trigger(detections=detections)

            # Ghi log nếu có xe đi ngang qua vạch
            for i, track_id in enumerate(detections.tracker_id):
                class_id = detections.class_id[i]
                confidence = detections.confidence[i]
                
                direction = None
                if crossed_in_entry[i]:
                    direction = "Entry"
                elif crossed_out_exit[i]:
                    direction = "Exit"
                
                if direction:
                    logger.add_log(
                        track_id=int(track_id),
                        class_id=int(class_id),
                        direction=direction,
                        frame_number=frame_index,
                        confidence=float(confidence)
                    )

        # Vẽ bounding box và label lên frame
        labels = []
        for i in range(len(detections)):
            if detections.tracker_id is not None:
                tracker_id = detections.tracker_id[i]
                class_name = VEHICLE_CLASS_MAP.get(detections.class_id[i], "unknown")
                conf = detections.confidence[i]
                labels.append(f"#{tracker_id} {class_name} {conf:.2f}")

        annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
        annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
        
        # Vẽ vạch ảo và bộ đếm tổng số
        if len(detections) > 0:
            line_zone_entry.in_count = logger.total_entry
            line_zone_entry.out_count = 0
            line_zone_exit.in_count = 0
            line_zone_exit.out_count = logger.total_exit
            
        annotated_frame = line_zone_annotator.annotate(annotated_frame, line_counter=line_zone_entry)
        annotated_frame = line_zone_annotator.annotate(annotated_frame, line_counter=line_zone_exit)

        # Ghi frame vào video đầu ra
        out_video.write(annotated_frame)

        if frame_index % 50 == 0:
            print(f"Đã xử lý frame {frame_index}... Entry: {logger.total_entry}, Exit: {logger.total_exit}")

    cap.release()
    out_video.release()

    print(f"\n[Hoàn thành] Đã xử lý xong video. Tổng frame: {frame_index}")
    print(f"Tổng số xe VÀO (Entry): {logger.total_entry}")
    print(f"Tổng số xe RA (Exit): {logger.total_exit}")

    # Xuất Excel
    report_path = f"outputs/report_{source_path.stem}.xlsx"
    final_path = logger.export_to_excel(report_path)
    print(f"Đã lưu video kết quả tại: {out_video_path}")
    print(f"Đã lưu báo cáo Excel tại: {final_path}")


if __name__ == "__main__":
    main()

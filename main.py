"""Entry point cho hệ thống đếm xe ra/vào.

Tích hợp YOLOv8, ByteTrack, LineZone, OpenCV và xuất Excel.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import cv2
import gc
import torch
import time
import supervision as sv

from database import init_db, insert_session
from processing.counter import VEHICLE_CLASS_MAP, VehicleLogger
from processing.tracker import build_yolo_kwargs, init_tracker, init_yolo


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vehicle Entry/Exit Counter")

    parser.add_argument("--source", type=str, default="data/video_easy.mp4")
    parser.add_argument("--model", type=str, default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.45)

    parser.add_argument("--track_thresh", type=float, default=0.25)
    parser.add_argument("--track_buffer", type=int, default=30)
    parser.add_argument("--match_thresh", type=float, default=0.8)

    parser.add_argument("--entry_line_y", type=int, default=430)
    parser.add_argument("--exit_line_y", type=int, default=330)
    parser.add_argument("--headless", action="store_true", help="Chạy không cần hiển thị cửa sổ OpenCV")

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Không tìm thấy video: {source_path}")
        return

    init_db()

    print("Đang khởi tạo YOLOv8 và ByteTrack...")

    model, class_ids = init_yolo(
        model_path=args.model,
        class_ids=VEHICLE_CLASS_MAP.keys(),
        conf=args.conf,
        iou=args.iou,
    )
    yolo_kwargs = build_yolo_kwargs(class_ids, conf=args.conf, iou=args.iou)

    cap = cv2.VideoCapture(str(source_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    os.makedirs("outputs", exist_ok=True)

    out_video_path = f"outputs/result_{source_path.stem}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(out_video_path, fourcc, fps, (width, height))

    tracker = init_tracker(
        track_thresh=args.track_thresh,
        track_buffer=args.track_buffer,
        match_thresh=args.match_thresh,
        frame_rate=int(fps),
    )

    logger = VehicleLogger(fps=fps)

    mid_x = width // 2

    entry_line = sv.LineZone(
        start=sv.Point(mid_x, args.entry_line_y),
        end=sv.Point(width, args.entry_line_y),
    )

    exit_line = sv.LineZone(
        start=sv.Point(0, args.exit_line_y),
        end=sv.Point(mid_x, args.exit_line_y),
    )

    box_annotator = sv.BoundingBoxAnnotator(thickness=2)
    label_annotator = sv.LabelAnnotator(text_thickness=2, text_scale=0.5)

    frame_index = 0
    prev_time = time.time()
    fps_display = 0.0
    print("Bắt đầu xử lý video...")

    while True:
        if os.path.exists("stop.flag"):
            print("Người dùng đã dừng tiến trình sớm.")
            os.remove("stop.flag")
            break

        ok, frame = cap.read()
        if not ok:
            break

        frame_index += 1
        
        current_time = time.time()
        time_diff = current_time - prev_time
        if time_diff > 0:
            fps_display = 1.0 / time_diff
        prev_time = current_time

        results = model.predict(frame, verbose=False, **yolo_kwargs)
        detections = sv.Detections.from_ultralytics(results[0])

        detections = tracker.update_with_detections(detections)

        if len(detections) > 0 and detections.tracker_id is not None:
            crossed_entry_in, crossed_entry_out = entry_line.trigger(detections=detections)
            crossed_exit_in, crossed_exit_out = exit_line.trigger(detections=detections)

            for i, track_id in enumerate(detections.tracker_id):
                class_id = int(detections.class_id[i])
                confidence = float(detections.confidence[i])

                if crossed_entry_in[i] or crossed_entry_out[i]:
                    logger.add_log(
                        track_id=int(track_id),
                        class_id=class_id,
                        direction="Entry",
                        frame_number=frame_index,
                        confidence=confidence,
                    )

                elif crossed_exit_in[i] or crossed_exit_out[i]:
                    logger.add_log(
                        track_id=int(track_id),
                        class_id=class_id,
                        direction="Exit",
                        frame_number=frame_index,
                        confidence=confidence,
                    )

        labels = []
        if len(detections) > 0 and detections.tracker_id is not None:
            for i in range(len(detections)):
                class_id = int(detections.class_id[i])
                class_name = VEHICLE_CLASS_MAP.get(class_id, "vehicle")
                labels.append(class_name)

        annotated_frame = box_annotator.annotate(
            scene=frame.copy(),
            detections=detections,
        )
        annotated_frame = label_annotator.annotate(
            scene=annotated_frame,
            detections=detections,
            labels=labels,
        )

        cv2.line(
            annotated_frame,
            (mid_x, args.entry_line_y),
            (width, args.entry_line_y),
            (0, 255, 0),
            2,
        )
        cv2.putText(
            annotated_frame,
            f"ENTRY: {logger.total_entry}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.line(
            annotated_frame,
            (0, args.exit_line_y),
            (mid_x, args.exit_line_y),
            (0, 0, 255),
            2,
        )
        cv2.putText(
            annotated_frame,
            f"EXIT: {logger.total_exit}",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )
        
        inside_zone = logger.total_entry - logger.total_exit
        cv2.putText(
            annotated_frame,
            f"INSIDE ZONE: {inside_zone}",
            (30, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (200, 0, 0),
            2,
        )
        
        # Hien thi FPS o goc tren ben phai
        cv2.putText(
            annotated_frame,
            f"FPS: {fps_display:.1f}",
            (width - 200, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2,
        )

        out_video.write(annotated_frame)

        if not args.headless:
            display_frame = cv2.resize(annotated_frame, (960, 540))
            cv2.imshow(
                "Vehicle Entry/Exit Counter - Processing Video",
                display_frame,
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        if frame_index % 50 == 0:
            print(
                f"Đã xử lý frame {frame_index}... "
                f"Entry: {logger.total_entry}, Exit: {logger.total_exit}"
            )
            
        # Giải phóng bộ nhớ thủ công để tránh rò rỉ RAM (Fix OutOfMemory)
        del frame
        del annotated_frame
        del results
        del detections
        
        if frame_index % 30 == 0:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    cap.release()
    out_video.release()
    cv2.destroyAllWindows()

    report_path = f"outputs/report_{source_path.stem}.xlsx"
    final_path = logger.export_to_excel(report_path)

    insert_session(
        video_source=source_path.name,
        total_entry=logger.total_entry,
        total_exit=logger.total_exit,
        excel_path=final_path
    )

    print("\n[Hoàn thành]")
    print(f"Tổng frame: {frame_index}")
    print(f"Tổng số xe VÀO (Entry): {logger.total_entry}")
    print(f"Tổng số xe RA (Exit): {logger.total_exit}")
    print(f"Đã lưu video kết quả tại: {out_video_path}")
    print(f"Đã lưu báo cáo Excel tại: {final_path}")


if __name__ == "__main__":
    main()
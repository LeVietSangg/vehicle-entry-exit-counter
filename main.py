"""Entry point cho hệ thống đếm xe ra/vào.

Hiện tại file này chỉ tích hợp cấu hình YOLOv8 và bộ lọc class phương tiện.
Các bước tracking và đếm hướng sẽ được bổ sung sau.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import supervision as sv

from processing.counter import VEHICLE_CLASS_MAP
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
		default=0.25,
		help="Nguong confidence cho YOLO",
	)
	parser.add_argument(
		"--iou",
		type=float,
		default=0.45,
		help="Nguong IoU cho NMS",
	)
	return parser.parse_args()


def main() -> None:
	args = _parse_args()

	model, class_ids = init_yolo(
		model_path=args.model,
		class_ids=VEHICLE_CLASS_MAP.keys(),
		conf=args.conf,
		iou=args.iou,
	)
	yolo_kwargs = build_yolo_kwargs(class_ids, conf=args.conf, iou=args.iou)

	source_path = Path(args.source)
	if not source_path.exists():
		print(f"Khong tim thay video: {source_path}")
		return

	cap = cv2.VideoCapture(str(source_path))
	fps = cap.get(cv2.CAP_PROP_FPS)
	if not fps or fps <= 0:
		fps = 30.0

	tracker = init_tracker(frame_rate=int(fps))
	unique_track_ids: set[int] = set()
	frame_index = 0

	while True:
		ok, frame = cap.read()
		if not ok:
			break
		frame_index += 1

		results = model.predict(frame, verbose=False, **yolo_kwargs)
		if not results:
			continue
		detections = sv.Detections.from_ultralytics(results[0])
		tracked = tracker.update_with_detections(detections)

		if tracked.tracker_id is not None:
			unique_track_ids.update(int(track_id) for track_id in tracked.tracker_id)

	print(
		"Da chay ByteTrack. "
		f"So frame: {frame_index}, so track_id: {len(unique_track_ids)}"
	)

	cap.release()


if __name__ == "__main__":
	main()

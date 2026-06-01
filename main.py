"""Entry point cho hệ thống đếm xe ra/vào.

Hiện tại file này chỉ tích hợp cấu hình YOLOv8 và bộ lọc class phương tiện.
Các bước tracking và đếm hướng sẽ được bổ sung sau.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

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

	tracker = init_tracker()

	source_path = Path(args.source)
	if not source_path.exists():
		print(f"Khong tim thay video: {source_path}")
		return

	cap = cv2.VideoCapture(str(source_path))
	ok, frame = cap.read()
	if not ok:
		print("Khong doc duoc frame tu video.")
		cap.release()
		return

	results = model.predict(frame, verbose=False, **yolo_kwargs)
	total_boxes = sum(len(r.boxes) for r in results)
	print(
	"Da khoi tao YOLOv8, ByteTrack va bo loc class phuong tien. "
	f"So detections o frame dau: {total_boxes}. "
	f"Tracker: {tracker.__class__.__name__}"
)

	cap.release()


if __name__ == "__main__":
	main()

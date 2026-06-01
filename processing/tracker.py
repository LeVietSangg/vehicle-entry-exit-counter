"""
tracker.py — Module cấu hình YOLOv8 và danh sách class phương tiện.

Chức năng chính:
- Khởi tạo model YOLOv8.
- Gán bộ lọc class phương tiện cần theo dõi.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import supervision as sv


import pickle

import inspect
import torch
from torch.nn.modules.container import Sequential
from ultralytics import YOLO
from ultralytics.nn.modules import Conv
from ultralytics.nn.tasks import DetectionModel

from processing.counter import VEHICLE_CLASS_MAP

# ============================================================
#  CẤU HÌNH MẶC ĐỊNH
# ============================================================
DEFAULT_MODEL_PATH = "yolov8n.pt"
DEFAULT_CONFIDENCE = 0.25
DEFAULT_IOU = 0.45


def _normalize_class_ids(class_ids: Iterable[int] | None) -> list[int]:
	"""Chuẩn hóa danh sách class_id hợp lệ.

	Args:
		class_ids: Danh sách class_id cần theo dõi. Nếu None, dùng mặc định.

	Returns:
		Danh sách class_id hợp lệ, đã sắp xếp tăng dần.
	"""
	if class_ids is None:
		return sorted(VEHICLE_CLASS_MAP.keys())

	# Chỉ giữ các class_id hợp lệ theo map
	normalized = [cid for cid in class_ids if cid in VEHICLE_CLASS_MAP]
	return sorted(set(normalized))


def init_yolo(
	model_path: str = DEFAULT_MODEL_PATH,
	class_ids: Iterable[int] | None = None,
	conf: float = DEFAULT_CONFIDENCE,
	iou: float = DEFAULT_IOU,
) -> tuple[YOLO, list[int]]:
	"""Khởi tạo model YOLOv8 và gán bộ lọc class phương tiện.

	Args:
		model_path: Đường dẫn hoặc tên model YOLOv8 (vd: "yolov8n.pt").
		class_ids: Danh sách class_id cần theo dõi (COCO). Nếu None,
			dùng mặc định từ VEHICLE_CLASS_MAP.
		conf: Ngưỡng confidence cho YOLO.
		iou: Ngưỡng IoU cho NMS.

	Returns:
		(model, class_ids) đã chuẩn hóa.
	"""
	# Torch 2.6+ default weights_only=True, allowlist known YOLO classes
	safe_types = [DetectionModel, Sequential, Conv]
	# add_safe_globals ensures nested torch.load() calls see the allowlist
	torch.serialization.add_safe_globals(safe_types)

	# Fallback for strict environments: disable weights_only default if available
	if hasattr(torch.serialization, "set_default_load_weights_only"):
		torch.serialization.set_default_load_weights_only(False)

	# Last-resort: patch torch.load to force weights_only=False when supported
	signature = inspect.signature(torch.load)
	if "weights_only" in signature.parameters:
		original_load = torch.load

		def _torch_load(*args, **kwargs):
			kwargs.setdefault("weights_only", False)
			return original_load(*args, **kwargs)

		torch.load = _torch_load

	model = YOLO(model_path)
	filtered_class_ids = _normalize_class_ids(class_ids)

	# Gán mặc định để dùng khi gọi model.predict() nếu không truyền lại
	model.overrides["conf"] = conf
	model.overrides["iou"] = iou
	model.overrides["classes"] = filtered_class_ids

	return model, filtered_class_ids


def build_yolo_kwargs(
	class_ids: Sequence[int],
	conf: float = DEFAULT_CONFIDENCE,
	iou: float = DEFAULT_IOU,
) -> dict:
	"""Tạo kwargs cho YOLO predict với bộ lọc class.

	Args:
		class_ids: Danh sách class_id đã chuẩn hóa.
		conf: Ngưỡng confidence cho YOLO.
		iou: Ngưỡng IoU cho NMS.

	Returns:
		Dict kwargs truyền vào model.predict().
	"""
	return {
		"classes": list(class_ids),
		"conf": conf,
		"iou": iou,
	}

def init_tracker(
	track_activation_threshold: float = 0.25,
	lost_track_buffer: int = 30,
	minimum_matching_threshold: float = 0.8,
	frame_rate: int = 30,
) -> sv.ByteTrack:
	"""Khởi tạo ByteTrack tracker.

	Tracker giúp bám vết phương tiện qua từng frame và giữ ổn định ID
	cho cùng một chiếc xe trong quá trình đi từ đầu đến cuối video.
	"""
	tracker = sv.ByteTrack(
		track_activation_threshold=track_activation_threshold,
		lost_track_buffer=lost_track_buffer,
		minimum_matching_threshold=minimum_matching_threshold,
		frame_rate=frame_rate,
	)

	return tracker

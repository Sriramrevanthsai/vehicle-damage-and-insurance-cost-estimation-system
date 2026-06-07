from pathlib import Path
import os

import cv2
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "best.pt"
ULTRALYTICS_CONFIG_DIR = BASE_DIR / ".ultralytics"
ULTRALYTICS_CONFIG_DIR.mkdir(exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(ULTRALYTICS_CONFIG_DIR))

from ultralytics import YOLO

MODEL = YOLO(str(MODEL_PATH))
FALLBACK_NAMES = {
    0: "broken_glass",
    1: "dent",
    2: "paint_damage",
    3: "missing_part",
    4: "scratch",
    5: "deformation",
}
CLASS_COLORS = {
    "broken_glass": (0, 169, 255),
    "dent": (255, 134, 13),
    "paint_damage": (42, 201, 94),
    "missing_part": (59, 89, 255),
    "scratch": (191, 86, 255),
    "deformation": (0, 80, 220),
}


def detect_damage_and_annotate(image: np.ndarray, confidence: float = 0.25) -> dict:
    annotated = image.copy()
    height, width = image.shape[:2]
    damage_mask = np.zeros((height, width), dtype=np.uint8)

    results = MODEL.predict(image, imgsz=768, conf=confidence, verbose=False)
    detections = []

    if results and results[0].boxes is not None:
        boxes = results[0].boxes
        xyxy = boxes.xyxy.cpu().numpy()
        scores = boxes.conf.cpu().numpy()
        classes = boxes.cls.cpu().numpy().astype(int)
        names = getattr(MODEL, "names", None) or FALLBACK_NAMES

        for index, box in enumerate(xyxy):
            x1, y1, x2, y2 = _clip_box(box, width, height)
            if x2 <= x1 or y2 <= y1:
                continue

            class_id = int(classes[index])
            label = str(names.get(class_id, FALLBACK_NAMES.get(class_id, "damage")))
            score = float(scores[index])
            area_pixels = int((x2 - x1) * (y2 - y1))
            area_ratio = area_pixels / float(width * height)

            damage_mask[y1:y2, x1:x2] = 255
            detections.append(
                {
                    "id": len(detections) + 1,
                    "class_id": class_id,
                    "damage_type": label,
                    "confidence": round(score, 4),
                    "bbox": [x1, y1, x2, y2],
                    "area_ratio": round(area_ratio, 5),
                }
            )

            _draw_detection(annotated, (x1, y1, x2, y2), label, score)

    damage_pixels = int(np.sum(damage_mask == 255))
    total_pixels = int(height * width)
    damage_ratio = damage_pixels / total_pixels if total_pixels else 0.0

    return {
        "annotated_image": annotated,
        "damage_detected": len(detections) > 0,
        "num_damages": len(detections),
        "damage_types": sorted({d["damage_type"] for d in detections}),
        "damage_area_ratio": round(damage_ratio, 5),
        "detections": detections,
        "model": {
            "name": "RT-DETR-L",
            "weights": str(MODEL_PATH),
            "input_size": 768,
            "confidence_threshold": confidence,
            "classes": list((getattr(MODEL, "names", None) or FALLBACK_NAMES).values()),
        },
    }


def _clip_box(box: np.ndarray, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box.tolist()
    return (
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(0, min(width, int(round(x2)))),
        max(0, min(height, int(round(y2)))),
    )


def _draw_detection(image: np.ndarray, box: tuple[int, int, int, int], label: str, score: float) -> None:
    x1, y1, x2, y2 = box
    color = CLASS_COLORS.get(label, (0, 0, 255))
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
    text = f"{label.replace('_', ' ')} {score * 100:.0f}%"
    (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.62, 2)
    label_y = max(y1, text_height + 12)
    cv2.rectangle(
        image,
        (x1, label_y - text_height - 10),
        (min(x1 + text_width + 12, image.shape[1] - 1), label_y + baseline - 4),
        color,
        -1,
    )
    cv2.putText(
        image,
        text,
        (x1 + 6, label_y - 7),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

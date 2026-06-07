from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class PreprocessingReport:
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    brightness: float
    contrast: float
    blur_score: float
    noise_score: float
    steps: list[str]

    def as_dict(self) -> dict:
        return {
            "original_size": {"width": self.original_width, "height": self.original_height},
            "processed_size": {"width": self.processed_width, "height": self.processed_height},
            "brightness": round(self.brightness, 2),
            "contrast": round(self.contrast, 2),
            "blur_score": round(self.blur_score, 2),
            "noise_score": round(self.noise_score, 2),
            "steps": self.steps,
        }


def preprocess_for_damage_detection(image: np.ndarray) -> tuple[np.ndarray, PreprocessingReport]:
    """Prepare real-world claim photos before RT-DETR inference."""
    if image is None or image.size == 0:
        raise ValueError("Image is empty or unreadable.")

    original_height, original_width = image.shape[:2]
    if original_width < 320 or original_height < 240:
        raise ValueError("Image resolution is too low. Upload at least 320x240 pixels.")

    processed = _ensure_bgr_uint8(image)
    steps = ["decoded image as BGR uint8"]

    processed, resized = _resize_long_edge(processed, max_edge=1920)
    if resized:
        steps.append("resized long edge to 1920px for stable memory use")

    processed = _gray_world_white_balance(processed)
    steps.append("applied gray-world white balance")

    brightness, contrast = _luma_stats(processed)
    if brightness < 85:
        processed = _gamma_correct(processed, gamma=0.75)
        steps.append("brightened low-light image with gamma correction")
    elif brightness > 190:
        processed = _gamma_correct(processed, gamma=1.25)
        steps.append("reduced overexposure with gamma correction")

    brightness, contrast = _luma_stats(processed)
    if contrast < 45:
        processed = _apply_clahe_on_luma(processed)
        steps.append("enhanced local contrast using CLAHE")

    noise_score = _noise_score(processed)
    if noise_score > 9:
        processed = cv2.fastNlMeansDenoisingColored(processed, None, 4, 4, 7, 21)
        steps.append("reduced sensor/compression noise")

    blur_score = _blur_score(processed)
    if blur_score < 95:
        processed = _unsharp_mask(processed)
        steps.append("applied mild sharpening for soft or motion-blurred image")

    processed_height, processed_width = processed.shape[:2]
    final_brightness, final_contrast = _luma_stats(processed)
    report = PreprocessingReport(
        original_width=original_width,
        original_height=original_height,
        processed_width=processed_width,
        processed_height=processed_height,
        brightness=final_brightness,
        contrast=final_contrast,
        blur_score=_blur_score(processed),
        noise_score=_noise_score(processed),
        steps=steps,
    )
    return processed, report


def _ensure_bgr_uint8(image: np.ndarray) -> np.ndarray:
    if image.dtype != np.uint8:
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    if len(image.shape) == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image.copy()


def _resize_long_edge(image: np.ndarray, max_edge: int) -> tuple[np.ndarray, bool]:
    height, width = image.shape[:2]
    scale = max_edge / max(height, width)
    if scale >= 1:
        return image, False
    new_size = (int(width * scale), int(height * scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA), True


def _gray_world_white_balance(image: np.ndarray) -> np.ndarray:
    image_float = image.astype(np.float32)
    channel_means = image_float.reshape(-1, 3).mean(axis=0)
    gray_mean = channel_means.mean()
    scale = gray_mean / np.maximum(channel_means, 1.0)
    balanced = np.clip(image_float * scale, 0, 255)
    return balanced.astype(np.uint8)


def _luma_stats(image: np.ndarray) -> tuple[float, float]:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    luma = lab[:, :, 0]
    return float(luma.mean()), float(luma.std())


def _gamma_correct(image: np.ndarray, gamma: float) -> np.ndarray:
    inv_gamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(image, table)


def _apply_clahe_on_luma(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    luma, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_luma = clahe.apply(luma)
    enhanced = cv2.merge((enhanced_luma, a_channel, b_channel))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def _blur_score(image: np.ndarray) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _noise_score(image: np.ndarray) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    median = cv2.medianBlur(gray, 3)
    return float(np.mean(np.abs(gray.astype(np.float32) - median.astype(np.float32))))


def _unsharp_mask(image: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(image, (0, 0), 1.2)
    return cv2.addWeighted(image, 1.35, blurred, -0.35, 0)

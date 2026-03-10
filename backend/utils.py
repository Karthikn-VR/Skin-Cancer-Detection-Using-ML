from __future__ import annotations

import base64
import io
from typing import Tuple

import numpy as np
from PIL import Image


def load_pil_image(file_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    return img


def pil_to_base64_png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def np_uint8_hwc_to_pil(arr: np.ndarray) -> Image.Image:
    if arr.dtype != np.uint8:
        raise ValueError("Expected uint8 array")
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("Expected HxWx3 array")
    return Image.fromarray(arr, mode="RGB")


def clamp01(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0.0, 1.0)


def softmax_np(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)


def topk(probs: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    idx = np.argsort(-probs)[:k]
    return idx, probs[idx]


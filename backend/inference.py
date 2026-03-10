from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from model_loader import ModelArtifacts


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


@dataclass
class Prediction:
    pred_idx: int
    pred_label: str
    confidence: float
    probabilities: Dict[str, float]
    method: str


def build_preprocess(input_size: int) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def pil_to_tensor(img: Image.Image, preprocess: transforms.Compose, device: torch.device) -> torch.Tensor:
    t = preprocess(img).unsqueeze(0).to(device)
    return t


@torch.inference_mode()
def predict(art: ModelArtifacts, img: Image.Image) -> Prediction:
    preprocess = build_preprocess(art.input_size)
    x = pil_to_tensor(img, preprocess, art.device)

    logits = art.model(x)
    probs_t = torch.softmax(logits, dim=1)[0]
    probs = probs_t.detach().cpu().numpy().astype(np.float64)

    method = "cnn"
    if art.knn is not None:
        try:
            # Extract embedding by running backbone+embed.
            feats = art.model.backbone(x)
            feats = torch.flatten(feats, 1)
            emb = art.model.embed(feats).detach().cpu().numpy()
            if hasattr(art.knn, "predict_proba"):
                probs_knn = art.knn.predict_proba(emb)[0].astype(np.float64)
                if probs_knn.shape[0] == probs.shape[0]:
                    probs = probs_knn
                    method = "knn"
        except Exception:
            method = "cnn"

    pred_idx = int(np.argmax(probs))
    confidence = float(probs[pred_idx])
    pred_label = art.idx_to_label[pred_idx]

    probabilities = {art.idx_to_label[i]: float(probs[i]) for i in range(len(probs))}

    return Prediction(
        pred_idx=pred_idx,
        pred_label=pred_label,
        confidence=confidence,
        probabilities=probabilities,
        method=method,
    )


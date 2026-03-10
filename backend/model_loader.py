from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torchvision.models as tvm
import torch.nn.functional as F


class DeepVisionNet(nn.Module):
    """
    ResNet50 backbone -> embedding head -> classifier head.

    Checkpoint keys observed:
    - backbone.*  (Sequential of resnet children excluding fc)
    - embed.0 / embed.2  (Linear -> ReLU -> Linear)
    - classifier.* (Linear to num_classes)
    """

    def __init__(self, embedding_dim: int = 128, num_classes: int = 7):
        super().__init__()
        resnet = tvm.resnet50(weights=None)
        # conv1, bn1, relu, maxpool, layer1..layer4, avgpool
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        self.embed = nn.Sequential(
            nn.Linear(2048, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, embedding_dim),
        )
        self.classifier = nn.Linear(embedding_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feats = self.backbone(x)  # [B, 2048, 1, 1]
        feats = torch.flatten(feats, 1)  # [B, 2048]
        emb = self.embed(feats)  # [B, embedding_dim]
        logits = self.classifier(emb)  # [B, num_classes]
        return logits


class SkinCNN(nn.Module):
    def __init__(self, num_classes: int = 7):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = F.relu(self.conv3(x))
        x = self.gap(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


@dataclass(frozen=True)
class ModelArtifacts:
    model: DeepVisionNet
    device: torch.device
    idx_to_label: List[str]
    label_to_idx: Dict[str, int]
    knn: Optional[object]
    target_layer: nn.Module
    input_size: int
    gradcam_model: Optional[nn.Module] = None
    gradcam_target_layer: Optional[nn.Module] = None
    cam_class_names: Optional[List[str]] = None


def load_artifacts(workingmodel_dir: str | Path) -> ModelArtifacts:
    d = Path(workingmodel_dir)
    if not d.exists():
        raise FileNotFoundError(f"Model directory not found: {d}")

    cfg_path = next(iter(d.glob("*_config.json")), None) or (d / "DeepVisionFinal_config.json")
    primary_ckpt = d / "deepvision.pth"
    if not primary_ckpt.exists():
        primary_ckpt = d / "DeepVisionFinal.pth"
    if not primary_ckpt.exists():
        candidates = [p for p in d.glob("*.pth") if p.name.lower() not in {"vision.pth", "modelg.pth"}]
        primary_ckpt = candidates[0] if candidates else d / "DeepVisionFinal.pth"
    knn_path = next(iter(d.glob("*_knn.pkl")), None) or (d / "DeepVisionFinal_knn.pkl")

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    label_to_idx: Dict[str, int] = cfg["label_map"]
    idx_to_label = [None] * (max(label_to_idx.values()) + 1)
    for lab, idx in label_to_idx.items():
        idx_to_label[idx] = lab

    embedding_dim = int(cfg.get("embedding_dim", 128))
    num_classes = len(idx_to_label)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DeepVisionNet(embedding_dim=embedding_dim, num_classes=num_classes)
    sd = torch.load(str(primary_ckpt), map_location="cpu")
    model.load_state_dict(sd, strict=True)
    model.eval().to(device)

    knn = None
    if knn_path.exists():
        try:
            import joblib

            knn = joblib.load(str(knn_path))
        except Exception:
            knn = None

    # Target layer for main model (DeepVisionNet)
    # DeepVisionNet.backbone is resnet50 without fc, target layer is usually last conv in layer4
    # resnet50 children: conv1, bn1, relu, maxpool, layer1, layer2, layer3, layer4, avgpool
    # backbone is nn.Sequential of these except avgpool. layer4 is index 7.
    target_layer = model.backbone[7][-1].conv3

    # Grad-CAM ResNet50 model from Resnet.pth
    gradcam_model: Optional[nn.Module] = None
    gradcam_target_layer: Optional[nn.Module] = None
    resnet_pth_path = d / "Resnet.pth"
    print("Searching for Resnet.pth...")
    if not resnet_pth_path.exists():
        print("ERROR: Resnet.pth NOT FOUND")
    else:
        print("model.pth located")
        try:
            checkpoint = torch.load(str(resnet_pth_path), map_location="cpu")
            print("checkpoint loaded")
            
            # Extract state_dict
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
            elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint
            print("state_dict extracted")

            # Detect classifier dimensions automatically from fc.1 and fc.4
            fc1_weight = state_dict["fc.1.weight"]
            fc2_weight = state_dict["fc.4.weight"]
            
            in_features = fc1_weight.shape[1]
            hidden_features = fc1_weight.shape[0]
            num_classes = fc2_weight.shape[0]
            
            print("Detected classifier structure:")
            print(f"{in_features} {hidden_features} {num_classes}")

            # Build exact Sequential architecture matching checkpoint indices
            res = tvm.resnet50(weights=None)
            res.fc = nn.Sequential(
                nn.Identity(),                  # index 0
                nn.Linear(in_features, hidden_features), # index 1
                nn.ReLU(),                      # index 2
                nn.Dropout(0.5),                # index 3
                nn.Linear(hidden_features, num_classes) # index 4
            )
            print("model architecture created")

            res.load_state_dict(state_dict, strict=True)
            print("Grad-CAM model loaded successfully")
            
            res.eval().to(device)
            gradcam_model = res
            # Target layer: last block of layer4
            gradcam_target_layer = res.layer4[-1]
            print("model ready")
        except Exception as e:
            print(f"Grad-CAM load error: {e}")
            gradcam_model = None
            gradcam_target_layer = None

    # ResNet-like default; if you have a known size in config later, wire it here.
    input_size = int(cfg.get("input_size", 224))

    return ModelArtifacts(
        model=model,
        device=device,
        idx_to_label=idx_to_label,
        label_to_idx=label_to_idx,
        knn=knn,
        target_layer=target_layer,
        input_size=input_size,
        gradcam_model=gradcam_model,
        gradcam_target_layer=gradcam_target_layer,
        cam_class_names=None, # Not needed for 3-class Resnet.pth
    )

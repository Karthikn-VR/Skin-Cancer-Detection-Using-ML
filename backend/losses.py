from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Multi-class focal loss.

    This is training-time only (not used for inference), but included so the project
    contains the full loss set referenced by the model.
    """

    def __init__(self, gamma: float = 2.0, alpha: float | None = None, reduction: str = "mean"):
        super().__init__()
        self.gamma = float(gamma)
        self.alpha = float(alpha) if alpha is not None else None
        if reduction not in {"none", "mean", "sum"}:
            raise ValueError("reduction must be one of: none, mean, sum")
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # logits: [B, C], targets: [B] (class indices)
        log_probs = F.log_softmax(logits, dim=1)
        probs = log_probs.exp()

        targets = targets.long()
        pt = probs.gather(1, targets.unsqueeze(1)).squeeze(1)  # [B]
        log_pt = log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)  # [B]

        focal = (1.0 - pt).clamp(min=0).pow(self.gamma) * (-log_pt)
        if self.alpha is not None:
            focal = focal * self.alpha

        if self.reduction == "mean":
            return focal.mean()
        if self.reduction == "sum":
            return focal.sum()
        return focal


from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
import traceback

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import torch
try:
    import tensorflow as tf  # type: ignore
except Exception:
    tf = None

from gradcam import GradCAM
from inference import predict
from model_loader import ModelArtifacts, load_artifacts, SkinCNN
from utils import load_pil_image, np_uint8_hwc_to_pil, pil_to_base64_png
from torchvision import transforms
import tensorflow as _tf_internal


APP_TITLE = "AI Skin Cancer Detection API"


def _env_model_dir() -> Path:
    # Prefer user's requested `workingmodel`, but also support existing `WorkingModels`.
    cwd = Path(__file__).resolve().parent.parent
    candidates = [
        Path(os.getenv("WORKINGMODEL_DIR", "")) if os.getenv("WORKINGMODEL_DIR") else None,
        Path("/app/WorkingModels"),
        cwd / "workingmodel",
        cwd / "WorkingModels",
        cwd / "WorkingModels" / "workingmodel",
    ]
    for c in candidates:
        if c and c.exists():
            return c
    # fallback to repo root/WorkingModels (most likely here)
    return cwd / "WorkingModels"


app = FastAPI(title=APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    model_dir = _env_model_dir()
    art = load_artifacts(model_dir)
    app.state.artifacts = art
    try:
        if art.gradcam_model is not None:
            print(f"CAM model: Resnet.pth loaded ({type(art.gradcam_model).__name__})")
        else:
            print("CAM model: not loaded; using DeepVision for CAM")
    except Exception:
        print("CAM model: status unknown; defaulting to DeepVision for CAM")


@app.get("/health")
def health() -> Dict[str, Any]:
    art: ModelArtifacts = app.state.artifacts
    return {
        "status": "ok",
        "device": str(art.device),
        "classes": art.idx_to_label,
        "input_size": art.input_size,
        "losses": [
            "Relational Learning Loss",
            "Lesion-Aware Learning Loss",
            "Attention Drift Regularization Loss",
            "Focal Loss",
        ],
    }


@app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Please upload an image file.")

        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty upload.")

        try:
            pil = load_pil_image(data)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode image.")

        art: ModelArtifacts = app.state.artifacts
        pred = predict(art, pil)

        # Original image for processing and display
        orig_rgb = np.array(pil.convert("RGB"), dtype=np.uint8)
        image_height, image_width = orig_rgb.shape[:2]

        # --- 1️⃣ GradCAM Model (Resnet.pth) ---
        model_for_cam = getattr(art, "gradcam_model", None)
        layer_for_cam = getattr(art, "gradcam_target_layer", None)
        heatmap_b64 = None
        cam_pred_index: int | None = None

        if model_for_cam is not None and layer_for_cam is not None:
            try:
                # Resnet.pth GradCAM logic with ImageNet normalization as per requirement
                x_cam = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ])(pil).unsqueeze(0).to(art.device)
                
                # Custom GradCAM function for Resnet.pth
                gradients = []
                activations = []

                def forward_hook(module, input, output):
                    activations.append(output)

                def backward_hook(module, grad_in, grad_out):
                    gradients.append(grad_out[0])

                h1 = layer_for_cam.register_forward_hook(forward_hook)
                h2 = layer_for_cam.register_backward_hook(backward_hook)

                try:
                    output = model_for_cam(x_cam)
                    pred_class = output.argmax()
                    cam_pred_index = int(pred_class)
                    
                    probs_cam = torch.softmax(output, dim=1)
                    conf_cam = float(probs_cam[0, pred_class].item())
                    num_labels = len(art.idx_to_label)
                    label_name = art.idx_to_label[int(pred_class)] if int(pred_class) < num_labels else "unknown"
                    
                    print("=====================================")
                    print("MODEL.PTH ACTIVATED")
                    print(f"Prediction Index: {int(pred_class)}")
                    print(f"Label: {label_name}")
                    print(f"Confidence: {conf_cam:.4f}")
                    print("=====================================")

                    model_for_cam.zero_grad()
                    output[0, pred_class].backward()

                    grad = gradients[0]
                    act = activations[0]

                    weights = grad.mean(dim=(2, 3), keepdim=True)
                    cam_val = (weights * act).sum(dim=1).squeeze()
                    cam_val = torch.nn.functional.relu(cam_val)
                    cam_val = cam_val.cpu().detach().numpy()

                    cam_val = cv2.resize(cam_val, (image_width, image_height))
                    cam_val = (cam_val - cam_val.min()) / (cam_val.max() - cam_val.min() + 1e-8)

                    heatmap = cv2.applyColorMap(np.uint8(255 * cam_val), cv2.COLORMAP_JET)
                    heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
                    heatmap_b64 = pil_to_base64_png(np_uint8_hwc_to_pil(heatmap_rgb))
                    print("GradCAM generated")
                finally:
                    h1.remove()
                    h2.remove()
            except Exception as e:
                print(f"GradCAM generation error: {e}")

        return {
            "prediction": pred.pred_label,
            "confidence": pred.confidence,
            "probabilities": pred.probabilities,
            "method": pred.method,
            "original_image": pil_to_base64_png(pil),
            "gradcam_heatmap": heatmap_b64,
            "cam_pred_index": cam_pred_index,
        }
    except HTTPException:
        raise
    except Exception as e:
        print("Prediction error:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

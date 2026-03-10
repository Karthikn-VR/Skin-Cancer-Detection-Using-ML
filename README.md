# AI Skin Cancer Detection System

End‑to‑end project with:
- FastAPI backend for classification and Grad‑CAM
- Next.js frontend for upload and visualization

The system predicts a skin‑lesion class, shows probabilities, and renders a Grad‑CAM overlay. Optionally, a Keras segmentation model can mask Grad‑CAM to ignore background.

## Project Structure

- backend/ — FastAPI service
  - main.py — API (/health, /predict)
  - inference.py — preprocessing and prediction
  - model_loader.py — loads models and label map
  - gradcam.py — Grad‑CAM generation
  - requirements.txt — Python deps
- app/ — Next.js app (pages, API proxy)
  - app/api/predict/route.ts — proxies to FastAPI /predict
  - app/page.tsx — main UI
  - components/** — UI components
- WorkingModels/ — model files (see below)

## Models

Place files under WorkingModels/ (or set WORKINGMODEL_DIR):
- deepvision.pth or DeepVisionFinal.pth — classifier (DeepVisionNet: ResNet‑50 backbone → embed → classifier)
- vision.pth — Grad‑CAM visualization model (SkinCNN: conv1 32 → conv2 64 → conv3 128 → GAP → fc 128→7)
- stable_skin_lesion_unet.keras — optional segmentation for masking Grad‑CAM only
- DeepVisionFinal_config.json — includes label_map and embedding_dim
- Optional: DeepVisionFinal_knn.pkl — if present, KNN over embeddings can provide probabilities

Notes:
- Prediction always uses deepvision.pth (DeepVisionNet).
- Grad‑CAM uses vision.pth (SkinCNN) when present; otherwise it falls back to the classifier model.
- Segmentation (.keras) is used only to gate Grad‑CAM; classification is unchanged.

## Backend

### Setup
```bash
python -m pip install --user -r backend/requirements.txt
```

### Run
From repository root:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Or from backend directory:
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Endpoints
- GET /health — device, classes, input size
- POST /predict — accepts multipart/form‑data field file; returns:
```json
{
  "prediction": "bcc",
  "confidence": 0.97,
  "probabilities": { "bcc": 0.97, "mel": 0.02, "...": 0.01 },
  "method": "cnn",
  "gradcam": {
    "heatmap_base64_png": "<base64>",
    "overlay_base64_png": "<base64>"
  }
}
```

## Frontend (Next.js)

### Setup
```bash
npm install
```

### Development
```bash
npm run dev
```
Open http://localhost:3000

### Backend URL
The Next route app/api/predict/route.ts proxies to FastAPI:
```bash
set BACKEND_URL=http://127.0.0.1:8000
```

## How Grad‑CAM Works Here
- For SkinCNN (vision.pth), the uploaded full‑resolution image is converted to a tensor without cropping and fed through conv3.
- Gradients are backpropagated from the predicted class to conv3; channel‑wise weighted activations form the CAM.
- The CAM is resized to the original image size, thresholded for clarity, colored (Turbo/Jet), and alpha‑blended with the original image.
- If a Keras segmentation mask is available, it gates the CAM so background is suppressed.

## Tips
- Place model files correctly in WorkingModels/ before starting the backend.
- If you see a state_dict mismatch, ensure vision.pth matches SkinCNN (32→64→128, fc 128→7) and deepvision.pth matches DeepVisionNet.

## License
Research/educational use only; not for clinical diagnosis.

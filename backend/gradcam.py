from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class GradCamResult:
    heatmap_color_uint8: np.ndarray  # HxWx3 RGB
    overlay_uint8: np.ndarray        # HxWx3 RGB
    raw_cam: np.ndarray              # HxW normalized [0,1]


class ImprovedGradCAM:
    def __init__(
        self, 
        model: nn.Module, 
        target_layers: List[nn.Module],  # Support multiple layers
        use_cuda: bool = False
    ):
        """
        Improved GradCAM with support for multiple target layers and better gradient handling.
        
        Args:
            model: The neural network model
            target_layers: List of target layers (can be single layer)
            use_cuda: Whether to use CUDA if available
        """
        self.model = model
        self.target_layers = target_layers if isinstance(target_layers, list) else [target_layers]
        self.device = torch.device("cuda" if use_cuda and torch.cuda.is_available() else "cpu")
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        self.activations_list = []
        self.grads_list = []
        self._handles = []
        
        # Register hooks for each target layer
        for target_layer in self.target_layers:
            activations = []
            grads = []
            
            def make_forward_hook(activations):
                def forward_hook(module, input, output):
                    activations.append(output.detach())
                return forward_hook
            
            def make_backward_hook(grads):
                def backward_hook(module, grad_input, grad_output):
                    grads.append(grad_output[0].detach())
                return backward_hook
            
            self._handles.append(
                target_layer.register_forward_hook(make_forward_hook(activations))
            )
            self._handles.append(
                target_layer.register_full_backward_hook(make_backward_hook(grads))
            )
            
            self.activations_list.append(activations)
            self.grads_list.append(grads)
    
    def close(self):
        """Remove all hooks"""
        for h in self._handles:
            h.remove()
        self._handles = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    @torch.enable_grad()
    def _compute_cam_per_layer(
        self,
        input_tensor: torch.Tensor,
        class_idx: Optional[int] = None,
        eigen_smooth: bool = True
    ) -> List[np.ndarray]:
        """
        Compute CAM for each target layer.
        
        Args:
            input_tensor: Input image tensor
            class_idx: Target class index (if None, use predicted class)
            eigen_smooth: Apply eigenvalue-based smoothing
        
        Returns:
            List of CAM arrays for each layer
        """
        # Clear previous activations and gradients
        for acts, grads in zip(self.activations_list, self.grads_list):
            acts.clear()
            grads.clear()
        
        # Ensure input requires grad
        input_tensor = input_tensor.to(self.device).requires_grad_(True)
        
        # Forward pass
        self.model.zero_grad()
        outputs = self.model(input_tensor)
        
        # Get target class
        if class_idx is None:
            class_idx = outputs.argmax(dim=1).item()
        
        # Create one-hot target
        one_hot = torch.zeros_like(outputs)
        one_hot[:, class_idx] = 1.0
        
        # Backward pass with one-hot vector
        outputs.backward(gradient=one_hot, retain_graph=True)
        
        cam_per_layer = []
        
        for activations, grads in zip(self.activations_list, self.grads_list):
            if not activations or not grads:
                raise RuntimeError("Failed to capture activations or gradients")
            
            activation = activations[0]
            gradient = grads[0]
            
            # Compute weights using global average pooling
            weights = gradient.mean(dim=(2, 3), keepdim=True)
            
            # Alternative: Use gradient^2 for better importance weighting
            # weights = (gradient.pow(2)).mean(dim=(2, 3), keepdim=True)
            
            # Weight the channels
            weighted_activations = weights * activation
            
            # Sum over channels
            cam = weighted_activations.sum(dim=1, keepdim=False)
            
            # Apply ReLU to focus on positive influence
            cam = F.relu(cam)
            
            # Convert to numpy
            cam_np = cam.squeeze().cpu().numpy()
            
            # Optional: Apply eigenvalue smoothing for cleaner visualization
            if eigen_smooth and cam_np.size > 0:
                cam_np = self._eigen_smooth(cam_np)
            
            cam_per_layer.append(cam_np)
        
        return cam_per_layer
    
    @staticmethod
    def _eigen_smooth(cam: np.ndarray, top_k: int = 3) -> np.ndarray:
        """
        Smooth CAM using top-k eigenvalues for cleaner visualization.
        """
        if cam.size == 0:
            return cam
        
        # Flatten and compute covariance
        h, w = cam.shape
        cam_flat = cam.reshape(-1, 1)
        
        # Simple smoothing using SVD
        U, s, Vt = np.linalg.svd(cam_flat, full_matrices=False)
        
        # Keep only top component
        s_filtered = np.zeros_like(s)
        s_filtered[0] = s[0]  # Keep primary component
        
        # Reconstruct
        cam_smooth = U @ np.diag(s_filtered) @ Vt
        cam_smooth = cam_smooth.reshape(h, w)
        
        return np.abs(cam_smooth)
    
    def __call__(
        self,
        input_tensor: torch.Tensor,
        class_idx: Optional[int] = None,
        orig_rgb_uint8: np.ndarray = None,
        heatmap_weight: float = 0.4,
        colormap: int = cv2.COLORMAP_JET,
        use_rgb: bool = True,
        eigen_smooth: bool = True,
        aug_smooth: bool = True,
        aug_samples: int = 8
    ) -> GradCamResult:
        """
        Generate GradCAM visualization.
        
        Args:
            input_tensor: Input image tensor (BxCxHxW)
            class_idx: Target class (None for predicted class)
            orig_rgb_uint8: Original RGB image as uint8 numpy array
            heatmap_weight: Weight for overlay (0=image only, 1=heatmap only)
            colormap: OpenCV colormap to use
            use_rgb: Whether input is RGB (True) or BGR (False)
            eigen_smooth: Apply eigenvalue smoothing
            aug_smooth: Use augmentation smoothing for more stable CAMs
            aug_samples: Number of augmentation samples
        
        Returns:
            GradCamResult with heatmap and overlay
        """
        # Validate input image
        orig_rgb_uint8 = ensure_rgb_uint8(orig_rgb_uint8)
        h_orig, w_orig = orig_rgb_uint8.shape[:2]
        
        if aug_smooth:
            # Generate CAM with augmentation for stability
            cam = self._augmented_cam(
                input_tensor, 
                class_idx, 
                eigen_smooth,
                aug_samples
            )
        else:
            # Standard CAM computation
            cam_per_layer = self._compute_cam_per_layer(
                input_tensor, 
                class_idx,
                eigen_smooth
            )
            
            # Aggregate CAMs from multiple layers
            if len(cam_per_layer) > 1:
                # Average multiple layers
                cam_shapes = [c.shape for c in cam_per_layer]
                target_shape = cam_shapes[0]
                
                cam_resized = []
                for c in cam_per_layer:
                    if c.shape != target_shape:
                        c = cv2.resize(c, (target_shape[1], target_shape[0]))
                    cam_resized.append(c)
                
                cam = np.mean(cam_resized, axis=0)
            else:
                cam = cam_per_layer[0]
        
        # Resize CAM to original image size
        cam = cv2.resize(cam, (w_orig, h_orig), interpolation=cv2.INTER_CUBIC)
        
        # Normalize CAM
        cam = self._normalize_cam(cam)
        
        # Apply post-processing
        cam = self._postprocess_cam(cam)
        
        # Create heatmap
        heatmap_uint8 = np.uint8(255 * cam)
        heatmap_bgr = cv2.applyColorMap(heatmap_uint8, colormap)
        
        # Create overlay
        if use_rgb:
            orig_bgr = cv2.cvtColor(orig_rgb_uint8, cv2.COLOR_RGB2BGR)
        else:
            orig_bgr = orig_rgb_uint8.copy()
        
        # Weighted combination
        overlay_bgr = cv2.addWeighted(
            heatmap_bgr,
            heatmap_weight,
            orig_bgr,
            1.0 - heatmap_weight,
            0
        )
        
        # Convert back to RGB if needed
        if use_rgb:
            heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)
            overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
        else:
            heatmap_rgb = heatmap_bgr
            overlay_rgb = overlay_bgr
        
        return GradCamResult(
            heatmap_color_uint8=heatmap_rgb,
            overlay_uint8=overlay_rgb,
            raw_cam=cam
        )
    
    def _augmented_cam(
        self,
        input_tensor: torch.Tensor,
        class_idx: Optional[int],
        eigen_smooth: bool,
        aug_samples: int = 8
    ) -> np.ndarray:
        """
        Generate more stable CAM using augmentation.
        """
        cams = []
        
        for i in range(aug_samples):
            # Apply random augmentation
            aug_tensor = input_tensor.clone()
            
            if i > 0:  # Keep first sample as original
                # Random small rotation
                angle = np.random.uniform(-5, 5)
                aug_tensor = self._rotate_tensor(aug_tensor, angle)
                
                # Random small scale
                scale = np.random.uniform(0.95, 1.05)
                aug_tensor = F.interpolate(
                    aug_tensor,
                    scale_factor=scale,
                    mode='bilinear',
                    align_corners=False
                )
                
                # Crop back to original size if needed
                if aug_tensor.shape[-2:] != input_tensor.shape[-2:]:
                    aug_tensor = F.interpolate(
                        aug_tensor,
                        size=input_tensor.shape[-2:],
                        mode='bilinear',
                        align_corners=False
                    )
            
            cam_per_layer = self._compute_cam_per_layer(
                aug_tensor,
                class_idx,
                eigen_smooth
            )
            
            # Use first layer CAM
            cams.append(cam_per_layer[0])
        
        # Average all CAMs
        # Resize all to same shape first
        target_shape = cams[0].shape
        cams_resized = []
        for c in cams:
            if c.shape != target_shape:
                c = cv2.resize(c, (target_shape[1], target_shape[0]))
            cams_resized.append(c)
        
        return np.mean(cams_resized, axis=0)
    
    @staticmethod
    def _rotate_tensor(tensor: torch.Tensor, angle: float) -> torch.Tensor:
        """Rotate tensor by angle degrees."""
        theta = np.radians(angle)
        rot_mat = torch.tensor([
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0]
        ], dtype=tensor.dtype, device=tensor.device).unsqueeze(0)
        
        grid = F.affine_grid(rot_mat, tensor.size(), align_corners=False)
        return F.grid_sample(tensor, grid, align_corners=False)
    
    @staticmethod
    def _normalize_cam(cam: np.ndarray) -> np.ndarray:
        """Normalize CAM to [0, 1] range."""
        cam_min = cam.min()
        cam_max = cam.max()
        
        if cam_max - cam_min > 0:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)
        
        return cam
    
    @staticmethod
    def _postprocess_cam(cam: np.ndarray, gamma: float = 2.0) -> np.ndarray:
        """
        Post-process CAM for better visualization.
        
        Args:
            cam: Normalized CAM [0, 1]
            gamma: Gamma correction factor (>1 increases contrast)
        """
        # Apply gamma correction for better contrast
        cam = np.power(cam, gamma)
        
        # Apply bilateral filter for edge-preserving smoothing
        cam_uint8 = np.uint8(255 * cam)
        cam_uint8 = cv2.bilateralFilter(cam_uint8, 9, 75, 75)
        cam = cam_uint8.astype(np.float32) / 255.0
        
        # Optional: Apply morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cam_uint8 = np.uint8(255 * cam)
        cam_uint8 = cv2.morphologyEx(cam_uint8, cv2.MORPH_CLOSE, kernel)
        cam = cam_uint8.astype(np.float32) / 255.0
        
        return cam


def ensure_rgb_uint8(img: np.ndarray) -> np.ndarray:
    """Validate image format."""
    if img.dtype != np.uint8:
        if img.dtype == np.float32 or img.dtype == np.float64:
            img = np.uint8(img * 255)
        else:
            raise ValueError(f"Unsupported image dtype: {img.dtype}")
    
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"Image must be HxWx3, got shape {img.shape}")
    
    return img


# Example usage function
def apply_gradcam(
    model: nn.Module,
    target_layers: List[nn.Module],
    input_tensor: torch.Tensor,
    orig_image: np.ndarray,
    class_idx: Optional[int] = None,
    use_cuda: bool = True
) -> GradCamResult:
    """
    Convenience function to apply GradCAM.
    
    Args:
        model: Your trained model
        target_layers: List of layers to visualize (e.g., [model.layer4[-1]])
        input_tensor: Preprocessed input tensor
        orig_image: Original image as RGB uint8 numpy array
        class_idx: Target class index (None for predicted class)
        use_cuda: Use GPU if available
    
    Returns:
        GradCamResult with visualizations
    """
    with ImprovedGradCAM(model, target_layers, use_cuda=use_cuda) as gradcam:
        result = gradcam(
            input_tensor,
            class_idx=class_idx,
            orig_rgb_uint8=orig_image,
            heatmap_weight=0.5,
            colormap=cv2.COLORMAP_JET,
            eigen_smooth=True,
            aug_smooth=True,
            aug_samples=4
        )
    
    return result


class GradCAM:
    """
    Simple Grad-CAM implementation used by the FastAPI backend.

    This follows the standard research pipeline you described:
    - ReLU on CAM
    - Normalize to [0, 1]
    - Resize to input image size
    - Optional Gaussian blur
    - JET colormap
    - Overlay: image * 0.4 + heatmap * 0.6
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self._activations: Optional[torch.Tensor] = None
        self._grads: Optional[torch.Tensor] = None
        self._handles: list = []

        def fwd_hook(_m, _inp, out):
            self._activations = out.detach()

        def bwd_hook(_m, grad_in, grad_out):
            self._grads = grad_out[0].detach()

        self._handles.append(self.target_layer.register_forward_hook(fwd_hook))
        try:
            self._handles.append(
                self.target_layer.register_full_backward_hook(bwd_hook)
            )
        except Exception:
            self._handles.append(
                self.target_layer.register_backward_hook(bwd_hook)
            )

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []

    @torch.inference_mode(False)
    def __call__(
        self,
        input_tensor: torch.Tensor,
        class_idx: int,
        orig_rgb_uint8: np.ndarray,
    ) -> GradCamResult:
        orig_rgb_uint8 = ensure_rgb_uint8(orig_rgb_uint8)
        self.model.zero_grad(set_to_none=True)
        logits = self.model(input_tensor)
        score = logits[:, class_idx].sum()
        score.backward()

        if self._activations is None or self._grads is None:
            raise RuntimeError("GradCAM hooks did not capture activations/gradients")

        acts = self._activations  # [B, C, H, W]
        grads = self._grads       # [B, C, H, W]

        weights = grads.mean(dim=(2, 3), keepdim=True)  # [B, C, 1, 1]

        cam = (weights * acts).sum(dim=1)               # [B, H, W]

        cam = torch.relu(cam)

        cam_np = cam[0].detach().cpu().numpy()

        cam_np = np.maximum(cam_np, 0)

        vmin = np.percentile(cam_np, 5.0)
        vmax = np.percentile(cam_np, 99.5)
        cam_np = (cam_np - vmin) / (max(vmax - vmin, 1e-8))
        cam_np = np.clip(cam_np, 0.0, 1.0)

        h0, w0 = orig_rgb_uint8.shape[:2]

        cam_resized = cv2.resize(
            cam_np,
            (w0, h0),
            interpolation=cv2.INTER_CUBIC,
        )

        cam_resized = cv2.GaussianBlur(cam_resized, (5, 5), 0)
        tau = 0.25
        cam_thresh = cam_resized.copy()
        cam_thresh[cam_thresh < tau] = 0.0
        mmax = cam_thresh.max()
        if mmax > 0:
            cam_thresh = cam_thresh / mmax

        colormap = getattr(cv2, "COLORMAP_TURBO", cv2.COLORMAP_JET)
        heatmap_bgr = cv2.applyColorMap(
            np.uint8(255 * cam_thresh),
            colormap,
        )

        orig_uint8 = ensure_rgb_uint8(orig_rgb_uint8)
        orig_bgr = cv2.cvtColor(orig_uint8, cv2.COLOR_RGB2BGR)

        alpha = (0.2 + 0.5 * cam_thresh).clip(0.0, 0.7).astype(np.float32)
        alpha3 = np.repeat(alpha[:, :, None], 3, axis=2)
        overlay_bgr = (orig_bgr.astype(np.float32) * (1.0 - alpha3) + heatmap_bgr.astype(np.float32) * alpha3).clip(0, 255).astype(np.uint8)

        heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)
        overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)

        return GradCamResult(
            heatmap_color_uint8=heatmap_rgb,
            overlay_uint8=overlay_rgb,
            raw_cam=cam_thresh,
        )

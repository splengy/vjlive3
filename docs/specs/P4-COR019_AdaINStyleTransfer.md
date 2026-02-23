# P4-COR019: AdaINStyleTransfer (adain)

## Description

`AdaINStyleTransfer` (from `VJlive-2/core/models/style_transfer/adain.py`) is a PyTorch-based neural network module that performs fast, arbitrary style transfer. It uses Adaptive Instance Normalization (AdaIN) to align the mean and variance of the content image feature map with those of a style embedding, enabling real-time neural restyling of the VJLive canvas.

## Public Interface Requirements

```python
from vjlive3.plugins.base import EffectNode
import torch
import torch.nn as nn
from typing import Optional

class AdaINStyleTransfer(EffectNode):
    """
    Real-time neural style transfer effect using Adaptive Instance Normalization.
    """
    METADATA = {
        "id": "AdaINStyleTransfer",
        "type": "ai_compute",
        "version": "1.0.0",
        "legacy_ref": "adain (AdaINStyleTransfer)"
    }

    def __init__(self, model_path: Optional[str] = None):
        super().__init__()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
    def process(self, content_tensor: torch.Tensor, style_embedding: torch.Tensor, alpha: float = 1.0) -> torch.Tensor:
        """Applies the AdaIN interpolation and decodes the stylized tensor."""
        pass
```

## Implementation Notes

- **Model Weights:** The legacy `adain.py` implemented the architecture (Encoder/MLP/Decoder) but didn't package weights natively. VJLive3 must handle checking `models/` for the `.pt` weights and gracefully falling back (or disabling) if the weights are omitted to keep the core install small.
- **GPU Synchronization:** PyTorch `tensors` must be zero-copy shared with the main OpenGL `FramebufferManager` via CUDA/OpenGL interop or `CudaGraphicsResource` mapping. Standard CPU `numpy` downloading is too slow for 60FPS.

## Test Plan

- **Pytest:** Initialize the model. Pass a dummy `content_tensor` (B,3,H,W) and a dummy `style_embedding`. Assert the output tensor shape matches the input and gradients are not stored/tracked (`torch.no_grad()`).
- Coverage must exceed 80%.

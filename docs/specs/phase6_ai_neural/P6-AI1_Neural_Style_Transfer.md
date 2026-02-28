# Spec: P6-AI1 — Neural Style Transfer (ML Effects)

**File naming:** `docs/specs/phase6_ai_neural/P6-AI1_Neural_Style_Transfer.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-AI1 — Neural Style Transfer

**Phase:** Phase 6 / P6-AI1
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Neural Style Transfer applies artistic styles from reference images to live video in real-time using machine learning. It uses a pre-trained neural network to separate and recombine content and style features, enabling live visual performance with painterly, abstract, or stylized effects.

---

## What It Does NOT Do

- Does not train neural networks (uses pre-trained models)
- Does not handle model training or fine-tuning
- Does not provide style library management
- Does not include advanced neural architecture customization

---

## Public Interface

```python
class NeuralStyleTransfer:
    def __init__(self, model_path: str, device: str = "cuda") -> None: ...
    
    def load_model(self) -> bool: ...
    def set_style_image(self, image: np.ndarray) -> None: ...
    def set_style_image_path(self, path: str) -> bool: ...
    
    def set_content_weight(self, weight: float) -> None: ...
    def set_style_weight(self, weight: float) -> None: ...
    
    def process(self, frame: np.ndarray, style_strength: float = 1.0) -> np.ndarray: ...
    
    def get_available_styles(self) -> List[str]: ...
    def load_style_preset(self, name: str) -> bool: ...
    
    def save_style_preset(self, name: str, image: np.ndarray) -> bool: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `model_path` | `str` | Path to pre-trained model | Valid file |
| `device` | `str` | Compute device | 'cuda' or 'cpu' |
| `image` | `np.ndarray` | Style reference image | HxWx3, uint8 |
| `path` | `str` | File path | Valid path |
| `weight` | `float` | Content/style weight | > 0 |
| `frame` | `np.ndarray` | Input video frame | HxWx3, uint8 |
| `style_strength` | `float` | Blend factor | 0.0 to 1.0 |
| `name` | `str` | Style preset name | Non-empty |

**Output:** `np.ndarray` — Stylized video frame

---

## Edge Cases and Error Handling

- What happens if model fails to load? → Raise error, log details
- What happens if style image is invalid? → Use default style, log warning
- What happens if CUDA not available? → Fallback to CPU, log warning
- What happens if frame is too large? → Resize to model input size
- What happens on cleanup? → Release model from GPU memory

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `torch` (PyTorch) — required for neural inference — fallback: raise ImportError
  - `torchvision` — for image preprocessing — fallback: raise ImportError
  - `opencv-python` — for image handling — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_model_loading` | Loads pre-trained model correctly |
| `test_style_image_setting` | Sets style images correctly |
| `test_content_style_weights` | Weight parameters affect output |
| `test_frame_processing` | Processes frames with style transfer |
| `test_style_presets` | Saves and loads style presets |
| `test_cuda_fallback` | Falls back to CPU if CUDA unavailable |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-AI1: Neural style transfer` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on VJlive-2 neural style transfer module.*
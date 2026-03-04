# P7-VE65: Slit Scan Effect

> **Task ID:** `P7-VE65`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/slit_scan.py`)
> **Class:** `SlitScanEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Slit-scan temporal visualization: a vertical or horizontal slice of the frame is
sampled over time and drawn to create a "time ribbon" with ghosting effect. Used
in VJLive for abstract temporal visualizations and performance art.

## Technical Requirements
- Manifest-registered `Effect` with temporal line buffer (stateful).
- Parameters: `scan_line`, `scan_mode`, `scan_speed`, `buffer_time`, `opacity`.
- GPU line buffer accumulation; CPU fallback with NumPy row/column slicing.
- Maintain 60 FPS; bounded buffer size based on frame history.
- ≥80 % test coverage; explicit buffer lifecycle.
- Spec <750 lines.

## Public Interface
```python
class SlitScanEffect(Effect):
    """Slit-scan temporal visualization."""
    def __init__(self, width=1920, height=1080, history=300):
        super().__init__("SlitScan", SLITSCAN_VERT, SLITSCAN_FRAG)
        self.effect_category = "temporal"
        self.effect_tags = ["slit", "temporal", "history"]
        self.parameters = {'scan_line': 5, 'scan_mode': 0, 'scan_speed': 5,
                          'buffer_time': 8, 'opacity': 10}
        self._state = {'history_buffer': None, 'write_idx': 0}
        self.history_frames = history

    def render(self, tex_in, **kwargs):
        # Draw horizontal/vertical slit to history buffer
        pass
```

### Parameter Remaps
- `scan_line` → y = int(map_linear(x, 0, 10, 0, height))
- `scan_mode` → m = int(x / 5) % 2  (0=horizontal, 1=vertical)
- `scan_speed` → speed = map_linear(x, 0, 10, 0.5, 4)
- `buffer_time` → frames = int(map_linear(x, 0, 10, 10, history))
- `opacity` → α = x / 10

## Shader Logic
```glsl
if(scan_mode == 0) {
    // horizontal slit at scan_line
    vec3 slit = texture(tex_in, vec2(uv.x, scan_line/height)).rgb;
} else {
    // vertical slit at scan_line
    vec3 slit = texture(tex_in, vec2(scan_line/width, uv.y)).rgb;
}
// Write to history buffer at current write_idx
vec3 history_sample = texture(history_buffer, ...);
output = mix(history_sample, slit, 0.1);
```

## CPU Fallback
```python
def slitscan_cpu(frame, scan_line, mode, history_buf, write_idx):
    h, w = frame.shape[:2]
    scan_y = int(scan_line)
    if mode == 0:  # horizontal
        slit = frame[scan_y, :, :]
    else:  # vertical
        slit = frame[:, int(scan_line), :]
    history_buf[write_idx % len(history_buf)] = slit
    # Composite history
    result = np.zeros_like(frame)
    for i in range(len(history_buf)):
        alpha = (history_frames - abs(i - write_idx)) / history_frames
        result += history_buf[i] * alpha
    return np.clip(result, 0, 255).astype(np.uint8)
```

## Presets
- `Horizontal Scan`: scan_mode=0, scan_speed=1
- `Vertical Scan`: scan_mode=1, scan_speed=1
- `Fast Ribbon`: scan_speed=3, buffer_time=5

## Edge Cases
- scan_line clamped to [0, height/width)
- Buffer wrapping handled via modulo indexing
- Undersampling at high speeds may produce artifacts

## Test Plan
- `test_slit_extraction`
- `test_history_buffer_wrapping`
- `test_scan_modes`
- `test_buffer_memory_bounded`

## Verification Checklist
- [ ] Slit line is correctly sampled
- [ ] History accumulates over time
- [ ] Buffer wraps without losing early data

---

**Note:** Stateful temporal buffer; reset on sequence boundaries.



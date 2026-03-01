# P3-INFRA-CIRCBUF: Circular Buffer (Ring Buffer) System

## Specification Status
- **Phase**: Pass 1 (Skeleton)
- **Target Phase**: Pass 2 (Detailed Technical Spec)
- **Priority**: P0
- **Module**: `core.buffers` infrastructure
- **Implementation Path**: `src/vjlive3/core/buffers/circular_buffer.py`
- **Class Type**: Data Structure / Real-Time Buffer

## Executive Summary

CircularBuffer is a fixed-size ring buffer implementation optimized for real-time audio, video, and sensor data streaming. It provides lock-free enqueue/dequeue operations (single producer/consumer) and memory-efficient storage for continuous data streams, enabling low-latency effect chains without dynamic memory allocation.

## Problem Statement

Real-time effects require buffering continuous streams:
- Audio frames (44.1 kHz, 16-bit stereo = 176 KB/sec)
- Video frames (1080p 60 FPS RGBA = ~500 MB/sec)
- Depth data (1080p 60 FPS 16-bit = ~250 MB/sec)

Traditional lists/arrays cause:
- Memory fragmentation (malloc/free on every frame)
- GC pauses (Python garbage collection)
- Unpredictable latency (memory allocation timing)

A pre-allocated circular buffer with fixed memory footprint provides:
- Zero allocation per operation (O(1) guaranteed)
- Predictable latency (<1ms)
- Cache-friendly memory layout
- No garbage collection triggers

## Solution Overview

CircularBuffer provides:
1. **Pre-allocated storage**: Fixed memory footprint determined at creation
2. **Enqueue operation**: O(1) append to write position
3. **Dequeue operation**: O(1) read from read position
4. **Wraparound handling**: Automatic index wrapping at buffer boundary
5. **Full/empty detection**: Constant-time state queries
6. **Peek operations**: Non-destructive reads (leave data in buffer)
7. **Batch operations**: Multi-element enqueue/dequeue

## Detailed Behavior

### Phase 1: Initialization
Allocate fixed-size buffer with read/write position tracking

### Phase 2: Enqueue
Append element(s) at write position, advance pointer (handle wraparound)

### Phase 3: Dequeue
Read element(s) at read position, advance pointer (handle wraparound)

### Phase 4: State Management
Track fill level and available space

### Phase 5: Boundary Handling
Detect full/empty and wrap positions automatically

### Phase 6: Query Support
Peek and status operations without side effects

## Public Interface

```python
from typing import TypeVar, Generic, Optional, List, Iterator
import numpy as np

T = TypeVar('T')

class CircularBuffer(Generic[T]):
    """Fixed-size circular ring buffer for real-time streaming."""
    
    def __init__(self, capacity: int, dtype=None):
        """
        Initialize circular buffer.
        Args:
            capacity: Maximum number of elements to store
            dtype: NumPy dtype for efficient array storage (optional)
        """
    
    def enqueue(self, item: T) -> None:
        """
        Add single item to buffer.
        Raises IndexError if buffer is full.
        """
    
    def enqueue_batch(self, items: List[T]) -> int:
        """
        Add multiple items. Returns number successfully enqueued.
        Partial enqueue possible if insufficient space.
        """
    
    def dequeue(self) -> T:
        """
        Remove and return oldest item.
        Raises IndexError if buffer is empty.
        """
    
    def dequeue_batch(self, count: int) -> List[T]:
        """
        Remove and return up to count items.
        Returns shorter list if insufficient items.
        """
    
    def peek(self, offset: int = 0) -> T:
        """
        Read item without removing. offset=0 is oldest, offset=-1 is newest.
        """
    
    def peek_batch(self, count: int, offset: int = 0) -> List[T]:
        """
        Non-destructive read of multiple items.
        """
    
    def clear(self) -> None:
        """Reset buffer to empty state."""
    
    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
    
    def is_empty(self) -> bool:
        """Check if buffer contains no elements."""
    
    def size(self) -> int:
        """Number of elements currently in buffer."""
    
    def capacity(self) -> int:
        """Maximum capacity of buffer."""
    
    def available_space(self) -> int:
        """Number of free slots remaining."""
    
    def fill_ratio(self) -> float:
        """Ratio of used to total capacity [0, 1]."""
    
    def __len__(self) -> int:
        """Return current size (for len() builtin)."""
    
    def __iter__(self) -> Iterator[T]:
        """Iterate over buffer contents without modifying."""
    
    def __getitem__(self, index: int) -> T:
        """Random access via index (0=oldest, -1=newest)."""
    
    # NumPy integration (for audio/video)
    def as_numpy(self) -> np.ndarray:
        """Return buffer as NumPy array (copy if non-contiguous)."""
    
    @staticmethod
    def from_numpy(arr: np.ndarray) -> 'CircularBuffer':
        """Create buffer from NumPy array."""
```

## Mathematical Formulations

### Wraparound Index Calculation
$$\text{pos}_{\text{next}} = (\text{pos}_{\text{current}} + 1) \mod \text{capacity}$$

### Fill Level
$$\text{fill} = (\text{write\_pos} - \text{read\_pos}) \mod \text{capacity}$$

### Available Space
$$\text{space} = \text{capacity} - \text{fill}$$

### Peek Offset (Circular Indexing)
$$\text{actual\_index} = (\text{read\_pos} + \text{offset}) \mod \text{capacity}$$

## Performance Characteristics

- **Enqueue**: O(1) single element
- **Enqueue batch**: O(n) for n elements (but no allocation)
- **Dequeue**: O(1) single element
- **Peek**: O(1) no side effects
- **Memory**: Fixed allocation, zero fragmentation
- **Latency**: <1µs per operation (deterministic)
- **Cache hit**: High (linear memory access)

## Test Plan

1. **Basic Operations**
   - Enqueue/dequeue cycle correct
   - Values retrieved in FIFO order
   - Size tracking accurate

2. **Boundary Conditions**
   - Correct behavior at full capacity
   - Correct behavior when empty
   - Wraparound logic correct

3. **Peek Operations**
   - Peek returns correct value
   - Peek doesn't modify state
   - Offset indexing correct

4. **Batch Operations**
   - Batch enqueue works for multiple items
   - Batch dequeue returns correct count
   - Partial batches handled correctly

5. **State Queries**
   - `is_full()` correct
   - `is_empty()` correct
   - `fill_ratio()` accurate
   - `available_space()` correct

6. **Edge Cases**
   - Single element capacity works
   - Large capacity works efficiently
   - Wraparound at boundary
   - Multiple full/empty cycles

7. **Iterator and Indexing**
   - `__iter__()` visits all elements
   - `__getitem__()` indexing correct
   - Negative indices work

8. **Performance**
   - Deterministic latency (<1µs)
   - No memory allocation per operation
   - Cache hit rate high

## Definition of Done

- [ ] Buffer pre-allocation working
- [ ] Enqueue operation O(1)
- [ ] Dequeue operation O(1)
- [ ] Wraparound logic correct
- [ ] Full/empty detection accurate
- [ ] Peek non-destructive
- [ ] Batch operations working
- [ ] Size tracking accurate
- [ ] Iterator implemented
- [ ] NumPy integration working
- [ ] 20+ test cases passing
- [ ] Performance <1µs per operation
- [ ] No memory leaks
- [ ] Complete docstrings
- [ ] Type hints throughout
- [ ] Edge cases handled
- [ ] ≤900 lines of code

## Dependencies

- `typing` module (standard library)
- NumPy (optional, for array support)

## Related Specs

- P3-AUDIO-BUFFER: Audio-specific buffer wrapper
- P3-VIDEO-BUFFER: Video frame buffer
- P3-DEPTH-BUFFER: Depth frame buffer
- P3-EFFECT-CHAIN: Consumer of buffered data

---

**Notes for Pass 2 Implementation:**
- Decide: Generic Python impl vs NumPy backing (recommend NumPy for performance)
- Confirm single producer/consumer or thread-safe multi-producer design
- Define dtype handling for mixed types vs NumPy arrays only
- Document memory usage formulas (e.g., 1000-element int32 buffer = 4KB)

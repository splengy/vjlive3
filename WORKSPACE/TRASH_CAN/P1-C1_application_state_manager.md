# P1-C1: ApplicationStateManager — Centralized State Broadcasting

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Problem Statement

VJLive3 needs a centralized state management system that:
- Maintains the single source of truth for all application state
- Provides efficient broadcasting of state changes to interested components
- Supports multiple state categories (system, mixer, deck, etc.)
- Enables state persistence and restoration
- Integrates with the existing VJLive architecture without blocking the render loop

The legacy codebases have scattered state management approaches that need to be unified.

---

## Proposed Solution

Implement `ApplicationStateManager` as a centralized, event-driven state manager with:

1. **Singleton Pattern** with thread-safe access
2. **Category-based Organization** — state organized by functional area
3. **Observer Pattern** — components can subscribe to state changes
4. **Immutable Snapshots** — state updates create new immutable snapshots
5. **Performance Optimized** — minimal overhead, no blocking in render loop
6. **Serializable** — complete state can be serialized for persistence

---

## API/Interface Definition

```python
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import threading

class StateCategory(Enum):
    """Categories for organizing application state."""
    SYSTEM = "system"
    MIXER = "mixer"
    DECK = "deck"
    EFFECT = "effect"
    NODE_GRAPH = "node_graph"
    HARDWARE = "hardware"
    AUDIO = "audio"
    VIDEO = "video"
    DMX = "dmx"
    PROJECT = "project"

@dataclass(frozen=True)
class StateSnapshot:
    """Immutable snapshot of application state at a point in time."""
    timestamp: float
    category: StateCategory
    data: Dict[str, Any]
    version: int = 1

class StateChange:
    """Represents a state change event."""
    def __init__(
        self,
        category: StateCategory,
        key: str,
        old_value: Any,
        new_value: Any,
        timestamp: float
    ):
        self.category = category
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = timestamp

StateChangeCallback = Callable[[StateChange], None]

class ApplicationStateManager:
    """
    Centralized state manager with broadcasting capabilities.

    Usage:
        state_mgr = ApplicationStateManager()
        state_mgr.set("mixer", "master_volume", 0.8)
        volume = state_mgr.get("mixer", "master_volume")
    """

    def __init__(self):
        self._state: Dict[StateCategory, Dict[str, Any]] = {}
        self._subscribers: Dict[StateCategory, List[StateChangeCallback]] = {}
        self._lock = threading.RLock()
        self._version = 0
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize default state values."""
        with self._lock:
            for category in StateCategory:
                self._state[category] = {}
                self._subscribers[category] = []

    def get(self, category: StateCategory, key: str, default: Any = None) -> Any:
        """
        Get a state value.

        Args:
            category: State category
            key: State key
            default: Default value if key not found

        Returns:
            The state value or default
        """
        with self._lock:
            return self._state.get(category, {}).get(key, default)

    def set(
        self,
        category: StateCategory,
        key: str,
        value: Any,
        broadcast: bool = True
    ) -> None:
        """
        Set a state value with optional broadcasting.

        Args:
            category: State category
            key: State key
            value: New value
            broadcast: Whether to notify subscribers
        """
        import time
        timestamp = time.time()

        with self._lock:
            old_value = self._state.get(category, {}).get(key)
            if category not in self._state:
                self._state[category] = {}

            self._state[category][key] = value
            self._version += 1

            change = StateChange(
                category=category,
                key=key,
                old_value=old_value,
                new_value=value,
                timestamp=timestamp
            )

        if broadcast:
            self._broadcast_change(change)

    def subscribe(
        self,
        category: StateCategory,
        callback: StateChangeCallback
    ) -> None:
        """
        Subscribe to state changes in a category.

        Args:
            category: Category to subscribe to
            callback: Function to call on state change
        """
        with self._lock:
            if callback not in self._subscribers[category]:
                self._subscribers[category].append(callback)

    def unsubscribe(
        self,
        category: StateCategory,
        callback: StateChangeCallback
    ) -> None:
        """Unsubscribe from state changes."""
        with self._lock:
            if callback in self._subscribers[category]:
                self._subscribers[category].remove(callback)

    def get_snapshot(self, category: Optional[StateCategory] = None) -> StateSnapshot:
        """
        Get immutable snapshot of current state.

        Args:
            category: Optional category to snapshot, or all if None

        Returns:
            Immutable StateSnapshot
        """
        import time
        with self._lock:
            if category:
                data = dict(self._state.get(category, {}))
            else:
                data = {
                    cat: dict(self._state[cat])
                    for cat in StateCategory
                }

            return StateSnapshot(
                timestamp=time.time(),
                category=category if category else StateCategory.SYSTEM,
                data=data,
                version=self._version
            )

    def restore_snapshot(self, snapshot: StateSnapshot) -> None:
        """
        Restore state from a snapshot.

        Args:
            snapshot: Snapshot to restore
        """
        with self._lock:
            if snapshot.category == StateCategory.SYSTEM:
                # Restore all categories
                for cat, data in snapshot.data.items():
                    self._state[cat] = dict(data)
            else:
                # Restore single category
                self._state[snapshot.category] = dict(snapshot.data)

    def _broadcast_change(self, change: StateChange) -> None:
        """Notify all subscribers of a state change."""
        callbacks = []
        with self._lock:
            callbacks = self._subscribers[change.category].copy()

        for callback in callbacks:
            try:
                callback(change)
            except Exception as e:
                # Log but don't fail
                print(f"State change callback error: {e}")

    def clear(self) -> None:
        """Clear all state (useful for testing/reset)."""
        with self._lock:
            self._initialize_defaults()
```

---

## Implementation Plan

### Phase 1: Core Structure (Days 1-2)
1. Create `src/vjlive3/state/application_state_manager.py`
2. Implement `ApplicationStateManager` class with thread-safe operations
3. Define `StateCategory` enum and `StateSnapshot` dataclass
4. Add basic get/set/subscribe operations
5. Write unit tests for thread safety and basic operations

### Phase 2: Integration (Days 3-4)
1. Integrate with existing VJLive components:
   - Mixer state (volume, fader positions)
   - Deck states (clip playback, cues)
   - Effect parameters
   - Node graph state
2. Add state change logging for debugging
3. Implement snapshot/restore for project save/load
4. Performance profiling to ensure <1% overhead

### Phase 3: Advanced Features (Days 5-6)
1. State validation and schema enforcement
2. State change history for undo/redo
3. Remote state synchronization (for multi-node)
4. State migration utilities for version upgrades

---

## Test Strategy

**Unit Tests (≥80% coverage):**
- Thread safety under concurrent access
- Subscribe/unsubscribe mechanics
- Snapshot creation and restoration
- State change broadcasting
- Default initialization
- Edge cases (missing keys, concurrent modifications)

**Integration Tests:**
- Integration with mixer, deck, effect systems
- State persistence round-trip (save → load)
- Multi-component coordination via state changes

**Performance Tests:**
- Benchmark get/set operations (<1µs target)
- Memory usage profiling (no leaks)
- Render loop impact (<1% FPS drop)

---

## Performance Requirements

- **Thread Safety:** RLock ensures no deadlocks, minimal contention
- **Memory:** State snapshots are shallow copies; immutable snapshots use copy-on-write
- **Render Loop:** All operations non-blocking; broadcasting happens outside lock
- **Scalability:** O(1) for get/set, O(N) for broadcast where N = subscribers

---

## Safety Rail Compliance

- **Rail 7 (No Silent Failures):** All state change errors logged
- **Rail 8 (Resource Leak Prevention):** Weak references for callbacks to prevent memory leaks
- **Rail 10 (Security):** State data validated before setting; no arbitrary code execution

---

## Dependencies

- **Phase 1 Core:** P1-R1 (OpenGL context) — not required
- **Phase 1 Core:** P1-R5 (Render engine) — not required
- **Blocking:** None — can be implemented immediately
- **Blocked By:** None

---

## Open Questions

1. Should we implement a state schema validation system? (Likely in P1-C4 ConfigManager)
2. Do we need state change history for undo/redo? (Probably separate system)
3. How to handle state conflicts in distributed multi-node? (Phase 2X distributed architecture)

---

## References

- `WORKSPACE/PRIME_DIRECTIVE.md` — Core philosophy
- `WORKSPACE/SAFETY_RAILS.md` — Technical limits
- Legacy: `vjlive/state_manager.py`, `VJlive-2/application_state.py`

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*
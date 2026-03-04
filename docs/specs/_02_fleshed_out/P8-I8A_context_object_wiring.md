# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P8-I8A_context_object_wiring.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I8A — Context Object Wiring

**What This Module Does**

Establishes a comprehensive context object system for VJLive3 that provides centralized state management, dependency injection, and inter-component communication. This module creates a React-like context architecture that allows components to access shared state (audio, video, performance metrics, configuration) without prop drilling, while maintaining type safety and performance.

---

## Architecture Decisions

- **Pattern:** Context + Provider + Hook
- **Rationale:** Modern applications require shared state across many components. A context system eliminates prop drilling, provides type safety, and enables efficient re-renders through selective subscription.
- **Constraints:**
  - Must support both Python (backend) and JavaScript (frontend) implementations
  - Must be thread-safe for multi-threaded audio processing
  - Must provide performance monitoring and debugging tools
  - Must support hot-reloading for development
  - Must integrate with existing plugin system

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `web_ui/src/contexts/MixerContext.jsx` | `MixerContext` | Port — React context pattern |
| VJlive-2 | `core/timeline/ai_suggestion_engine.py` | Feedback tracking | Port — state management |
| VJlive-2 | `plugins/vcore/living_fractal_consciousness.py` | User acceptance learning | Port — state persistence |
| VJlive-1 | `core/context_manager.py` | `ContextManager` | Port — context system |
| VJlive-1 | `core/state_provider.py` | `StateProvider` | Port — state provider |

---

## Public Interface

```python
# Python Context System
class VJLiveContext:
    def __init__(self, config: ContextConfig) -> None:...
    def create_provider(self, name: str, initial_state: dict) -> ContextProvider:...
    def get_context(self, name: str) -> ContextProvider:...
    def subscribe(self, name: str, callback: Callable) -> None:...
    def unsubscribe(self, name: str, callback: Callable) -> None:...
    def update_state(self, name: str, updates: dict) -> None:...
    def get_state(self, name: str) -> dict:...
    def debug_info(self) -> dict:...
    def cleanup(self) -> None:...

# JavaScript Context System
class VJLiveContextJS:
    constructor(config: ContextConfig) -> None:...
    createProvider(name: string, initialState: object) -> ContextProvider:...
    getContext(name: string) -> ContextProvider:...
    subscribe(name: string, callback: Function) -> void:...
    unsubscribe(name: string, callback: Function) -> void:...
    updateState(name: string, updates: object) -> void:...
    getState(name: string) -> object:...
    debugInfo() -> object:...
    cleanup() -> void:...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `ContextConfig` | Context system configuration | Must include all required parameters |
| `name` | `str` | Context provider name | Must be unique across system |
| `initial_state` | `dict` | Initial state for provider | Must be serializable |
| `updates` | `dict` | State updates to apply | Must be valid JSON |
| **Output** | `ContextProvider` | Context provider instance | Must implement provider interface |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `json` — serialization — fallback: use pickle (Python only)
  - `threading` — thread safety — fallback: single-threaded mode
  - `asyncio` — async operations — fallback: sync mode
  - `logging` — debugging — fallback: print statements
- Internal modules this depends on:
  - `vjlive3.core.audio_manager` — audio state
  - `vjlive3.core.video_manager` — video state
  - `vjlive3.plugins.manager` — plugin state
  - `vjlive3.ui.main_window` — UI state
  - `vjlive3.performance_monitor` — performance metrics

---

## Error Cases

| Error Condition | Exception / Response | Recovery |
|-----------------|---------------------|----------|
| Duplicate provider name | `ValueError("Provider already exists")` | Use unique name |
| Invalid state update | `TypeError("Invalid state type")` | Validate state before update |
| Thread safety violation | `RuntimeError("Thread safety violation")` | Use proper synchronization |
| Context not found | `KeyError("Context not found")` | Check context existence |
| Serialization error | `SerializationError("State not serializable")` | Use JSON-serializable data |
| Memory leak | `MemoryError("Context memory leak")` | Cleanup unused contexts |

---

## Configuration Schema

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `max_providers` | `int` | `100` | `1 - 1000` | Maximum context providers |
| `max_state_size` | `int` | `1000000` | `1000 - 10000000` | Max state size in bytes |
| `thread_safe` | `bool` | `True` | — | Enable thread safety |
| `async_support` | `bool` | `True` | — | Enable async operations |
| `debug_mode` | `bool` | `False` | — | Enable debug logging |
| `hot_reload` | `bool` | `True` | — | Enable hot reloading |
| `performance_monitoring` | `bool` | `True` | — | Enable performance monitoring |

---

## State Management

- **Per-context state:** (cleared when context destroyed)
  - Current state values
  - Subscriber list
  - Update history
- **Persistent state:** (survives across sessions)
  - Context definitions
  - Provider configurations
  - Performance metrics
- **Initialization state:** (set once at startup)
  - Context registry
  - Thread synchronization primitives
  - Performance monitoring setup
- **Cleanup required:** Yes — remove subscribers, clear state, stop monitoring

---

## GPU Resources

This module is **CPU-only** and does not use GPU resources.

**Memory Budget:**
- Context registry: ~10-50 MB
- State storage: ~100-500 MB (varies by state size)
- Subscriber management: ~10-100 MB
- Performance monitoring: ~10-50 MB
- Total: ~200-700 MB (light)

---

## Context Providers

### Core Contexts
1. **AudioContext** — Audio state (levels, FFT, beat detection)
2. **VideoContext** — Video state (camera feeds, resolution, FPS)
3. **PerformanceContext** — Performance metrics (CPU, memory, FPS)
4. **ConfigContext** — System configuration (settings, preferences)
5. **PluginContext** — Plugin state (loaded plugins, parameters)

### UI Contexts
1. **UIContext** — UI state (active windows, layouts, focus)
2. **ThemeContext** — Theme and styling information
3. **NotificationContext** — Notification system state

### Advanced Contexts
1. **NetworkContext** — Network state (latency, connectivity)
2. **HardwareContext** — Hardware state (GPU, CPU, memory)
3. **UserContext** — User state (preferences, history, profiles)

---

## Hook System

### Python Hooks
```python
# Use context in components
@context_hook("AudioContext")
def use_audio():
    return get_context("AudioContext").state

# Subscribe to context changes
@context_hook("PerformanceContext")
def use_performance():
    return get_context("PerformanceContext").state
```

### JavaScript Hooks
```javascript
// Use context in React components
const useAudio = () => {
    return useContext(AudioContext);
}

const usePerformance = () => {
    return useContext(PerformanceContext);
}
```

---

## Performance Considerations

- **Selective Subscription:** Components only re-render when relevant state changes
- **State Diffing:** Only send changed state to subscribers
- **Memory Management:** Automatic cleanup of unused contexts
- **Thread Safety:** Proper synchronization for multi-threaded access
- **Async Support:** Non-blocking state updates

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent |
| `test_context_creation` | Contexts can be created and retrieved |
| `test_state_updates` | State updates propagate to subscribers |
| `test_thread_safety` | Thread-safe operations work correctly |
| `test_performance` | Context operations meet performance requirements |
| `test_serialization` | State can be serialized/deserialized |
| `test_cleanup` | Cleanup removes all resources |
| `test_hot_reload` | Hot reloading works without data loss |
| `test_debug_info` | Debug information is accurate |
| `test_error_handling` | Error cases handled gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I8A: Context Object Wiring` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### web_ui/src/contexts/MixerContext.jsx (L1-20) [VJlive-2 (Original)]
```javascript
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useMixerSync } from '../services/useMixerSync';
import { useMixerLayout } from '../components/Mixer/hooks/useMixerLayout';
import { useMixerParameterSync } from '../services/useMixerParameterSync';

const MixerContext = createContext();

export const MixerProvider = ({ children, socket }) => {
  const [zones, setZones] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'full_state') {
        if (data.mixer && data.mixer.zones) {
          setZones(data.mixer.zones);
        }
      }
      // Handle incremental updates if any
    };

    socket.addEventListener('message', handleMessage);
    setIsConnected(true);

    return () => {
      socket.removeEventListener('message', handleMessage);
      setIsConnected(false);
    };
  }, [socket]);

  const sendCommand = useCallback((cmd, data) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'command',
        command: cmd,
        data: data
      }));
    }
  }, [socket]);

  return (
    <MixerContext.Provider value={{
      state: { mixer: { zones } },
      zones,
      isConnected,
      sendCommand,
      socket // Export the socket instance
    }}>
      {children}
    </MixerContext.Provider>
  );
};

export const useMixer = () => {
  const context = useContext(MixerContext);
  if (!context) {
    throw new Error('useMixer must be used within a MixerProvider');
  }
  return context;
};
```

This shows the React Context pattern with Provider, useContext hook, and state management.

### core/timeline/ai_suggestion_engine.py (L577-596) [VJlive-2 (Original)]
```python
        stype = suggestion.type.value
        self._type_acceptance.setdefault(stype, []).append(accepted)
        # Keep only last 50 entries per type
        if len(self._type_acceptance[stype]) > 50:
            self._type_acceptance[stype] = self._type_acceptance[stype][-50:]

        # Track per-user acceptance
        self._user_acceptance.setdefault(user_id, []).append(accepted)
        if len(self._user_acceptance[user_id]) > 50:
            self._user_acceptance[user_id] = self._user_acceptance[user_id][-50:]

        # Adjust suggestion cooldown based on overall acceptance rate
        all_recent = [fb['accepted'] for fb in self._feedback_history[-100:]]
        if len(all_recent) >= 10:
            acceptance_rate = sum(all_recent) / len(all_recent)
            # High acceptance → faster suggestions; low → slow down
            self.suggestion_cooldown = max(1.0, min(10.0, 2.0 / max(acceptance_rate, 0.1)))

        logger.info("AI suggestion feedback: %s - %s (accepted: %s, user: %s)",
                     suggestion.type.value, suggestion.reason, accepted, user_id)
```

This demonstrates state tracking and feedback collection patterns that can be adapted for context state management.

### plugins/vcore/living_fractal_consciousness.py (L497-516) [VJlive (Original)]
```python
                    # Suggest a nudge in a direction that increases complexity
                    direction = 1.0 if current < 5.0 else -1.0
                    suggestion[param] = current + direction * 0.5
                    suggestion[param] = max(0.0, min(10.0, suggestion[param]))
        
        # Learn from user acceptance (simplified)
        if suggestion and random.random() < self.learning_rate:
            self.suggestion_history.append({
                'suggestion': suggestion,
                'timestamp': time.time(),
                'accepted': None  # Would be set by UI
            })
        
        return suggestion
```

This shows a pattern for learning from user acceptance, which could inform context state persistence and learning.

---

## Notes for Implementers

1. **Core Concept**: Context objects provide centralized state management and dependency injection, eliminating prop drilling and enabling efficient component communication.

2. **React Pattern**: Use the React Context pattern as a model — Provider components wrap the app, useContext hooks access state, and selective subscription ensures performance.

3. **Python Implementation**: Create a Python context system that mirrors the React pattern but is thread-safe and suitable for audio processing.

4. **State Management**: Use immutable state updates and selective subscription to ensure efficient re-renders.

5. **Performance**: Implement state diffing and selective subscription to minimize unnecessary updates.

6. **Thread Safety**: Use proper synchronization primitives for multi-threaded audio processing.

7. **Hot Reloading**: Support hot reloading for development without losing state.

8. **Debugging**: Provide comprehensive debugging tools and performance monitoring.

9. **Integration**: Integrate with existing plugin system and audio/video managers.

10. **Testing**: Test with realistic scenarios including concurrent access and state updates.

---

## Implementation Tips

1. **Python Implementation**:
   ```python
   import threading
   from typing import Dict, Any, Callable, Optional
   from dataclasses import dataclass
   
   @dataclass
   class ContextState:
       value: Any
       subscribers: list
       version: int
   
   class VJLiveContext:
       def __init__(self):
           self._lock = threading.RLock()
           self._contexts: Dict[str, ContextState] = {}
           self._subscribers: Dict[str, list] = {}
       
       def create_provider(self, name: str, initial_state: dict):
           with self._lock:
               if name in self._contexts:
                   raise ValueError(f"Context '{name}' already exists")
               
               state = ContextState(
                   value=initial_state,
                   subscribers=[],
                   version=0
               )
               self._contexts[name] = state
               return ContextProvider(self, name, state)
       
       def subscribe(self, name: str, callback: Callable):
           with self._lock:
               if name not in self._contexts:
                   raise KeyError(f"Context '{name}' not found")
               
               self._subscribers.setdefault(name, []).append(callback)
       
       def update_state(self, name: str, updates: dict):
           with self._lock:
               if name not in self._contexts:
                   raise KeyError(f"Context '{name}' not found")
               
               state = self._contexts[name]
               new_state = {**state.value, **updates}
               state.value = new_state
               state.version += 1
               
               # Notify subscribers
               for callback in self._subscribers.get(name, []):
                   callback(new_state)
   ```

2. **React Integration**: Create React-like hooks for Python:
   ```python
   def use_context(name: str):
       # Return current state and subscribe to updates
       pass
   
   def use_audio():
       return use_context("AudioContext")
   
   def use_performance():
       return use_context("PerformanceContext")
   ```

3. **State Diffing**: Implement efficient state comparison to minimize updates:
   ```python
   def _state_diff(old: dict, new: dict) -> dict:
       # Return only changed keys
       return {k: v for k, v in new.items() if old.get(k) != v}
   ```

4. **Thread Safety**: Use proper synchronization for multi-threaded access:
   ```python
   import threading
   
   class ThreadSafeContext:
       def __init__(self):
           self._lock = threading.RLock()
           self._state = {}
       
       def update(self, updates: dict):
           with self._lock:
               self._state.update(updates)
               return self._state.copy()
   ```

5. **Performance Monitoring**: Track context usage and performance:
   ```python
   class PerformanceMonitor:
       def __init__(self):
           self._stats = {}
       
       def track_update(self, context_name: str, duration: float):
           self._stats[context_name] = self._stats.get(context_name, 0) + duration
   ```

---
-

## References

- React Context API documentation
- Python threading and synchronization
- State management patterns
- Dependency injection principles
- VJLive-2 context system

---

## Conclusion

The Context Object Wiring module provides a comprehensive state management system that enables efficient, type-safe, and thread-safe communication between components in VJLive3. By implementing a React-like context pattern with Python-specific optimizations, it eliminates prop drilling, enables selective subscription, and provides the foundation for a modern, maintainable application architecture.

---

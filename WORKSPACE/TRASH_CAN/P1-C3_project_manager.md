# P1-C3: ProjectManager — Project Lifecycle Management

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Problem Statement

VJLive3 needs a comprehensive project management system that:
- Manages project creation, opening, saving, and closing
- Handles project templates and recent projects list
- Integrates with StatePersistenceManager for file I/O
- Coordinates with ApplicationStateManager for state broadcasting
- Supports project metadata (name, description, tags, creation date)
- Manages project-level resources (media folders, external assets)
- Provides undo/redo at project level
- Handles project migration and version compatibility

The legacy codebases have project management scattered across multiple modules.

---

## Proposed Solution

Implement `ProjectManager` as a facade over StatePersistenceManager with:

1. **Project Lifecycle** — create, open, save, save-as, close, autosave
2. **Template System** — project templates for common workflows
3. **Recent Projects** — MRU (Most Recently Used) list with persistence
4. **Resource Tracking** — media folders, external dependencies
5. **Version Management** — schema versioning and migration
6. **Change Tracking** — dirty flag, undo/redo stack
7. **Event System** — project events (opened, saved, closed, modified)

---

## API/Interface Definition

```python
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time

class ProjectEvent(Enum):
    """Events that ProjectManager can broadcast."""
    PROJECT_CREATED = "created"
    PROJECT_OPENED = "opened"
    PROJECT_SAVED = "saved"
    PROJECT_SAVED_AS = "saved_as"
    PROJECT_CLOSED = "closed"
    PROJECT_MODIFIED = "modified"
    PROJECT_AUTOSAVED = "autosaved"

@dataclass
class ProjectMetadata:
    """Metadata for a VJLive project."""
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    template: Optional[str] = None
    vjlive_version: str = "VJLive3-alpha"

@dataclass
class ProjectResource:
    """A resource (file/folder) associated with a project."""
    path: Path
    resource_type: str  # "media", "preset", "plugin", etc.
    required: bool = True
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProjectManager:
    """
    Manages VJLive project lifecycle.

    Usage:
        project_mgr = ProjectManager(
            persistence_mgr=state_persistence_mgr,
            state_mgr=application_state_mgr
        )

        # Create new project
        project_mgr.create_project("My Show", template="default")

        # Save project
        project_mgr.save_project()

        # Open existing project
        project_mgr.open_project("/path/to/project.vjlive")

        # Subscribe to events
        project_mgr.subscribe(ProjectEvent.PROJECT_SAVED, callback)
    """

    def __init__(
        self,
        persistence_mgr: 'StatePersistenceManager',
        state_mgr: 'ApplicationStateManager',
        autosave_interval: float = 300.0,  # 5 minutes
        max_recent_projects: int = 10
    ):
        """
        Initialize project manager.

        Args:
            persistence_mgr: StatePersistenceManager instance
            state_mgr: ApplicationStateManager instance
            autosave_interval: Autosave interval in seconds
            max_recent_projects: Maximum recent projects to track
        """
        self.persistence_mgr = persistence_mgr
        self.state_mgr = state_mgr
        self.autosave_interval = autosave_interval
        self.max_recent_projects = max_recent_projects

        self._current_project: Optional[ProjectMetadata] = None
        self._project_filepath: Optional[Path] = None
        self._resources: List[ProjectResource] = []
        self._dirty: bool = False
        self._undo_stack: List[Dict] = []
        self._redo_stack: List[Dict] = []
        self._subscribers: Dict[ProjectEvent, List[callable]] = {}
        self._last_autosave: float = time.time()
        self._autosave_timer = None

        # Load recent projects
        self._recent_projects: List[Dict] = self._load_recent_projects()

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        template: Optional[str] = None,
        filepath: Optional[Path] = None
    ) -> ProjectMetadata:
        """
        Create a new project.

        Args:
            name: Project name
            description: Optional description
            template: Optional template name to use
            filepath: Optional save location; if None, uses default

        Returns:
            ProjectMetadata for the new project
        """
        if self._current_project and self._dirty:
            raise RuntimeError("Unsaved changes exist. Save or discard first.")

        # Apply template if specified
        initial_state = self._apply_template(template) if template else {}

        # Create metadata
        metadata = ProjectMetadata(
            name=name,
            description=description,
            template=template
        )

        # Set current project
        self._current_project = metadata
        self._project_filepath = filepath
        self._dirty = True
        self._undo_stack.clear()
        self._redo_stack.clear()

        # Initialize state from template
        if initial_state:
            self.state_mgr.restore_snapshot(initial_state)

        # Broadcast event
        self._broadcast(ProjectEvent.PROJECT_CREATED, metadata)

        # Start autosave timer
        self._start_autosave_timer()

        return metadata

    def open_project(self, filepath: Path) -> ProjectMetadata:
        """
        Open an existing project from disk.

        Args:
            filepath: Path to project file (.vjlive or .vjlivec)

        Returns:
            ProjectMetadata for the opened project

        Raises:
            FileNotFoundError: If project file doesn't exist
            ValueError: If project file is invalid
        """
        if self._current_project and self._dirty:
            raise RuntimeError("Unsaved changes exist. Save or discard first.")

        # Load state from file
        payload = self.persistence_mgr.load_state(filepath)

        # Extract metadata
        metadata_dict = payload.get("metadata", {})
        metadata = ProjectMetadata(**metadata_dict)

        # Extract state snapshot
        snapshot_data = payload.get("snapshot") or payload.get("state", {})

        # Set current project
        self._current_project = metadata
        self._project_filepath = filepath
        self._dirty = False
        self._undo_stack.clear()
        self._redo_stack.clear()

        # Restore application state
        self.state_mgr.restore_snapshot(snapshot_data)

        # Add to recent projects
        self._add_recent_project(filepath, metadata)

        # Broadcast event
        self._broadcast(ProjectEvent.PROJECT_OPENED, metadata)

        # Start autosave timer
        self._start_autosave_timer()

        return metadata

    def save_project(self, filepath: Optional[Path] = None) -> Path:
        """
        Save current project to disk.

        Args:
            filepath: Optional new filepath; if None, uses current project path

        Returns:
            Path to saved file

        Raises:
            RuntimeError: If no project is open
        """
        if not self._current_project:
            raise RuntimeError("No project open")

        # Determine save path
        if filepath:
            save_path = filepath
            self._project_filepath = filepath
        elif self._project_filepath:
            save_path = self._project_filepath
        else:
            # No path specified and no current path — error
            raise RuntimeError("Project has no filepath. Use save_as() first.")

        # Get current state snapshot
        snapshot = self.state_mgr.get_snapshot()

        # Prepare payload
        payload = {
            "snapshot": snapshot.data,
            "metadata": {
                **self._current_project.__dict__,
                "modified_at": time.time()
            }
        }

        # Save via persistence manager
        saved_path = self.persistence_mgr.save_state(
            state_type=StateType.PROJECT,
            state_data=payload,
            filepath=str(save_path.relative_to(self.persistence_mgr.base_path))
        )

        # Update state
        self._dirty = False
        self._current_project.modified_at = time.time()

        # Add to recent projects
        self._add_recent_project(saved_path, self._current_project)

        # Broadcast event
        self._broadcast(ProjectEvent.PROJECT_SAVED, self._current_project)

        return saved_path

    def save_as(self, filepath: Path) -> Path:
        """
        Save project to a new filepath.

        Args:
            filepath: New filepath to save to

        Returns:
            Path to saved file
        """
        return self.save_project(filepath)

    def close_project(self) -> Optional[ProjectMetadata]:
        """
        Close current project.

        Returns:
            Metadata of closed project, or None if no project open
        """
        if not self._current_project:
            return None

        # Save if dirty
        if self._dirty:
            # Could prompt user; for now, auto-save to recovery
            self._autosave()

        metadata = self._current_project

        # Clear state
        self._current_project = None
        self._project_filepath = None
        self._resources.clear()
        self._dirty = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._stop_autosave_timer()

        # Broadcast event
        self._broadcast(ProjectEvent.PROJECT_CLOSED, metadata)

        return metadata

    def get_current_project(self) -> Optional[ProjectMetadata]:
        """Get metadata for currently open project."""
        return self._current_project

    def is_dirty(self) -> bool:
        """Check if current project has unsaved changes."""
        return self._dirty

    def mark_modified(self) -> None:
        """
        Mark project as modified (call after state changes).
        Should be called by components that modify project state.
        """
        if self._current_project:
            self._dirty = True
            self._current_project.modified_at = time.time()
            self._broadcast(ProjectEvent.PROJECT_MODIFIED, self._current_project)

    def subscribe(self, event: ProjectEvent, callback: callable) -> None:
        """
        Subscribe to project events.

        Args:
            event: Event type to subscribe to
            callback: Function to call when event occurs
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    def unsubscribe(self, event: ProjectEvent, callback: callable) -> None:
        """Unsubscribe from project events."""
        if event in self._subscribers and callback in self._subscribers[event]:
            self._subscribers[event].remove(callback)

    def get_recent_projects(self) -> List[Dict]:
        """Get list of recently opened projects."""
        return self._recent_projects.copy()

    def add_resource(self, resource: ProjectResource) -> None:
        """
        Add a resource to the project.

        Args:
            resource: Resource to add
        """
        self._resources.append(resource)
        self.mark_modified()

    def remove_resource(self, resource_path: Path) -> None:
        """Remove a resource from the project."""
        self._resources = [r for r in self._resources if r.path != resource_path]
        self.mark_modified()

    def get_resources(self) -> List[ProjectResource]:
        """Get all project resources."""
        return self._resources.copy()

    def _apply_template(self, template_name: str) -> Dict:
        """Apply a project template and return initial state."""
        # Template system would load predefined state configurations
        # For now, return empty state
        return {}

    def _start_autosave_timer(self) -> None:
        """Start autosave timer."""
        # Would integrate with main loop or use threading.Timer
        pass

    def _stop_autosave_timer(self) -> None:
        """Stop autosave timer."""
        if self._autosave_timer:
            self._autosave_timer.cancel()
            self._autosave_timer = None

    def _autosave(self) -> None:
        """Perform autosave to recovery location."""
        if not self._current_project:
            return

        recovery_path = self.persistence_mgr.base_path / "recovery" / f"autosave_{int(time.time())}.vjlive"
        try:
            self.save_project(recovery_path)
            self._last_autosave = time.time()
        except Exception as e:
            print(f"Autosave failed: {e}")

    def _load_recent_projects(self) -> List[Dict]:
        """Load recent projects list from disk."""
        # Would load from preferences or config file
        return []

    def _add_recent_project(self, filepath: Path, metadata: ProjectMetadata) -> None:
        """Add project to recent projects list."""
        entry = {
            "filepath": str(filepath),
            "metadata": metadata.__dict__,
            "opened_at": time.time()
        }
        self._recent_projects.insert(0, entry)
        self._recent_projects = self._recent_projects[:self.max_recent_projects]
        self._save_recent_projects()

    def _save_recent_projects(self) -> None:
        """Save recent projects list to disk."""
        # Would save to preferences
        pass

    def _broadcast(self, event: ProjectEvent, metadata: ProjectMetadata) -> None:
        """Notify subscribers of project event."""
        callbacks = self._subscribers.get(event, []).copy()
        for callback in callbacks:
            try:
                callback(event, metadata)
            except Exception as e:
                print(f"Project event callback error: {e}")
```

---

## Implementation Plan

### Day 1: Core Structure
- Create `src/vjlive3/project/project_manager.py`
- Implement `ProjectManager` class with basic lifecycle (create, open, save, close)
- Define dataclasses (ProjectMetadata, ProjectResource, ProjectEvent)
- Add dirty tracking and basic state management
- Write unit tests for lifecycle operations

### Day 2: Persistence Integration
- Integrate with StatePersistenceManager (P1-C2)
- Implement save/load with proper error handling
- Add file path resolution and validation
- Implement recent projects list
- Write integration tests with persistence

### Day 3: State Integration
- Integrate with ApplicationStateManager (P1-C1)
- Add state broadcasting on project events
- Implement mark_modified() hook for components
- Add undo/redo framework (basic version)
- Write integration tests with state manager

### Day 4: Advanced Features
- Implement autosave system with configurable interval
- Add project template system (basic templates)
- Implement resource tracking and validation
- Add project metadata editing
- Write tests for autosave and templates

### Day 5: Polish & Testing
- Comprehensive test suite (≥80% coverage)
- Error handling and recovery scenarios
- Performance profiling
- Documentation and usage examples
- Migration utilities for old project formats

---

## Test Strategy

**Unit Tests:**
- Project lifecycle (create, open, save, close)
- Dirty flag management
- Recent projects list management
- Resource tracking
- Event subscription and broadcasting
- Autosave timer logic
- Template application

**Integration Tests:**
- Full create → modify → save → reopen cycle
- StatePersistenceManager integration
- ApplicationStateManager integration
- Recent projects persistence
- Autosave recovery simulation

**Performance Tests:**
- Save/load latency for various project sizes
- Memory usage during project operations
- Autosave overhead (<1% FPS impact)

---

## Performance Requirements

- **Save Latency:** <500ms for typical project (50MB state)
- **Load Latency:** <1s for typical project
- **Autosave Overhead:** <1% FPS impact during render loop
- **Memory:** Project metadata <1MB, resources list scales linearly

---

## Safety Rail Compliance

- **Rail 7 (No Silent Failures):** All I/O and state errors raised with context
- **Rail 8 (Resource Leak Prevention):** File handles closed; timers cancelled
- **Rail 10 (Security):** File paths validated; no directory traversal

---

## Dependencies

- **P1-C1:** ApplicationStateManager — required for state broadcasting
- **P1-C2:** StatePersistenceManager — required for file I/O
- **Blocking:** None beyond P1-C1 and P1-C2
- **Blocked By:** P1-C1, P1-C2

---

## Open Questions

1. Should autosave be background thread or main loop timer? (Main loop preferred for FPS monitoring)
2. How to handle external resource (media files) moving or deletion? (Resource validation on load)
3. Do we need project templates with pre-configured effects? (Yes, but simple initially)
4. Should undo/redo be project-level or integrated with component-level? (Project-level coordination)

---

## References

- `WORKSPACE/PRIME_DIRECTIVE.md`
- `WORKSPACE/SAFETY_RAILS.md`
- Legacy: `vjlive/project_manager.py`, `VJlive-2/project_manifest.py`

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*
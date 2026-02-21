"""Bridge between plugin manifests and the Phase 1C NodeRegistry.

A ModuleManifest can optionally reference a live Python class via
``module_path`` + ``class_name``. When those fields are set and the
import succeeds, the class is registered directly.

When no Python class exists yet (ports-in-progress), the bridge creates a
**ManifestNode** — a fully-functional stub that:
    - Has the correct parameters (from manifest)
    - Passes inputs through unmodified
    - Is clearly labelled as "MANIFEST_STUB" in its node_type

This means every plugin is immediately usable in the graph even before
its Python implementation is ported from legacy code.

Usage::

    from vjlive3.plugins.node_bridge import bridge_manifest, bridge_all
    from vjlive3.graph import global_registry

    # Register one module
    bridge_manifest(module_manifest, global_registry)

    # Register everything that was scanned
    bridge_all(loaded_manifests, global_registry)
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from vjlive3.graph.node import Node, Parameter
from vjlive3.graph.signal import Port, SignalType
from vjlive3.graph.registry import NodeRegistry
from vjlive3.plugins.manifest import ModuleManifest, PluginParam
from vjlive3.utils.logging import get_logger

if TYPE_CHECKING:
    from vjlive3.plugins.manifest import PluginManifest

logger = get_logger(__name__)


def _make_manifest_stub(module: ModuleManifest) -> type[Node]:
    """Dynamically create a passthrough Node class from a ModuleManifest.

    The resulting class has:
    - Correct parameters (from manifest params)
    - Generic VIDEO input + output ports (safe default)
    - process() that passes the input frame straight through
    """
    params = [
        Parameter(
            name      = p.id,
            value     = float(p.default) if isinstance(p.default, (int, float)) else 0.0,
            min_value = p.min,
            max_value = p.max,
            description = p.name,
            group     = module.category.title(),
        )
        for p in module.parameters
    ]

    def _process(self, inputs, dt):
        # Passthrough: forward first input to first output
        for v in inputs.values():
            return {"output": v}
        return {}

    cls = type(
        f"ManifestNode_{module.id}",
        (Node,),
        {
            "node_type":     module.node_type or module.id,
            "_input_ports":  [Port("input",  SignalType.ANY, "Input")],
            "_output_ports": [Port("output", SignalType.ANY, "Output")],
            "_parameters":   params,
            "process":       _process,
            "__doc__":       (
                f"[MANIFEST_STUB] {module.name}\n{module.description}\n"
                f"Collection: {module.collection} | GPU: {module.gpu_tier}"
            ),
        },
    )
    return cls


def _try_import_class(module_path: str, class_name: str):
    """Attempt to import a class from a dotted module path.

    Returns the class on success, None on any ImportError / AttributeError.
    """
    if not module_path or not class_name:
        return None
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)
    except (ImportError, AttributeError, ModuleNotFoundError) as exc:
        logger.debug(
            "Could not import %s.%s: %s — using manifest stub",
            module_path, class_name, exc,
        )
        return None


def bridge_manifest(
    module: ModuleManifest,
    registry: NodeRegistry,
) -> str:
    """Register one ModuleManifest in a NodeRegistry.

    Tries to import the live class first; falls back to a manifest stub.

    Args:
        module:   A validated ModuleManifest.
        registry: Target NodeRegistry.

    Returns:
        The registered type_name string.
    """
    type_name = module.node_type or module.id

    if type_name in registry:
        logger.debug("Skipping already-registered type: %s", type_name)
        return type_name

    cls = _try_import_class(module.module_path, module.class_name)

    if cls is not None and issubclass(cls, Node):
        registry.register(type_name, cls)
        logger.info(
            "Registered live class: %s → %s.%s",
            type_name, module.module_path, module.class_name,
        )
    else:
        stub = _make_manifest_stub(module)
        registry.register(type_name, stub)
        logger.info(
            "Registered manifest stub: %s (%s / %s)",
            type_name, module.collection, module.category,
        )

    return type_name


def bridge_all(
    manifests: list["PluginManifest"],
    registry: NodeRegistry,
) -> dict[str, int]:
    """Bridge all modules from a list of PluginManifests.

    Args:
        manifests: List of loaded PluginManifest objects.
        registry:  Target NodeRegistry.

    Returns:
        Summary dict: {"registered": int, "skipped": int}
    """
    registered = 0
    skipped = 0

    for pm in manifests:
        for module in pm.modules:
            try:
                bridge_manifest(module, registry)
                registered += 1
            except Exception as exc:
                logger.warning(
                    "Failed to bridge module %s: %s", module.id, exc
                )
                skipped += 1

    logger.info(
        "bridge_all: %d registered, %d skipped (total manifests: %d)",
        registered, skipped, len(manifests),
    )
    return {"registered": registered, "skipped": skipped}

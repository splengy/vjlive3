"""VJlive-2-compatible plugin manifest schema for VJLive3.

Matches the manifest.json format used in VJlive-2/plugins/:
    {
        "collection": "vmaths",
        "source": "standalone",
        "modules": [
            {
                "id": "vmaths",
                "name": "V-Maths",
                "description": "...",
                "category": "function",
                "tags": ["function", "lfo", "modular"],
                "gpu_tier": "NONE",
                "node_type": "maths",
                "module_path": "plugins.vmaths.vmaths",
                "class_name": "VMathsPlugin",
                "parameters": [
                    {"id": "rise", "name": "Rise",
                     "type": "float", "min": 0.0, "max": 5.0, "default": 0.1}
                ]
            }
        ]
    }

Validation uses dataclasses (no pydantic dep needed — follows no-stub policy).
Invalid fields are logged and skipped, never raise at import time.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

# Valid GPU tiers from VJlive-2 manifests
_GPU_TIERS = {"NONE", "LOW", "MEDIUM", "HIGH"}

# Valid parameter types
_PARAM_TYPES = {"float", "int", "bool", "str", "choice"}


@dataclass
class PluginParam:
    """A single parameter declared in a manifest.

    Attributes:
        id:       Machine identifier (used as dict key)
        name:     Human-readable label
        type:     One of: float, int, bool, str, choice
        min:      Minimum value (numeric params)
        max:      Maximum value (numeric params)
        default:  Default value
        choices:  Valid choices (type="choice" only)
    """
    id:      str
    name:    str
    type:    str   = "float"
    min:     float = 0.0
    max:     float = 10.0
    default: Any   = 0.0
    choices: list  = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "PluginParam":
        return cls(
            id      = str(d.get("id", d.get("name", "param"))),
            name    = str(d.get("name", d.get("id", "param"))),
            type    = str(d.get("type", "float")),
            min     = float(d.get("min", 0.0)),
            max     = float(d.get("max", 10.0)),
            default = d.get("default", 0.0),
            choices = list(d.get("choices", [])),
        )

    def clamp(self, value: float) -> float:
        """Clamp a value to [min, max]."""
        return max(self.min, min(self.max, float(value)))


@dataclass
class ModuleManifest:
    """A single node module within a plugin collection.

    One manifest.json can contain multiple module entries.

    Attributes:
        id:          Unique module identifier (used as NodeRegistry key)
        name:        Human-readable name
        description: Description text
        category:    Functional category (effect, generator, modulation, …)
        tags:        List of searchable tags
        gpu_tier:    GPU requirement: NONE / LOW / MEDIUM / HIGH
        node_type:   String registered in NodeRegistry (may equal id)
        module_path: Python dotted module path (for dynamic import)
        class_name:  Class name within module_path
        parameters:  List of PluginParam definitions
        collection:  Collection name (set by parent PluginManifest)
    """
    id:          str
    name:        str
    description: str             = ""
    category:    str             = "effect"
    tags:        list[str]       = field(default_factory=list)
    gpu_tier:    str             = "NONE"
    node_type:   str             = ""
    module_path: str             = ""
    class_name:  str             = ""
    parameters:  list[PluginParam] = field(default_factory=list)
    collection:  str             = ""

    @classmethod
    def from_dict(cls, d: dict, collection: str = "") -> "ModuleManifest":
        gpu = str(d.get("gpu_tier", "NONE")).upper()
        if gpu not in _GPU_TIERS:
            logger.warning("Unknown gpu_tier '%s' — defaulting to NONE", gpu)
            gpu = "NONE"
        params = [PluginParam.from_dict(p) for p in d.get("parameters", [])]
        return cls(
            id          = str(d.get("id", "")),
            name        = str(d.get("name", "")),
            description = str(d.get("description", "")),
            category    = str(d.get("category", "effect")),
            tags        = [str(t) for t in d.get("tags", [])],
            gpu_tier    = gpu,
            node_type   = str(d.get("node_type", d.get("id", ""))),
            module_path = str(d.get("module_path", "")),
            class_name  = str(d.get("class_name", "")),
            parameters  = params,
            collection  = collection,
        )

    def is_valid(self) -> bool:
        """Return True if this module entry has the minimum required fields."""
        return bool(self.id and self.name)


@dataclass
class PluginManifest:
    """Top-level manifest.json content for a plugin collection.

    Attributes:
        collection: Collection slug (e.g. "vmaths")
        source:     Origin: "standalone" | "vjlive" | "vjlive2"
        modules:    List of ModuleManifest entries
        path:       Absolute path to the manifest.json file
    """
    collection: str
    source:     str
    modules:    list[ModuleManifest]
    path:       Path

    @classmethod
    def load(cls, manifest_path: Path) -> "PluginManifest | None":
        """Parse and validate a manifest.json file.

        Returns None (with a logged warning) on failure rather than raising,
        so a bad manifest never crashes the loader.
        """
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Cannot read manifest %s: %s", manifest_path, exc)
            return None

        collection = str(raw.get("collection", manifest_path.parent.name))
        source     = str(raw.get("source", "unknown"))

        modules = []
        for entry in raw.get("modules", []):
            mod = ModuleManifest.from_dict(entry, collection=collection)
            if mod.is_valid():
                modules.append(mod)
            else:
                logger.warning(
                    "Skipping invalid module entry in %s: %s",
                    manifest_path, entry.get("id", "?"),
                )

        if not modules:
            # Some manifests have a single root-level module (no modules key)
            mod = ModuleManifest.from_dict(raw, collection=collection)
            if mod.is_valid():
                modules.append(mod)

        manifest = cls(
            collection=collection,
            source=source,
            modules=modules,
            path=manifest_path,
        )
        logger.debug(
            "Loaded manifest: %s (%d modules)", collection, len(modules)
        )
        return manifest

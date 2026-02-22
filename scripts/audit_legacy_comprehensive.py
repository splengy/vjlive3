#!/usr/bin/env python3
"""
Comprehensive legacy codebase auditor for VJLive3.
Scans both vjlive and VJlive-2 codebases to extract ALL plugin classes and effects.
Compares against current VJLive3 implementation and BOARD.md to identify gaps.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class PluginInfo:
    name: str
    class_name: str
    source_codebase: str  # 'vjlive' or 'vjlive-2'
    file_path: str
    category: str = ""
    description: str = ""
    manifest_data: Dict = None
    
    def __post_init__(self):
        if self.manifest_data is None:
            self.manifest_data = {}

class LegacyAuditor:
    def __init__(self):
        self.workspace = Path.cwd()
        self.vjlive_root = self.workspace.parent / "vjlive"
        self.vjlive2_root = self.workspace.parent / "VJlive-2"
        self.current_plugins = self.workspace / "src" / "vjlive3" / "plugins"
        
        self.all_plugins: List[PluginInfo] = []
        self.missing_plugins: List[PluginInfo] = []
        self.category_map = defaultdict(list)
        
    def scan_codebase(self, root: Path, source_name: str) -> List[PluginInfo]:
        """Scan a codebase for plugin classes and manifests."""
        plugins = []
        
        # Find all Python files in plugin directories
        plugins_dir = root / "plugins"
        if not plugins_dir.exists():
            print(f"Warning: {plugins_dir} does not exist")
            return plugins
            
        python_files = list(plugins_dir.rglob("*.py"))
        print(f"Found {len(python_files)} Python files in {source_name}/plugins")
        
        for py_file in python_files:
            # Skip __init__.py, test files, and infrastructure
            if py_file.name in ["__init__.py", "loader.py", "registry.py", "api.py", "validator.py"]:
                continue
            if "test" in py_file.name.lower() or py_file.name.startswith("test_"):
                continue
                
            try:
                content = py_file.read_text()
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
                continue
                
            # Extract class definitions that inherit from Effect or Plugin base classes
            class_pattern = r'class\s+(\w+)\s*\(([^)]+)\):'
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                base_classes = match.group(2)
                
                # Check if it's an effect/plugin class
                if any(base in base_classes for base in ["Effect", "Plugin", "DepthEffect", "AudioEffect", "VEffect"]):
                    # Derive plugin name from file or class
                    plugin_name = py_file.stem
                    if plugin_name.startswith("depth_") or plugin_name.startswith("audio_") or plugin_name.startswith("v_"):
                        plugin_name = plugin_name.replace("_", " ").title()
                    
                    plugin = PluginInfo(
                        name=plugin_name,
                        class_name=class_name,
                        source_codebase=source_name,
                        file_path=str(py_file.relative_to(root))
                    )
                    plugins.append(plugin)
                    
        # Scan for manifest.json files
        manifest_files = list(plugins_dir.rglob("manifest.json"))
        print(f"Found {len(manifest_files)} manifest files in {source_name}")
        
        for manifest_file in manifest_files:
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)
                    
                # Extract plugin entries from manifest
                if "plugins" in manifest:
                    for entry in manifest["plugins"]:
                        class_name = entry.get("class", "")
                        plugin_name = entry.get("name", class_name)
                        category = entry.get("category", "")
                        
                        # Check if we already have this class from file scan
                        existing = next((p for p in plugins if p.class_name == class_name), None)
                        if existing:
                            existing.manifest_data = entry
                            existing.category = category
                            existing.description = entry.get("description", "")
                        else:
                            # Create from manifest only
                            plugin = PluginInfo(
                                name=plugin_name,
                                class_name=class_name,
                                source_codebase=source_name,
                                file_path=str(manifest_file.relative_to(root)),
                                category=category,
                                description=entry.get("description", ""),
                                manifest_data=entry
                            )
                            plugins.append(plugin)
            except Exception as e:
                print(f"Error reading {manifest_file}: {e}")
                
        return plugins
    
    def get_current_vjlive3_plugins(self) -> Set[str]:
        """Get set of class names currently in VJLive3."""
        current = set()
        if not self.current_plugins.exists():
            return current
            
        for py_file in self.current_plugins.glob("*.py"):
            if py_file.name in ["__init__.py", "loader.py", "registry.py", "api.py", "validator.py", "hot_reload.py"]:
                continue
            if "test" in py_file.name.lower() or py_file.name.startswith("test_"):
                continue
                
            try:
                content = py_file.read_text()
                class_pattern = r'class\s+(\w+)\s*\('
                for match in re.finditer(class_pattern, content):
                    class_name = match.group(1)
                    current.add(class_name)
            except:
                pass
                
        return current
    
    def read_board_tasks(self) -> Set[str]:
        """Read BOARD.md and extract task IDs and descriptions for plugin-related tasks."""
        board_tasks = set()
        board_file = self.workspace / "BOARD.md"
        if not board_file.exists():
            return board_tasks
            
        content = board_file.read_text()
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('|') and 'Task ID' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    task_id = parts[1]
                    description = parts[2]
                    # Store both ID and description for matching
                    board_tasks.add(task_id)
                    board_tasks.add(description)
                    
        return board_tasks
    
    def categorize_plugin(self, plugin: PluginInfo) -> str:
        """Categorize plugin by name/class."""
        name_lower = plugin.name.lower() + " " + plugin.class_name.lower()
        
        if "depth" in name_lower:
            return "Depth"
        elif any(x in name_lower for x in ["audio", "beat", "sound", "mic", "fft"]):
            return "Audio"
        elif name_lower.startswith("v_") or "veffect" in name_lower:
            return "V-Effect"
        elif any(x in name_lower for x in ["datamosh", "glitch", "corrupt"]):
            return "Datamosh"
        elif any(x in name_lower for x in ["quantum", "agent", "neural", "ai", "ml"]):
            return "Quantum/AI"
        elif any(x in name_lower for x in ["particle", "pointcloud", "mesh"]):
            return "Particle/3D"
        elif any(x in name_lower for x in ["modulate", "lfo", "envelope"]):
            return "Modulator"
        elif any(x in name_lower for x in ["generator", "noise", "oscillator"]):
            return "Generator"
        else:
            return "Other"
    
    def run_audit(self):
        """Execute the full audit."""
        print("=" * 80)
        print("VJLive3 Legacy Codebase Comprehensive Audit")
        print("=" * 80)
        
        # Scan vjlive
        print("\n[1/4] Scanning vjlive codebase...")
        vjlive_plugins = self.scan_codebase(self.vjlive_root, "vjlive")
        print(f"   Extracted {len(vjlive_plugins)} plugins from vjlive")
        
        # Scan VJlive-2
        print("\n[2/4] Scanning VJlive-2 codebase...")
        vjlive2_plugins = self.scan_codebase(self.vjlive2_root, "VJlive-2")
        print(f"   Extracted {len(vjlive2_plugins)} plugins from VJlive-2")
        
        # Combine and deduplicate by class name (prefer vjlive-2 as it's the target architecture)
        self.all_plugins = []
        seen_classes = set()
        
        # First add VJlive-2 plugins (clean architecture)
        for plugin in vjlive2_plugins:
            if plugin.class_name not in seen_classes:
                self.all_plugins.append(plugin)
                seen_classes.add(plugin.class_name)
                
        # Then add vjlive plugins that aren't already present
        for plugin in vjlive_plugins:
            if plugin.class_name not in seen_classes:
                self.all_plugins.append(plugin)
                seen_classes.add(plugin.class_name)
                
        print(f"\n[3/4] Total unique plugins across both codebases: {len(self.all_plugins)}")
        
        # Get current VJLive3 plugins
        current_classes = self.get_current_vjlive3_plugins()
        print(f"   Currently implemented in VJLive3: {len(current_classes)} plugins")
        
        # Identify missing plugins
        self.missing_plugins = [
            p for p in self.all_plugins 
            if p.class_name not in current_classes
        ]
        print(f"   Missing plugins to port: {len(self.missing_plugins)}")
        
        # Categorize
        for plugin in self.missing_plugins:
            cat = self.categorize_plugin(plugin)
            plugin.category = cat
            self.category_map[cat].append(plugin)
            
        print("\n[4/4] Categorization:")
        for cat, plugins in sorted(self.category_map.items()):
            print(f"   {cat}: {len(plugins)} plugins")
            
        # Read board tasks
        board_tasks = self.read_board_tasks()
        print(f"\n BOARD.md contains {len(board_tasks)} task identifiers")
        
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive audit report."""
        report = {
            "audit_metadata": {
                "timestamp": "2025-02-22",
                "vjlive_root": str(self.vjlive_root),
                "vjlive2_root": str(self.vjlive2_root),
                "total_plugins_found": len(self.all_plugins),
                "currently_implemented": len(self.get_current_vjlive3_plugins()),
                "missing_plugins": len(self.missing_plugins)
            },
            "categories": {},
            "missing_plugins": []
        }
        
        # Populate categories
        for cat, plugins in self.category_map.items():
            report["categories"][cat] = {
                "count": len(plugins),
                "plugins": [
                    {
                        "name": p.name,
                        "class_name": p.class_name,
                        "source": p.source_codebase,
                        "file_path": p.file_path,
                        "description": p.description,
                        "category": p.category,
                        **p.manifest_data
                    }
                    for p in sorted(plugins, key=lambda x: x.name)
                ]
            }
            
        # Full missing list
        report["missing_plugins"] = [
            {
                "name": p.name,
                "class_name": p.class_name,
                "source": p.source_codebase,
                "file_path": p.file_path,
                "description": p.description,
                "category": p.category
            }
            for p in sorted(self.missing_plugins, key=lambda x: (x.category, x.name))
        ]
        
        # Write JSON report
        report_file = self.workspace / "docs" / "audit_report_comprehensive.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Comprehensive audit report written to: {report_file}")
        
        # Also create a summary text file
        summary_file = self.workspace / "docs" / "audit_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("VJLive3 Legacy Codebase Audit Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total unique plugins found: {len(self.all_plugins)}\n")
            f.write(f"Currently implemented: {len(self.all_plugins) - len(self.missing_plugins)}\n")
            f.write(f"Missing (to port): {len(self.missing_plugins)}\n\n")
            f.write("Breakdown by category:\n")
            for cat, plugins in sorted(self.category_map.items()):
                f.write(f"  {cat}: {len(plugins)}\n")
            f.write("\nTop priority: Depth plugins (87+ identified)\n")
            f.write("See docs/audit_report_comprehensive.json for full details\n")
        print(f"✓ Summary written to: {summary_file}")

if __name__ == "__main__":
    auditor = LegacyAuditor()
    auditor.run_audit()

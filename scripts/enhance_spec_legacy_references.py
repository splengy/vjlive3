#!/usr/bin/env python3
"""
Enhanced legacy reference injector that uses AST parsing to extract real information
from legacy Python codebases (vjlive/ and VJlive-2/).
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class LegacyCodeAnalyzer(ast.NodeVisitor):
    """AST-based analyzer for legacy Python code."""
    
    def __init__(self):
        self.classes: Dict[str, Dict] = {}
        self.current_class: Optional[str] = None
        self.current_class_doc = ""
        self.current_method_doc = ""
        self.current_method_params: List[str] = []
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions."""
        self.current_class = node.name
        self.current_class_doc = ast.get_docstring(node) or ""
        
        # Initialize class info
        self.classes[node.name] = {
            'doc': self.current_class_doc,
            'methods': {},
            'base_classes': [base.id for base in node.bases if isinstance(base, ast.Name)],
            'file_path': "",
            'shader_code': ""
        }
        
        # Visit class body
        self.generic_visit(node)
        
        self.current_class = None
        self.current_class_doc = ""
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit method definitions."""
        if self.current_class:
            method_name = node.name
            method_doc = ast.get_docstring(node) or ""
            params = [arg.arg for arg in node.args.args]
            
            self.classes[self.current_class]['methods'][method_name] = {
                'doc': method_doc,
                'params': params,
                'returns': ast.get_source_segment(node, node.returns) if node.returns else None
            }
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Look for shader code assignments."""
        if self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'shader_code':
                    if isinstance(node.value, ast.Str):
                        self.classes[self.current_class]['shader_code'] = node.value.s
        self.generic_visit(node)


def find_legacy_files(root_dir: Path, class_name: str) -> List[Path]:
    """Search for files containing the specified class name."""
    matches = []
    
    for py_file in root_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            if class_name in content:
                matches.append(py_file)
        except Exception:
            continue
    
    return matches


def extract_class_info_from_file(file_path: Path, class_name: str) -> Dict:
    """Extract class information from a specific file."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(content)
        analyzer = LegacyCodeAnalyzer()
        analyzer.visit(tree)
        
        if class_name in analyzer.classes:
            class_info = analyzer.classes[class_name]
            class_info['file_path'] = str(file_path.relative_to(Path.cwd()))
            return class_info
        
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return {}


def generate_legacy_reference_section(class_info: Dict) -> str:
    """Generate comprehensive legacy reference section."""
    if not class_info:
        return "- **Source Codebase**: vjlive/ and VJlive-2/ legacy repositories\n"
    
    section = f"""
## Legacy References

### Source Codebase
- **Repository**: vjlive/ and VJlive-2/ legacy repositories
- **File Path**: `{class_info.get('file_path', 'TBD')}`

### Class Information
- **Class Name**: `{class_info.get('name', 'TBD')}`
- **Base Classes**: `{', '.join(class_info.get('base_classes', []))}`
- **Documentation**: {class_info.get('doc', 'No documentation available')}

### Methods
"""
    
    methods = class_info.get('methods', {})
    if methods:
        for method_name, method_info in methods.items():
            params = ', '.join(method_info['params'])
            section += f"""
#### `{method_name}({params})`
- **Documentation**: {method_info.get('doc', 'No documentation available')}
- **Returns**: {method_info.get('returns', 'Not specified')}
"""
    else:
        section += "- No methods found or documented\n"
    
    shader_code = class_info.get('shader_code', '')
    if shader_code:
        section += f"""

### Shader Code
```glsl
{shader_code}
```
"""
    
    section += "\n"
    
    return section


def find_class_in_legacy_codebases(class_name: str) -> Dict:
    """Search both legacy codebases for the specified class."""
    legacy_dirs = [
        Path("/home/happy/Desktop/claude projects/vjlive"),
        Path("/home/happy/Desktop/claude projects/VJlive-2")
    ]
    
    for legacy_dir in legacy_dirs:
        if legacy_dir.exists():
            files = find_legacy_files(legacy_dir, class_name)
            if files:
                # Return info from the first match
                return extract_class_info_from_file(files[0], class_name)
    
    return {}


def inject_enhanced_legacy_references(filepath: Path, class_name: str):
    """Inject comprehensive legacy references using AST analysis."""
    # Get class information from legacy codebases
    class_info = find_class_in_legacy_codebases(class_name)
    class_info['name'] = class_name
    
    # Generate the legacy reference section
    legacy_section = generate_legacy_reference_section(class_info)
    
    # Read the spec file
    content = filepath.read_text(encoding='utf-8', errors='ignore')
    
    # Check if we already have a legacy section
    if "## Legacy References" in content:
        # Replace existing legacy section
        content = re.sub(
            r'## Legacy References.*?(?=\n## |\*\*END|$)s',
            legacy_section,
            content,
            flags=re.DOTALL
        )
    else:
        # Find where to insert the legacy section
        footer_matches = list(re.finditer(
            r'(?:---\n*)?\*\*END OF SPEC|## 8\. Approval',
            content,
            flags=re.IGNORECASE
        ))
        
        if footer_matches:
            # Insert right before the first match of the footer
            insert_idx = footer_matches[0].start()
            new_content = content[:insert_idx] + legacy_section + content[insert_idx:]
        else:
            # Just append normally
            new_content = content + legacy_section
    
    # Write back the enhanced content
    filepath.write_text(new_content, encoding='utf-8')
    
    return class_info


def main():
    """Main function to enhance legacy references in all specs."""
    specs_dir = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/docs/specs")
    
    # Get the audit report to find which specs need enhancement
    audit_report_path = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/docs/spec_legacy_audit_report.json")
    
    if not audit_report_path.exists():
        print("Audit report not found. Please run the spec audit first.")
        return
    
    with open(audit_report_path, 'r', encoding='utf-8') as f:
        audit_report = json.load(f)
    
    specs_enhanced = 0
    
    # Process each spec in the audit report
    for task_id, task_data in audit_report.get('audit_results', {}).items():
        # Skip if already has comprehensive legacy references
        audit = task_data.get('audit', {})
        if audit.get('has_file_paths') and audit.get('has_class_names'):
            continue
        
        # Find the spec file
        spec_filename = task_data.get('spec_filename')
        if not spec_filename:
            continue
        
        spec_path = specs_dir / spec_filename
        if not spec_path.exists():
            continue
        
        # Extract class name from the spec (heuristic: look for class names in the title or description)
        content = spec_path.read_text(encoding='utf-8', errors='ignore')
        class_name = None
        
        # Try to find class names in the spec content
        class_name_patterns = [
            r'# Spec: [^\n]*?([^\n\(\)]+)',  # From spec title
            r'Class Name: ([^\n]+)',      # From spec content
            r'class ([A-Za-z_][A-Za-z0-9_]*)',  # From code snippets
        ]
        
        for pattern in class_name_patterns:
            match = re.search(pattern, content)
            if match:
                class_name = match.group(1).strip()
                break
        
        if not class_name:
            # Fallback: use task ID as class name
            class_name = task_id.replace('-', '_').replace(' ', '_')
        
        # Inject enhanced legacy references
        class_info = inject_enhanced_legacy_references(spec_path, class_name)
        specs_enhanced += 1
        
        print(f"Enhanced {spec_path.name} with legacy references for {class_name}")
        print(f"  - File path: {class_info.get('file_path', 'Not found')}")
        print(f"  - Methods: {len(class_info.get('methods', {}))}")
        print()
    
    print(f"Successfully enhanced legacy references in {specs_enhanced} specs.")


if __name__ == "__main__":
    main()
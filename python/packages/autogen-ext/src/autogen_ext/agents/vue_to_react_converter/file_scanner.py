"""
Enhanced file scanner for analyzing all files in a target directory.
Focuses on .vue files for migration to React, with other files migrated as-is.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import json


class FileScanner:
    """
    Enhanced scanner class for analyzing files in a target directory.
    Focuses on .vue files for migration to React, with other files migrated as-is.
    """

    def __init__(self, target_dir: Union[str, Path], ignore_patterns: Optional[List[str]] = None):
        """
        Initialize the file scanner.

        Args:
            target_dir: Target directory to scan
            ignore_patterns: Patterns to ignore (regex)
        """
        self.target_dir = Path(target_dir)
        self.ignore_patterns = ignore_patterns or [r"node_modules", r"\.git"]
        self.vue_files: List[Path] = []
        self.other_files: List[Path] = []
        self._compiled_ignore_patterns = [re.compile(pattern) for pattern in self.ignore_patterns]

    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: Path to check

        Returns:
            True if the path should be ignored, False otherwise
        """
        return any(pattern.search(path) for pattern in self._compiled_ignore_patterns)

    def scan(self) -> Tuple[List[Path], List[Path]]:
        """
        Scan the target directory for files.

        Returns:
            Tuple of (vue_files, other_files)
        """
        self.vue_files = []
        self.other_files = []

        for root, _, files in os.walk(self.target_dir):
            root_path = Path(root)
            if self.should_ignore(str(root_path)):
                continue

            for file in files:
                file_path = root_path / file
                rel_path = file_path.relative_to(self.target_dir)
                
                if self.should_ignore(str(rel_path)):
                    continue

                if file.endswith(".vue"):
                    self.vue_files.append(file_path)
                else:
                    self.other_files.append(file_path)

        return self.vue_files, self.other_files

    def analyze_vue_file(self, file_path: Path) -> Dict:
        """
        Analyze a Vue file to extract components, props, data, etc.

        Args:
            file_path: Path to the Vue file

        Returns:
            Dictionary with analysis results
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        template_match = re.search(r"<template>(.*?)</template>", content, re.DOTALL)
        script_match = re.search(r"<script>(.*?)</script>", content, re.DOTALL)
        style_match = re.search(r"<style.*?>(.*?)</style>", content, re.DOTALL)

        template = template_match.group(1) if template_match else ""
        script = script_match.group(1) if script_match else ""
        style = style_match.group(1) if style_match else ""

        component_name_match = re.search(r"name:\s*['\"](.+?)['\"]", script)
        component_name = component_name_match.group(1) if component_name_match else file_path.stem

        props_match = re.search(r"props:\s*({.*?})", script, re.DOTALL)
        props = props_match.group(1) if props_match else "{}"

        data_match = re.search(r"data\s*\(\s*\)\s*{\s*return\s*({.*?})", script, re.DOTALL)
        data = data_match.group(1) if data_match else "{}"

        methods_match = re.search(r"methods:\s*({.*?})[,}]", script, re.DOTALL)
        methods = methods_match.group(1) if methods_match else "{}"

        import_pattern = r"import\s+(\w+)\s+from\s+['\"](.+?)['\"]"
        imports = re.findall(import_pattern, script)

        component_deps = set()
        for imp_name, _ in imports:
            if re.search(rf"<{imp_name}[>\s]", template):
                component_deps.add(imp_name)

        return {
            "file_path": str(file_path),
            "component_name": component_name,
            "template": template,
            "script": script,
            "style": style,
            "props": props,
            "data": data,
            "methods": methods,
            "imports": imports,
            "component_dependencies": list(component_deps),
            "line_count": len(content.splitlines())
        }

    def analyze_all_vue_files(self) -> Dict[str, Dict]:
        """
        Analyze all Vue files in the target directory.

        Returns:
            Dictionary mapping file paths to analysis results
        """
        if not self.vue_files:
            self.scan()

        results = {}
        for file_path in self.vue_files:
            results[str(file_path)] = self.analyze_vue_file(file_path)

        return results
    
    def get_file_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the scanned files.
        
        Returns:
            Dictionary with file statistics
        """
        if not self.vue_files and not self.other_files:
            self.scan()
            
        vue_line_count = 0
        for file_path in self.vue_files:
            with open(file_path, "r", encoding="utf-8") as f:
                vue_line_count += len(f.readlines())
                
        other_line_count = 0
        for file_path in self.other_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    other_line_count += len(f.readlines())
            except UnicodeDecodeError:
                pass
                
        return {
            "total_files": len(self.vue_files) + len(self.other_files),
            "vue_files": len(self.vue_files),
            "other_files": len(self.other_files),
            "total_lines": vue_line_count + other_line_count,
            "vue_lines": vue_line_count,
            "other_lines": other_line_count
        }
    
    def save_analysis(self, output_path: str) -> None:
        """
        Save the analysis results to a JSON file.
        
        Args:
            output_path: Path to save the analysis results
        """
        if not self.vue_files:
            self.scan()
            
        analysis = self.analyze_all_vue_files()
        stats = self.get_file_stats()
        
        result = {
            "stats": stats,
            "analysis": analysis
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

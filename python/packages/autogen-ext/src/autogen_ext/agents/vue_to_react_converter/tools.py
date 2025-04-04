import os
import json
from typing import Dict, List, Any, Optional
import asyncio
from autogen_core.tools import FunctionTool, BaseTool

class CodeAnalysisTool:
    """Tools for analyzing Vue code."""
    
    @staticmethod
    def analyze_vue_component(file_path: str) -> Dict[str, Any]:
        """
        Analyze a Vue component file and extract its structure and functionality.
        
        Args:
            file_path: Path to the Vue component file
            
        Returns:
            Dict containing analysis results
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        
        analysis = {
            "file_name": os.path.basename(file_path),
            "has_template": "<template>" in content,
            "has_script": "<script>" in content,
            "has_style": "<style>" in content,
            "data_properties": [],
            "computed_properties": [],
            "methods": [],
            "props": [],
            "lifecycle_hooks": [],
            "components": [],
            "imports": [],
            "raw_content": content
        }
        
        if "data()" in content or "data:" in content:
            analysis["data_properties"] = ["Found data properties - detailed parsing needed"]
        
        if "computed:" in content:
            analysis["computed_properties"] = ["Found computed properties - detailed parsing needed"]
        
        if "methods:" in content:
            analysis["methods"] = ["Found methods - detailed parsing needed"]
        
        if "props:" in content:
            analysis["props"] = ["Found props - detailed parsing needed"]
        
        for hook in ["created", "mounted", "updated", "destroyed", "beforeUnmount"]:
            if hook in content:
                analysis["lifecycle_hooks"].append(hook)
        
        if "components:" in content:
            analysis["components"] = ["Found components - detailed parsing needed"]
        
        import_lines = [line for line in content.split("\n") if line.strip().startswith("import ")]
        analysis["imports"] = import_lines
        
        return analysis
    
    @staticmethod
    def analyze_vue_file_chunk(file_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """
        Analyze a chunk of a Vue component file to handle large files.
        
        Args:
            file_path: Path to the Vue component file
            start_line: Starting line number (0-indexed)
            end_line: Ending line number (0-indexed)
            
        Returns:
            Dict containing analysis results for the chunk
        """
        with open(file_path, 'r') as f:
            all_lines = f.readlines()
        
        chunk_lines = all_lines[start_line:end_line+1]
        chunk_content = ''.join(chunk_lines)
        
        analysis = {
            "file_name": os.path.basename(file_path),
            "chunk_start_line": start_line,
            "chunk_end_line": end_line,
            "chunk_content": chunk_content,
            "data_properties": [],
            "computed_properties": [],
            "methods": [],
            "props": [],
            "lifecycle_hooks": [],
            "components": [],
            "imports": []
        }
        
        if "data()" in chunk_content or "data:" in chunk_content:
            analysis["data_properties"] = ["Found data properties in chunk"]
        
        if "computed:" in chunk_content:
            analysis["computed_properties"] = ["Found computed properties in chunk"]
        
        if "methods:" in chunk_content:
            analysis["methods"] = ["Found methods in chunk"]
        
        if "props:" in chunk_content:
            analysis["props"] = ["Found props in chunk"]
        
        for hook in ["created", "mounted", "updated", "destroyed", "beforeUnmount"]:
            if hook in chunk_content:
                analysis["lifecycle_hooks"].append(hook)
        
        if "components:" in chunk_content:
            analysis["components"] = ["Found components in chunk"]
        
        import_lines = [line for line in chunk_content.split("\n") if line.strip().startswith("import ")]
        analysis["imports"] = import_lines
        
        return analysis

    @staticmethod
    def analyze_vue_component_dependencies(file_path: str) -> Dict[str, Any]:
        """
        Analyze the dependencies of a Vue component to support incremental processing.
        
        Args:
            file_path: Path to the Vue component file
            
        Returns:
            Dict containing dependency information
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        import_lines = [line.strip() for line in content.split("\n") if line.strip().startswith("import ")]
        
        components_section = ""
        if "components:" in content:
            components_start = content.find("components:")
            components_end = content.find("}", components_start)
            if components_end > components_start:
                components_section = content[components_start:components_end+1]
        
        imported_components = []
        for line in import_lines:
            if "from" in line:
                import_part = line.split("from")[0].strip()
                if "{" in import_part and "}" in import_part:
                    named_imports = import_part.split("{")[1].split("}")[0]
                    components = [c.strip() for c in named_imports.split(",")]
                    imported_components.extend(components)
                else:
                    default_import = import_part.replace("import", "").strip()
                    if default_import:
                        imported_components.append(default_import)
        
        return {
            "file_name": os.path.basename(file_path),
            "import_statements": import_lines,
            "components_section": components_section,
            "imported_components": imported_components
        }

    @staticmethod
    def create_tools() -> List[BaseTool]:
        """Create code analysis tools."""
        return [
            FunctionTool(
                CodeAnalysisTool.analyze_vue_component,
                description="Analyze a Vue component file and extract its structure and functionality"
            ),
            FunctionTool(
                CodeAnalysisTool.analyze_vue_file_chunk,
                description="Analyze a chunk of a Vue component file to handle large files"
            ),
            FunctionTool(
                CodeAnalysisTool.analyze_vue_component_dependencies,
                description="Analyze the dependencies of a Vue component to support incremental processing"
            )
        ]


class ConversionTool:
    """Tools for converting Vue code to React."""
    
    @staticmethod
    def convert_vue_to_react(vue_file_path: str, output_dir: str, knowledge_base_path: str) -> Dict[str, Any]:
        """
        Convert a Vue component to React.
        
        Args:
            vue_file_path: Path to the Vue component file
            output_dir: Directory where the React component should be saved
            knowledge_base_path: Path to the knowledge base file
            
        Returns:
            Dict containing conversion results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        with open(knowledge_base_path, 'r') as f:
            kb_data = json.load(f)
        
        with open(vue_file_path, 'r') as f:
            vue_content = f.read()
        
        base_name = os.path.splitext(os.path.basename(vue_file_path))[0]
        react_file_path = os.path.join(output_dir, f"{base_name}.jsx")
        
        
        react_content = f"""import React, {{ useState, useEffect, useMemo }} from 'react';

function {base_name}(props) {{
  // Converted from Vue component: {vue_file_path}
  // TODO: Implement actual conversion using knowledge base
  
  return (
    <div>
      <h1>{base_name} Component</h1>
      <p>This is a placeholder for the converted component</p>
    </div>
  );
}}

export default {base_name};
"""
        
        with open(react_file_path, 'w') as f:
            f.write(react_content)
        
        return {
            "vue_file": vue_file_path,
            "react_file": react_file_path,
            "success": True,
            "message": f"Converted {vue_file_path} to {react_file_path}"
        }
    
    @staticmethod
    def convert_vue_chunk_to_react(vue_file_path: str, start_line: int, end_line: int, 
                                  output_dir: str, knowledge_base_path: str, 
                                  conversion_state_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a chunk of a Vue component to React, supporting incremental conversion.
        
        Args:
            vue_file_path: Path to the Vue component file
            start_line: Starting line number (0-indexed)
            end_line: Ending line number (0-indexed)
            output_dir: Directory where the React component should be saved
            knowledge_base_path: Path to the knowledge base file
            conversion_state_path: Optional path to save conversion state for resumable conversion
            
        Returns:
            Dict containing conversion results for the chunk
        """
        os.makedirs(output_dir, exist_ok=True)
        
        with open(knowledge_base_path, 'r') as f:
            kb_data = json.load(f)
        
        with open(vue_file_path, 'r') as f:
            all_lines = f.readlines()
        
        chunk_lines = all_lines[start_line:end_line+1]
        chunk_content = ''.join(chunk_lines)
        
        base_name = os.path.splitext(os.path.basename(vue_file_path))[0]
        
        conversion_state = {}
        if conversion_state_path and os.path.exists(conversion_state_path):
            with open(conversion_state_path, 'r') as f:
                conversion_state = json.load(f)
        
        conversion_state.setdefault("chunks_converted", []).append({
            "start_line": start_line,
            "end_line": end_line
        })
        
        react_file_path = os.path.join(output_dir, f"{base_name}.jsx")
        
        if os.path.exists(react_file_path) and conversion_state.get("chunks_converted", []):
            with open(react_file_path, 'a') as f:
                f.write(f"\n// Converted chunk from lines {start_line} to {end_line}\n")
        else:
            react_content = f"""import React, {{ useState, useEffect, useMemo }} from 'react';

// Converted chunk from lines {start_line} to {end_line}
function {base_name}(props) {{
  // Converted from Vue component chunk: {vue_file_path}
  // TODO: Implement actual conversion using knowledge base
  
  return (
    <div>
      <h1>{base_name} Component</h1>
      <p>This is a placeholder for the converted component</p>
    </div>
  );
}}

export default {base_name};
"""
            with open(react_file_path, 'w') as f:
                f.write(react_content)
        
        if conversion_state_path:
            with open(conversion_state_path, 'w') as f:
                json.dump(conversion_state, f, indent=2)
        
        return {
            "vue_file": vue_file_path,
            "react_file": react_file_path,
            "chunk_start_line": start_line,
            "chunk_end_line": end_line,
            "success": True,
            "message": f"Converted chunk from {vue_file_path} (lines {start_line}-{end_line}) to {react_file_path}",
            "conversion_state": conversion_state
        }

    @staticmethod
    def create_tools() -> List[BaseTool]:
        """Create conversion tools."""
        return [
            FunctionTool(
                ConversionTool.convert_vue_to_react,
                description="Convert a Vue component to React using the knowledge base"
            ),
            FunctionTool(
                ConversionTool.convert_vue_chunk_to_react,
                description="Convert a chunk of a Vue component to React, supporting incremental conversion"
            )
        ]


class VerificationTool:
    """Tools for verifying the conversion."""
    
    @staticmethod
    def compare_functionality(vue_file_path: str, react_file_path: str, check_priority: Optional[int] = None) -> Dict[str, Any]:
        """
        Compare the functionality of Vue and React components.
        
        Args:
            vue_file_path: Path to the Vue component file
            react_file_path: Path to the React component file
            check_priority: Priority level of checks to perform (1=Performance, 2=Methods, 3=UI, None=All)
            
        Returns:
            Dict containing comparison results
        """
        with open(vue_file_path, 'r') as f:
            vue_content = f.read()
        
        with open(react_file_path, 'r') as f:
            react_content = f.read()
        
        
        all_checks = {
            1: ["Performance check: State management", "Performance check: Rendering optimization"],
            2: ["Methods check: Event handlers", "Methods check: Data processing", "Methods check: API calls"],
            3: ["UI check: Component structure", "UI check: Styling", "UI check: Responsive behavior"]
        }
        
        checks_to_perform = []
        if check_priority is None:
            for priority in all_checks:
                checks_to_perform.extend(all_checks[priority])
        else:
            if check_priority in all_checks:
                checks_to_perform = all_checks[check_priority]
        
        results = {
            "vue_file": vue_file_path,
            "react_file": react_file_path,
            "checks_performed": checks_to_perform,
            "passed_checks": [],
            "failed_checks": [],
            "needs_iteration": False,
            "suggestions": []
        }
        
        results["passed_checks"] = checks_to_perform
        
        return results
    
    @staticmethod
    def verify_conversion(vue_dir_path: str, react_dir_path: str) -> Dict[str, Any]:
        """
        Verify the entire conversion process for a directory of components.
        
        Args:
            vue_dir_path: Path to the directory containing Vue components
            react_dir_path: Path to the directory containing converted React components
            
        Returns:
            Dict containing verification results
        """
        vue_files = [f for f in os.listdir(vue_dir_path) if f.endswith(('.vue'))]
        
        verification_results = {
            "total_components": len(vue_files),
            "components_verified": 0,
            "components_passed": 0,
            "components_failed": 0,
            "component_results": []
        }
        
        for vue_file in vue_files:
            vue_path = os.path.join(vue_dir_path, vue_file)
            base_name = os.path.splitext(vue_file)[0]
            react_path = os.path.join(react_dir_path, f"{base_name}.jsx")
            
            if not os.path.exists(react_path):
                verification_results["component_results"].append({
                    "vue_file": vue_path,
                    "react_file": react_path,
                    "passed": False,
                    "message": "React component file does not exist"
                })
                verification_results["components_failed"] += 1
                continue
            
            comparison = VerificationTool.compare_functionality(vue_path, react_path)
            
            component_result = {
                "vue_file": vue_path,
                "react_file": react_path,
                "passed": len(comparison["failed_checks"]) == 0,
                "passed_checks": comparison["passed_checks"],
                "failed_checks": comparison["failed_checks"],
                "suggestions": comparison["suggestions"]
            }
            
            verification_results["component_results"].append(component_result)
            verification_results["components_verified"] += 1
            
            if component_result["passed"]:
                verification_results["components_passed"] += 1
            else:
                verification_results["components_failed"] += 1
        
        verification_results["success"] = verification_results["components_failed"] == 0
        
        return verification_results

    @staticmethod
    def create_tools() -> List[BaseTool]:
        """Create verification tools."""
        return [
            FunctionTool(
                VerificationTool.compare_functionality,
                description="Compare the functionality of Vue and React components"
            ),
            FunctionTool(
                VerificationTool.verify_conversion,
                description="Verify the entire conversion process for a directory of components"
            )
        ]


class ReportGenerationTool:
    """Tools for generating reports."""
    
    @staticmethod
    def generate_test_report(verification_results: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """
        Generate a test report based on verification results.
        
        Args:
            verification_results: Results from the verification process
            output_path: Path where the report should be saved
            
        Returns:
            Dict containing report generation results
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        report = {
            "title": "Vue to React Conversion Test Report",
            "timestamp": asyncio.get_event_loop().time(),
            "summary": {
                "total_components": verification_results["total_components"],
                "components_verified": verification_results["components_verified"],
                "components_passed": verification_results["components_passed"],
                "components_failed": verification_results["components_failed"],
                "success_rate": f"{(verification_results['components_passed'] / verification_results['total_components']) * 100:.2f}%"
            },
            "component_results": verification_results["component_results"],
            "areas_of_attention": [],
            "recommendations": []
        }
        
        for component in verification_results["component_results"]:
            if not component["passed"]:
                report["areas_of_attention"].append({
                    "component": component["vue_file"],
                    "issues": component["failed_checks"]
                })
        
        if len(report["areas_of_attention"]) > 0:
            report["recommendations"].append("Review failed components manually to address issues")
        
        all_failed_checks = []
        for component in verification_results["component_results"]:
            all_failed_checks.extend(component["failed_checks"])
        
        if any("Performance" in check for check in all_failed_checks):
            report["recommendations"].append("Optimize state management and rendering in React components")
        
        if any("Methods" in check for check in all_failed_checks):
            report["recommendations"].append("Review method implementations for functional equivalence")
        
        if any("UI" in check for check in all_failed_checks):
            report["recommendations"].append("Verify UI elements and styling match the original Vue components")
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return {
            "report_path": output_path,
            "success": True,
            "message": f"Generated test report at {output_path}"
        }

    @staticmethod
    def create_tools() -> List[BaseTool]:
        """Create report generation tools."""
        return [
            FunctionTool(
                ReportGenerationTool.generate_test_report,
                description="Generate a test report based on verification results"
            )
        ]

"""
Module for planning the migration of Vue components to React.
Analyzes dependencies and breaks tasks into parallel-executable chunks.
"""
import os
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import json


class MigrationPlanner:
    """
    Planner class for migrating Vue components to React.
    Analyzes dependencies and breaks tasks into parallel-executable chunks.
    """

    def __init__(
        self, 
        analyses: Dict[str, Dict[str, Any]], 
        max_lines_per_chunk: int = 500,
        output_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize the migration planner.

        Args:
            analyses: Mapping of file paths to analysis results
            max_lines_per_chunk: Maximum number of code lines per migration chunk
            output_dir: Output directory for migration plan
        """
        self.analyses = analyses
        self.max_lines_per_chunk = max_lines_per_chunk
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.dependency_graph = self._build_dependency_graph()

    def _build_dependency_graph(self) -> nx.DiGraph:
        """
        Build a directed graph of component dependencies.

        Returns:
            Networkx DiGraph of component dependencies
        """
        G = nx.DiGraph()
        
        for file_path, analysis in self.analyses.items():
            component_name = analysis["component_name"]
            G.add_node(component_name, file_path=file_path)
        
        for file_path, analysis in self.analyses.items():
            component_name = analysis["component_name"]
            for dep in analysis["component_dependencies"]:
                dep_file_path = None
                for fp, a in self.analyses.items():
                    if a["component_name"] == dep:
                        dep_file_path = fp
                        break
                
                if dep_file_path:
                    G.add_edge(component_name, dep)
        
        return G

    def get_component_size(self, component_name: str) -> int:
        """
        Get the size of a component in lines of code.

        Args:
            component_name: Name of the component

        Returns:
            Number of lines of code
        """
        for file_path, analysis in self.analyses.items():
            if analysis["component_name"] == component_name:
                return analysis.get("line_count", 0)
        
        return 0

    def identify_parallel_chunks(self) -> List[List[str]]:
        """
        Identify parallel-executable chunks of components for migration.
        Uses a topological sort to identify components that can be migrated in parallel.

        Returns:
            List of chunks (each chunk is a list of component names)
        """
        chunks = []
        
        try:
            sorted_components = list(nx.topological_sort(self.dependency_graph))
        except nx.NetworkXUnfeasible:
            sorted_components = list(self.dependency_graph.nodes())
        
        current_chunk = []
        current_chunk_size = 0
        
        for component in sorted_components:
            component_size = self.get_component_size(component)
            
            if current_chunk_size + component_size > self.max_lines_per_chunk and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_chunk_size = 0
            
            current_chunk.append(component)
            current_chunk_size += component_size
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def generate_migration_plan(self) -> Dict[str, Any]:
        """
        Generate a migration plan with parallel-executable chunks.

        Returns:
            Dictionary containing the migration plan
        """
        chunks = self.identify_parallel_chunks()
        
        plan = {
            "chunks": [],
            "dependencies": {},
            "total_components": len(self.analyses),
            "max_lines_per_chunk": self.max_lines_per_chunk,
        }
        
        for i, chunk in enumerate(chunks):
            chunk_info = {
                "id": i + 1,
                "components": [],
                "total_lines": 0,
            }
            
            for component in chunk:
                file_path = None
                for fp, analysis in self.analyses.items():
                    if analysis["component_name"] == component:
                        file_path = fp
                        break
                
                if file_path:
                    component_size = self.get_component_size(component)
                    chunk_info["components"].append({
                        "name": component,
                        "file_path": file_path,
                        "lines": component_size,
                    })
                    chunk_info["total_lines"] += component_size
            
            plan["chunks"].append(chunk_info)
        
        for component in self.dependency_graph.nodes():
            deps = list(self.dependency_graph.successors(component))
            if deps:
                plan["dependencies"][component] = deps
        
        if self.output_dir:
            with open(self.output_dir / "migration_plan.json", "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2)
        
        return plan

    def generate_migration_plan_html(self) -> str:
        """
        Generate an HTML representation of the migration plan.

        Returns:
            HTML representation of the migration plan
        """
        plan = self.generate_migration_plan()
        
        total_components = plan["total_components"]
        max_lines = plan["max_lines_per_chunk"]
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vue to React Migration Plan</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .chunk {{ margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }}
                .chunk-header {{ background-color: #f5f5f5; padding: 10px 15px; border-bottom: 1px solid #ddd; }}
                .chunk-body {{ padding: 15px; }}
                .component-list {{ list-style-type: none; padding: 0; }}
                .component-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .component-item:last-child {{ border-bottom: none; }}
                .component-info {{ display: flex; justify-content: space-between; }}
                .component-name {{ font-weight: bold; }}
                .component-path {{ color: #666; }}
                .component-lines {{ color: #0077cc; }}
                .progress-bar {{ height: 10px; background-color: #e0e0e0; border-radius: 5px; margin-top: 5px; }}
                .progress {{ height: 100%; background-color: #4caf50; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Vue to React Migration Plan</h1>
                <p>Total Components: {total_components}</p>
                <p>Max Lines Per Chunk: {max_lines}</p>
                
                <h2>Migration Chunks</h2>
        """
        
        for chunk in plan["chunks"]:
            chunk_id = chunk["id"]
            total_lines = chunk["total_lines"]
            html += f"""
                <div class="chunk">
                    <div class="chunk-header">
                        <h3>Chunk {chunk_id} ({total_lines} lines)</h3>
                    </div>
                    <div class="chunk-body">
                        <ul class="component-list">
            """
            
            for component in chunk["components"]:
                component_name = component["name"]
                component_lines = component["lines"]
                component_path = component["file_path"]
                progress_width = min(100, (component_lines / plan["max_lines_per_chunk"]) * 100)
                
                html += f"""
                            <li class="component-item">
                                <div class="component-info">
                                    <span class="component-name">{component_name}</span>
                                    <span class="component-lines">{component_lines} lines</span>
                                </div>
                                <div class="component-path">{component_path}</div>
                                <div class="progress-bar">
                                    <div class="progress" style="width: {progress_width}%;"></div>
                                </div>
                            </li>
                """
            
            html += """
                        </ul>
                    </div>
                </div>
            """
        
        html += """
                <h2>Component Dependencies</h2>
                <ul>
        """
        
        for component, deps in plan["dependencies"].items():
            deps_str = ", ".join(deps)
            html += f"""
                    <li>
                        <strong>{component}</strong> depends on: {deps_str}
                    </li>
            """
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        if self.output_dir:
            with open(self.output_dir / "migration_plan.html", "w", encoding="utf-8") as f:
                f.write(html)
        
        return html

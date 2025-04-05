"""
Enhanced Vue to React converter that integrates file scanning, documentation generation,
and migration planning capabilities.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import json

from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat

from .constants import MAX_CONVERSION_ITERATIONS
from .knowledge_base import KnowledgeBase
from .agents import create_vue_to_react_team
from .file_scanner import FileScanner
from .doc_generator import DocumentationGenerator
from .migration_planner import MigrationPlanner


class EnhancedVueToReactConverter:
    """
    Enhanced system for converting Vue code to React using AutoGen agents.
    
    This class extends the original VueToReactConverter with:
    - Comprehensive file scanning for all files in a target directory
    - HTML documentation generation for files and features
    - Migration planning that analyzes dependencies and breaks tasks into chunks
    - Post-migration documentation generation
    
    The system supports multiple rounds of iterations if functionality differences are detected.
    """
    
    def __init__(
        self,
        model_client: ChatCompletionClient,
        knowledge_base: Optional[KnowledgeBase] = None,
        knowledge_base_path: Optional[str] = None,
        max_iterations: int = MAX_CONVERSION_ITERATIONS,
        max_lines_per_chunk: int = 500
    ):
        """
        Initialize the enhanced Vue to React converter.
        
        Args:
            model_client: The model client to use for the agents
            knowledge_base: Optional knowledge base instance
            knowledge_base_path: Optional path to a knowledge base file
            max_iterations: Maximum number of conversion iterations
            max_lines_per_chunk: Maximum number of code lines per migration chunk
        """
        self.model_client = model_client
        self.max_iterations = max_iterations
        self.max_lines_per_chunk = max_lines_per_chunk
        
        if knowledge_base:
            self.knowledge_base = knowledge_base
        elif knowledge_base_path and os.path.exists(knowledge_base_path):
            self.knowledge_base = KnowledgeBase.load_from_file(knowledge_base_path)
        else:
            self.knowledge_base = KnowledgeBase.create_default()
        
        self.team = create_vue_to_react_team(model_client, max_iterations)
    
    def save_knowledge_base(self, file_path: str) -> None:
        """
        Save the knowledge base to a file.
        
        Args:
            file_path: Path where the knowledge base should be saved
        """
        self.knowledge_base.save_to_file(file_path)
    
    async def analyze_project(
        self,
        source_dir: Union[str, Path],
        output_dir: Union[str, Path],
        ignore_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a Vue project directory and generate documentation.
        
        Args:
            source_dir: Directory containing Vue files
            output_dir: Directory where documentation should be saved
            ignore_patterns: Patterns to ignore (regex)
            
        Returns:
            Dict containing analysis results
        """
        source_dir = Path(source_dir)
        output_dir = Path(output_dir)
        
        docs_dir = output_dir / "docs"
        plan_dir = output_dir / "plan"
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(plan_dir, exist_ok=True)
        
        scanner = FileScanner(source_dir, ignore_patterns)
        vue_files, other_files = scanner.scan()
        
        print(f"Found {len(vue_files)} Vue files and {len(other_files)} other files")
        
        analyses = scanner.analyze_all_vue_files()
        
        analysis_path = output_dir / "analysis.json"
        scanner.save_analysis(analysis_path)
        
        doc_generator = DocumentationGenerator(docs_dir)
        doc_generator.save_documentation(analyses)
        
        planner = MigrationPlanner(analyses, self.max_lines_per_chunk, plan_dir)
        plan = planner.generate_migration_plan()
        planner.generate_migration_plan_html()
        
        return {
            "source_dir": str(source_dir),
            "output_dir": str(output_dir),
            "vue_files": len(vue_files),
            "other_files": len(other_files),
            "analysis_path": str(analysis_path),
            "docs_dir": str(docs_dir),
            "plan_dir": str(plan_dir),
            "plan": plan
        }
    
    async def convert_project(
        self,
        source_dir: Union[str, Path],
        output_dir: Union[str, Path],
        knowledge_base_path: Optional[str] = None,
        ignore_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convert a Vue project to React following the migration plan.
        
        Args:
            source_dir: Directory containing Vue files
            output_dir: Directory where React files should be saved
            knowledge_base_path: Optional path to a knowledge base file
            ignore_patterns: Patterns to ignore (regex)
            
        Returns:
            Dict containing conversion results
        """
        source_dir = Path(source_dir)
        output_dir = Path(output_dir)
        
        react_dir = output_dir / "react"
        docs_dir = output_dir / "docs"
        plan_dir = output_dir / "plan"
        os.makedirs(react_dir, exist_ok=True)
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(plan_dir, exist_ok=True)
        
        if not knowledge_base_path:
            kb_dir = output_dir / ".kb"
            os.makedirs(kb_dir, exist_ok=True)
            knowledge_base_path = str(kb_dir / "vue_to_react_kb.json")
            self.save_knowledge_base(knowledge_base_path)
        
        analysis_result = await self.analyze_project(source_dir, output_dir, ignore_patterns)
        
        analysis_path = output_dir / "analysis.json"
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        analyses = analysis_data["analysis"]
        
        plan_path = plan_dir / "migration_plan.json"
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
        
        results = []
        for chunk in plan["chunks"]:
            chunk_results = []
            for component in chunk["components"]:
                file_path = component["file_path"]
                result = await self.convert_file(file_path, str(react_dir), knowledge_base_path)
                chunk_results.append(result)
            
            results.append({
                "chunk_id": chunk["id"],
                "components": [c["name"] for c in chunk["components"]],
                "results": chunk_results
            })
        
        scanner = FileScanner(source_dir, ignore_patterns)
        _, other_files = scanner.scan()
        
        for file_path in other_files:
            rel_path = file_path.relative_to(source_dir)
            dest_path = react_dir / rel_path
            os.makedirs(dest_path.parent, exist_ok=True)
            
            try:
                with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())
            except Exception as e:
                print(f"Error copying {file_path}: {e}")
        
        doc_generator = DocumentationGenerator(docs_dir)
        doc_generator.save_post_migration_doc(analyses, react_dir)
        
        return {
            "source_dir": str(source_dir),
            "output_dir": str(output_dir),
            "react_dir": str(react_dir),
            "docs_dir": str(docs_dir),
            "plan_dir": str(plan_dir),
            "chunks_converted": len(results),
            "chunk_results": results
        }
    
    async def convert_file(
        self,
        vue_file_path: str,
        output_dir: str,
        knowledge_base_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert a Vue file to React.
        
        Args:
            vue_file_path: Path to the Vue file
            output_dir: Directory where the React file should be saved
            knowledge_base_path: Optional path to a knowledge base file
            
        Returns:
            Dict containing conversion results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if not knowledge_base_path:
            kb_dir = os.path.join(output_dir, ".kb")
            os.makedirs(kb_dir, exist_ok=True)
            knowledge_base_path = os.path.join(kb_dir, "vue_to_react_kb.json")
            self.save_knowledge_base(knowledge_base_path)
        
        initial_message = f"""
I need to convert a Vue component to React.

Vue file: {vue_file_path}
Output directory: {output_dir}
Knowledge base: {knowledge_base_path}

Please analyze the Vue component, convert it to React, verify the conversion, and generate a test report.
"""
        
        messages = []
        async for message in self.team.run_stream(task=initial_message):
            messages.append(message)
        
        report_path = None
        for message in messages:
            if "report_path" in str(message):
                content = str(message)
                if "Generated test report at " in content:
                    report_path = content.split("Generated test report at ")[1].split("\n")[0].strip()
        
        report = None
        if report_path and os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report = json.load(f)
        
        conversion_result = {
            "vue_file": vue_file_path,
            "output_dir": output_dir,
            "success": True,  # Simplified - in a real implementation, this would be based on the report
            "report_path": report_path,
            "report": report,
            "chat_history": messages
        }
        
        return conversion_result

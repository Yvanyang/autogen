import os
from typing import Dict, List, Any, Optional
import json

from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat

from .constants import MAX_CONVERSION_ITERATIONS
from .knowledge_base import KnowledgeBase
from .agents import create_vue_to_react_team


class VueToReactConverter:
    """
    A system for converting Vue code to React using AutoGen agents.
    
    This class orchestrates the conversion process using a team of specialized agents:
    - Code Analysis Agent: Evaluates the original Vue implementation
    - Conversion Agent: Performs the actual code transformation
    - Verification Agent: Compares pre and post conversion functionality
    - Report Generation Agent: Creates a test report
    
    The system supports multiple rounds of iterations if functionality differences are detected.
    """
    
    def __init__(
        self,
        model_client: ChatCompletionClient,
        knowledge_base: Optional[KnowledgeBase] = None,
        knowledge_base_path: Optional[str] = None,
        max_iterations: int = MAX_CONVERSION_ITERATIONS
    ):
        """
        Initialize the Vue to React converter.
        
        Args:
            model_client: The model client to use for the agents
            knowledge_base: Optional knowledge base instance
            knowledge_base_path: Optional path to a knowledge base file
            max_iterations: Maximum number of conversion iterations
        """
        self.model_client = model_client
        self.max_iterations = max_iterations
        
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
    
    async def convert_directory(
        self,
        vue_dir_path: str,
        output_dir: str,
        knowledge_base_path: Optional[str] = None,
        file_pattern: str = "*.vue"
    ) -> Dict[str, Any]:
        """
        Convert all Vue files in a directory to React.
        
        Args:
            vue_dir_path: Path to the directory containing Vue files
            output_dir: Directory where the React files should be saved
            knowledge_base_path: Optional path to a knowledge base file
            file_pattern: Pattern to match Vue files
            
        Returns:
            Dict containing conversion results
        """
        import glob
        
        os.makedirs(output_dir, exist_ok=True)
        
        if not knowledge_base_path:
            kb_dir = os.path.join(output_dir, ".kb")
            os.makedirs(kb_dir, exist_ok=True)
            knowledge_base_path = os.path.join(kb_dir, "vue_to_react_kb.json")
            self.save_knowledge_base(knowledge_base_path)
        
        vue_files = glob.glob(os.path.join(vue_dir_path, file_pattern))
        
        results = []
        for vue_file in vue_files:
            result = await self.convert_file(vue_file, output_dir, knowledge_base_path)
            results.append(result)
        
        conversion_result = {
            "vue_dir": vue_dir_path,
            "output_dir": output_dir,
            "total_files": len(vue_files),
            "successful_conversions": sum(1 for r in results if r["success"]),
            "failed_conversions": sum(1 for r in results if not r["success"]),
            "file_results": results
        }
        
        return conversion_result
    
    async def convert_large_file(
        self,
        vue_file_path: str,
        output_dir: str,
        chunk_size: int = 100,
        knowledge_base_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert a large Vue file to React by processing it in chunks.
        
        Args:
            vue_file_path: Path to the Vue file
            output_dir: Directory where the React file should be saved
            chunk_size: Number of lines to process in each chunk
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
        
        state_dir = os.path.join(output_dir, ".state")
        os.makedirs(state_dir, exist_ok=True)
        conversion_state_path = os.path.join(state_dir, f"{os.path.basename(vue_file_path)}.state.json")
        
        with open(vue_file_path, 'r') as f:
            lines = f.readlines()
        total_lines = len(lines)
        
        results = []
        for start_line in range(0, total_lines, chunk_size):
            end_line = min(start_line + chunk_size - 1, total_lines - 1)
            
            initial_message = f"""
I need to convert a chunk of a Vue component to React.

Vue file: {vue_file_path}
Chunk: lines {start_line} to {end_line} (of {total_lines} total lines)
Output directory: {output_dir}
Knowledge base: {knowledge_base_path}
Conversion state: {conversion_state_path}

Please analyze this chunk of the Vue component, convert it to React, and update the conversion state.
"""
            
            messages = []
            async for message in self.team.run_stream(task=initial_message):
                messages.append(message)
            
            chunk_result = {
                "vue_file": vue_file_path,
                "chunk_start_line": start_line,
                "chunk_end_line": end_line,
                "output_dir": output_dir,
                "success": True,  # Simplified
                "chat_history": messages
            }
            
            results.append(chunk_result)
        
        conversion_result = {
            "vue_file": vue_file_path,
            "output_dir": output_dir,
            "total_lines": total_lines,
            "chunks_processed": len(results),
            "successful_chunks": sum(1 for r in results if r["success"]),
            "failed_chunks": sum(1 for r in results if not r["success"]),
            "chunk_results": results
        }
        
        return conversion_result

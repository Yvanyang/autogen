"""Repository structure analyzer agent implementation."""

import os
import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseChatMessage,
    TextMessage,
)
from autogen_core import CancellationToken, Component, ComponentModel
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
)
from pydantic import BaseModel, Field
from typing_extensions import Self


class RepositoryStructure(BaseModel):
    """Repository structure analysis results."""
    
    repo_path: str = Field(description="Path to the repository")
    total_files: int = Field(description="Total number of files in the repository")
    total_directories: int = Field(description="Total number of directories in the repository")
    
    pages: List[str] = Field(description="List of identified pages/views", default_factory=list)
    total_pages: int = Field(description="Total number of pages/views", default=0)
    
    components: List[str] = Field(description="List of identified reusable components", default_factory=list)
    total_components: int = Field(description="Total number of reusable components", default=0)
    
    utilities: List[str] = Field(description="List of identified utility classes/functions", default_factory=list)
    total_utilities: int = Field(description="Total number of utility classes/functions", default=0)
    
    file_types: Dict[str, int] = Field(description="Count of files by extension", default_factory=dict)
    
    directory_structure: Dict[str, List[str]] = Field(
        description="Directory structure with files", default_factory=dict
    )


class StructureAnalyzerAgentConfig(BaseModel):
    """Configuration for StructureAnalyzerAgent."""

    name: str
    model_client: ComponentModel
    description: str | None = None


class StructureAnalyzerAgent(BaseChatAgent, Component[StructureAnalyzerAgentConfig]):
    """An agent that analyzes repository structure.
    
    This agent traverses the repository file system and categorizes files based on
    patterns and naming conventions to identify pages, components, and utilities.
    
    Args:
        name (str): The agent's name
        model_client (ChatCompletionClient): The model to use
        description (str): The agent's description. Defaults to DEFAULT_DESCRIPTION
        repo_path (str): The path to the repository to analyze. Defaults to the current working directory.
    """

    component_config_schema = StructureAnalyzerAgentConfig
    component_provider_override = "autogen_ext.agents.repo_doc.StructureAnalyzerAgent"

    DEFAULT_DESCRIPTION = "An agent that analyzes repository structure."

    DEFAULT_SYSTEM_MESSAGES = [
        SystemMessage(
            content="""
            You are a helpful AI Assistant specialized in analyzing code repository structures.
            You can identify pages, components, and utilities based on file patterns and naming conventions."""
        ),
    ]

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        description: str = DEFAULT_DESCRIPTION,
        repo_path: str = os.getcwd(),
    ) -> None:
        super().__init__(name, description)
        self._model_client = model_client
        self._repo_path = repo_path
        
        self._page_patterns = [
            r"pages?[/\\]",
            r"views?[/\\]",
            r"screens?[/\\]",
            r"routes?[/\\]",
            r"[A-Z][a-z]*Page\.[a-z]+$",
            r"[A-Z][a-z]*View\.[a-z]+$",
            r"[A-Z][a-z]*Screen\.[a-z]+$",
        ]
        
        self._component_patterns = [
            r"components?[/\\]",
            r"ui[/\\]",
            r"elements?[/\\]",
            r"[A-Z][a-z]*(Button|Card|Modal|Form|Input|Select|Dropdown|Table|List|Item)\.[a-z]+$",
        ]
        
        self._utility_patterns = [
            r"utils?[/\\]",
            r"helpers?[/\\]",
            r"lib[/\\]",
            r"common[/\\]",
            r"services?[/\\]",
            r"[a-z]+Utils?\.[a-z]+$",
            r"[a-z]+Helpers?\.[a-z]+$",
            r"[a-z]+Service\.[a-z]+$",
        ]
        
        self._ignore_extensions = {
            ".git", ".gitignore", ".DS_Store", ".env", ".vscode", ".idea",
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".pdf",
            ".md", ".txt", ".csv", ".json", ".lock", ".toml", ".yml", ".yaml",
        }
        
        self._ignore_directories = {
            ".git", "node_modules", "venv", "env", "dist", "build", "coverage",
            "__pycache__", ".vscode", ".idea", "assets", "public", "static",
        }

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def analyze_structure(self, cancellation_token: CancellationToken) -> RepositoryStructure:
        """Analyze the repository structure and categorize files."""
        structure = RepositoryStructure(
            repo_path=self._repo_path,
            total_files=0,
            total_directories=0,
        )
        
        self._traverse_repository(structure)
        
        self._categorize_files(structure)
        
        structure.total_pages = len(structure.pages)
        structure.total_components = len(structure.components)
        structure.total_utilities = len(structure.utilities)
        
        return structure

    def _traverse_repository(self, structure: RepositoryStructure) -> None:
        """Traverse the repository and build the directory structure."""
        total_files = 0
        total_directories = 0
        file_types = {}
        directory_structure = {}
        
        for root, dirs, files in os.walk(self._repo_path):
            dirs[:] = [d for d in dirs if d not in self._ignore_directories]
            
            rel_path = os.path.relpath(root, self._repo_path)
            if rel_path == ".":
                rel_path = ""
            
            directory_structure[rel_path] = []
            total_directories += 1
            
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in self._ignore_extensions:
                    continue
                
                file_path = os.path.join(rel_path, file) if rel_path else file
                directory_structure[rel_path].append(file)
                
                if ext in file_types:
                    file_types[ext] += 1
                else:
                    file_types[ext] = 1
                
                total_files += 1
        
        structure.total_files = total_files
        structure.total_directories = total_directories
        structure.file_types = file_types
        structure.directory_structure = directory_structure

    def _categorize_files(self, structure: RepositoryStructure) -> None:
        """Categorize files as pages, components, or utilities."""
        pages = []
        components = []
        utilities = []
        
        for directory, files in structure.directory_structure.items():
            dir_path = directory
            
            is_page_dir = any(re.search(pattern, dir_path, re.IGNORECASE) for pattern in self._page_patterns)
            is_component_dir = any(re.search(pattern, dir_path, re.IGNORECASE) for pattern in self._component_patterns)
            is_utility_dir = any(re.search(pattern, dir_path, re.IGNORECASE) for pattern in self._utility_patterns)
            
            for file in files:
                file_path = os.path.join(dir_path, file) if dir_path else file
                
                is_page_file = is_page_dir or any(re.search(pattern, file, re.IGNORECASE) for pattern in self._page_patterns)
                is_component_file = is_component_dir or any(re.search(pattern, file, re.IGNORECASE) for pattern in self._component_patterns)
                is_utility_file = is_utility_dir or any(re.search(pattern, file, re.IGNORECASE) for pattern in self._utility_patterns)
                
                if is_page_file:
                    pages.append(file_path)
                elif is_component_file:
                    components.append(file_path)
                elif is_utility_file:
                    utilities.append(file_path)
        
        structure.pages = pages
        structure.components = components
        structure.utilities = utilities

    def _to_config(self) -> StructureAnalyzerAgentConfig:
        """Convert current instance to config object."""
        return StructureAnalyzerAgentConfig(
            name=self.name,
            model_client=self._model_client.dump_component(),
            description=self.description,
        )

    @classmethod
    def _from_config(cls, config: StructureAnalyzerAgentConfig) -> Self:
        """Create instance from config object."""
        return cls(
            name=config.name,
            model_client=ChatCompletionClient.load_component(config.model_client),
            description=config.description or cls.DEFAULT_DESCRIPTION,
        )

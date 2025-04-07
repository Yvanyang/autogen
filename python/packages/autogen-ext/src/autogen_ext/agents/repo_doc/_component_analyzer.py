"""Repository component analyzer agent implementation."""

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

from ._structure_analyzer import RepositoryStructure


class ComponentAnalysis(BaseModel):
    """Component analysis results."""
    
    components: Dict[str, Dict[str, str]] = Field(
        description="Dictionary of components with their properties",
        default_factory=dict,
    )
    
    component_dependencies: Dict[str, List[str]] = Field(
        description="Dictionary of component dependencies",
        default_factory=dict,
    )
    
    component_usage: Dict[str, List[str]] = Field(
        description="Dictionary of where components are used",
        default_factory=dict,
    )
    
    component_categories: Dict[str, List[str]] = Field(
        description="Dictionary of component categories",
        default_factory=dict,
    )


class ComponentAnalyzerAgentConfig(BaseModel):
    """Configuration for ComponentAnalyzerAgent."""

    name: str
    model_client: ComponentModel
    description: str | None = None


class ComponentAnalyzerAgent(BaseChatAgent, Component[ComponentAnalyzerAgentConfig]):
    """An agent that analyzes repository components.
    
    This agent analyzes component files to extract properties, dependencies,
    usage patterns, and categorizes them by functionality.
    
    Args:
        name (str): The agent's name
        model_client (ChatCompletionClient): The model to use
        description (str): The agent's description. Defaults to DEFAULT_DESCRIPTION
        repo_path (str): The path to the repository to analyze. Defaults to the current working directory.
    """

    component_config_schema = ComponentAnalyzerAgentConfig
    component_provider_override = "autogen_ext.agents.repo_doc.ComponentAnalyzerAgent"

    DEFAULT_DESCRIPTION = "An agent that analyzes repository components."

    DEFAULT_SYSTEM_MESSAGES = [
        SystemMessage(
            content="""
            You are a helpful AI Assistant specialized in analyzing UI components in code repositories.
            You can identify component properties, dependencies, usage patterns, and categorize them by functionality."""
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
        
        self._component_categories = {
            "input": ["input", "textfield", "textarea", "form", "select", "dropdown", "checkbox", "radio", "switch"],
            "display": ["text", "image", "icon", "avatar", "badge", "card", "table", "list", "grid"],
            "navigation": ["menu", "navbar", "sidebar", "tab", "breadcrumb", "pagination", "link", "button"],
            "feedback": ["alert", "notification", "toast", "progress", "spinner", "skeleton", "modal", "dialog", "tooltip"],
            "layout": ["container", "row", "column", "grid", "flex", "box", "divider", "spacer", "section"],
        }
        
        self._property_patterns = {
            "props": r"(interface|type)\s+(\w+Props)",
            "state": r"(const|let|var)\s+\[(\w+),\s*set(\w+)\]",
            "handlers": r"(on\w+)|(handle\w+)",
            "styles": r"(styles|className|sx|style)",
        }

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def analyze_components(
        self, structure: RepositoryStructure, cancellation_token: CancellationToken
    ) -> ComponentAnalysis:
        """Analyze the repository components."""
        component_analysis = ComponentAnalysis()
        
        for component_file in structure.components:
            await self._analyze_component_file(
                component_file, component_analysis, structure, cancellation_token
            )
        
        self._categorize_components(component_analysis)
        
        return component_analysis

    async def _analyze_component_file(
        self,
        component_file: str,
        analysis: ComponentAnalysis,
        structure: RepositoryStructure,
        cancellation_token: CancellationToken,
    ) -> None:
        """Analyze a single component file."""
        file_path = os.path.join(self._repo_path, component_file)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            component_name = os.path.basename(component_file)
            component_name = os.path.splitext(component_name)[0]
            
            component_props = {
                "name": component_name,
                "file": component_file,
                "description": self._extract_component_description(content),
                "props": self._extract_component_props(content),
                "state": self._extract_component_state(content),
                "handlers": self._extract_component_handlers(content),
                "styles": self._extract_component_styles(content),
            }
            
            analysis.components[component_name] = component_props
            
            dependencies = self._extract_component_dependencies(content)
            analysis.component_dependencies[component_name] = dependencies
            
            usage = self._find_component_usage(component_name, structure)
            analysis.component_usage[component_name] = usage
            
        except Exception as e:
            print(f"Error analyzing component {component_file}: {str(e)}")

    def _extract_component_description(self, content: str) -> str:
        """Extract component description from JSDoc or comments."""
        jsdoc_match = re.search(r"/\*\*\s*([\s\S]*?)\s*\*/", content)
        if jsdoc_match:
            description = jsdoc_match.group(1)
            description = re.sub(r"^\s*\*\s*", "", description, flags=re.MULTILINE)
            description = re.sub(r"@\w+.*$", "", description, flags=re.MULTILINE)
            return description.strip()
        
        comment_match = re.search(r"//\s*(.*?)\s*\n\s*(export|function|class|const)", content)
        if comment_match:
            return comment_match.group(1).strip()
        
        return "No description available"

    def _extract_component_props(self, content: str) -> str:
        """Extract component props interface or type."""
        props_match = re.search(self._property_patterns["props"], content)
        if props_match:
            type_name = props_match.group(2)
            type_def_match = re.search(
                rf"{props_match.group(1)}\s+{type_name}\s*{{([^}}]*)}}", content
            )
            if type_def_match:
                return type_def_match.group(1).strip()
        
        return "No props defined"

    def _extract_component_state(self, content: str) -> str:
        """Extract component state variables."""
        state_vars = []
        
        for match in re.finditer(self._property_patterns["state"], content):
            state_name = match.group(2)
            state_vars.append(state_name)
        
        return ", ".join(state_vars) if state_vars else "No state variables defined"

    def _extract_component_handlers(self, content: str) -> str:
        """Extract component event handlers."""
        handlers = []
        
        for match in re.finditer(r"(const|function)\s+(\w+)\s*=?\s*(\(|=>)", content):
            handler_name = match.group(2)
            if re.match(r"(on\w+)|(handle\w+)", handler_name):
                handlers.append(handler_name)
        
        return ", ".join(handlers) if handlers else "No event handlers defined"

    def _extract_component_styles(self, content: str) -> str:
        """Extract component styling approach."""
        if "styled" in content or "css`" in content:
            return "Styled Components"
        elif "makeStyles" in content or "createStyles" in content:
            return "Material-UI Styles"
        elif "className=" in content:
            return "CSS Classes"
        elif "style=" in content:
            return "Inline Styles"
        else:
            return "No styling detected"

    def _extract_component_dependencies(self, content: str) -> List[str]:
        """Extract component dependencies from import statements."""
        dependencies = []
        
        for match in re.finditer(r"import\s+{([^}]*)}\s+from\s+['\"]([^'\"]*)['\"]", content):
            imported_items = match.group(1).split(",")
            for item in imported_items:
                item = item.strip()
                if item and not item.startswith("type "):
                    dependencies.append(item)
        
        for match in re.finditer(r"import\s+(\w+)\s+from\s+['\"]([^'\"]*)['\"]", content):
            dependencies.append(match.group(1))
        
        return dependencies

    def _find_component_usage(self, component_name: str, structure: RepositoryStructure) -> List[str]:
        """Find where the component is used in the repository."""
        usage = []
        
        for directory, files in structure.directory_structure.items():
            for file in files:
                file_path = os.path.join(self._repo_path, directory, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    import_pattern = rf"import\s+{{{component_name}}}\s+from"
                    import_pattern_alt = rf"import\s+{component_name}\s+from"
                    
                    tag_pattern = rf"<{component_name}[ >]"
                    
                    if (re.search(import_pattern, content) or 
                        re.search(import_pattern_alt, content) or 
                        re.search(tag_pattern, content)):
                        rel_path = os.path.join(directory, file)
                        usage.append(rel_path)
                
                except Exception:
                    pass
        
        return usage

    def _categorize_components(self, analysis: ComponentAnalysis) -> None:
        """Categorize components by their functionality."""
        categories = {category: [] for category in self._component_categories.keys()}
        
        for component_name, props in analysis.components.items():
            name_lower = component_name.lower()
            
            for category, keywords in self._component_categories.items():
                if any(keyword in name_lower for keyword in keywords):
                    categories[category].append(component_name)
                    break
            
            if not any(component_name in category_list for category_list in categories.values()):
                props_str = props.get("props", "").lower()
                handlers_str = props.get("handlers", "").lower()
                
                if any(keyword in props_str or keyword in handlers_str for keyword in ["value", "onChange", "onInput", "onSubmit"]):
                    categories["input"].append(component_name)
                elif any(keyword in props_str or keyword in handlers_str for keyword in ["onClick", "onNavigate", "href", "to"]):
                    categories["navigation"].append(component_name)
                elif any(keyword in props_str for keyword in ["message", "notification", "alert", "loading"]):
                    categories["feedback"].append(component_name)
                else:
                    categories["display"].append(component_name)
        
        analysis.component_categories = categories

    def _to_config(self) -> ComponentAnalyzerAgentConfig:
        """Convert current instance to config object."""
        return ComponentAnalyzerAgentConfig(
            name=self.name,
            model_client=self._model_client.dump_component(),
            description=self.description,
        )

    @classmethod
    def _from_config(cls, config: ComponentAnalyzerAgentConfig) -> Self:
        """Create instance from config object."""
        return cls(
            name=config.name,
            model_client=ChatCompletionClient.load_component(config.model_client),
            description=config.description or cls.DEFAULT_DESCRIPTION,
        )

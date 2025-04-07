"""Repository documentation generator agent implementation."""

import os
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
from ._component_analyzer import ComponentAnalysis
from ._page_analyzer import PageAnalysis, PageFlow
from ._interaction_analyzer import InteractionAnalysis


class DocumentationGeneratorAgentConfig(BaseModel):
    """Configuration for DocumentationGeneratorAgent."""

    name: str
    model_client: ComponentModel
    description: str | None = None


class DocumentationGeneratorAgent(BaseChatAgent, Component[DocumentationGeneratorAgentConfig]):
    """An agent that generates repository documentation.
    
    This agent generates comprehensive markdown documentation with diagrams
    based on the analysis results from other agents.
    
    Args:
        name (str): The agent's name
        model_client (ChatCompletionClient): The model to use
        description (str): The agent's description. Defaults to DEFAULT_DESCRIPTION
        repo_path (str): The path to the repository to analyze. Defaults to the current working directory.
    """

    component_config_schema = DocumentationGeneratorAgentConfig
    component_provider_override = "autogen_ext.agents.repo_doc.DocumentationGeneratorAgent"

    DEFAULT_DESCRIPTION = "An agent that generates repository documentation."

    DEFAULT_SYSTEM_MESSAGES = [
        SystemMessage(
            content="""
            You are a helpful AI Assistant specialized in generating documentation for code repositories.
            You can create comprehensive markdown documentation with diagrams based on repository analysis."""
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

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def generate_documentation(
        self,
        structure: RepositoryStructure,
        component_analysis: ComponentAnalysis,
        page_analysis: PageAnalysis,
        interaction_analysis: InteractionAnalysis,
        cancellation_token: CancellationToken,
    ) -> str:
        """Generate comprehensive markdown documentation."""
        overview = self._generate_overview(structure)
        structure_analysis = self._generate_structure_analysis(structure)
        component_docs = self._generate_component_documentation(component_analysis)
        page_docs = self._generate_page_documentation(
            page_analysis, component_analysis, interaction_analysis
        )
        
        documentation = "\n\n".join([
            overview,
            structure_analysis,
            component_docs,
            page_docs,
        ])
        
        return documentation

    def _generate_overview(self, structure: RepositoryStructure) -> str:
        """Generate repository overview section."""
        repo_name = os.path.basename(structure.repo_path)
        
        overview = f"""# {repo_name} Documentation


This documentation provides a comprehensive analysis of the {repo_name} repository structure, components, pages, and interactions.


- **Total Files**: {structure.total_files}
- **Total Directories**: {structure.total_directories}
- **Total Pages/Views**: {structure.total_pages}
- **Total Components**: {structure.total_components}
- **Total Utilities**: {structure.total_utilities}


| Extension | Count |
|-----------|-------|
"""
        
        for ext, count in structure.file_types.items():
            overview += f"| {ext} | {count} |\n"
        
        return overview

    def _generate_structure_analysis(self, structure: RepositoryStructure) -> str:
        """Generate repository structure analysis section."""
        structure_analysis = """


```
"""
        
        structure_analysis += self._generate_directory_tree(structure.directory_structure)
        structure_analysis += "```\n"
        
        structure_analysis += "\n### Pages/Views\n\n"
        if structure.pages:
            for page in structure.pages:
                structure_analysis += f"- `{page}`\n"
        else:
            structure_analysis += "No pages/views detected in the repository.\n"
        
        structure_analysis += "\n### Reusable Components\n\n"
        if structure.components:
            for component in structure.components:
                structure_analysis += f"- `{component}`\n"
        else:
            structure_analysis += "No reusable components detected in the repository.\n"
        
        structure_analysis += "\n### Shared Utility Classes\n\n"
        if structure.utilities:
            for utility in structure.utilities:
                structure_analysis += f"- `{utility}`\n"
        else:
            structure_analysis += "No shared utility classes detected in the repository.\n"
        
        return structure_analysis

    def _generate_directory_tree(self, directory_structure: Dict[str, List[str]]) -> str:
        """Generate a directory tree representation."""
        tree = ""
        
        sorted_dirs = sorted(directory_structure.keys())
        
        for directory in sorted_dirs:
            if directory == "":
                for file in sorted(directory_structure[directory]):
                    tree += f"{file}\n"
                continue
            
            depth = directory.count(os.path.sep)
            indent = "  " * depth
            
            dir_name = os.path.basename(directory)
            tree += f"{indent}{dir_name}/\n"
            
            for file in sorted(directory_structure[directory]):
                tree += f"{indent}  {file}\n"
        
        return tree

    def _generate_component_documentation(self, component_analysis: ComponentAnalysis) -> str:
        """Generate component documentation section."""
        component_docs = """


"""
        
        for category, components in component_analysis.component_categories.items():
            if components:
                component_docs += f"#### {category.capitalize()} Components\n\n"
                for component in components:
                    component_docs += f"- `{component}`\n"
                component_docs += "\n"
        
        component_docs += "### Component Details\n\n"
        
        for component_name, props in component_analysis.components.items():
            component_docs += f"#### {component_name}\n\n"
            
            component_docs += f"- **File**: `{props.get('file', '')}`\n"
            component_docs += f"- **Description**: {props.get('description', 'No description available')}\n"
            
            props_str = props.get('props', '')
            if props_str and props_str != "No props defined":
                component_docs += "- **Props**:\n```\n"
                component_docs += props_str + "\n```\n"
            else:
                component_docs += "- **Props**: None\n"
            
            state_str = props.get('state', '')
            if state_str and state_str != "No state variables defined":
                component_docs += f"- **State**: {state_str}\n"
            
            handlers_str = props.get('handlers', '')
            if handlers_str and handlers_str != "No event handlers defined":
                component_docs += f"- **Event Handlers**: {handlers_str}\n"
            
            styles_str = props.get('styles', '')
            if styles_str:
                component_docs += f"- **Styling**: {styles_str}\n"
            
            dependencies = component_analysis.component_dependencies.get(component_name, [])
            if dependencies:
                component_docs += "- **Dependencies**:\n"
                for dependency in dependencies:
                    component_docs += f"  - `{dependency}`\n"
            
            usage = component_analysis.component_usage.get(component_name, [])
            if usage:
                component_docs += "- **Used in**:\n"
                for file in usage:
                    component_docs += f"  - `{file}`\n"
            
            component_docs += "\n"
        
        return component_docs

    def _generate_page_documentation(
        self,
        page_analysis: PageAnalysis,
        component_analysis: ComponentAnalysis,
        interaction_analysis: InteractionAnalysis,
    ) -> str:
        """Generate page documentation section."""
        page_docs = """

"""
        
        page_docs += "### Page Navigation Flowchart\n\n"
        page_docs += self._generate_navigation_flowchart(page_analysis.page_flows)
        
        page_docs += "\n### Page Details\n\n"
        
        for page_name, props in page_analysis.pages.items():
            page_docs += f"#### {page_name}\n\n"
            
            page_docs += f"- **File**: `{props.get('file', '')}`\n"
            page_docs += f"- **Description**: {props.get('description', 'No description available')}\n"
            page_docs += f"- **Route**: `{props.get('route', '')}`\n"
            page_docs += f"- **Title**: {props.get('title', 'Untitled')}\n"
            
            params = page_analysis.page_parameters.get(page_name, [])
            if params:
                page_docs += "- **URL Parameters**:\n"
                for param in params:
                    page_docs += f"  - `{param}`\n"
            
            components = page_analysis.page_components.get(page_name, [])
            if components:
                page_docs += "- **Components**:\n"
                for component in components:
                    page_docs += f"  - `{component}`\n"
            
            interactions = interaction_analysis.interactions.get(page_name, [])
            if interactions:
                page_docs += "- **Interactions**:\n"
                for interaction in interactions:
                    page_docs += f"  - **{interaction.event}** on `{interaction.component}` handled by `{interaction.handler}`\n"
                    page_docs += f"    - {interaction.description}\n"
                    page_docs += "    - Effects:\n"
                    for effect in interaction.effects:
                        page_docs += f"      - {effect}\n"
            
            interaction_flows = interaction_analysis.interaction_flows.get(page_name, {})
            if interaction_flows:
                page_docs += "- **Interaction Flow**:\n\n"
                page_docs += self._generate_interaction_flowchart(page_name, interaction_flows)
            
            page_docs += "\n"
        
        return page_docs

    def _generate_navigation_flowchart(self, page_flows: List[PageFlow]) -> str:
        """Generate a Mermaid.js flowchart for page navigation."""
        flowchart = "```mermaid\nflowchart TD\n"
        
        processed_flows = set()
        
        for flow in page_flows:
            flow_key = f"{flow.source}->{flow.target}"
            
            if flow_key not in processed_flows:
                source_id = flow.source.replace(" ", "_")
                target_id = flow.target.replace(" ", "_")
                
                flowchart += f"    {source_id}[{flow.source}] --> |{flow.trigger}| {target_id}[{flow.target}]\n"
                
                processed_flows.add(flow_key)
        
        flowchart += "```"
        
        return flowchart

    def _generate_interaction_flowchart(self, page_name: str, interaction_flows: Dict[str, List[str]]) -> str:
        """Generate a Mermaid.js flowchart for interaction flows."""
        flowchart = "```mermaid\nflowchart LR\n"
        
        page_id = page_name.replace(" ", "_")
        flowchart += f"    {page_id}[{page_name}]\n"
        
        for component, flows in interaction_flows.items():
            component_id = component.replace(" ", "_")
            flowchart += f"    {component_id}[{component}]\n"
            
            flowchart += f"    {page_id} --> {component_id}\n"
            
            for i, flow in enumerate(flows):
                flow_id = f"{component_id}_flow_{i}"
                flowchart += f"    {flow_id}[{flow}]\n"
                flowchart += f"    {component_id} --> {flow_id}\n"
        
        flowchart += "```"
        
        return flowchart

    def _to_config(self) -> DocumentationGeneratorAgentConfig:
        """Convert current instance to config object."""
        return DocumentationGeneratorAgentConfig(
            name=self.name,
            model_client=self._model_client.dump_component(),
            description=self.description,
        )

    @classmethod
    def _from_config(cls, config: DocumentationGeneratorAgentConfig) -> Self:
        """Create instance from config object."""
        return cls(
            name=config.name,
            model_client=ChatCompletionClient.load_component(config.model_client),
            description=config.description or cls.DEFAULT_DESCRIPTION,
        )

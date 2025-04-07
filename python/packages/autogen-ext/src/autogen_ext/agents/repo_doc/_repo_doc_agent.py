"""Repository documentation agent implementation."""

import os
from typing import List, Optional, Sequence, Tuple

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseChatMessage,
    TextMessage,
)
from autogen_core import CancellationToken, Component, ComponentModel, FunctionCall
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
)
from pydantic import BaseModel
from typing_extensions import Self

from ._structure_analyzer import StructureAnalyzerAgent
from ._component_analyzer import ComponentAnalyzerAgent
from ._page_analyzer import PageAnalyzerAgent
from ._interaction_analyzer import InteractionAnalyzerAgent
from ._documentation_generator import DocumentationGeneratorAgent


class RepoDocAgentConfig(BaseModel):
    """Configuration for RepoDocAgent."""

    name: str
    model_client: ComponentModel
    description: str | None = None


class RepoDocAgent(BaseChatAgent, Component[RepoDocAgentConfig]):
    """An agent that analyzes a repository and generates comprehensive documentation.

    This agent coordinates a team of specialized agents to analyze repository structure,
    components, pages, and interactions, then generates markdown documentation with diagrams.

    Args:
        name (str): The agent's name
        model_client (ChatCompletionClient): The model to use (must be tool-use enabled)
        description (str): The agent's description. Defaults to DEFAULT_DESCRIPTION
        repo_path (str): The path to the repository to analyze. Defaults to the current working directory.
    """

    component_config_schema = RepoDocAgentConfig
    component_provider_override = "autogen_ext.agents.repo_doc.RepoDocAgent"

    DEFAULT_DESCRIPTION = "An agent that analyzes repositories and generates documentation."

    DEFAULT_SYSTEM_MESSAGES = [
        SystemMessage(
            content="""
            You are a helpful AI Assistant specialized in analyzing code repositories and generating documentation.
            When given a repository path, you will analyze its structure, components, pages, and interactions,
            then generate comprehensive markdown documentation with diagrams."""
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
        self._chat_history: List[BaseChatMessage] = []
        self._repo_path = repo_path
        
        self._structure_analyzer = StructureAnalyzerAgent(
            name=f"{name}_structure_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        self._component_analyzer = ComponentAnalyzerAgent(
            name=f"{name}_component_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        self._page_analyzer = PageAnalyzerAgent(
            name=f"{name}_page_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        self._interaction_analyzer = InteractionAnalyzerAgent(
            name=f"{name}_interaction_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        self._documentation_generator = DocumentationGeneratorAgent(
            name=f"{name}_documentation_generator",
            model_client=model_client,
            repo_path=repo_path,
        )

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def on_messages(self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken) -> Response:
        """Process incoming messages and generate a response."""
        for chat_message in messages:
            self._chat_history.append(chat_message)
        
        try:
            repo_path = self._extract_repo_path(messages[-1].content)
            if repo_path:
                self._repo_path = repo_path
                self._update_analyzer_paths(repo_path)
            
            documentation = await self._generate_documentation(cancellation_token)
            
            response_message = TextMessage(
                content=documentation,
                source=self.name,
            )
            
            return Response(chat_message=response_message)
        
        except Exception as e:
            error_message = f"Error generating repository documentation: {str(e)}"
            return Response(chat_message=TextMessage(content=error_message, source=self.name))

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """Reset the agent state."""
        self._chat_history.clear()

    def _extract_repo_path(self, message_content: str) -> Optional[str]:
        """Extract repository path from message content if provided."""
        if "path:" in message_content.lower():
            lines = message_content.split("\n")
            for line in lines:
                if "path:" in line.lower():
                    path = line.split("path:", 1)[1].strip()
                    if os.path.exists(path):
                        return path
        return None

    def _update_analyzer_paths(self, repo_path: str) -> None:
        """Update repository paths for all analyzer agents."""
        self._structure_analyzer._repo_path = repo_path
        self._component_analyzer._repo_path = repo_path
        self._page_analyzer._repo_path = repo_path
        self._interaction_analyzer._repo_path = repo_path
        self._documentation_generator._repo_path = repo_path

    async def _generate_documentation(self, cancellation_token: CancellationToken) -> str:
        """Coordinate the analysis process and generate documentation."""
        structure_analysis = await self._structure_analyzer.analyze_structure(cancellation_token)
        
        component_analysis = await self._component_analyzer.analyze_components(
            structure_analysis, cancellation_token
        )
        
        page_analysis = await self._page_analyzer.analyze_pages(
            structure_analysis, component_analysis, cancellation_token
        )
        
        interaction_analysis = await self._interaction_analyzer.analyze_interactions(
            structure_analysis, component_analysis, page_analysis, cancellation_token
        )
        
        documentation = await self._documentation_generator.generate_documentation(
            structure_analysis, component_analysis, page_analysis, interaction_analysis, cancellation_token
        )
        
        return documentation

    def _to_config(self) -> RepoDocAgentConfig:
        """Convert current instance to config object."""
        return RepoDocAgentConfig(
            name=self.name,
            model_client=self._model_client.dump_component(),
            description=self.description,
        )

    @classmethod
    def _from_config(cls, config: RepoDocAgentConfig) -> Self:
        """Create instance from config object."""
        return cls(
            name=config.name,
            model_client=ChatCompletionClient.load_component(config.model_client),
            description=config.description or cls.DEFAULT_DESCRIPTION,
        )

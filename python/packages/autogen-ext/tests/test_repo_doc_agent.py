"""Tests for the repository documentation agent."""

import os
import pytest
from unittest.mock import patch, MagicMock

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.repo_doc import (
    RepoDocAgent,
    StructureAnalyzerAgent,
    ComponentAnalyzerAgent,
    PageAnalyzerAgent,
    InteractionAnalyzerAgent,
    DocumentationGeneratorAgent,
)


class TestRepoDocAgent:
    """Test the repository documentation agent."""

    @pytest.fixture
    def model_client(self):
        """Create a mock model client."""
        mock_client = MagicMock(spec=ChatCompletionClient)
        mock_client.model_info = {"vision": False}
        return mock_client

    @pytest.fixture
    def repo_path(self):
        """Get the test repository path."""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_structure_analyzer_initialization(self, model_client, repo_path):
        """Test the structure analyzer agent initialization."""
        agent = StructureAnalyzerAgent(
            name="test_structure_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        assert agent.name == "test_structure_analyzer"
        assert agent._repo_path == repo_path

    def test_component_analyzer_initialization(self, model_client, repo_path):
        """Test the component analyzer agent initialization."""
        agent = ComponentAnalyzerAgent(
            name="test_component_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        assert agent.name == "test_component_analyzer"
        assert agent._repo_path == repo_path

    def test_page_analyzer_initialization(self, model_client, repo_path):
        """Test the page analyzer agent initialization."""
        agent = PageAnalyzerAgent(
            name="test_page_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        assert agent.name == "test_page_analyzer"
        assert agent._repo_path == repo_path

    def test_interaction_analyzer_initialization(self, model_client, repo_path):
        """Test the interaction analyzer agent initialization."""
        agent = InteractionAnalyzerAgent(
            name="test_interaction_analyzer",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        assert agent.name == "test_interaction_analyzer"
        assert agent._repo_path == repo_path

    def test_documentation_generator_initialization(self, model_client, repo_path):
        """Test the documentation generator agent initialization."""
        agent = DocumentationGeneratorAgent(
            name="test_documentation_generator",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        assert agent.name == "test_documentation_generator"
        assert agent._repo_path == repo_path

    def test_repo_doc_agent_initialization(self, model_client, repo_path):
        """Test the repository documentation agent initialization."""
        agent = RepoDocAgent(
            name="test_repo_doc",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        assert agent.name == "test_repo_doc"
        assert agent._repo_path == repo_path
        assert isinstance(agent._structure_analyzer, StructureAnalyzerAgent)
        assert isinstance(agent._component_analyzer, ComponentAnalyzerAgent)
        assert isinstance(agent._page_analyzer, PageAnalyzerAgent)
        assert isinstance(agent._interaction_analyzer, InteractionAnalyzerAgent)
        assert isinstance(agent._documentation_generator, DocumentationGeneratorAgent)

    @pytest.mark.asyncio
    async def test_extract_repo_path(self, model_client, repo_path):
        """Test extracting repository path from message content."""
        agent = RepoDocAgent(
            name="test_repo_doc",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        message_content = f"Please analyze the repository at path: {repo_path}"
        extracted_path = agent._extract_repo_path(message_content)
        assert extracted_path == repo_path
        
        message_content = "Please analyze the repository at path: /invalid/path"
        extracted_path = agent._extract_repo_path(message_content)
        assert extracted_path is None

    @pytest.mark.asyncio
    @patch.object(StructureAnalyzerAgent, "analyze_structure")
    @patch.object(ComponentAnalyzerAgent, "analyze_components")
    @patch.object(PageAnalyzerAgent, "analyze_pages")
    @patch.object(InteractionAnalyzerAgent, "analyze_interactions")
    @patch.object(DocumentationGeneratorAgent, "generate_documentation")
    async def test_generate_documentation(
        self,
        mock_generate_documentation,
        mock_analyze_interactions,
        mock_analyze_pages,
        mock_analyze_components,
        mock_analyze_structure,
        model_client,
        repo_path,
    ):
        """Test generating documentation."""
        mock_structure = MagicMock()
        mock_components = MagicMock()
        mock_pages = MagicMock()
        mock_interactions = MagicMock()
        mock_documentation = "# Test Documentation"
        
        mock_analyze_structure.return_value = mock_structure
        mock_analyze_components.return_value = mock_components
        mock_analyze_pages.return_value = mock_pages
        mock_analyze_interactions.return_value = mock_interactions
        mock_generate_documentation.return_value = mock_documentation
        
        agent = RepoDocAgent(
            name="test_repo_doc",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        cancellation_token = CancellationToken()
        result = await agent._generate_documentation(cancellation_token)
        
        mock_analyze_structure.assert_called_once_with(cancellation_token)
        mock_analyze_components.assert_called_once_with(mock_structure, cancellation_token)
        mock_analyze_pages.assert_called_once_with(mock_structure, mock_components, cancellation_token)
        mock_analyze_interactions.assert_called_once_with(
            mock_structure, mock_components, mock_pages, cancellation_token
        )
        mock_generate_documentation.assert_called_once_with(
            mock_structure, mock_components, mock_pages, mock_interactions, cancellation_token
        )
        
        assert result == mock_documentation

    @pytest.mark.asyncio
    @patch.object(RepoDocAgent, "_generate_documentation")
    async def test_on_messages(self, mock_generate_documentation, model_client, repo_path):
        """Test processing messages."""
        mock_documentation = "# Test Documentation"
        mock_generate_documentation.return_value = mock_documentation
        
        agent = RepoDocAgent(
            name="test_repo_doc",
            model_client=model_client,
            repo_path=repo_path,
        )
        
        message = TextMessage(content="Please analyze the repository", source="user")
        
        cancellation_token = CancellationToken()
        response = await agent.on_messages([message], cancellation_token)
        
        mock_generate_documentation.assert_called_once_with(cancellation_token)
        
        assert isinstance(response.chat_message, TextMessage)
        assert response.chat_message.content == mock_documentation
        assert response.chat_message.source == "test_repo_doc"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

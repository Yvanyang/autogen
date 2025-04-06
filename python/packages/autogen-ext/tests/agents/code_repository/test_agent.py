import os
import shutil
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from autogen_core import Component
from autogen_ext.agents.code_repository.agent import CodeRepositoryAgent, CodeRepositoryAgentConfig
from autogen_ext.agents.code_repository.memory import CodeRepositoryMemory

@pytest.fixture
def temp_dir():
    """Create a temporary directory for the test."""
    test_dir = tempfile.mkdtemp()
    
    repo_dir = os.path.join(test_dir, "test_repo")
    os.makedirs(repo_dir)
    
    with open(os.path.join(repo_dir, "test.py"), "w") as f:
        f.write("print('Hello, World!')")
    
    yield repo_dir
    
    shutil.rmtree(test_dir)

@pytest.fixture
def db_dir():
    """Create a temporary directory for the database."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir)

@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    mock_client = MagicMock()
    mock_client.dump_component = MagicMock(return_value=MagicMock(dict=MagicMock(return_value={"type": "mock_client"})))
    return mock_client

@pytest.mark.asyncio
async def test_code_repository_agent_initialization(temp_dir, db_dir, mock_model_client):
    """Test initialization of CodeRepositoryAgent."""
    with patch("autogen_core._component_config.ComponentLoader.load_component", return_value=mock_model_client):
        agent = CodeRepositoryAgent(
            config=CodeRepositoryAgentConfig(
                name="test_agent",
                repository_path=temp_dir,
                persistence_path=db_dir,
                model_client={"type": "mock_client"},
            )
        )
        
        assert agent._config.name == "test_agent"
        assert agent._config.repository_path == temp_dir
        assert agent._config.persistence_path == db_dir
        
        await agent.close()

@pytest.mark.asyncio
async def test_code_repository_agent_prepare(temp_dir, db_dir, mock_model_client):
    """Test preparing the agent."""
    with patch("autogen_core._component_config.ComponentLoader.load_component", return_value=mock_model_client), \
         patch("autogen_ext.agents.code_repository.agent.AssistantAgent") as mock_assistant:
        
        mock_memory = AsyncMock()
        mock_memory.is_vectorized = AsyncMock(return_value=False)
        mock_memory.vectorize_repository = AsyncMock(return_value=5)
        
        with patch("autogen_ext.agents.code_repository.agent.CodeRepositoryMemory", return_value=mock_memory):
            agent = CodeRepositoryAgent(
                config=CodeRepositoryAgentConfig(
                    name="test_agent",
                    repository_path=temp_dir,
                    persistence_path=db_dir,
                    model_client={"type": "mock_client"},
                )
            )
            
            result = await agent.prepare()
            
            assert result is True
            
            mock_memory.is_vectorized.assert_called_once()
            mock_memory.vectorize_repository.assert_called_once()
            
            mock_assistant.assert_called_once()
            
            await agent.close()

@pytest.mark.asyncio
async def test_code_repository_agent_run(temp_dir, db_dir, mock_model_client):
    """Test running a query with the agent."""
    with patch("autogen_core._component_config.ComponentLoader.load_component", return_value=mock_model_client):
        mock_assistant = AsyncMock()
        mock_assistant.run = AsyncMock(return_value="Test response")
        
        mock_memory = AsyncMock()
        mock_memory.is_vectorized = AsyncMock(return_value=True)
        
        with patch("autogen_ext.agents.code_repository.agent.AssistantAgent", return_value=mock_assistant), \
             patch("autogen_ext.agents.code_repository.agent.CodeRepositoryMemory", return_value=mock_memory):
            
            agent = CodeRepositoryAgent(
                config=CodeRepositoryAgentConfig(
                    name="test_agent",
                    repository_path=temp_dir,
                    persistence_path=db_dir,
                    model_client={"type": "mock_client"},
                )
            )
            
            await agent.prepare()
            
            response = await agent.run("How does this code work?")
            
            assert response == "Test response"
            
            mock_assistant.run.assert_called_once_with(task="How does this code work?")
            
            await agent.close()

"""Tests for the commit analysis agent."""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import git
import pytest
from autogen_core import Component
from autogen_ext.agents.commit_analysis.agent import (
    CommitAnalysisAgent,
    CommitAnalysisConfig,
    CommitInfo,
    FileChange,
    TestItem,
    TestReport,
)


@pytest.fixture
def temp_repo():
    """Create a temporary git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo_path = os.path.join(temp_dir, "test_repo")
    os.makedirs(repo_path)
    
    repo = git.Repo.init(repo_path)
    
    src_dir = os.path.join(repo_path, "src")
    tests_dir = os.path.join(repo_path, "tests")
    os.makedirs(src_dir)
    os.makedirs(tests_dir)
    
    with open(os.path.join(src_dir, "main.py"), "w") as f:
        f.write("def hello_world():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello_world()")
    
    with open(os.path.join(src_dir, "utils.py"), "w") as f:
        f.write("def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b")
    
    with open(os.path.join(tests_dir, "test_main.py"), "w") as f:
        f.write("from src.main import hello_world\n\ndef test_hello_world():\n    # Just test that it runs without error\n    hello_world()")
    
    with open(os.path.join(tests_dir, "test_utils.py"), "w") as f:
        f.write("from src.utils import add, subtract\n\ndef test_add():\n    assert add(1, 2) == 3\n\ndef test_subtract():\n    assert subtract(5, 3) == 2")
    
    repo.git.add(A=True)
    repo.git.commit(m="Initial commit")
    
    with open(os.path.join(src_dir, "utils.py"), "w") as f:
        f.write("def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n\ndef multiply(a, b):\n    return a * b")
    
    repo.git.add(A=True)
    repo.git.commit(m="Add multiply function")
    
    yield repo_path
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def db_dir():
    """Create a temporary directory for the database."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    mock_client = MagicMock()
    mock_client.create = AsyncMock(return_value="This is a mock response")
    
    mock_component = MagicMock()
    mock_component.model_dump = MagicMock(return_value={
        "provider": "mock",
        "type": "model_client",
        "config": {}
    })
    
    mock_client.dump_component = MagicMock(return_value=mock_component)
    return mock_client


@pytest.mark.asyncio
async def test_commit_analysis_agent_initialization(temp_repo, db_dir, mock_model_client):
    """Test initialization of CommitAnalysisAgent."""
    agent = CommitAnalysisAgent(
        config=CommitAnalysisConfig(
            name="test_agent",
            repository_path=temp_repo,
            persistence_path=db_dir,
            model_client={
                "provider": "mock",
                "type": "model_client",
                "config": {"model": "mock-model"}
            },
        )
    )
    
    mock_code_repo_agent = MagicMock()
    mock_code_repo_agent.prepare = AsyncMock(return_value=True)
    mock_code_repo_agent.run = AsyncMock(return_value="Mock response")
    mock_code_repo_agent.close = AsyncMock()
    
    
    assert agent._config.name == "test_agent"
    assert agent._config.repository_path == temp_repo
    
    with patch("autogen_ext.agents.commit_analysis.agent.CodeRepositoryAgent", return_value=mock_code_repo_agent):
        await agent.prepare()
    
    mock_code_repo_agent.prepare.assert_called_once()
    
    await agent.close()
    
    mock_code_repo_agent.close.assert_called_once()


@pytest.mark.asyncio
async def test_get_file_changes(temp_repo, db_dir, mock_model_client):
    """Test getting file changes from a commit."""
    agent = CommitAnalysisAgent(
        config=CommitAnalysisConfig(
            name="test_agent",
            repository_path=temp_repo,
            persistence_path=db_dir,
            model_client={
                "provider": "mock",
                "type": "model_client",
                "config": {"model": "mock-model"}
            },
        )
    )
    
    mock_code_repo_agent = MagicMock()
    mock_code_repo_agent.prepare = AsyncMock(return_value=True)
    mock_code_repo_agent.run = AsyncMock(return_value="Mock response")
    mock_code_repo_agent.close = AsyncMock()
    
    agent._code_repo_agent = mock_code_repo_agent
    
    await agent.prepare()
    
    repo = git.Repo(temp_repo)
    latest_commit = repo.head.commit
    
    file_changes = await agent._get_file_changes(latest_commit.hexsha)
    
    assert len(file_changes) == 1
    assert file_changes[0].file_path == "src/utils.py"
    assert file_changes[0].change_type == "modified"
    
    await agent.close()
    
    mock_code_repo_agent.close.assert_called_once()


@pytest.mark.asyncio
async def test_find_test_items(temp_repo, db_dir, mock_model_client):
    """Test finding test items for file changes."""
    agent = CommitAnalysisAgent(
        config=CommitAnalysisConfig(
            name="test_agent",
            repository_path=temp_repo,
            persistence_path=db_dir,
            model_client={
                "provider": "mock",
                "type": "model_client",
                "config": {"model": "mock-model"}
            },
        )
    )
    
    mock_code_repo_agent = MagicMock()
    mock_code_repo_agent.prepare = AsyncMock(return_value=True)
    mock_code_repo_agent.run = AsyncMock(return_value="Mock response")
    mock_code_repo_agent.close = AsyncMock()
    
    agent._code_repo_agent = mock_code_repo_agent
    
    await agent.prepare()
    
    commit_info = CommitInfo(
        commit_hash="1234567890",
        author="Test Author",
        date="2025-04-07 10:00:00",
        message="Test commit message",
        files_changed=["src/utils.py"]
    )
    
    file_changes = [
        FileChange(
            file_path="src/utils.py",
            change_type="modified",
            lines_added=3,
            lines_removed=0,
        )
    ]
    
    mock_memory = MagicMock()
    mock_memory.query = AsyncMock(return_value=MagicMock(results=[]))
    mock_code_repo_agent._code_repo_memory = mock_memory
    
    test_items = await agent._find_test_items(commit_info, file_changes)
    
    assert len(test_items) > 0
    
    test_utils_items = [item for item in test_items if "test_utils.py" in item.test_path]
    assert len(test_utils_items) > 0
    
    await agent.close()
    
    mock_code_repo_agent.close.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_commit(temp_repo, db_dir, mock_model_client):
    """Test analyzing a commit."""
    agent = CommitAnalysisAgent(
        config=CommitAnalysisConfig(
            name="test_agent",
            repository_path=temp_repo,
            persistence_path=db_dir,
            model_client={
                "provider": "mock",
                "type": "model_client",
                "config": {"model": "mock-model"}
            },
        )
    )
    
    mock_code_repo_agent = MagicMock()
    mock_code_repo_agent.prepare = AsyncMock(return_value=True)
    mock_code_repo_agent.run = AsyncMock(return_value="Mock response")
    mock_code_repo_agent.close = AsyncMock()
    
    mock_memory = MagicMock()
    mock_memory.query = AsyncMock(return_value=MagicMock(results=[]))
    mock_code_repo_agent._code_repo_memory = mock_memory
    
    agent._code_repo_agent = mock_code_repo_agent
    
    await agent.prepare()
    
    repo = git.Repo(temp_repo)
    latest_commit = repo.head.commit
    
    report = await agent.analyze_commit(latest_commit.hexsha)
    
    assert isinstance(report, TestReport)
    assert report.commit_info.commit_hash == latest_commit.hexsha
    assert report.commit_info.message.strip() == "Add multiply function"
    assert len(report.file_changes) == 1
    assert report.file_changes[0].file_path == "src/utils.py"
    assert len(report.test_items) > 0
    
    await agent.close()
    
    mock_code_repo_agent.close.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_latest_commit(temp_repo, db_dir, mock_model_client):
    """Test analyzing the latest commit."""
    agent = CommitAnalysisAgent(
        config=CommitAnalysisConfig(
            name="test_agent",
            repository_path=temp_repo,
            persistence_path=db_dir,
            model_client={
                "provider": "mock",
                "type": "model_client",
                "config": {"model": "mock-model"}
            },
        )
    )
    
    mock_code_repo_agent = MagicMock()
    mock_code_repo_agent.prepare = AsyncMock(return_value=True)
    mock_code_repo_agent.run = AsyncMock(return_value="Mock response")
    mock_code_repo_agent.close = AsyncMock()
    
    mock_memory = MagicMock()
    mock_memory.query = AsyncMock(return_value=MagicMock(results=[]))
    mock_code_repo_agent._code_repo_memory = mock_memory
    
    agent._code_repo_agent = mock_code_repo_agent
    
    await agent.prepare()
    
    report = await agent.analyze_latest_commit()
    
    assert isinstance(report, TestReport)
    assert report.commit_info.message.strip() == "Add multiply function"
    assert len(report.file_changes) == 1
    assert report.file_changes[0].file_path == "src/utils.py"
    assert len(report.test_items) > 0
    
    await agent.close()
    
    mock_code_repo_agent.close.assert_called_once()


@pytest.mark.asyncio
async def test_generate_report(temp_repo, db_dir, mock_model_client):
    """Test generating a report."""
    agent = CommitAnalysisAgent(
        config=CommitAnalysisConfig(
            name="test_agent",
            repository_path=temp_repo,
            persistence_path=db_dir,
            model_client={
                "provider": "mock",
                "type": "model_client",
                "config": {"model": "mock-model"}
            },
        )
    )
    
    mock_code_repo_agent = MagicMock()
    mock_code_repo_agent.prepare = AsyncMock(return_value=True)
    mock_code_repo_agent.run = AsyncMock(return_value="Mock response")
    mock_code_repo_agent.close = AsyncMock()
    
    mock_memory = MagicMock()
    mock_memory.query = AsyncMock(return_value=MagicMock(results=[]))
    mock_code_repo_agent._code_repo_memory = mock_memory
    
    agent._code_repo_agent = mock_code_repo_agent
    
    await agent.prepare()
    
    report = TestReport(
        commit_info=CommitInfo(
            commit_hash="1234567890",
            author="Test Author",
            date=datetime.now(),
            message="Test commit message",
            files_changed=["src/utils.py"],
        ),
        file_changes=[
            FileChange(
                file_path="src/utils.py",
                change_type="modified",
                lines_added=3,
                lines_removed=0,
            )
        ],
        test_items=[
            TestItem(
                test_path="tests/test_utils.py",
                relevance_score=0.9,
                reason="Test for modified file",
            )
        ],
        summary="This is a test summary",
    )
    
    markdown_report = await agent.generate_report(report, format="markdown")
    
    assert "# Test Report for Commit" in markdown_report
    assert "Test Author" in markdown_report
    assert "Test commit message" in markdown_report
    assert "src/utils.py" in markdown_report
    assert "tests/test_utils.py" in markdown_report
    assert "This is a test summary" in markdown_report
    
    html_report = await agent.generate_report(report, format="html")
    
    assert "<html" in html_report
    assert "<title>Test Report for Commit 12345678</title>" in html_report
    assert "Test Author" in html_report
    assert "Test commit message" in html_report
    assert "src/utils.py" in html_report
    assert "tests/test_utils.py" in html_report
    assert "This is a test summary" in html_report
    
    await agent.close()
    
    mock_code_repo_agent.close.assert_called_once()


@pytest.mark.asyncio
async def test_component_serialization(temp_repo, db_dir, mock_model_client):
    """Test component serialization."""
    config = CommitAnalysisConfig(
        name="test_agent",
        repository_path=temp_repo,
        persistence_path=db_dir,
        model_client={
            "provider": "mock",
            "type": "model_client",
            "config": {"model": "mock-model"}
        },
    )
    
    agent = CommitAnalysisAgent(config=config)
    
    serialized = agent._to_config()
    
    assert serialized.name == "test_agent"
    assert serialized.repository_path == temp_repo
    assert serialized.persistence_path == db_dir
    
    deserialized = CommitAnalysisAgent._from_config(serialized)
    
    assert deserialized._config.name == "test_agent"
    assert deserialized._config.repository_path == temp_repo
    assert deserialized._config.persistence_path == db_dir

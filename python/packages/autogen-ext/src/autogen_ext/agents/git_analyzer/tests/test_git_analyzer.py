"""Tests for the GitHistoryAnalyzerAgent."""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import git
from git import Repo

from autogen_core import CancellationToken
from autogen_ext.agents.git_analyzer import GitHistoryAnalyzerAgent, GitTools


class TestGitTools(unittest.TestCase):
    """Test the GitTools class."""

    def setUp(self):
        """Set up a temporary git repository for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        
        self.repo = Repo.init(self.repo_path)
        
        self.repo.git.config("user.name", "Test User")
        self.repo.git.config("user.email", "test@example.com")
        
        test_file_path = os.path.join(self.repo_path, "test_file.txt")
        with open(test_file_path, "w") as f:
            f.write("Initial content")
        
        self.repo.git.add("test_file.txt")
        self.repo.git.commit("-m", "Initial commit")
        
        self.git_tools = GitTools(self.repo_path)

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    def test_get_commit_history(self):
        """Test getting commit history."""
        commits = self.git_tools.get_commit_history()
        
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["message"], "Initial commit")
        self.assertEqual(commits[0]["author"].split("<")[0].strip(), "Test User")
        self.assertTrue("test_file.txt" in commits[0]["stats"]["files"])

    def test_get_commit_diff(self):
        """Test getting commit diff."""
        commit_hash = self.repo.head.commit.hexsha
        diffs = self.git_tools.get_commit_diff(commit_hash)
        
        self.assertTrue("test_file.txt" in diffs)
        self.assertIn("Initial content", diffs["test_file.txt"])

    def test_create_branch_with_commits(self):
        """Test creating a new branch with commits."""
        test_file_path = os.path.join(self.repo_path, "test_file.txt")
        with open(test_file_path, "w") as f:
            f.write("Updated content")
        
        self.repo.git.add("test_file.txt")
        self.repo.git.commit("-m", "Update test file")
        
        commits = list(self.repo.iter_commits())
        commit_hashes = [commit.hexsha for commit in commits]
        
        result = self.git_tools.create_branch_with_commits(
            "test-branch", 
            base_branch="HEAD", 
            commit_hashes=[commit_hashes[1]]  # Use the initial commit
        )
        
        self.assertIn("Successfully created branch", result)
        self.assertIn("test-branch", [b.name for b in self.repo.branches])


class TestGitHistoryAnalyzerAgent(unittest.TestCase):
    """Test the GitHistoryAnalyzerAgent."""

    @patch("autogen_ext.agents.git_analyzer._git_history_analyzer.GitTools")
    @patch("autogen_ext.agents.git_analyzer._git_history_analyzer.OpenAIChatCompletionClient")
    def setUp(self, mock_client, mock_git_tools):
        """Set up the test environment."""
        self.mock_client = mock_client.return_value
        self.mock_git_tools = mock_git_tools.return_value
        
        self.mock_git_tools.get_commit_history.return_value = [
            {
                "hash": "abc123",
                "short_hash": "abc123",
                "author": "Test User <test@example.com>",
                "message": "feat: Add new feature #123",
                "date": "2023-01-01T12:00:00",
                "is_merge": False,
                "stats": {
                    "files": {"test_file.py": {"insertions": 10, "deletions": 2}},
                    "total": {"insertions": 10, "deletions": 2}
                }
            },
            {
                "hash": "def456",
                "short_hash": "def456",
                "author": "Test User <test@example.com>",
                "message": "fix: Fix bug in feature #123",
                "date": "2023-01-01T13:00:00",
                "is_merge": False,
                "stats": {
                    "files": {"test_file.py": {"insertions": 5, "deletions": 3}},
                    "total": {"insertions": 5, "deletions": 3}
                }
            }
        ]
        
        self.mock_git_tools.get_commit_diff.return_value = {
            "test_file.py": "+ def new_function():\n+     return 'Hello, world!'"
        }
        
        self.agent = GitHistoryAnalyzerAgent(
            model_client=self.mock_client,
            repo_path="/fake/repo/path"
        )
        
        self.agent.run = MagicMock()
        self.agent.run.return_value = "Analysis: This commit adds a new feature."

    @patch("autogen_ext.agents.git_analyzer._git_history_analyzer.Repo")
    async def test_get_commits(self, mock_repo):
        """Test getting commits from the repository."""
        commits = await self.agent._get_commits()
        
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]["hash"], "abc123")
        self.assertEqual(commits[1]["hash"], "def456")
        self.mock_git_tools.get_commit_history.assert_called_once()

    @patch("autogen_ext.agents.git_analyzer._git_history_analyzer.Repo")
    async def test_analyze_commit(self, mock_repo):
        """Test analyzing a commit."""
        mock_repo.return_value.commit.return_value = MagicMock(
            hexsha="abc123",
            message="feat: Add new feature",
            author=MagicMock(name="Test User", email="test@example.com"),
            committed_datetime="2023-01-01T12:00:00",
            parents=[MagicMock(hexsha="parent123")]
        )
        
        result = await self.agent._analyze_commit("abc123")
        
        self.assertIn("original_commit", result)
        self.assertIn("analysis", result)
        self.assertEqual(result["analysis"], "Analysis: This commit adds a new feature.")
        self.agent.run.assert_called_once()

    @patch("autogen_ext.agents.git_analyzer._git_history_analyzer.Repo")
    async def test_group_related_commits(self, mock_repo):
        """Test grouping related commits."""
        groups = await self.agent._group_related_commits(group_by="pr")
        
        self.assertEqual(len(groups), 1)  # Both commits have PR #123
        self.assertEqual(groups[0]["pr_number"], 123)
        self.assertEqual(len(groups[0]["commits"]), 2)

    @patch("autogen_ext.agents.git_analyzer._git_history_analyzer.Repo")
    async def test_improve_commit_message(self, mock_repo):
        """Test improving a commit message."""
        mock_repo.return_value.commit.return_value = MagicMock(
            hexsha="abc123",
            message="Add feature",
            author=MagicMock(name="Test User", email="test@example.com"),
            committed_datetime="2023-01-01T12:00:00",
            parents=[MagicMock(hexsha="parent123")]
        )
        
        result = await self.agent._improve_commit_message("abc123")
        
        self.assertEqual(result["original_commit_hash"], "abc123")
        self.assertEqual(result["standardized_message"], "Analysis: This commit adds a new feature.")
        self.agent.run.assert_called_once()

    async def test_analyze_repository(self):
        """Test analyzing the entire repository."""
        report = await self.agent.analyze_repository(max_count=2)
        
        self.assertEqual(report["commits_count"], 2)
        self.assertIn("commit_groups", report)
        self.assertIn("sample_analyses", report)
        self.assertEqual(len(report["sample_analyses"]), 2)


if __name__ == "__main__":
    unittest.main()

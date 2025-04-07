"""Commit analysis agent for identifying test requirements based on code changes."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple, Type, Union

import git
from autogen_core import Component, ComponentBase
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.agents.code_repository.agent import CodeRepositoryAgent, CodeRepositoryAgentConfig
from autogen_ext.agents.code_repository.memory import CodeRepositoryMemory, CodeRepositoryMemoryConfig
from pydantic import BaseModel, Field
from typing_extensions import Self

logger = logging.getLogger(__name__)

class CommitAnalysisConfig(BaseModel):
    """Configuration for commit analysis agent."""
    
    name: str = Field(default="commit_analysis_agent", description="Name of the agent")
    model_client: Dict[str, Any] = Field(description="Model client configuration")
    repository_path: str = Field(default="", description="Path to the local repository")
    persistence_path: str = Field(default="./commit_analysis_db", description="Path for persistent storage")
    system_message: str = Field(
        default="You are a specialized agent for analyzing code commits and identifying necessary tests. "
               "Your task is to examine code changes, find related components, and determine which tests "
               "should be run to ensure code quality.",
        description="System message for the agent",
    )
    code_repo_config: Dict[str, Any] = Field(default={}, description="Additional configuration for CodeRepositoryAgent")
    description: str = Field(
        default="An agent that analyzes code commits and generates test reports",
        description="Description of the agent",
    )
    test_patterns: List[str] = Field(
        default=[
            r"test_.*\.py$",
            r".*_test\.py$",
            r".*\.test\.js$",
            r".*\.spec\.js$",
            r".*Test\.java$",
            r".*Tests\.cs$",
        ],
        description="Patterns to identify test files",
    )
    max_commits: int = Field(default=1, description="Maximum number of commits to analyze")
    include_file_types: List[str] = Field(
        default=["py", "js", "ts", "java", "c", "cpp", "cs", "go", "rs", "php", "rb", "swift"],
        description="File extensions to include in analysis",
    )
    exclude_patterns: List[str] = Field(
        default=[
            r"\.git/", r"node_modules/", r"__pycache__/", r"\.venv/", r"\.env/",
            r"\.pyc$", r"\.pyo$", r"\.pyd$", r"\.so$", r"\.dll$", r"\.exe$", 
            r"\.min\.js$", r"\.min\.css$",
        ],
        description="Regular expressions for files/directories to exclude from analysis",
    )

class CommitInfo(BaseModel):
    """Information about a commit."""
    
    commit_hash: str = Field(description="Commit hash")
    author: str = Field(description="Author of the commit")
    date: datetime = Field(description="Date of the commit")
    message: str = Field(description="Commit message")
    files_changed: List[str] = Field(description="List of files changed in the commit")
    
class FileChange(BaseModel):
    """Information about a file change."""
    
    file_path: str = Field(description="Path to the file")
    change_type: str = Field(description="Type of change (added, modified, deleted)")
    lines_added: int = Field(default=0, description="Number of lines added")
    lines_removed: int = Field(default=0, description="Number of lines removed")
    content_before: Optional[str] = Field(default=None, description="Content before the change")
    content_after: Optional[str] = Field(default=None, description="Content after the change")
    diff: Optional[str] = Field(default=None, description="Diff of the change")

class TestItem(BaseModel):
    """Information about a test item."""
    
    test_path: str = Field(description="Path to the test file")
    relevance_score: float = Field(description="Relevance score (0-1)")
    reason: str = Field(description="Reason why this test is relevant")
    
class TestReport(BaseModel):
    """Test report generated from commit analysis."""
    
    commit_info: CommitInfo = Field(description="Information about the analyzed commit")
    file_changes: List[FileChange] = Field(description="List of file changes")
    test_items: List[TestItem] = Field(description="List of test items to run")
    summary: str = Field(description="Summary of the test report")
    generated_at: datetime = Field(default_factory=datetime.now, description="When the report was generated")

class CommitAnalysisAgent(ComponentBase[CommitAnalysisConfig], Component[CommitAnalysisConfig]):
    """Agent for analyzing code commits and identifying test requirements.
    
    This agent analyzes code commits to identify which tests should be run based on
    the changes made. It uses a code repository agent to understand the codebase and
    find related components.
    
    Args:
        config (CommitAnalysisConfig): Configuration for the agent
        
    Example:
        ```python
        import asyncio
        from autogen_ext.agents.commit_analysis.agent import CommitAnalysisAgent, CommitAnalysisConfig
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        async def main():
            model_client = OpenAIChatCompletionClient(
                model="gpt-4o",
            )
            
            agent = CommitAnalysisAgent(
                config=CommitAnalysisConfig(
                    name="commit_analysis_agent",
                    repository_path="/path/to/repo",
                    persistence_path="./commit_analysis_db",
                    model_client=model_client.dump_component().model_dump(),
                )
            )
            
            report = await agent.analyze_latest_commit()
            print(report.summary)
            
            await agent.close()
            
        asyncio.run(main())
        ```
    """
    
    component_config_schema = CommitAnalysisConfig
    component_type: ClassVar[str] = "agent"
    
    def __init__(self, config: CommitAnalysisConfig) -> None:
        """Initialize CommitAnalysisAgent."""
        self._config = config
        self._repo = None
        self._code_repo_agent = None
        
    async def prepare(self) -> bool:
        """Prepare the agent by initializing the repository and code repository agent.
        
        Returns:
            bool: True if the agent is ready
        """
        if not self._config.repository_path:
            raise ValueError("Repository path must be provided")
        
        try:
            self._repo = git.Repo(self._config.repository_path)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Invalid git repository: {self._config.repository_path}")
        
        if self._code_repo_agent is None:
            
            model_client_config = self._config.model_client
            
            code_repo_config = CodeRepositoryAgentConfig(
                name=f"{self._config.name}_repo",
                repository_path=self._config.repository_path,
                persistence_path=self._config.persistence_path,
                model_client=model_client_config,
                **self._config.code_repo_config,
            )
            
            self._code_repo_agent = CodeRepositoryAgent(config=code_repo_config)
            
            await self._code_repo_agent.prepare()
        
        return True
    
    async def analyze_latest_commit(self) -> TestReport:
        """Analyze the latest commit and generate a test report.
        
        Returns:
            TestReport: Test report generated from the analysis
        """
        if not self._repo or not self._code_repo_agent:
            await self.prepare()
        
        latest_commit = self._repo.head.commit
        
        return await self.analyze_commit(latest_commit.hexsha)
    
    async def analyze_commit(self, commit_hash: str) -> TestReport:
        """Analyze a specific commit and generate a test report.
        
        Args:
            commit_hash (str): Hash of the commit to analyze
            
        Returns:
            TestReport: Test report generated from the analysis
        """
        if not self._repo or not self._code_repo_agent:
            await self.prepare()
        
        commit = self._repo.commit(commit_hash)
        
        commit_info = CommitInfo(
            commit_hash=commit.hexsha,
            author=f"{commit.author.name} <{commit.author.email}>",
            date=datetime.fromtimestamp(commit.committed_date),
            message=commit.message,
            files_changed=[item.a_path for item in commit.diff(commit.parents[0])] if commit.parents else [],
        )
        
        file_changes = await self._get_file_changes(commit)
        
        test_items = await self._find_test_items(commit_info, file_changes)
        
        summary = await self._generate_summary(commit_info, file_changes, test_items)
        
        report = TestReport(
            commit_info=commit_info,
            file_changes=file_changes,
            test_items=test_items,
            summary=summary,
        )
        
        return report
    
    async def analyze_commits(self, num_commits: int = None) -> List[TestReport]:
        """Analyze multiple commits and generate test reports.
        
        Args:
            num_commits (int, optional): Number of commits to analyze. Defaults to the value in config.
            
        Returns:
            List[TestReport]: List of test reports generated from the analysis
        """
        if not self._repo or not self._code_repo_agent:
            await self.prepare()
        
        if num_commits is None:
            num_commits = self._config.max_commits
        
        commits = list(self._repo.iter_commits(max_count=num_commits))
        
        reports = []
        for commit in commits:
            report = await self.analyze_commit(commit.hexsha)
            reports.append(report)
        
        return reports
    
    async def _get_file_changes(self, commit) -> List[FileChange]:
        """Get file changes for a commit.
        
        Args:
            commit: Git commit object
            
        Returns:
            List[FileChange]: List of file changes
        """
        file_changes = []
        
        if not commit.parents:
            return file_changes
        
        parent = commit.parents[0]
        
        diffs = parent.diff(commit)
        
        for diff in diffs:
            if any(re.search(pattern, diff.a_path) for pattern in self._config.exclude_patterns):
                continue
            
            file_ext = os.path.splitext(diff.a_path)[1].lstrip('.')
            if file_ext not in self._config.include_file_types:
                continue
            
            change_type = "modified"
            if diff.new_file:
                change_type = "added"
            elif diff.deleted_file:
                change_type = "deleted"
            elif diff.renamed:
                change_type = "renamed"
            
            content_before = None
            content_after = None
            
            try:
                if not diff.deleted_file:
                    content_after = self._repo.git.show(f"{commit.hexsha}:{diff.a_path}")
                
                if not diff.new_file:
                    content_before = self._repo.git.show(f"{parent.hexsha}:{diff.a_path}")
            except git.exc.GitCommandError:
                continue
            
            lines_added = 0
            lines_removed = 0
            
            diff_text = diff.diff.decode('utf-8', errors='replace') if isinstance(diff.diff, bytes) else diff.diff
            
            for line in diff_text.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    lines_added += 1
                elif line.startswith('-') and not line.startswith('---'):
                    lines_removed += 1
            
            file_change = FileChange(
                file_path=diff.a_path,
                change_type=change_type,
                lines_added=lines_added,
                lines_removed=lines_removed,
                content_before=content_before,
                content_after=content_after,
                diff=diff_text,
            )
            
            file_changes.append(file_change)
        
        return file_changes
    
    async def _find_test_items(self, commit_info: CommitInfo, file_changes: List[FileChange]) -> List[TestItem]:
        """Find test items related to the file changes.
        
        Args:
            commit_info (CommitInfo): Information about the commit
            file_changes (List[FileChange]): List of file changes
            
        Returns:
            List[TestItem]: List of test items
        """
        test_items = []
        
        test_files = self._find_test_files()
        
        for file_change in file_changes:
            if any(re.search(pattern, file_change.file_path) for pattern in self._config.test_patterns):
                continue
            
            related_tests = await self._find_related_tests(file_change, test_files)
            
            test_items.extend(related_tests)
        
        unique_test_items = {}
        for item in test_items:
            if item.test_path not in unique_test_items or item.relevance_score > unique_test_items[item.test_path].relevance_score:
                unique_test_items[item.test_path] = item
        
        sorted_test_items = sorted(unique_test_items.values(), key=lambda x: x.relevance_score, reverse=True)
        
        return sorted_test_items
    
    def _find_test_files(self) -> List[str]:
        """Find all test files in the repository.
        
        Returns:
            List[str]: List of test file paths
        """
        test_files = []
        
        for root, _, files in os.walk(self._config.repository_path):
            if any(re.search(pattern, os.path.relpath(root, self._config.repository_path)) for pattern in self._config.exclude_patterns):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self._config.repository_path)
                
                if any(re.search(pattern, rel_path) for pattern in self._config.exclude_patterns):
                    continue
                
                if any(re.search(pattern, rel_path) for pattern in self._config.test_patterns):
                    test_files.append(rel_path)
        
        return test_files
    
    async def _find_related_tests(self, file_change: FileChange, test_files: List[str]) -> List[TestItem]:
        """Find test files related to a file change.
        
        Args:
            file_change (FileChange): File change to find related tests for
            test_files (List[str]): List of all test files
            
        Returns:
            List[TestItem]: List of related test items
        """
        related_tests = []
        
        file_name = os.path.basename(file_change.file_path)
        file_name_without_ext = os.path.splitext(file_name)[0]
        
        name_matched_tests = []
        for test_file in test_files:
            test_file_name = os.path.basename(test_file)
            if file_name_without_ext in test_file_name:
                name_matched_tests.append(test_file)
        
        for test_file in name_matched_tests:
            test_item = TestItem(
                test_path=test_file,
                relevance_score=0.9,
                reason=f"Test file name matches the changed file name: {file_name_without_ext}",
            )
            related_tests.append(test_item)
        
        for test_file in test_files:
            if test_file in [item.test_path for item in related_tests]:
                continue
            
            test_file_path = os.path.join(self._config.repository_path, test_file)
            
            try:
                with open(test_file_path, 'r', encoding='utf-8') as f:
                    test_content = f.read()
            except Exception:
                continue
            
            file_path_parts = file_change.file_path.split('/')
            file_module = '.'.join(file_path_parts[:-1] + [os.path.splitext(file_path_parts[-1])[0]])
            
            if file_name_without_ext in test_content or file_module in test_content:
                test_item = TestItem(
                    test_path=test_file,
                    relevance_score=0.8,
                    reason=f"Test file references the changed file: {file_change.file_path}",
                )
                related_tests.append(test_item)
        
        if file_change.content_after:
            query = f"Find tests related to this code:\n\n```\n{file_change.content_after}\n```"
            
            results = await self._code_repo_agent._code_repo_memory.query(query)
            
            for result in results.results:
                file_path = result.metadata.get("file_path")
                if file_path and any(re.search(pattern, file_path) for pattern in self._config.test_patterns):
                    if file_path in [item.test_path for item in related_tests]:
                        continue
                    
                    test_item = TestItem(
                        test_path=file_path,
                        relevance_score=min(0.7, float(result.metadata.get("score", 0.0))),
                        reason=f"Test file is semantically related to the changed file: {file_change.file_path}",
                    )
                    related_tests.append(test_item)
        
        return related_tests
    
    async def _generate_summary(self, commit_info: CommitInfo, file_changes: List[FileChange], test_items: List[TestItem]) -> str:
        """Generate a summary of the test report.
        
        Args:
            commit_info (CommitInfo): Information about the commit
            file_changes (List[FileChange]): List of file changes
            test_items (List[TestItem]): List of test items
            
        Returns:
            str: Summary of the test report
        """
        query = f"""
        Generate a summary of the test report for the following commit:
        
        Commit: {commit_info.commit_hash}
        Author: {commit_info.author}
        Date: {commit_info.date}
        Message: {commit_info.message}
        
        Files changed ({len(file_changes)}):
        {', '.join(file_change.file_path for file_change in file_changes[:5])}
        {f'... and {len(file_changes) - 5} more' if len(file_changes) > 5 else ''}
        
        Tests to run ({len(test_items)}):
        {', '.join(test_item.test_path for test_item in test_items[:5])}
        {f'... and {len(test_items) - 5} more' if len(test_items) > 5 else ''}
        
        Please provide a concise summary of what was changed and why these tests should be run.
        """
        
        result = await self._code_repo_agent.run(task=query)
        
        if hasattr(result, 'content'):
            return result.content
        elif hasattr(result, 'messages') and result.messages:
            return str(result.messages[-1].content)
        else:
            return str(result)
    
    async def generate_report(self, test_report: TestReport, format: str = "markdown") -> str:
        """Generate a formatted report from a test report.
        
        Args:
            test_report (TestReport): Test report to format
            format (str, optional): Format of the report. Defaults to "markdown".
            
        Returns:
            str: Formatted report
        """
        if format.lower() == "markdown":
            return self._generate_markdown_report(test_report)
        elif format.lower() == "html":
            return self._generate_html_report(test_report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_markdown_report(self, test_report: TestReport) -> str:
        """Generate a markdown report from a test report.
        
        Args:
            test_report (TestReport): Test report to format
            
        Returns:
            str: Markdown report
        """
        report = f"""# Test Report for Commit {test_report.commit_info.commit_hash[:8]}

- **Hash:** {test_report.commit_info.commit_hash}
- **Author:** {test_report.commit_info.author}
- **Date:** {test_report.commit_info.date}
- **Message:** {test_report.commit_info.message}

{test_report.summary}

| File | Change Type | Lines Added | Lines Removed |
|------|-------------|-------------|---------------|
"""
        
        for file_change in test_report.file_changes:
            report += f"| {file_change.file_path} | {file_change.change_type} | {file_change.lines_added} | {file_change.lines_removed} |\n"
        
        report += f"\n## Tests to Run ({len(test_report.test_items)})\n"
        report += "| Test | Relevance | Reason |\n"
        report += "|------|-----------|--------|\n"
        
        for test_item in test_report.test_items:
            report += f"| {test_item.test_path} | {test_item.relevance_score:.2f} | {test_item.reason} |\n"
        
        report += f"\n\n*Report generated at {test_report.generated_at} by {self._config.name}*"
        
        return report
    
    def _generate_html_report(self, test_report: TestReport) -> str:
        """Generate an HTML report from a test report.
        
        Args:
            test_report (TestReport): Test report to format
            
        Returns:
            str: HTML report
        """
        report = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report for Commit {test_report.commit_info.commit_hash[:8]}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .summary {{ background-color: #f0f7ff; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        .footer {{ color: #777; font-size: 0.8em; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>Test Report for Commit {test_report.commit_info.commit_hash[:8]}</h1>
    
    <h2>Commit Information</h2>
    <table>
        <tr><th>Hash</th><td>{test_report.commit_info.commit_hash}</td></tr>
        <tr><th>Author</th><td>{test_report.commit_info.author}</td></tr>
        <tr><th>Date</th><td>{test_report.commit_info.date}</td></tr>
        <tr><th>Message</th><td>{test_report.commit_info.message}</td></tr>
    </table>
    
    <h2>Summary</h2>
    <div class="summary">
        {test_report.summary.replace('\n', '<br>')}
    </div>
    
    <h2>Files Changed ({len(test_report.file_changes)})</h2>
    <table>
        <tr>
            <th>File</th>
            <th>Change Type</th>
            <th>Lines Added</th>
            <th>Lines Removed</th>
        </tr>
"""
        
        for file_change in test_report.file_changes:
            report += f"""        <tr>
            <td>{file_change.file_path}</td>
            <td>{file_change.change_type}</td>
            <td>{file_change.lines_added}</td>
            <td>{file_change.lines_removed}</td>
        </tr>
"""
        
        report += f"""    </table>
    
    <h2>Tests to Run ({len(test_report.test_items)})</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>Relevance</th>
            <th>Reason</th>
        </tr>
"""
        
        for test_item in test_report.test_items:
            report += f"""        <tr>
            <td>{test_item.test_path}</td>
            <td>{test_item.relevance_score:.2f}</td>
            <td>{test_item.reason}</td>
        </tr>
"""
        
        report += f"""    </table>
    
    <div class="footer">
        Report generated at {test_report.generated_at} by {self._config.name}
    </div>
</body>
</html>"""
        
        return report
    
    async def close(self) -> None:
        """Close and clean up resources."""
        if self._code_repo_agent:
            await self._code_repo_agent.close()
            self._code_repo_agent = None
        
        self._repo = None
    
    def _to_config(self) -> CommitAnalysisConfig:
        """Serialize the agent configuration."""
        return self._config
    
    @classmethod
    def _from_config(cls, config: CommitAnalysisConfig) -> Self:
        """Deserialize the agent configuration."""
        return cls(config=config)

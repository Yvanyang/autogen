"""Git History Analyzer Agent for improved commit messaging and organization."""
import os
import re
import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union

import git
from git import Repo, Commit

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken
from autogen_core.tools import BaseTool, FunctionTool

class BaseAgent:
    """Base class for the GitHistoryAnalyzerAgent."""
    
    def __init__(self, name, system_message, model_client, tools, **kwargs):
        self.name = name
        self.system_message = system_message
        self.model_client = model_client
        self.tools = tools
        
    async def run(self, task, cancellation_token=None):
        """Run a task using the model client."""
        response = await self.model_client.complete(
            messages=[{"role": "system", "content": self.system_message},
                     {"role": "user", "content": task}],
            temperature=0.7,
        )
        return response.choices[0].message.content
from autogen_ext.models.openai import OpenAIChatCompletionClient

from ._git_tools import GitTools


@dataclass
class CommitInfo:
    """Information about a git commit."""
    hash: str
    message: str
    author: str
    date: datetime
    files_changed: List[str]
    code_changes: Dict[str, str]  # Map of filename to diff
    parent_hashes: List[str]
    is_merge_commit: bool


@dataclass
class ImprovedCommitInfo:
    """Improved commit information with standardized message."""
    original_commit_hash: str
    standardized_message: str
    original_message: str
    code_analysis: str
    potential_issues: List[str]


@dataclass
class CommitGroup:
    """A group of related commits that can be squashed together."""
    commits: List[CommitInfo]
    suggested_message: str
    pr_number: Optional[int] = None
    related_issue: Optional[int] = None


class GitHistoryAnalyzerAgent(BaseAgent):
    """An agent that analyzes git repository history and suggests improvements.
    
    This agent can analyze commit messages, identify related commits for squashing,
    and generate standardized commit messages according to conventions.
    """
    
    def __init__(
        self,
        name: str = "GitHistoryAnalyzer",
        model_client: Optional[Any] = None,
        repo_path: str = ".",
        commit_message_convention: str = "react",
        **kwargs
    ):
        """Initialize the GitHistoryAnalyzerAgent.
        
        Args:
            name: The name of the agent.
            model_client: The model client to use for generating improved commit messages.
            repo_path: Path to the git repository.
            commit_message_convention: Convention to use for standardized commit messages.
            **kwargs: Additional arguments to pass to the parent class.
        """
        if model_client is None:
            model_client = OpenAIChatCompletionClient(model="gpt-4o")
        
        system_message = (
            f"You are a Git History Analyzer that helps improve repository history. "
            f"You follow the {commit_message_convention} commit message convention. "
            f"Your goal is to analyze commits, suggest improved messages, and identify "
            f"commits that should be squashed together."
        )
        
        self.git_tools = GitTools(repo_path)
        self.repo_path = repo_path
        self.commit_message_convention = commit_message_convention
        
        tools = [
            self._get_commits,
            self._analyze_commit,
            self._group_related_commits,
            self._improve_commit_message,
            self._create_new_branch,
        ]
        
        super().__init__(
            name=name,
            system_message=system_message,
            model_client=model_client,
            tools=tools,
            **kwargs
        )

    async def _get_commits(
        self, 
        branch: str = "HEAD", 
        max_count: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get commits from the repository.
        
        Args:
            branch: The branch to get commits from.
            max_count: Maximum number of commits to retrieve.
            skip: Number of commits to skip.
            
        Returns:
            List of commit information dictionaries.
        """
        commits = self.git_tools.get_commit_history(branch, max_count, skip)
        
        for commit in commits:
            commit["date"] = datetime.fromisoformat(commit["date"])
            
        return commits
    
    def _extract_commit_info(self, commit_hash: str) -> CommitInfo:
        """Extract detailed information from a git commit.
        
        Args:
            commit_hash: The hash of the commit to analyze.
            
        Returns:
            CommitInfo object with extracted information.
        """
        repo = Repo(self.repo_path)
        commit = repo.commit(commit_hash)
        
        code_changes = self.git_tools.get_commit_diff(commit_hash)
        
        files_changed = list(code_changes.keys())
        
        return CommitInfo(
            hash=commit.hexsha,
            message=str(commit.message),
            author=f"{commit.author.name} <{commit.author.email}>",
            date=commit.committed_datetime,
            files_changed=files_changed,
            code_changes=code_changes,
            parent_hashes=[p.hexsha for p in commit.parents],
            is_merge_commit=len(commit.parents) > 1
        )

    async def _analyze_commit(self, commit_hash: str) -> Dict[str, Any]:
        """Analyze a commit and provide detailed information.
        
        Args:
            commit_hash: The hash of the commit to analyze.
            
        Returns:
            Dictionary with commit analysis information.
        """
        commit_info = self._extract_commit_info(commit_hash)
        
        task = (
            f"Analyze the following git commit:\n"
            f"Message: {commit_info.message}\n"
            f"Files changed: {', '.join(commit_info.files_changed)}\n"
            f"Is merge commit: {commit_info.is_merge_commit}\n\n"
            f"For each file, here are the changes:\n"
        )
        
        for file, diff in list(commit_info.code_changes.items())[:3]:
            diff_preview = diff[:500] + "..." if len(diff) > 500 else diff
            task += f"\nFile: {file}\nDiff:\n{diff_preview}\n"
            
        task += (
            f"\nPlease analyze this commit and provide:\n"
            f"1. A brief description of what the commit does\n"
            f"2. Whether the commit message accurately describes the changes\n"
            f"3. Any potential issues or concerns\n"
            f"4. A suggested improved commit message following {self.commit_message_convention} convention"
        )
        
        response = await self.run(task=task, cancellation_token=CancellationToken())
        
        result = {
            "original_commit": commit_info.__dict__,
            "analysis": response,
        }
        
        return result
    
    async def _group_related_commits(
        self,
        branch: str = "HEAD",
        max_count: int = 100,
        group_by: str = "pr"
    ) -> List[Dict[str, Any]]:
        """Group related commits that should be squashed together.
        
        Args:
            branch: The branch to analyze commits from.
            max_count: Maximum number of commits to analyze.
            group_by: Grouping strategy ('pr', 'time', 'files').
            
        Returns:
            List of commit groups.
        """
        commits = await self._get_commits(branch, max_count)
        
        groups = []
        
        if group_by == "pr":
            pr_pattern = re.compile(r'#(\d+)')
            pr_groups = {}
            
            for commit in commits:
                pr_matches = pr_pattern.findall(commit["message"])
                if pr_matches:
                    pr_number = int(pr_matches[0])
                    if pr_number not in pr_groups:
                        pr_groups[pr_number] = []
                    pr_groups[pr_number].append(commit)
                else:
                    groups.append({
                        "commits": [commit],
                        "suggested_message": commit["message"],
                        "pr_number": None
                    })
            
            for pr_number, pr_commits in pr_groups.items():
                if len(pr_commits) > 1:
                    pr_commits.sort(key=lambda c: c["date"])
                    
                    message_first_line = pr_commits[-1]['message'].split('\n')[0] if '\n' in pr_commits[-1]['message'] else pr_commits[-1]['message']
                    suggested_message = f"PR #{pr_number}: {message_first_line}"
                    
                    groups.append({
                        "commits": pr_commits,
                        "suggested_message": suggested_message,
                        "pr_number": pr_number
                    })
                else:
                    groups.append({
                        "commits": pr_commits,
                        "suggested_message": pr_commits[0]["message"],
                        "pr_number": pr_number
                    })
        
        elif group_by == "files":
            current_group = []
            current_files = set()
            
            for commit in commits:
                commit_files = set(commit["stats"]["files"].keys())
                if current_group and (current_files & commit_files):
                    current_group.append(commit)
                    current_files |= commit_files
                else:
                    if current_group:
                        groups.append({
                            "commits": current_group,
                            "suggested_message": current_group[-1]["message"]
                        })
                    
                    current_group = [commit]
                    current_files = commit_files
            
            if current_group:
                groups.append({
                    "commits": current_group,
                    "suggested_message": current_group[-1]["message"]
                })
        
        elif group_by == "time":
            time_window_seconds = 3600  # 1 hour
            current_group = []
            
            for commit in commits:
                if (current_group and 
                    commit["author"].split("<")[0].strip() == current_group[-1]["author"].split("<")[0].strip() and
                    (commit["date"] - current_group[-1]["date"]).total_seconds() < time_window_seconds):
                    current_group.append(commit)
                else:
                    if current_group:
                        groups.append({
                            "commits": current_group,
                            "suggested_message": current_group[-1]["message"]
                        })
                    current_group = [commit]
            
            if current_group:
                groups.append({
                    "commits": current_group,
                    "suggested_message": current_group[-1]["message"]
                })
        
        return groups
    
    async def _improve_commit_message(
        self,
        commit_hash: str
    ) -> Dict[str, Any]:
        """Generate an improved commit message based on the commit content.
        
        Args:
            commit_hash: The hash of the commit to improve.
            
        Returns:
            Dictionary with the original and improved commit messages.
        """
        commit_info = self._extract_commit_info(commit_hash)
        
        task = (
            f"Generate an improved commit message for the following changes:\n\n"
            f"Original message: {commit_info.message}\n\n"
            f"Files changed: {', '.join(commit_info.files_changed)}\n\n"
        )
        
        for file, diff in list(commit_info.code_changes.items())[:3]:
            diff_preview = diff[:500] + "..." if len(diff) > 500 else diff
            task += f"\nFile: {file}\nDiff:\n{diff_preview}\n"
        
        task += (
            f"\nPlease generate a standardized commit message following the {self.commit_message_convention} convention. "
            f"For React convention, use prefixes like 'feat', 'fix', 'chore', 'docs', 'style', 'refactor', 'perf', or 'test'."
            f"\n\nThe message should be concise but descriptive of what the commit actually does. "
            f"Also analyze if there are potential issues with the changes."
        )
        
        response = await self.run(task=task, cancellation_token=CancellationToken())
        
        potential_issues = []
        if "potential issue" in response.lower() or "concern" in response.lower():
            issues_section = response.split("potential issues:", 1)[-1].split("\n\n")[0] if "potential issues:" in response.lower() else ""
            if issues_section:
                potential_issues = [issue.strip() for issue in issues_section.split("-") if issue.strip()]
        
        result = {
            "original_commit_hash": commit_hash,
            "standardized_message": response.split("\n\n")[0] if "\n\n" in response else response,
            "original_message": commit_info.message,
            "code_analysis": response,
            "potential_issues": potential_issues
        }
        
        return result
    
    async def _create_new_branch(
        self,
        groups: List[Dict[str, Any]],
        new_branch_name: str,
    ) -> str:
        """Create a new branch with reorganized commits.
        
        Args:
            groups: List of commit groups to reorganize.
            new_branch_name: Name for the new branch.
            
        Returns:
            Message with the result of the operation.
        """
        
        return (
            f"Creating a new branch '{new_branch_name}' with reorganized commits would involve:\n\n"
            f"1. Creating a new branch from the current state\n"
            f"2. Cherry-picking and squashing commits from each group\n"
            f"3. Applying the improved commit messages\n\n"
            f"This operation requires complex git operations and is provided as a conceptual guide. "
            f"In a full implementation, this would execute git commands to create the actual branch."
        )
    
    async def analyze_repository(
        self, 
        branch: str = "HEAD",
        max_count: int = 50,
        group_strategy: str = "pr"
    ) -> Dict[str, Any]:
        """Analyze the repository and provide a complete report.
        
        Args:
            branch: The branch to analyze.
            max_count: Maximum number of commits to analyze.
            group_strategy: Strategy for grouping commits.
            
        Returns:
            Analysis report.
        """
        commits = await self._get_commits(branch, max_count)
        groups = await self._group_related_commits(branch, max_count, group_strategy)
        
        sample_size = min(5, len(commits))
        detailed_analyses = []
        
        for i in range(sample_size):
            analysis = await self._analyze_commit(commits[i]["hash"])
            detailed_analyses.append(analysis)
        
        report = {
            "repository": self.repo_path,
            "branch_analyzed": branch,
            "commits_count": len(commits),
            "commit_groups": groups,
            "sample_analyses": detailed_analyses,
            "group_strategy": group_strategy,
        }
        
        return report

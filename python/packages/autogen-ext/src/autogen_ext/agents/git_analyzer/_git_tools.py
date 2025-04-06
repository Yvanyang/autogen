"""Tools for Git operations and analysis."""
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import git
from git import Repo, Commit
from git.exc import GitCommandError


class GitTools:
    """Tools for interacting with Git repositories."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize GitTools with a repository path.
        
        Args:
            repo_path: Path to the git repository.
        """
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
    
    def get_commit_history(
        self,
        branch: str = "HEAD",
        max_count: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get the commit history from the repository.
        
        Args:
            branch: The branch to get history from.
            max_count: Maximum number of commits to retrieve.
            skip: Number of commits to skip.
            
        Returns:
            List of commit dictionaries.
        """
        commits = []
        for commit in self.repo.iter_commits(branch, max_count=max_count, skip=skip):
            commit_data = {
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:7],
                "author": f"{commit.author.name} <{commit.author.email}>",
                "message": commit.message,
                "date": commit.committed_datetime.isoformat(),
                "is_merge": len(commit.parents) > 1,
                "stats": {
                    "files": commit.stats.files,
                    "total": commit.stats.total,
                }
            }
            commits.append(commit_data)
        return commits
    
    def get_commit_diff(self, commit_hash: str) -> Dict[str, str]:
        """Get the diff for a specific commit.
        
        Args:
            commit_hash: The hash of the commit.
            
        Returns:
            Dictionary mapping filenames to their diffs.
        """
        commit = self.repo.commit(commit_hash)
        diffs = {}
        
        if not commit.parents:
            for item in commit.tree.traverse():
                if isinstance(item, git.Blob):
                    diffs[item.path] = f"+ {item.data_stream.read().decode('utf-8', errors='replace')}"
            return diffs
        
        parent = commit.parents[0]
        diff_index = parent.diff(commit)
        
        for diff in diff_index:
            if diff.a_path and diff.b_path:
                try:
                    diffs[diff.b_path] = diff.diff.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    diffs[diff.b_path] = "[Binary file changed]"
        
        return diffs
    
    def create_branch_with_commits(
        self,
        new_branch_name: str,
        base_branch: str = "HEAD",
        commit_hashes: Optional[List[str]] = None
    ) -> str:
        """Create a new branch with specified commits.
        
        Args:
            new_branch_name: Name for the new branch.
            base_branch: Base branch to start from.
            commit_hashes: List of commit hashes to include.
            
        Returns:
            Result message.
        """
        try:
            current_branch = self.repo.active_branch.name
            self.repo.git.checkout(base_branch)
            self.repo.git.checkout('-b', new_branch_name)
            
            if commit_hashes:
                for commit_hash in commit_hashes:
                    try:
                        self.repo.git.cherry_pick(commit_hash)
                    except GitCommandError as e:
                        self.repo.git.cherry_pick('--abort')
                        return f"Error cherry-picking {commit_hash}: {str(e)}"
            
            self.repo.git.checkout(current_branch)
            
            return f"Successfully created branch '{new_branch_name}' from {base_branch}"
        
        except Exception as e:
            try:
                self.repo.git.checkout(current_branch)
            except:
                pass
            return f"Error creating branch: {str(e)}"
    
    def squash_commits(
        self,
        branch_name: str,
        commit_hashes: List[str],
        message: str
    ) -> str:
        """Squash multiple commits into one with a new message.
        
        Args:
            branch_name: Name of branch to work on.
            commit_hashes: List of commit hashes to squash.
            message: New commit message.
            
        Returns:
            Result message.
        """
        try:
            current_branch = self.repo.active_branch.name
            
            temp_branch = f"temp-squash-{os.urandom(4).hex()}"
            
            oldest_commit = self.repo.commit(commit_hashes[-1])
            if oldest_commit.parents:
                base_commit = oldest_commit.parents[0].hexsha
            else:
                return "Cannot squash the root commit"
            
            self.repo.git.checkout('-b', temp_branch, base_commit)
            
            for commit_hash in reversed(commit_hashes):
                try:
                    self.repo.git.cherry_pick(commit_hash)
                except GitCommandError:
                    self.repo.git.cherry_pick('--abort')
                    self.repo.git.checkout(current_branch)
                    self.repo.git.branch('-D', temp_branch)
                    return f"Conflict while cherry-picking {commit_hash}"
            
            self.repo.git.reset('--soft', base_commit)
            
            self.repo.git.commit('-m', message)
            
            squashed_commit = self.repo.head.commit.hexsha
            self.repo.git.checkout(branch_name)
            
            self.repo.git.reset('--hard', squashed_commit)
            
            self.repo.git.checkout(current_branch)
            self.repo.git.branch('-D', temp_branch)
            
            return f"Successfully squashed commits with message: {message}"
            
        except Exception as e:
            try:
                self.repo.git.checkout(current_branch)
                self.repo.git.branch('-D', temp_branch)
            except:
                pass
            return f"Error squashing commits: {str(e)}"
    
    def generate_repository_stats(self) -> Dict[str, Any]:
        """Generate statistics about the repository.
        
        Returns:
            Dictionary with repository statistics.
        """
        stats = {
            "active_branch": self.repo.active_branch.name,
            "branches": [b.name for b in self.repo.branches],
            "tags": [t.name for t in self.repo.tags],
            "contributors": {},
            "file_types": {},
            "commit_count": 0,
        }
        
        for commit in self.repo.iter_commits():
            stats["commit_count"] += 1
            author = commit.author.name
            if author not in stats["contributors"]:
                stats["contributors"][author] = 0
            stats["contributors"][author] += 1
        
        for item in self.repo.head.commit.tree.traverse():
            if isinstance(item, git.Blob):
                _, ext = os.path.splitext(item.path)
                ext = ext if ext else "no_extension"
                if ext not in stats["file_types"]:
                    stats["file_types"][ext] = 0
                stats["file_types"][ext] += 1
        
        return stats

# Git History Analyzer Agent

The Git History Analyzer Agent is an extension for AutoGen that helps improve repository history by analyzing commit messages, identifying related commits for squashing, and generating standardized commit messages according to conventions.

## Features

- Analyze git repository history and commit content
- Compare commit messages with actual code changes
- Identify related/linked commits that could be squashed together
- Generate standardized commit messages following conventions (e.g., React)
- Create a new branch with reorganized commits

## Installation

```bash
pip install autogen-ext
```

## Usage

```python
import asyncio
from autogen_ext.agents.git_analyzer import GitHistoryAnalyzerAgent

async def main():
    # Initialize the agent
    agent = GitHistoryAnalyzerAgent(
        repo_path="/path/to/your/repo",
        commit_message_convention="react"
    )
    
    # Analyze the repository
    report = await agent.analyze_repository(
        branch="main",
        max_count=50,
        group_strategy="pr"  # Group by PR numbers
    )
    
    # Print the report
    print(f"Found {report['commits_count']} commits")
    print(f"Identified {len(report['commit_groups'])} commit groups")
    
    # Analyze a specific commit
    analysis = await agent.analyze_commit("commit_hash")
    print(analysis)
    
    # Improve a commit message
    improved = await agent.improve_commit_message("commit_hash")
    print(f"Original: {improved['original_message']}")
    print(f"Improved: {improved['standardized_message']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Grouping Strategies

The agent supports different strategies for grouping related commits:

- `pr`: Group commits by PR numbers mentioned in commit messages
- `files`: Group commits that modify the same files
- `time`: Group commits made within a short time window by the same author

## Commit Message Conventions

The agent can generate standardized commit messages following different conventions:

- `react`: Uses prefixes like 'feat', 'fix', 'chore', 'docs', 'style', 'refactor', 'perf', or 'test'
- Other conventions can be added by extending the agent

## API Reference

### GitHistoryAnalyzerAgent

```python
GitHistoryAnalyzerAgent(
    name="GitHistoryAnalyzer",
    model_client=None,  # Defaults to OpenAIChatCompletionClient with gpt-4o
    repo_path=".",
    commit_message_convention="react",
    **kwargs
)
```

#### Methods

- `analyze_repository(branch="HEAD", max_count=50, group_strategy="pr")`: Analyze the repository and provide a complete report
- `analyze_commit(commit_hash)`: Analyze a specific commit and provide detailed information
- `improve_commit_message(commit_hash)`: Generate an improved commit message based on the commit content
- `group_related_commits(branch="HEAD", max_count=100, group_by="pr")`: Group related commits that should be squashed together
- `create_new_branch(groups, new_branch_name)`: Create a new branch with reorganized commits

### GitTools

Utility class for git operations:

```python
GitTools(repo_path=".")
```

#### Methods

- `get_commit_history(branch="HEAD", max_count=100, skip=0)`: Get the commit history from the repository
- `get_commit_diff(commit_hash)`: Get the diff for a specific commit
- `create_branch_with_commits(new_branch_name, base_branch="HEAD", commit_hashes=None)`: Create a new branch with specified commits
- `squash_commits(branch_name, commit_hashes, message)`: Squash multiple commits into one with a new message
- `generate_repository_stats()`: Generate statistics about the repository

# Git History Analyzer Agent

The Git History Analyzer Agent is an extension for AutoGen that helps improve repository history by analyzing commit messages, identifying related commits for squashing, and generating standardized commit messages according to conventions. It uses AI-powered analysis to intelligently group related commits and create a cleaner repository history.

## Features

- Analyze git repository history and commit content with AI-powered insights
- Compare commit messages with actual code changes to identify inconsistencies
- Identify related/linked commits that could be squashed together using multiple strategies
- Generate standardized commit messages following conventions (e.g., React)
- Create a new branch with reorganized commits while preserving original changes
- Support for pagination to handle large repositories efficiently
- Detailed operation logging for tracking repository changes
- Intelligent analysis of commit relationships using LLM capabilities

## Installation

```bash
pip install autogen-ext
```

## Basic Usage

```python
import asyncio
from autogen_ext.agents.git_analyzer import GitHistoryAnalyzerAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    # Initialize the model client
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    # Initialize the agent
    agent = GitHistoryAnalyzerAgent(
        model_client=model_client,
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
    
    # Close the model client
    await model_client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Usage: Merging Related Commits

```python
import asyncio
from datetime import datetime
from autogen_ext.agents.git_analyzer import GitHistoryAnalyzerAgent, GitTools
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def merge_related_commits():
    # Initialize with DeepSeek API
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key="your_deepseek_api_key",
        api_base="https://api.deepseek.com/v1"
    )
    
    # Initialize the agent
    agent = GitHistoryAnalyzerAgent(
        model_client=model_client,
        repo_path="/path/to/your/repo",
        commit_message_convention="react"
    )
    
    # Find related commits using time-based grouping
    report = await agent.analyze_repository(
        branch="main",
        max_count=50,
        group_strategy="time"
    )
    
    # Find a group with multiple commits
    merge_group = None
    for group in report['commit_groups']:
        if len(group['commits']) > 1:
            merge_group = group
            break
    
    if merge_group:
        # Create a new branch name with timestamp
        timestamp = int(datetime.now().timestamp())
        new_branch = f"merged-commits-{timestamp}"
        
        # Get commit hashes
        commit_hashes = [commit['hash'] for commit in merge_group['commits']]
        
        # Get an improved commit message
        improved = await agent.improve_commit_message(merge_group['commits'][0]['hash'])
        
        # Create a new branch with merged commits
        git_tools = GitTools(agent.repo_path)
        
        # Get the current branch
        current_branch = git_tools.repo.active_branch.name
        
        # Create a new branch
        git_tools.repo.git.checkout('-b', new_branch)
        
        # Get the parent of the oldest commit
        oldest_commit = merge_group['commits'][-1]
        parent_commit = git_tools.repo.commit(oldest_commit['hash']).parents[0].hexsha
        
        # Reset to the parent commit
        git_tools.repo.git.reset('--hard', parent_commit)
        
        # Cherry-pick all commits in the group
        for commit_hash in reversed(commit_hashes):
            git_tools.repo.git.cherry_pick(commit_hash)
        
        # Squash the commits
        git_tools.repo.git.reset('--soft', parent_commit)
        
        # Commit with the improved message
        git_tools.repo.git.commit('-m', improved['standardized_message'])
        
        # Return to the original branch
        git_tools.repo.git.checkout(current_branch)
        
        print(f"Successfully created branch '{new_branch}' with merged commits")
    else:
        print("No groups with multiple commits found")
    
    # Close the model client
    await model_client.close()

if __name__ == "__main__":
    asyncio.run(merge_related_commits())
```

## Grouping Strategies

The agent supports different strategies for grouping related commits:

- `pr`: Group commits by PR numbers mentioned in commit messages
  - Identifies PR numbers using regex pattern `#(\d+)`
  - Groups commits with the same PR number
  - Useful for repositories that follow PR-based workflow

- `files`: Group commits that modify the same files
  - Groups commits that touch the same files
  - Useful for identifying changes to related components
  - Helps find commits that should be reviewed together

- `time`: Group commits made within a short time window by the same author
  - Default time window is 1 hour (3600 seconds)
  - Groups commits by the same author within the time window
  - Useful for finding commits that are part of the same logical change

## Commit Message Conventions

The agent can generate standardized commit messages following different conventions:

- `react`: Uses prefixes like 'feat', 'fix', 'chore', 'docs', 'style', 'refactor', 'perf', or 'test'
  - `feat`: A new feature
  - `fix`: A bug fix
  - `docs`: Documentation only changes
  - `style`: Changes that do not affect the meaning of the code
  - `refactor`: A code change that neither fixes a bug nor adds a feature
  - `perf`: A code change that improves performance
  - `test`: Adding missing tests or correcting existing tests
  - `chore`: Changes to the build process or auxiliary tools

- Other conventions can be added by extending the agent

## Intelligent Analysis

The agent uses AI-powered analysis to:

1. Analyze code changes and compare them with commit messages
2. Identify inconsistencies between commit messages and actual changes
3. Generate improved commit messages that accurately describe changes
4. Detect potential issues in the code changes
5. Group related commits based on content similarity, not just metadata

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
  - `branch`: The branch to analyze
  - `max_count`: Maximum number of commits to analyze
  - `group_strategy`: Strategy for grouping commits ("pr", "files", or "time")
  - Returns a dictionary with repository analysis information

- `analyze_commit(commit_hash)`: Analyze a specific commit and provide detailed information
  - `commit_hash`: The hash of the commit to analyze
  - Returns a dictionary with commit analysis information

- `improve_commit_message(commit_hash)`: Generate an improved commit message based on the commit content
  - `commit_hash`: The hash of the commit to improve
  - Returns a dictionary with original and improved commit messages

- `group_related_commits(branch="HEAD", max_count=100, group_by="pr")`: Group related commits that should be squashed together
  - `branch`: The branch to analyze
  - `max_count`: Maximum number of commits to analyze
  - `group_by`: Strategy for grouping commits ("pr", "files", or "time")
  - Returns a list of commit groups

- `create_new_branch(groups, new_branch_name)`: Create a new branch with reorganized commits
  - `groups`: List of commit groups to reorganize
  - `new_branch_name`: Name for the new branch
  - Returns a message with the result of the operation

### GitTools

Utility class for git operations:

```python
GitTools(repo_path=".")
```

#### Methods

- `get_commit_history(branch="HEAD", max_count=100, skip=0)`: Get the commit history from the repository
  - `branch`: The branch to get history from
  - `max_count`: Maximum number of commits to retrieve
  - `skip`: Number of commits to skip (for pagination)
  - Returns a list of commit dictionaries

- `get_commit_diff(commit_hash)`: Get the diff for a specific commit
  - `commit_hash`: The hash of the commit
  - Returns a dictionary mapping filenames to their diffs

- `create_branch_with_commits(new_branch_name, base_branch="HEAD", commit_hashes=None)`: Create a new branch with specified commits
  - `new_branch_name`: Name for the new branch
  - `base_branch`: Base branch to start from
  - `commit_hashes`: List of commit hashes to include
  - Returns a result message

- `squash_commits(branch_name, commit_hashes, message)`: Squash multiple commits into one with a new message
  - `branch_name`: Name of branch to work on
  - `commit_hashes`: List of commit hashes to squash
  - `message`: New commit message
  - Returns a result message

- `generate_repository_stats()`: Generate statistics about the repository
  - Returns a dictionary with repository statistics

## Example Output

```python
# Repository Analysis Report
{
    "repository": "/path/to/repo",
    "branch_analyzed": "main",
    "commits_count": 50,
    "commit_groups": [
        {
            "commits": [
                {
                    "hash": "abcd1234...",
                    "short_hash": "abcd123",
                    "message": "Add feature X (#123)",
                    "author": "John Doe <john@example.com>",
                    "date": "2025-04-01T12:34:56",
                    "is_merge": False
                },
                {
                    "hash": "efgh5678...",
                    "short_hash": "efgh567",
                    "message": "Fix bug in feature X (#123)",
                    "author": "John Doe <john@example.com>",
                    "date": "2025-04-01T13:45:12",
                    "is_merge": False
                }
            ],
            "suggested_message": "PR #123: Add and fix feature X",
            "pr_number": 123
        }
    ],
    "sample_analyses": [
        {
            "original_commit": {...},
            "analysis": "This commit adds feature X with proper error handling..."
        }
    ],
    "group_strategy": "pr"
}

# Improved Commit Message
{
    "original_commit_hash": "abcd1234...",
    "standardized_message": "feat: Add feature X with proper error handling",
    "original_message": "Add feature X (#123)",
    "code_analysis": "This commit adds a new feature X with proper error handling...",
    "potential_issues": [
        "Missing unit tests for edge cases",
        "Could improve performance by caching results"
    ]
}
```

## Pagination Support

For large repositories, the agent supports pagination to avoid loading all commits at once:

```python
# First batch of commits
report1 = await agent.analyze_repository(
    branch="main",
    max_count=50,
    group_strategy="pr"
)

# Second batch of commits
report2 = await agent.analyze_repository(
    branch="main",
    max_count=50,
    skip=50,  # Skip the first 50 commits
    group_strategy="pr"
)
```

## Model Client Configuration

The agent supports different model clients for AI-powered analysis:

```python
# Using OpenAI
from autogen_ext.models.openai import OpenAIChatCompletionClient
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key="your_openai_api_key"
)

# Using DeepSeek
model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    api_key="your_deepseek_api_key",
    api_base="https://api.deepseek.com/v1"
)

# Using Anthropic
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
model_client = AnthropicChatCompletionClient(
    model="claude-3-opus-20240229",
    api_key="your_anthropic_api_key"
)
```

## Operation Logging

The agent can log all operations performed on the repository:

```python
# Initialize the agent with logging
agent = GitHistoryAnalyzerAgent(
    model_client=model_client,
    repo_path="/path/to/your/repo",
    commit_message_convention="react",
    log_operations=True,
    log_file="/path/to/operations.log"
)

# Get the operations log
operations_log = agent.get_operations_log()
print(operations_log)

# Save the operations log to a file
agent.save_operations_log("/path/to/operations.log")
```

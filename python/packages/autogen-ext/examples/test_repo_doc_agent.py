"""Test script for the Repository Documentation Agent.

This script demonstrates how to use the Repository Documentation Agent
to analyze a repository and generate comprehensive documentation.
"""

import asyncio
import os
import sys
from pathlib import Path

from autogen_agentchat.ui import Console
from autogen_ext.agents.repo_doc import RepoDocAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def analyze_repository(repo_path: str) -> str:
    """Analyze a repository and return the generated documentation.
    
    Args:
        repo_path: Path to the repository to analyze
        
    Returns:
        The generated markdown documentation
    """
    print(f"Analyzing repository at: {repo_path}")
    
    model_client = OpenAIChatCompletionClient(model="gpt-4")
    
    agent = RepoDocAgent(
        name="repo_doc_agent",
        model_client=model_client,
        repo_path=repo_path,
    )
    
    result = await agent.run(
        task=f"Generate comprehensive documentation for the repository at path: {repo_path}"
    )
    
    documentation = result.chat_message.content
    
    return documentation


async def save_documentation(documentation: str, output_path: str) -> None:
    """Save the documentation to a file.
    
    Args:
        documentation: The markdown documentation to save
        output_path: Path to save the documentation to
    """
    print(f"Saving documentation to: {output_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(documentation)
    
    print(f"Documentation saved to: {output_path}")


async def main() -> None:
    """Run the repository documentation agent test."""
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = os.getcwd()
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = os.path.join(os.getcwd(), "repository_documentation.md")
    
    documentation = await analyze_repository(repo_path)
    
    await save_documentation(documentation, output_path)
    
    print("\nSample of the generated documentation:")
    print("=" * 80)
    print(documentation[:500] + "..." if len(documentation) > 500 else documentation)
    print("=" * 80)
    
    print(f"\nFull documentation saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())

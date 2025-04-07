"""Demo script for the Repository Documentation Agent.

This script demonstrates how to use the Repository Documentation Agent
to analyze a repository and generate comprehensive documentation.

Usage:
    python run_repo_doc_demo.py [repo_path] [output_path]

Example:
    python run_repo_doc_demo.py ~/repos/autogen ~/repo_documentation.md
"""

import asyncio
import os
import sys
from pathlib import Path

from autogen_agentchat.ui import Console
from autogen_ext.agents.repo_doc import RepoDocAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def main() -> None:
    """Run the repository documentation agent demo."""
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = os.path.join(os.path.expanduser("~"), "repos", "autogen")
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = os.path.join(os.getcwd(), "repository_documentation.md")
    
    print(f"Analyzing repository at: {repo_path}")
    print(f"Documentation will be saved to: {output_path}")
    
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
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(documentation)
    
    print(f"\nDocumentation generated successfully!")
    print(f"Documentation saved to: {output_path}")
    
    print("\nSample of the generated documentation:")
    print("=" * 80)
    print(documentation[:500] + "..." if len(documentation) > 500 else documentation)
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

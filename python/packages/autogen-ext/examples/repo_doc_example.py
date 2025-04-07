"""Example usage of the repository documentation agent."""

import asyncio
import os
import sys

from autogen_agentchat.ui import Console
from autogen_ext.agents.repo_doc import RepoDocAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def main() -> None:
    """Run the repository documentation agent example."""
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = os.getcwd()
    
    print(f"Analyzing repository at: {repo_path}")
    
    model_client = OpenAIChatCompletionClient(model="gpt-4")
    
    agent = RepoDocAgent(
        name="repo_doc_agent",
        model_client=model_client,
        repo_path=repo_path,
    )
    
    await Console(
        agent.run_stream(
            task=f"Generate comprehensive documentation for the repository at path: {repo_path}"
        )
    )


if __name__ == "__main__":
    asyncio.run(main())

import logging
import os
from typing import Any, Dict, List, Optional, Union

from autogen_agentchat.agents import AssistantAgent
from autogen_core import Component
from autogen_core.memory import Memory
from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.code_repository.memory import CodeRepositoryMemory, CodeRepositoryMemoryConfig
from pydantic import BaseModel, Field
from typing_extensions import Self

logger = logging.getLogger(__name__)

class CodeRepositoryAgentConfig(BaseModel):
    """Configuration for the code repository agent."""
    
    name: str = Field(default="code_repository_agent", description="Name of the agent")
    model_client: Dict[str, Any] = Field(description="Model client configuration") 
    repository_path: str = Field(default="", description="Path to the local repository")
    repository_url: str = Field(default="", description="URL to the repository, used if repository_path is not provided")
    persistence_path: str = Field(default="./code_repo_db", description="Path for persistent storage")
    system_message: str = Field(
        default="You are a helpful AI assistant specialized in understanding and answering questions about code repositories. "
               "When asked a question, you'll search the repository for relevant code and provide detailed, accurate answers "
               "based on the actual implementation.",
        description="System message for the agent",
    )
    code_repo_memory: Dict[str, Any] = Field(default={}, description="Additional configuration for CodeRepositoryMemory")
    description: str = Field(
        default="A specialized agent for code repository understanding and question answering",
        description="Description of the agent",
    )

class CodeRepositoryAgent(Component[CodeRepositoryAgentConfig]):
    """Agent for code repository vectorization and querying.
    
    This agent extends AssistantAgent and provides functionality to vectorize and query
    code repositories. It can accept a repository URL or path, check if it's already 
    vectorized, process it if not, and then enable question-answering functionality.
    
    Args:
        config (CodeRepositoryAgentConfig): Configuration for the agent
        
    Example:
        ```python
        import asyncio
        from autogen_ext.agents.code_repository.agent import CodeRepositoryAgent, CodeRepositoryAgentConfig
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        async def main():
            model_client = OpenAIChatCompletionClient(
                model="gpt-4o",
            )
            
            agent = CodeRepositoryAgent(
                config=CodeRepositoryAgentConfig(
                    name="repo_agent",
                    repository_url="https://github.com/username/repo",
                    persistence_path="./code_repo_db",
                    model_client=model_client.dump_component().dict(),
                )
            )
            
            await agent.prepare()
            
            response = await agent.run(task="How is database connection handled in this repository?")
            print(response)
            
            await agent.close()
            
        asyncio.run(main())
        ```
    """
    
    component_config_schema = CodeRepositoryAgentConfig
    
    def __init__(self, config: CodeRepositoryAgentConfig) -> None:
        """Initialize CodeRepositoryAgent."""
        self._config = config
        self._code_repo_memory = None
        self._assistant_agent = None
        
    async def prepare(self) -> bool:
        """Prepare the agent by vectorizing the repository if needed.
        
        Returns:
            bool: True if the repository is now vectorized and the agent is ready
        """
        if not self._config.repository_path and not self._config.repository_url:
            raise ValueError("Either repository_path or repository_url must be provided")
        
        if self._code_repo_memory is None:
            memory_config = CodeRepositoryMemoryConfig(
                repository_path=self._config.repository_path,
                repository_url=self._config.repository_url,
                persistence_path=self._config.persistence_path,
                allow_reset=True,
                **self._config.code_repo_memory,
            )
            
            self._code_repo_memory = CodeRepositoryMemory(config=memory_config)
        
        is_vectorized = await self._code_repo_memory.is_vectorized()
        
        if not is_vectorized:
            logger.info("Repository not vectorized. Starting vectorization process...")
            chunk_count = await self._code_repo_memory.vectorize_repository()
            logger.info(f"Vectorization complete. Added {chunk_count} chunks to the database.")
        else:
            logger.info("Repository already vectorized. Ready to answer questions.")
        
        if self._assistant_agent is None:
            from autogen_core import load_component
            model_client = load_component(self._config.model_client)
            
            self._assistant_agent = AssistantAgent(
                name=self._config.name,
                model_client=model_client,
                memory=[self._code_repo_memory],
                system_message=self._config.system_message,
                description=self._config.description,
            )
        
        return True
        
    async def run(self, task: str) -> str:
        """Run a query against the vectorized repository.
        
        Args:
            task (str): The query to run
            
        Returns:
            str: The agent's response
        """
        if not self._assistant_agent:
            await self.prepare()
        
        response = await self._assistant_agent.run(task=task)
        return response
    
    async def close(self) -> None:
        """Close and clean up resources."""
        if self._code_repo_memory:
            await self._code_repo_memory.close()
            self._code_repo_memory = None
        
        self._assistant_agent = None
    
    def _to_config(self) -> CodeRepositoryAgentConfig:
        """Serialize the agent configuration."""
        return self._config
    
    @classmethod
    def _from_config(cls, config: CodeRepositoryAgentConfig) -> Self:
        """Deserialize the agent configuration."""
        return cls(config=config)

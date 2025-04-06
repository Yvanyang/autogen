import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import git
from autogen_core import CancellationToken
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType, MemoryQueryResult, UpdateContextResult
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import SystemMessage
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig
from pydantic import BaseModel, Field
from typing_extensions import Self

logger = logging.getLogger(__name__)

class CodeRepositoryMemoryConfig(PersistentChromaDBVectorMemoryConfig):
    """Configuration for code repository memory."""

    repository_path: str = Field(default="", description="Path to the local repository")
    repository_url: str = Field(default="", description="URL to the repository, used if repository_path is not provided")
    collection_prefix: str = Field(default="code_repo_", description="Prefix for ChromaDB collections")
    include_file_types: List[str] = Field(
        default=["py", "js", "ts", "java", "c", "cpp", "cs", "go", "rs", "php", "rb", "swift", "md", "txt", "html", "css", "json", "yaml", "yml"],
        description="File extensions to include in vectorization",
    )
    exclude_patterns: List[str] = Field(
        default=[
            r"\.git/", r"node_modules/", r"__pycache__/", r"\.venv/", r"\.env/",
            r"\.pyc$", r"\.pyo$", r"\.pyd$", r"\.so$", r"\.dll$", r"\.exe$", 
            r"\.png$", r"\.jpg$", r"\.jpeg$", r"\.gif$", r"\.svg$", r"\.ico$",
            r"\.min\.js$", r"\.min\.css$", r"\.ttf$", r"\.woff$", r"\.woff2$",
        ],
        description="Regular expressions for files/directories to exclude from vectorization",
    )
    chunk_size: int = Field(default=1000, description="Number of characters per chunk")
    chunk_overlap: int = Field(default=200, description="Number of characters to overlap between chunks")
    max_file_size: int = Field(default=500000, description="Maximum file size in bytes to process (0 = no limit)")
    check_first: int = Field(default=5000, description="Number of characters to check to determine if file is binary")

class CodeRepositoryMemory(ChromaDBVectorMemory):
    """Memory for code repositories.
    
    This memory implementation extends ChromaDBVectorMemory to handle code repositories.
    It provides functionality to vectorize a repository (local or remote) and query it.
    
    Args:
        config (CodeRepositoryMemoryConfig): Configuration for the code repository memory
    
    Example:
        ```python
        from autogen_ext.agents.code_repository.memory import CodeRepositoryMemory, CodeRepositoryMemoryConfig
        
        memory = CodeRepositoryMemory(
            config=CodeRepositoryMemoryConfig(
                repository_path="/path/to/local/repo",
                persistence_path="./code_repo_db",
                allow_reset=True,
            )
        )
        
        if not await memory.is_vectorized():
            await memory.vectorize_repository()
            
        results = await memory.query("How is the database connection implemented?")
        for result in results.results:
            print(f"File: {result.metadata.get('file_path')}")
            print(f"Content: {result.content}")
            print(f"Score: {result.metadata.get('score')}")
        ```
    """
    
    def __init__(self, config: CodeRepositoryMemoryConfig) -> None:
        """Initialize CodeRepositoryMemory."""
        self._repo_config = config
        collection_name = self._get_collection_name()
        
        chromadb_config = PersistentChromaDBVectorMemoryConfig(
            client_type="persistent",
            collection_name=collection_name,
            persistence_path=config.persistence_path,
            distance_metric=config.distance_metric,
            k=config.k,
            score_threshold=config.score_threshold,
            allow_reset=config.allow_reset,
            tenant=config.tenant,
            database=config.database,
        )
        
        super().__init__(config=chromadb_config)
        
        self._repo_path = self._repo_config.repository_path
        self._temp_dir = None
    
    def _get_collection_name(self) -> str:
        """Get the collection name based on repository path or URL."""
        if self._repo_config.repository_path:
            repo_name = os.path.basename(os.path.normpath(self._repo_config.repository_path))
        elif self._repo_config.repository_url:
            repo_name = os.path.basename(self._repo_config.repository_url)
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
        else:
            raise ValueError("Either repository_path or repository_url must be provided")
        
        sanitized_name = re.sub(r"[^a-zA-Z0-9_]", "_", repo_name)
        return f"{self._repo_config.collection_prefix}{sanitized_name}"
        
    async def is_vectorized(self) -> bool:
        """Check if the repository is already vectorized.
        
        Returns:
            bool: True if the repository is already vectorized, False otherwise
        """
        self._ensure_initialized()
        if self._collection is None:
            return False
        
        try:
            results = self._collection.get()
            return results["ids"] and len(results["ids"]) > 0
        except Exception as e:
            logger.error(f"Error checking if repository is vectorized: {e}")
            return False
    
    async def vectorize_repository(self) -> int:
        """Vectorize the repository.
        
        This method processes all files in the repository and adds them to the vector database.
        If a repository URL is provided and no local path, it will clone the repository to a
        temporary directory.
        
        Returns:
            int: Number of chunks added to the vector database
        """
        if not self._repo_path and self._repo_config.repository_url:
            self._temp_dir = tempfile.TemporaryDirectory()
            self._repo_path = self._temp_dir.name
            
            logger.info(f"Cloning repository from {self._repo_config.repository_url} to {self._repo_path}")
            try:
                git.Repo.clone_from(self._repo_config.repository_url, self._repo_path)
            except Exception as e:
                logger.error(f"Error cloning repository: {e}")
                if self._temp_dir:
                    self._temp_dir.cleanup()
                    self._temp_dir = None
                raise RuntimeError(f"Failed to clone repository: {e}")
        
        if not self._repo_path or not os.path.isdir(self._repo_path):
            raise ValueError("Invalid repository path")
        
        await self.clear()
        
        chunk_count = 0
        for file_path, content in self._walk_repository():
            chunks = self._chunk_content(content, file_path)
            
            for i, chunk in enumerate(chunks):
                await self.add(
                    MemoryContent(
                        content=chunk,
                        mime_type=MemoryMimeType.TEXT,
                        metadata={
                            "file_path": file_path,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                        }
                    )
                )
                chunk_count += 1
        
        logger.info(f"Added {chunk_count} chunks from repository to vector database")
        return chunk_count
    
    def _walk_repository(self) -> List[Tuple[str, str]]:
        """Walk through the repository and yield file path and content.
        
        Returns:
            List[Tuple[str, str]]: List of tuples with file path (relative to repo root) and content
        """
        repo_files = []
        exclude_patterns = [re.compile(pattern) for pattern in self._repo_config.exclude_patterns]
        
        for root, _, files in os.walk(self._repo_path):
            if any(pattern.search(os.path.relpath(root, self._repo_path)) for pattern in exclude_patterns):
                continue
            
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, self._repo_path)
                
                if any(pattern.search(rel_path) for pattern in exclude_patterns):
                    continue
                
                file_ext = os.path.splitext(file)[1].lstrip('.')
                if file_ext not in self._repo_config.include_file_types:
                    continue
                
                if self._repo_config.max_file_size > 0:
                    file_size = os.path.getsize(abs_path)
                    if file_size > self._repo_config.max_file_size:
                        logger.warning(f"Skipping large file: {rel_path} ({file_size} bytes)")
                        continue
                
                try:
                    content = self._read_file(abs_path)
                    if content:  # Skip if None (binary files)
                        repo_files.append((rel_path, content))
                except Exception as e:
                    logger.warning(f"Error reading file {rel_path}: {e}")
        
        return repo_files
    
    def _read_file(self, file_path: str) -> Optional[str]:
        """Read file content, checking if it's binary first.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            Optional[str]: File content or None if file is binary
        """
        try:
            with open(file_path, 'rb') as f:
                check_bytes = f.read(self._repo_config.check_first)
                if b'\0' in check_bytes:  # Simple binary check
                    return None
        except Exception as e:
            logger.warning(f"Error checking file {file_path}: {e}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Error reading file {file_path} with latin-1 encoding: {e}")
                return None
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return None
    
    def _chunk_content(self, content: str, file_path: str) -> List[str]:
        """Chunk file content based on chunk size and overlap.
        
        Args:
            content (str): File content
            file_path (str): Path to the file
            
        Returns:
            List[str]: List of chunks
        """
        chunks = []
        
        header = f"File: {file_path}\n\n"
        
        if len(content) < self._repo_config.chunk_size:
            chunks.append(header + content)
            return chunks
        
        current_index = 0
        while current_index < len(content):
            chunk_end = min(current_index + self._repo_config.chunk_size, len(content))
            chunk = content[current_index:chunk_end]
            
            chunk_with_header = header + chunk
            chunks.append(chunk_with_header)
            
            current_index += (self._repo_config.chunk_size - self._repo_config.chunk_overlap)
            
            if current_index >= len(content):
                break
        
        return chunks
    
    async def update_context(
        self,
        model_context: ChatCompletionContext,
    ) -> UpdateContextResult:
        """Update the model context with relevant code repository content.
        
        Args:
            model_context (ChatCompletionContext): The model context to update
            
        Returns:
            UpdateContextResult: Result containing the memories that were used to update the context
        """
        messages = await model_context.get_messages()
        if not messages:
            return UpdateContextResult(memories=MemoryQueryResult(results=[]))
        
        last_message = messages[-1]
        query_text = last_message.content if isinstance(last_message.content, str) else str(last_message)
        
        query_results = await self.query(query_text)
        
        if query_results.results:
            memory_strings = []
            for i, memory in enumerate(query_results.results, 1):
                file_path = memory.metadata.get("file_path", "unknown")
                score = memory.metadata.get("score", 0.0)
                memory_strings.append(f"{i}. File: {file_path} (relevance: {score:.2f})\n```\n{memory.content}\n```")
            
            memory_context = "\nRelevant code repository files:\n" + "\n\n".join(memory_strings)
            
            await model_context.add_message(SystemMessage(content=memory_context))
        
        return UpdateContextResult(memories=query_results)
    
    async def close(self) -> None:
        """Clean up resources."""
        await super().close()
        
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None

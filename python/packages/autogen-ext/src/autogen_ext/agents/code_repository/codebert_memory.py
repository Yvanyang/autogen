"""CodeBERT-based memory for code repositories."""

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import git
import numpy as np
import torch
from autogen_core import CancellationToken
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType, MemoryQueryResult, UpdateContextResult
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import SystemMessage
from pydantic import BaseModel, Field
from transformers import AutoModel, AutoTokenizer
from typing_extensions import Self

logger = logging.getLogger(__name__)

class CodeBERTRepositoryMemoryConfig(BaseModel):
    """Configuration for CodeBERT repository memory."""

    repository_path: str = Field(default="", description="Path to the local repository")
    repository_url: str = Field(default="", description="URL to the repository, used if repository_path is not provided")
    persistence_path: str = Field(default="./code_repo_db", description="Path for persistent storage")
    model_name: str = Field(default="microsoft/codebert-base", description="CodeBERT model name")
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
    chunk_size: int = Field(default=512, description="Number of characters per chunk")
    chunk_overlap: int = Field(default=100, description="Number of characters to overlap between chunks")
    max_file_size: int = Field(default=500000, description="Maximum file size in bytes to process (0 = no limit)")
    check_first: int = Field(default=5000, description="Number of characters to check to determine if file is binary")
    max_sequence_length: int = Field(default=512, description="Maximum sequence length for CodeBERT tokenizer")
    top_k: int = Field(default=5, description="Number of top results to return in query")
    score_threshold: float = Field(default=0.5, description="Minimum similarity score threshold")

class CodeBERTRepositoryMemory(Memory):
    """Memory for code repositories using CodeBERT embeddings.
    
    This memory implementation uses CodeBERT to generate embeddings for code files
    and provides functionality to vectorize a repository (local or remote) and query it.
    
    Args:
        config (CodeBERTRepositoryMemoryConfig): Configuration for the CodeBERT repository memory
    
    Example:
        ```python
        from autogen_ext.agents.code_repository.codebert_memory import CodeBERTRepositoryMemory, CodeBERTRepositoryMemoryConfig
        
        memory = CodeBERTRepositoryMemory(
            config=CodeBERTRepositoryMemoryConfig(
                repository_path="/path/to/local/repo",
                persistence_path="./code_repo_db",
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
    
    def __init__(self, config: CodeBERTRepositoryMemoryConfig) -> None:
        """Initialize CodeBERTRepositoryMemory."""
        self._config = config
        
        self._repo_path = self._config.repository_path
        self._temp_dir = None
        
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._tokenizer = None
        self._model = None
        
        self._embeddings = []
        self._contents = []
        self._metadata = []
        
        os.makedirs(self._config.persistence_path, exist_ok=True)
        
        self._db_path = self._get_db_path()
    
    def _get_db_path(self) -> str:
        """Get the database path based on repository path or URL."""
        if self._config.repository_path:
            repo_name = os.path.basename(os.path.normpath(self._config.repository_path))
        elif self._config.repository_url:
            repo_name = os.path.basename(self._config.repository_url)
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
        else:
            raise ValueError("Either repository_path or repository_url must be provided")
        
        sanitized_name = re.sub(r"[^a-zA-Z0-9_]", "_", repo_name)
        return os.path.join(self._config.persistence_path, f"codebert_{sanitized_name}")
    
    async def _load_model(self) -> None:
        """Load CodeBERT model and tokenizer."""
        if self._model is None or self._tokenizer is None:
            logger.info(f"Loading CodeBERT model: {self._config.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self._config.model_name)
            self._model = AutoModel.from_pretrained(self._config.model_name).to(self._device)
            self._model.eval()  # Set model to evaluation mode
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text using CodeBERT."""
        if self._tokenizer is None or self._model is None:
            try:
                await self._load_model()
            except Exception as e:
                logger.error(f"Error loading CodeBERT model: {e}")
                raise RuntimeError(f"Failed to load CodeBERT model: {e}")
        
        if self._tokenizer is None:
            raise RuntimeError("CodeBERT tokenizer is not loaded")
        if self._model is None:
            raise RuntimeError("CodeBERT model is not loaded")
        
        if len(text) > self._config.max_sequence_length * 4:  # Rough character estimate
            text = text[:self._config.max_sequence_length * 4]
        
        try:
            with torch.no_grad():
                inputs = self._tokenizer(
                    text, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True, 
                    max_length=self._config.max_sequence_length
                )
                
                inputs = {k: v.to(self._device) for k, v in inputs.items()}
                
                outputs = self._model(**inputs)
                
                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]
                
                return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")

    
    async def is_vectorized(self) -> bool:
        """Check if the repository is already vectorized.
        
        Returns:
            bool: True if the repository is already vectorized, False otherwise
        """
        embeddings_path = os.path.join(self._db_path, "embeddings.npy")
        contents_path = os.path.join(self._db_path, "contents.npy")
        metadata_path = os.path.join(self._db_path, "metadata.npy")
        
        if os.path.exists(embeddings_path) and os.path.exists(contents_path) and os.path.exists(metadata_path):
            try:
                self._embeddings = np.load(embeddings_path, allow_pickle=True)
                self._contents = np.load(contents_path, allow_pickle=True).tolist()
                self._metadata = np.load(metadata_path, allow_pickle=True).tolist()
                return len(self._embeddings) > 0
            except Exception as e:
                logger.error(f"Error loading vectorized repository: {e}")
                return False
        
        return False
    
    async def vectorize_repository(self) -> int:
        """Vectorize the repository.
        
        This method processes all files in the repository and generates embeddings for them.
        If a repository URL is provided and no local path, it will clone the repository to a
        temporary directory.
        
        Returns:
            int: Number of chunks added to the vector database
        """
        if not self._repo_path and self._config.repository_url:
            self._temp_dir = tempfile.TemporaryDirectory()
            self._repo_path = self._temp_dir.name
            
            logger.info(f"Cloning repository from {self._config.repository_url} to {self._repo_path}")
            try:
                git.Repo.clone_from(self._config.repository_url, self._repo_path)
            except Exception as e:
                logger.error(f"Error cloning repository: {e}")
                if self._temp_dir:
                    self._temp_dir.cleanup()
                    self._temp_dir = None
                raise RuntimeError(f"Failed to clone repository: {e}")
        
        if not self._repo_path or not os.path.isdir(self._repo_path):
            raise ValueError("Invalid repository path")
        
        self._embeddings = []
        self._contents = []
        self._metadata = []
        
        chunk_count = 0
        for file_path, content in self._walk_repository():
            chunks = self._chunk_content(content, file_path)
            
            for i, chunk in enumerate(chunks):
                embedding = await self._get_embedding(chunk)
                
                self._embeddings.append(embedding)
                self._contents.append(chunk)
                self._metadata.append({
                    "file_path": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                })
                
                chunk_count += 1
        
        os.makedirs(self._db_path, exist_ok=True)
        np.save(os.path.join(self._db_path, "embeddings.npy"), np.array(self._embeddings))
        np.save(os.path.join(self._db_path, "contents.npy"), np.array(self._contents))
        np.save(os.path.join(self._db_path, "metadata.npy"), np.array(self._metadata))
        
        logger.info(f"Added {chunk_count} chunks from repository to vector database")
        return chunk_count
    
    def _walk_repository(self) -> List[Tuple[str, str]]:
        """Walk through the repository and yield file path and content.
        
        Returns:
            List[Tuple[str, str]]: List of tuples with file path (relative to repo root) and content
        """
        repo_files = []
        exclude_patterns = [re.compile(pattern) for pattern in self._config.exclude_patterns]
        
        for root, _, files in os.walk(self._repo_path):
            if any(pattern.search(os.path.relpath(root, self._repo_path)) for pattern in exclude_patterns):
                continue
            
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, self._repo_path)
                
                if any(pattern.search(rel_path) for pattern in exclude_patterns):
                    continue
                
                file_ext = os.path.splitext(file)[1].lstrip('.')
                if file_ext not in self._config.include_file_types:
                    continue
                
                if self._config.max_file_size > 0:
                    file_size = os.path.getsize(abs_path)
                    if file_size > self._config.max_file_size:
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
                check_bytes = f.read(self._config.check_first)
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
        
        if len(content) < self._config.chunk_size:
            chunks.append(header + content)
            return chunks
        
        current_index = 0
        while current_index < len(content):
            chunk_end = min(current_index + self._config.chunk_size, len(content))
            chunk = content[current_index:chunk_end]
            
            chunk_with_header = header + chunk
            chunks.append(chunk_with_header)
            
            current_index += (self._config.chunk_size - self._config.chunk_overlap)
            
            if current_index >= len(content):
                break
        
        return chunks
    
    async def add(self, content: MemoryContent) -> None:
        """Add content to memory.
        
        Args:
            content (MemoryContent): Content to add to memory
        """
        text = content.content if isinstance(content.content, str) else str(content.content)
        embedding = await self._get_embedding(text)
        
        self._embeddings.append(embedding)
        self._contents.append(text)
        self._metadata.append(content.metadata or {})
        
        os.makedirs(self._db_path, exist_ok=True)
        np.save(os.path.join(self._db_path, "embeddings.npy"), np.array(self._embeddings))
        np.save(os.path.join(self._db_path, "contents.npy"), np.array(self._contents))
        np.save(os.path.join(self._db_path, "metadata.npy"), np.array(self._metadata))
    
    async def query(
        self, 
        query_text: str, 
        cancellation_token: Optional[CancellationToken] = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        """Query the memory for relevant content.
        
        Args:
            query_text (str): Query text
            cancellation_token (Optional[CancellationToken]): Cancellation token
            **kwargs: Additional arguments
            
        Returns:
            MemoryQueryResult: Query results
        """
        if not self._embeddings or len(self._embeddings) == 0:
            if not await self.is_vectorized():
                logger.warning("Repository not vectorized. Call vectorize_repository() first.")
                return MemoryQueryResult(results=[])
        
        query_embedding = await self._get_embedding(query_text)
        
        similarities = []
        for embedding in self._embeddings:
            similarity = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            similarities.append(similarity)
        
        top_k = min(self._config.top_k, len(similarities))
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            
            if score < self._config.score_threshold:
                continue
            
            metadata = dict(self._metadata[idx])
            metadata["score"] = float(score)
            
            memory_content = MemoryContent(
                content=self._contents[idx],
                mime_type=MemoryMimeType.TEXT,
                metadata=metadata,
            )
            
            results.append(memory_content)
        
        return MemoryQueryResult(results=results)
    
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
    
    async def clear(self) -> None:
        """Clear all memory content."""
        self._embeddings = []
        self._contents = []
        self._metadata = []
        
        embeddings_path = os.path.join(self._db_path, "embeddings.npy")
        contents_path = os.path.join(self._db_path, "contents.npy")
        metadata_path = os.path.join(self._db_path, "metadata.npy")
        
        if os.path.exists(embeddings_path):
            os.remove(embeddings_path)
        if os.path.exists(contents_path):
            os.remove(contents_path)
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
    
    async def close(self) -> None:
        """Clean up resources."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
        
        self._model = None
        self._tokenizer = None

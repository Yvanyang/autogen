import os
import shutil
import tempfile
from pathlib import Path

import pytest
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.agents.code_repository.memory import CodeRepositoryMemory, CodeRepositoryMemoryConfig

@pytest.fixture
def temp_dir():
    """Create a temporary directory for the test."""
    test_dir = tempfile.mkdtemp()
    
    repo_dir = os.path.join(test_dir, "test_repo")
    os.makedirs(repo_dir)
    
    os.makedirs(os.path.join(repo_dir, "src"))
    os.makedirs(os.path.join(repo_dir, "docs"))
    
    with open(os.path.join(repo_dir, "src", "main.py"), "w") as f:
        f.write("def hello_world():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello_world()")
    
    with open(os.path.join(repo_dir, "src", "script.js"), "w") as f:
        f.write("function sayHello() {\n    console.log('Hello from JavaScript');\n}\n\nsayHello();")
    
    with open(os.path.join(repo_dir, "docs", "README.md"), "w") as f:
        f.write("# Test Repository\n\nThis is a test repository for CodeRepositoryMemory tests.")
    
    with open(os.path.join(repo_dir, "src", "binary.bin"), "wb") as f:
        f.write(os.urandom(100))
    
    yield repo_dir
    
    shutil.rmtree(test_dir)

@pytest.fixture
def db_dir():
    """Create a temporary directory for the database."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir)

@pytest.mark.asyncio
async def test_code_repository_memory_initialization(temp_dir, db_dir):
    """Test initialization of CodeRepositoryMemory."""
    memory = CodeRepositoryMemory(
        config=CodeRepositoryMemoryConfig(
            repository_path=temp_dir,
            persistence_path=db_dir,
            allow_reset=True,
        )
    )
    
    assert memory._repo_path == temp_dir
    
    await memory.close()

@pytest.mark.asyncio
async def test_code_repository_vectorization(temp_dir, db_dir):
    """Test repository vectorization."""
    memory = CodeRepositoryMemory(
        config=CodeRepositoryMemoryConfig(
            repository_path=temp_dir,
            persistence_path=db_dir,
            allow_reset=True,
        )
    )
    
    is_vectorized = await memory.is_vectorized()
    assert not is_vectorized
    
    chunk_count = await memory.vectorize_repository()
    
    assert chunk_count >= 3
    
    is_vectorized = await memory.is_vectorized()
    assert is_vectorized
    
    await memory.close()

@pytest.mark.asyncio
async def test_code_repository_query(temp_dir, db_dir):
    """Test querying the vectorized repository."""
    memory = CodeRepositoryMemory(
        config=CodeRepositoryMemoryConfig(
            repository_path=temp_dir,
            persistence_path=db_dir,
            allow_reset=True,
        )
    )
    
    await memory.vectorize_repository()
    
    results = await memory.query("Python hello world function")
    
    assert len(results.results) > 0
    
    python_found = False
    for result in results.results:
        if "main.py" in result.metadata.get("file_path", ""):
            python_found = True
            break
    
    assert python_found
    
    await memory.close()

@pytest.mark.asyncio
async def test_code_repository_collection_name(temp_dir, db_dir):
    """Test collection name generation."""
    memory = CodeRepositoryMemory(
        config=CodeRepositoryMemoryConfig(
            repository_path=temp_dir,
            persistence_path=db_dir,
            collection_prefix="test_prefix_",
            allow_reset=True,
        )
    )
    
    collection_name = memory._get_collection_name()
    assert collection_name.startswith("test_prefix_")
    
    await memory.close()

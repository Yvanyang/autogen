"""
Test script for the documentation generator functionality.
"""
import os
import sys
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent

sys.path.append(str(parent_dir))

from file_scanner import FileScanner
from doc_generator import DocumentationGenerator

def test_doc_generator():
    """Test the documentation generator functionality."""
    print("\n=== Testing Documentation Generator ===")
    
    scanner = FileScanner(current_dir)
    vue_files, _ = scanner.scan()
    analyses = scanner.analyze_all_vue_files()
    
    print(f"Analyzed {len(analyses)} Vue files")
    
    docs_dir = current_dir / "output" / "docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    doc_generator = DocumentationGenerator(docs_dir)
    
    print(f"Generating documentation in {docs_dir}...")
    doc_generator.save_documentation(analyses)
    
    generated_files = list(docs_dir.glob("*.html"))
    print(f"Generated {len(generated_files)} HTML files:")
    for file in generated_files:
        print(f"  - {file}")
    
    return docs_dir

if __name__ == "__main__":
    test_doc_generator()

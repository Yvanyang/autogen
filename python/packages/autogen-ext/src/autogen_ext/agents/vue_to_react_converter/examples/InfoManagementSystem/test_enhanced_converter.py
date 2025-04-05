"""
Test script for the enhanced Vue to React converter using the Information Management System demo.
"""
import os
import asyncio
import sys
from pathlib import Path

current_dir = Path(__file__).parent
converter_dir = current_dir.parent.parent

sys.path.append(str(converter_dir))

from file_scanner import FileScanner
from doc_generator import DocumentationGenerator
from migration_planner import MigrationPlanner
from enhanced_converter import EnhancedVueToReactConverter
from mock_converter import MockModelClient


async def test_file_scanner():
    """Test the file scanner functionality."""
    print("\n=== Testing File Scanner ===")
    
    current_dir = Path(__file__).parent
    
    scanner = FileScanner(current_dir)
    
    vue_files, other_files = scanner.scan()
    
    print(f"Found {len(vue_files)} Vue files:")
    for file in vue_files:
        print(f"  - {file}")
    
    print(f"\nFound {len(other_files)} other files:")
    for file in other_files:
        print(f"  - {file}")
    
    print("\nAnalyzing Vue files...")
    analyses = scanner.analyze_all_vue_files()
    
    for file_path, analysis in analyses.items():
        print(f"\nAnalysis for {file_path}:")
        print(f"  Component name: {analysis['component_name']}")
        print(f"  Line count: {analysis['line_count']}")
        print(f"  Dependencies: {analysis['component_dependencies']}")
    
    stats = scanner.get_file_stats()
    print("\nFile Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return analyses


async def test_doc_generator(analyses):
    """Test the documentation generator functionality."""
    print("\n=== Testing Documentation Generator ===")
    
    current_dir = Path(__file__).parent
    
    docs_dir = current_dir / "output" / "docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    doc_generator = DocumentationGenerator(docs_dir)
    
    print(f"Generating documentation in {docs_dir}...")
    doc_generator.save_documentation(analyses)
    
    print("Documentation generated successfully.")
    print(f"HTML files created: {len(os.listdir(docs_dir))}")
    
    return docs_dir


async def test_migration_planner(analyses):
    """Test the migration planner functionality."""
    print("\n=== Testing Migration Planner ===")
    
    current_dir = Path(__file__).parent
    
    plan_dir = current_dir / "output" / "plan"
    os.makedirs(plan_dir, exist_ok=True)
    
    planner = MigrationPlanner(analyses, max_lines_per_chunk=200, output_dir=plan_dir)
    
    print("Generating migration plan...")
    plan = planner.generate_migration_plan()
    
    print(f"Migration plan generated with {len(plan['chunks'])} chunks:")
    for i, chunk in enumerate(plan['chunks']):
        print(f"  Chunk {i+1}: {len(chunk['components'])} components, {chunk['total_lines']} lines")
        for component in chunk['components']:
            print(f"    - {component['name']} ({component['lines']} lines)")
    
    print("\nGenerating HTML migration plan...")
    planner.generate_migration_plan_html()
    
    print("Migration plan HTML generated successfully.")
    
    return plan_dir


async def test_enhanced_converter():
    """Test the enhanced converter functionality."""
    print("\n=== Testing Enhanced Converter ===")
    
    current_dir = Path(__file__).parent
    
    output_dir = current_dir / "output"
    os.makedirs(output_dir, exist_ok=True)
    
    model_client = MockModelClient()
    
    converter = EnhancedVueToReactConverter(model_client, max_lines_per_chunk=200)
    
    print("Analyzing project...")
    analysis_result = await converter.analyze_project(
        source_dir=current_dir,
        output_dir=output_dir,
        ignore_patterns=[r"output", r"__pycache__", r"\.git"]
    )
    
    print("\nAnalysis result:")
    for key, value in analysis_result.items():
        print(f"  {key}: {value}")
    
    print("\nConverting project...")
    conversion_result = await converter.convert_project(
        source_dir=current_dir,
        output_dir=output_dir,
        ignore_patterns=[r"output", r"__pycache__", r"\.git"]
    )
    
    print("\nConversion result:")
    print(f"  Source directory: {conversion_result['source_dir']}")
    print(f"  Output directory: {conversion_result['output_dir']}")
    print(f"  React directory: {conversion_result['react_dir']}")
    print(f"  Chunks converted: {conversion_result['chunks_converted']}")
    
    return conversion_result


async def main():
    """Run all tests."""
    print("Starting tests for the enhanced Vue to React converter...")
    
    analyses = await test_file_scanner()
    
    docs_dir = await test_doc_generator(analyses)
    
    plan_dir = await test_migration_planner(analyses)
    
    conversion_result = await test_enhanced_converter()
    
    print("\n=== All Tests Completed ===")
    print(f"Documentation generated in: {docs_dir}")
    print(f"Migration plan generated in: {plan_dir}")
    print(f"React components generated in: {conversion_result['react_dir']}")
    print("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())

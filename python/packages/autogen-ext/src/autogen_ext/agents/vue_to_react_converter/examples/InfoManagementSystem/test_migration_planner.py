"""
Test script for the migration planner functionality.
"""
import os
import sys
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent

sys.path.append(str(parent_dir))

from file_scanner import FileScanner
from migration_planner import MigrationPlanner

def test_migration_planner():
    """Test the migration planner functionality."""
    print("\n=== Testing Migration Planner ===")
    
    scanner = FileScanner(current_dir)
    vue_files, _ = scanner.scan()
    analyses = scanner.analyze_all_vue_files()
    
    print(f"Analyzed {len(analyses)} Vue files")
    
    plan_dir = current_dir / "output" / "plan"
    os.makedirs(plan_dir, exist_ok=True)
    
    max_lines_per_chunk = 200
    planner = MigrationPlanner(analyses, max_lines_per_chunk, plan_dir)
    
    print(f"Generating migration plan with max {max_lines_per_chunk} lines per chunk...")
    plan = planner.generate_migration_plan()
    
    print(f"\nMigration plan generated with {len(plan['chunks'])} chunks:")
    for i, chunk in enumerate(plan['chunks']):
        print(f"  Chunk {i+1}: {len(chunk['components'])} components, {chunk['total_lines']} lines")
        for component in chunk['components']:
            print(f"    - {component['name']} ({component['lines']} lines)")
    
    print("\nGenerating HTML migration plan...")
    planner.generate_migration_plan_html()
    
    generated_files = list(plan_dir.glob("*.html")) + list(plan_dir.glob("*.json"))
    print(f"Generated {len(generated_files)} files:")
    for file in generated_files:
        print(f"  - {file}")
    
    return plan_dir

if __name__ == "__main__":
    test_migration_planner()

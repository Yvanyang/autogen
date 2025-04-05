"""
Test script for the file scanner functionality.
"""
import os
import sys
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent

sys.path.append(str(parent_dir))

from file_scanner import FileScanner

def test_file_scanner():
    """Test the file scanner functionality."""
    print("\n=== Testing File Scanner ===")
    
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
        print(f"  Line count: {analysis.get('line_count', 'N/A')}")
        print(f"  Dependencies: {analysis['component_dependencies']}")
    
    stats = scanner.get_file_stats()
    print("\nFile Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return analyses

if __name__ == "__main__":
    test_file_scanner()

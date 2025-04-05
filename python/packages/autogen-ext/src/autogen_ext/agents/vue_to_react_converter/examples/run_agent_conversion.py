"""
Script to run the Vue to React conversion using the mock agent with detailed logging.
"""
import sys
import asyncio
import os
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from agent_converter import EnhancedChatCompletionClient, AgentVueToReactConverter

async def main():
    """Run the Vue to React conversion using the mock agent."""
    model_client = EnhancedChatCompletionClient(
        model="gpt-4",
        api_key="mock-key",
        api_base="mock-base",
        retry_wait_time=1,  # Reduced for faster testing
        max_retry_period=1,
        seed=42
    )
    
    converter = AgentVueToReactConverter(model_client)
    
    source_dir = Path('./InfoManagementSystem')
    output_dir = Path('./InfoManagementSystem-React/src')
    
    print(f"Converting Vue project: {source_dir}")
    print(f"Output directory: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dir / "components", exist_ok=True)
    
    kb_dir = output_dir / ".kb"
    os.makedirs(kb_dir, exist_ok=True)
    kb_path = kb_dir / "vue_to_react_kb.json"
    converter.save_knowledge_base(str(kb_path))
    
    vue_files = list(source_dir.glob("**/*.vue"))
    if not vue_files:
        print("No Vue files found in the source directory.")
        return
    
    print(f"Found {len(vue_files)} Vue files to convert:")
    for vue_file in vue_files:
        print(f"  - {vue_file}")
    
    for vue_file in vue_files:
        print(f"\nConverting {vue_file}...")
        output_subdir = output_dir
        if vue_file.parent.name == "components":
            output_subdir = output_dir / "components"
        
        result = await converter.convert_file(
            vue_file_path=str(vue_file),
            output_dir=str(output_subdir),
            knowledge_base_path=str(kb_path)
        )
        
        print(f"  React component saved to: {result['react_file']}")
        print(f"  CSS saved to: {result['css_file']}")
        print(f"  Report saved to: {result['report_path']}")
        
        if not (output_dir / "index.js").exists():
            with open(output_dir / "index.js", "w") as f:
                f.write("""
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
""")
        
        if not (output_dir / "index.css").exists():
            with open(output_dir / "index.css", "w") as f:
                f.write("""
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
""")
    
    logs_path = converter.save_conversion_logs(output_dir)
    print(f"\nConversion logs saved to: {logs_path}")
    
    print('\nConversion completed successfully!')

if __name__ == '__main__':
    asyncio.run(main())

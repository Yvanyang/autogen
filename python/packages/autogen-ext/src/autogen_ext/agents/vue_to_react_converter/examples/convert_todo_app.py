import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent.parent))

from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.vue_to_react_converter import VueToReactConverter

async def main():
    """
    Example script to convert the Todo app from Vue to React.
    
    Usage:
        python convert_todo_app.py
        
    Environment variables:
        OPENAI_API_KEY: Your OpenAI API key
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it with: export OPENAI_API_KEY=your_api_key")
        return
    
    model_client = ChatCompletionClient(
        model="gpt-4",
        api_key=api_key
    )
    
    converter = VueToReactConverter(model_client)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    vue_file_path = os.path.join(current_dir, "TodoApp.vue")
    output_dir = os.path.join(current_dir, "output")
    
    print(f"Converting Vue component: {vue_file_path}")
    print(f"Output directory: {output_dir}")
    
    result = await converter.convert_file(
        vue_file_path=vue_file_path,
        output_dir=output_dir
    )
    
    print("\nConversion completed!")
    print(f"React component saved to: {result['react_file']}")
    print(f"Test report saved to: {result['report_path']}")
    
    if result['report']:
        print("\nConversion Summary:")
        print(f"Success Rate: {result['report']['summary']['success_rate']}")
        print(f"Components Passed: {result['report']['summary']['components_passed']}/{result['report']['summary']['total_components']}")
        
        if result['report']['areas_of_attention']:
            print("\nAreas Needing Attention:")
            for area in result['report']['areas_of_attention']:
                print(f"- {area['component']}: {', '.join(area['issues'])}")
        
        if result['report']['recommendations']:
            print("\nRecommendations:")
            for rec in result['report']['recommendations']:
                print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main())

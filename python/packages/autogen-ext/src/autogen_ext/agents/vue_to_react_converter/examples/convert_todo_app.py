import asyncio
import os
import sys

from custom_client import CustomChatCompletionClient
from autogen_ext.agents.vue_to_react_converter import VueToReactConverter

async def main():
    """
    Example script to convert the Todo app from Vue to React.
    
    Usage:
        python convert_todo_app.py
        
    Note:
        Before running, configure your API credentials as environment variables.
        See the README for configuration details.
    """
    
    model_client = CustomChatCompletionClient()
    
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
    
    react_file = os.path.join(output_dir, os.path.splitext(os.path.basename(vue_file_path))[0] + '.jsx')
    if os.path.exists(react_file):
        print(f"React component saved to: {react_file}")
    
    report_files = [f for f in os.listdir(output_dir) if f.endswith('_report.json')]
    if report_files:
        report_path = os.path.join(output_dir, report_files[0])
        print(f"Test report saved to: {report_path}")
        
        if os.path.exists(report_path):
            try:
                import json
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                print("\nConversion Summary:")
                if 'summary' in report:
                    summary = report['summary']
                    if 'success_rate' in summary:
                        print(f"Success Rate: {summary['success_rate']}")
                    if 'components_passed' in summary and 'total_components' in summary:
                        print(f"Components Passed: {summary['components_passed']}/{summary['total_components']}")
                
                if 'areas_of_attention' in report and report['areas_of_attention']:
                    print("\nAreas Needing Attention:")
                    for area in report['areas_of_attention']:
                        if 'component' in area and 'issues' in area:
                            print(f"- {area['component']}: {', '.join(area['issues'])}")
                
                if 'recommendations' in report and report['recommendations']:
                    print("\nRecommendations:")
                    for rec in report['recommendations']:
                        print(f"- {rec}")
            except Exception as e:
                print(f"Error parsing report: {e}")
    
    if 'chat_history' in result:
        print("\nConversion Process Summary:")
        print(f"Total messages exchanged: {len(result['chat_history'])}")
        
        agents = {}
        for msg in result['chat_history']:
            if hasattr(msg, 'sender'):
                sender = msg.sender
                agents[sender] = agents.get(sender, 0) + 1
        
        if agents:
            print("\nAgent Participation:")
            for agent, count in agents.items():
                print(f"- {agent}: {count} messages")

if __name__ == "__main__":
    asyncio.run(main())

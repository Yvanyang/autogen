"""
Mock modules for testing the enhanced Vue to React converter.
"""
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import asyncio
import json


class MockChatCompletionClient:
    """Mock implementation of ChatCompletionClient for testing."""
    
    def __init__(self):
        self.messages = []
    
    async def create(self, messages, **kwargs):
        """Mock create method."""
        self.messages.extend(messages)
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a mock response from the model."
                    }
                }
            ]
        }


class MockAssistantAgent:
    """Mock implementation of AssistantAgent for testing."""
    
    def __init__(self, name, llm_config=None):
        self.name = name
        self.llm_config = llm_config
    
    async def generate_reply(self, messages, **kwargs):
        """Mock generate_reply method."""
        return "This is a mock reply from the assistant agent."


class MockUserProxyAgent:
    """Mock implementation of UserProxyAgent for testing."""
    
    def __init__(self, name, human_input_mode="NEVER"):
        self.name = name
        self.human_input_mode = human_input_mode
    
    async def generate_reply(self, messages, **kwargs):
        """Mock generate_reply method."""
        return "This is a mock reply from the user proxy agent."


class MockSelectorGroupChat:
    """Mock implementation of SelectorGroupChat for testing."""
    
    def __init__(self, agents, selector=None):
        self.agents = agents
        self.selector = selector
    
    async def run_stream(self, task, **kwargs):
        """Mock run_stream method."""
        yield f"Starting task: {task}"
        yield "Analyzing Vue component..."
        yield "Converting to React..."
        yield "Verifying conversion..."
        yield "Generated test report at /tmp/mock_report.json"
        yield "Conversion completed successfully."


class MockKnowledgeBase:
    """Mock implementation of KnowledgeBase for testing."""
    
    @classmethod
    def create_default(cls):
        """Create a default knowledge base."""
        return cls()
    
    @classmethod
    def load_from_file(cls, file_path):
        """Load a knowledge base from a file."""
        return cls()
    
    def save_to_file(self, file_path):
        """Save the knowledge base to a file."""
        with open(file_path, 'w') as f:
            json.dump({"mock": "knowledge_base"}, f)


def create_vue_to_react_team(model_client, max_iterations):
    """Mock implementation of create_vue_to_react_team for testing."""
    return MockSelectorGroupChat(
        agents=[
            MockAssistantAgent("analysis_agent"),
            MockAssistantAgent("conversion_agent"),
            MockAssistantAgent("verification_agent"),
            MockAssistantAgent("report_agent"),
            MockUserProxyAgent("user_proxy")
        ]
    )


with open('/tmp/mock_report.json', 'w') as f:
    json.dump({
        "conversion_status": "success",
        "functionality_match": "high",
        "issues": [],
        "recommendations": []
    }, f)

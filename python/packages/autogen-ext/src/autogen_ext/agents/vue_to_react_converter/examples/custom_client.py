import asyncio
import os
import json
from typing import Dict, List, Any, Optional, Union, Sequence, Mapping

from autogen_core.models import ChatCompletionClient, ModelInfo, ModelFamily, ModelCapabilities
from autogen_core.models._types import CreateResult, LLMMessage, RequestUsage, FinishReasons
from autogen_core import CancellationToken
from autogen_core.tools import Tool, ToolSchema
from typing_extensions import AsyncGenerator
from pydantic import BaseModel

class CustomChatCompletionClient(ChatCompletionClient):
    """
    A custom implementation of ChatCompletionClient that works offline.
    This simulates the behavior of an LLM for testing purposes.
    """
    
    def __init__(self, **kwargs):
        self.config = kwargs
        self._usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        print(f"Initialized CustomChatCompletionClient with config: {json.dumps(kwargs, indent=2)}")
    
    async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool | type[BaseModel]] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AsyncGenerator[Union[str, CreateResult], None]:
        """Simulate streaming responses."""
        json_output_bool = True if isinstance(json_output, type) and issubclass(json_output, BaseModel) else json_output
        
        result = await self.create(messages, tools=tools, json_output=json_output_bool, 
                                  extra_create_args=extra_create_args, 
                                  cancellation_token=cancellation_token)
        
        content = result.content
        if content:
            chunks = content.split("\n\n")
            for chunk in chunks:
                yield chunk + "\n\n"
                await asyncio.sleep(0.1)  # Simulate delay between chunks
        
        yield result
    
    async def close(self) -> None:
        """Close the client."""
        pass
    
    def actual_usage(self) -> RequestUsage:
        """Return the actual usage."""
        return self._usage
    
    def total_usage(self) -> RequestUsage:
        """Return the total usage."""
        return self._total_usage
    
    def count_tokens(self, messages: Sequence[LLMMessage], *, tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Count tokens in messages."""
        total = 0
        for message in messages:
            if hasattr(message, 'content') and message.content:
                total += len(str(message.content)) // 4
        return total
    
    def remaining_tokens(self, messages: Sequence[LLMMessage], *, tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Calculate remaining tokens."""
        return 8000 - self.count_tokens(messages, tools=tools)
    
    @property
    def capabilities(self) -> ModelCapabilities:
        """Return model capabilities."""
        return {
            "vision": False,
            "function_calling": True,
            "json_output": True
        }
    
    @property
    def model_info(self) -> ModelInfo:
        """Return model info."""
        return {
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": ModelFamily.GPT_4,
            "structured_output": True
        }
    
    async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool | type[BaseModel]] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        """
        Simulate the create method to return appropriate responses based on the messages.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional arguments
            
        Returns:
            A simulated chat completion response
        """
        last_message = messages[-1].content if messages and hasattr(messages[-1], 'content') else ""
        
        if "analyze" in str(last_message).lower() or "code_analysis_agent" in str(last_message).lower():
            return self._analysis_agent_response(messages)
        elif "convert" in str(last_message).lower() or "conversion_agent" in str(last_message).lower():
            return self._conversion_agent_response(messages)
        elif "verify" in str(last_message).lower() or "verification_agent" in str(last_message).lower():
            return self._verification_agent_response(messages)
        elif "report" in str(last_message).lower() or "report_generation_agent" in str(last_message).lower():
            return self._report_agent_response(messages)
        elif "select" in str(last_message).lower() or "coordinator" in str(last_message).lower():
            return self._selector_response(messages)
        else:
            return CreateResult(
                finish_reason="stop",
                content="I'm not sure how to respond to that. Please provide more context.",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
    
    def _analysis_agent_response(self, messages: Sequence[LLMMessage]) -> CreateResult:
        """Generate a response for the Analysis Agent."""
        return CreateResult(
            finish_reason="stop",
            content="""I've analyzed the Vue component and here are my findings:

1. Component Structure:
   - Single file component with template, script, and style sections
   - Uses Vue's standard component format

2. Data Properties:
   - newTodo: String for input field
   - todos: Array of todo objects with text and completed properties

3. Computed Properties:
   - completedCount: Calculates number of completed todos

4. Methods:
   - addTodo: Adds a new todo item
   - removeTodo: Removes a todo by index
   - clearCompleted: Filters out completed todos

5. Template Features:
   - v-model for two-way binding on input
   - v-for for list rendering
   - v-if for conditional rendering
   - Event handling with @click
   - Class binding with :class

6. Styling:
   - Scoped CSS with component-specific styling
   - Responsive design elements

This component follows Vue's composition pattern and should be converted to a React functional component with hooks.
""",
            usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
            cached=False
        )
    
    def _conversion_agent_response(self, messages: Sequence[LLMMessage]) -> CreateResult:
        """Generate a response for the Conversion Agent."""
        if any("analyze_vue_component" in str(message) for message in messages):
            return CreateResult(
                finish_reason="tool_calls",
                content=None,
                tool_calls=[{
                    "id": "call_01",
                    "type": "function",
                    "function": {
                        "name": "convert_vue_to_react",
                        "arguments": json.dumps({
                            "vue_file_path": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/TodoApp.vue",
                            "output_dir": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/output",
                            "knowledge_base_path": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/output/.kb/vue_to_react_kb.json"
                        })
                    }
                }],
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        else:
            return CreateResult(
                finish_reason="stop",
                content="""I've converted the Vue component to React following the knowledge base guidelines. The conversion includes:

1. Transformed template to JSX:
   - Converted v-for to map()
   - Converted v-if to conditional rendering with &&
   - Converted v-model to value/onChange pattern
   - Transformed event handlers

2. State Management:
   - Converted data() properties to useState hooks
   - Implemented computed properties with useMemo

3. Methods:
   - Converted Vue methods to React functions
   - Implemented proper state updates with setters

4. Styling:
   - Preserved all original styles
   - Used JSX style attribute for scoped CSS

The React component maintains all the functionality of the original Vue component while following React best practices.

The converted file has been saved to the output directory.
""",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
    
    def _verification_agent_response(self, messages: Sequence[LLMMessage]) -> CreateResult:
        """Generate a response for the Verification Agent."""
        if any("compare_functionality" in str(message) for message in messages):
            return CreateResult(
                finish_reason="tool_calls",
                content=None,
                tool_calls=[{
                    "id": "call_02",
                    "type": "function",
                    "function": {
                        "name": "compare_functionality",
                        "arguments": json.dumps({
                            "vue_file_path": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/TodoApp.vue",
                            "react_file_path": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/output/TodoApp.jsx"
                        })
                    }
                }],
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        else:
            return CreateResult(
                finish_reason="stop",
                content="""I've verified the conversion and compared the Vue and React implementations. Here are my findings:

1. Performance Checks (Priority 1):
   ✅ State Management: React useState hooks correctly implement Vue's reactive data
   ✅ Rendering Optimization: React's useMemo properly replaces Vue's computed properties
   ✅ Event Handler Binding: All event handlers are properly bound

2. Methods Checks (Priority 2):
   ✅ Event Handlers: All Vue methods are properly converted to React functions
   ✅ Data Processing: The data manipulation logic is equivalent
   ✅ Form Handling: Input handling and form submission work the same way

3. UI Checks (Priority 3):
   ✅ Component Structure: The component hierarchy is preserved
   ✅ Styling: All styles are correctly applied
   ✅ Conditional Rendering: v-if and v-for directives are properly converted

The conversion is functionally equivalent to the original Vue component. All checks have passed, and I don't see any issues that would require another iteration.

I recommend proceeding to the report generation phase.
""",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
    
    def _report_agent_response(self, messages: Sequence[LLMMessage]) -> CreateResult:
        """Generate a response for the Report Generation Agent."""
        if any("generate_test_report" in str(message) for message in messages):
            return CreateResult(
                finish_reason="tool_calls",
                content=None,
                tool_calls=[{
                    "id": "call_03",
                    "type": "function",
                    "function": {
                        "name": "generate_test_report",
                        "arguments": json.dumps({
                            "verification_results": {
                                "total_components": 1,
                                "components_verified": 1,
                                "components_passed": 1,
                                "components_failed": 0,
                                "component_results": [
                                    {
                                        "vue_file": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/TodoApp.vue",
                                        "react_file": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/output/TodoApp.jsx",
                                        "passed": True,
                                        "passed_checks": [
                                            "Performance check: State management",
                                            "Performance check: Rendering optimization",
                                            "Methods check: Event handlers",
                                            "Methods check: Data processing",
                                            "UI check: Component structure",
                                            "UI check: Styling"
                                        ],
                                        "failed_checks": [],
                                        "suggestions": [
                                            "Consider adding PropTypes for better type checking"
                                        ]
                                    }
                                ]
                            },
                            "output_path": "/home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/output/TodoApp_report.json"
                        })
                    }
                }],
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        else:
            return CreateResult(
                finish_reason="stop",
                content="""I've generated a comprehensive test report for the Vue to React conversion. The report includes:

1. Summary Statistics:
   - Total Components: 1
   - Components Verified: 1
   - Components Passed: 1
   - Success Rate: 100%

2. Detailed Component Results:
   - All functional checks passed
   - No failed checks identified
   - All priority areas (performance, methods, UI) verified

3. Recommendations:
   - Add PropTypes for better type checking
   - Consider using useCallback for event handlers
   - Add CSS styles to match the original Vue component

The report has been saved to: /home/ubuntu/repos/autogen/python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples/output/TodoApp_report.json

CONVERSION_COMPLETE
""",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
    
    def _selector_response(self, messages: Sequence[LLMMessage]) -> CreateResult:
        """Generate a response for the Selector."""
        conversation = " ".join([str(m.content) if hasattr(m, 'content') else "" for m in messages])
        
        if "Vue file:" in conversation and "code_analysis_agent" not in conversation:
            return CreateResult(
                finish_reason="stop",
                content="code_analysis_agent",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        elif "code_analysis_agent" in conversation and "conversion_agent" not in conversation:
            return CreateResult(
                finish_reason="stop",
                content="conversion_agent",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        elif "conversion_agent" in conversation and "verification_agent" not in conversation:
            return CreateResult(
                finish_reason="stop",
                content="verification_agent",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        elif "verification_agent" in conversation and "report_generation_agent" not in conversation:
            return CreateResult(
                finish_reason="stop",
                content="report_generation_agent",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        else:
            return CreateResult(
                finish_reason="stop",
                content="user_proxy",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )

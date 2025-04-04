# Vue to React Converter

A multi-agent system for converting Vue components to React components using AutoGen.

## Overview

This system uses a team of specialized agents to convert Vue code to React code while following specific standards. The system includes:

1. **Code Analysis Agent**: Evaluates the original Vue implementation before conversion
2. **Conversion Agent**: Performs the actual code transformation following knowledge base guidelines
3. **Verification Agent**: Compares pre and post-conversion functionality, initiating additional iterations if needed
4. **Report Generation Agent**: Creates a test report highlighting areas needing attention

## Features

- Knowledge base with component mapping and syntax style guidelines
- Prioritized functional consistency checks (performance, methods, UI)
- Support for multiple rounds of iterations if functionality differences are detected
- Test report generation highlighting areas that need special attention
- Support for handling large codebases through chunking and incremental processing
- Custom client implementation for offline usage or alternative API providers

## Getting Started

### Installation

1. Ensure you have AutoGen installed:
   ```bash
   pip install pyautogen
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/Yvanyang/autogen.git
   cd autogen
   ```

3. Install the package in development mode:
   ```bash
   pip install -e ./python/packages/autogen-ext
   ```

### Quick Start

The easiest way to get started is to use the provided example script:

```bash
cd python/packages/autogen-ext/src/autogen_ext/agents/vue_to_react_converter/examples
python convert_todo_app.py
```

This will convert the included Vue Todo app to React and generate a test report.

### Usage Options

#### Standard Usage with OpenAI API

```python
import os
import asyncio
from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.vue_to_react_converter import VueToReactConverter

async def main():
    # Set your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
    
    # Create a model client
    model_client = ChatCompletionClient(
        model="gpt-4",
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Create the converter
    converter = VueToReactConverter(model_client)
    
    # Convert a single Vue file
    result = await converter.convert_file(
        vue_file_path="/path/to/component.vue",
        output_dir="/path/to/output"
    )
    
    print("Conversion completed!")
    print(f"Check the output directory: {output_dir}")

# Run the example
asyncio.run(main())
```

#### Using Custom API Configuration

For users who need to use alternative API providers or work offline:

```python
import asyncio
import os
from custom_client import CustomChatCompletionClient
from autogen_ext.agents.vue_to_react_converter import VueToReactConverter

async def main():
    # Create a custom model client with specific API configuration
    model_client = CustomChatCompletionClient(
        model="gpt-4",
        api_key="your-api-key",
        api_base="https://your-custom-api-endpoint/v1",
        retry_wait_time=60,
        max_retry_period=10,
        seed=42
    )
    
    # Create the converter with the custom client
    converter = VueToReactConverter(model_client)
    
    # Convert a Vue file
    result = await converter.convert_file(
        vue_file_path="/path/to/component.vue",
        output_dir="/path/to/output"
    )
    
    print(f"Conversion completed!")
    
    # Check for the converted React file
    react_file = os.path.join(output_dir, os.path.splitext(os.path.basename(vue_file_path))[0] + '.jsx')
    if os.path.exists(react_file):
        print(f"React component saved to: {react_file}")

# Run the example
asyncio.run(main())
```

#### Advanced Usage

For more advanced scenarios, the system supports:

```python
# Convert all Vue files in a directory
result = await converter.convert_directory(
    vue_dir_path="/path/to/vue/components",
    output_dir="/path/to/output"
)

# Convert a large Vue file by processing it in chunks
result = await converter.convert_large_file(
    vue_file_path="/path/to/large-component.vue",
    output_dir="/path/to/output",
    chunk_size=100
)
```

## Knowledge Base

The knowledge base includes:

1. **Component Mapping**: Mappings between Vue and React components and patterns
2. **Syntax Style Guidelines**: Guidelines for writing React code
3. **Conversion Rules**: Specific rules for converting Vue patterns to React
4. **Functional Consistency Checks**: Prioritized checks for verifying the conversion

You can customize the knowledge base by:

```python
from autogen_ext.agents.vue_to_react_converter import VueToReactConverter
from autogen_ext.agents.vue_to_react_converter.knowledge_base import KnowledgeBase, ConversionRule

# Create a custom knowledge base
kb = KnowledgeBase.create_default()

# Add a custom rule
kb.add_rule(ConversionRule(
    vue_pattern="<custom-pattern>",
    react_pattern="<custom-react-equivalent>",
    description="Custom pattern conversion",
    example_vue="<example-vue-code>",
    example_react="<example-react-code>"
))

# Save the knowledge base
kb.save_to_file("/path/to/custom-kb.json")

# Use the custom knowledge base
converter = VueToReactConverter(
    model_client=model_client,
    knowledge_base=kb
)
```

## Handling Large Codebases

The system includes several strategies for handling large codebases that exceed context limits:

1. **Chunking**: Process large components in smaller chunks
2. **Incremental Analysis**: Analyze component dependencies and process in order
3. **Stream Processing**: Process files as streams rather than loading entirely
4. **State Preservation**: Save conversion state for resumable processing
5. **Component Prioritization**: Convert core components first

## Offline Usage

For scenarios where you need to work offline or with limited API access, you can implement a custom client that simulates the LLM responses:

1. Create a custom client that implements the `ChatCompletionClient` interface
2. Implement specialized response methods for each agent type
3. Use the custom client with the converter

See the `examples/custom_client.py` for a complete implementation example.

## Test Reports

The system generates test reports that include:

1. Summary of the conversion process
2. Metrics on functional consistency
3. Areas that required special attention
4. Recommendations for manual review
5. Detailed results for each component

## Example Conversion

The system successfully converts Vue-specific features to their React equivalents:

| Vue Feature | React Equivalent |
|-------------|------------------|
| v-model | useState + onChange handlers |
| v-for | map() function |
| v-if | Conditional rendering with && |
| Computed properties | useMemo hook |
| Methods | Regular functions |
| Scoped CSS | JSX styles |
| Class binding | Template literals with conditionals |

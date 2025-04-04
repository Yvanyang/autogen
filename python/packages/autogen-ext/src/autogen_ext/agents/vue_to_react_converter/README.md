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

## Usage

```python
import asyncio
from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.vue_to_react_converter import VueToReactConverter

async def main():
    # Create a model client
    model_client = ChatCompletionClient(
        model="gpt-4",
        api_key="your-api-key"
    )
    
    # Create the converter
    converter = VueToReactConverter(model_client)
    
    # Convert a single Vue file
    result = await converter.convert_file(
        vue_file_path="/path/to/component.vue",
        output_dir="/path/to/output"
    )
    
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

# Run the example
asyncio.run(main())
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

## Test Reports

The system generates test reports that include:

1. Summary of the conversion process
2. Metrics on functional consistency
3. Areas that required special attention
4. Recommendations for manual review
5. Detailed results for each component

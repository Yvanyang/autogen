# Vue to React Converter Examples

This directory contains example Vue components that can be used to test the Vue to React conversion system.

## TodoApp.vue

A simple Todo application built with Vue that demonstrates:

1. Component structure with template, script, and style sections
2. Data properties and state management
3. Computed properties
4. Methods for adding, removing, and updating todos
5. Conditional rendering with v-if
6. List rendering with v-for
7. Event handling with @click and @keyup
8. Two-way binding with v-model
9. Class binding with :class
10. Scoped styling

## How to Test the Conversion

You can use the Vue to React converter to transform this Todo application:

```python
import asyncio
import os
from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.vue_to_react_converter import VueToReactConverter

async def main():
    # Create a model client
    model_client = ChatCompletionClient(
        model="gpt-4",
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Create the converter
    converter = VueToReactConverter(model_client)
    
    # Get the path to the example
    current_dir = os.path.dirname(os.path.abspath(__file__))
    vue_file_path = os.path.join(current_dir, "TodoApp.vue")
    output_dir = os.path.join(current_dir, "output")
    
    # Convert the Vue component to React
    result = await converter.convert_file(
        vue_file_path=vue_file_path,
        output_dir=output_dir
    )
    
    print(f"Conversion completed. React component saved to: {result['react_file']}")
    print(f"Test report saved to: {result['report_path']}")

if __name__ == "__main__":
    asyncio.run(main())
```

The conversion system will:
1. Analyze the Vue component structure
2. Convert it to a React functional component
3. Verify the functionality
4. Generate a test report

## Expected Output

The converted React component should:
1. Use React hooks (useState, useEffect, useMemo) for state management
2. Implement the same functionality as the Vue component
3. Follow React best practices and patterns
4. Maintain the same styling and appearance

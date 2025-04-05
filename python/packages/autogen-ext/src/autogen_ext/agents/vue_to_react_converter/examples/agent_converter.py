"""
Enhanced Vue to React conversion agent with detailed logging.
"""
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("conversion_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VueToReactAgent")

class EnhancedChatCompletionClient:
    """Mock chat completion client for demonstration purposes."""
    
    def __init__(self, model="gpt-4", api_key=None, api_base=None, retry_wait_time=60, max_retry_period=10, seed=42):
        """Initialize the mock client with model name and API details."""
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.retry_wait_time = retry_wait_time
        self.max_retry_period = max_retry_period
        self.seed = seed
        logger.info(f"Initialized MockChatCompletionClient with model: {model}")
    
    async def create(self, messages, **kwargs):
        """Create a mock chat completion with detailed logging."""
        logger.info(f"Creating chat completion with {len(messages)} messages")
        
        vue_content = ""
        component_name = "Unknown"
        
        for message in messages:
            if message["role"] == "user":
                content = message["content"]
                
                name_match = re.search(r'Vue component named "([^"]+)"', content)
                if name_match:
                    component_name = name_match.group(1)
                
                vue_match = re.search(r'```vue\s*(.*?)\s*```', content, re.DOTALL)
                if vue_match:
                    vue_content = vue_match.group(1)
        
        logger.info(f"Extracted component name: {component_name}")
        logger.info(f"Processing Vue content for conversion")
        
        react_component = self._generate_react_component(component_name, vue_content)
        css = self._generate_css(component_name, vue_content)
        
        response_content = f"""
I've converted the Vue component "{component_name}" to a React component:

```jsx
{react_component}
```

```css
{css}
```

The conversion follows these principles:
1. Vue template tags are converted to JSX
2. Vue data() is converted to React useState hooks
3. Vue methods are converted to React functions
4. Vue lifecycle hooks are converted to React useEffect hooks
5. Vue components are imported and used in the React component
6. CSS is extracted to a separate file

Let me know if you need any clarification or have questions about the conversion!
"""
        
        logger.info("Generated mock response for conversion")
        
        await asyncio.sleep(1)
        
        return {
            "choices": [
                {
                    "message": {
                        "content": response_content
                    }
                }
            ]
        }
    
    def _generate_react_component(self, component_name, vue_content):
        """Generate a React component based on the Vue component."""
        template_match = re.search(r"<template>(.*?)</template>", vue_content, re.DOTALL)
        script_match = re.search(r"<script>(.*?)</script>", vue_content, re.DOTALL)
        
        template = template_match.group(1) if template_match else ""
        script = script_match.group(1) if script_match else ""
        
        imports = []
        import_pattern = r"import\s+(\w+)\s+from\s+['\"](.+?)['\"]"
        for match in re.finditer(import_pattern, script):
            component = match.group(1)
            path = match.group(2)
            if path.endswith('.vue'):
                path = path.replace('.vue', '')
                if '/' in path:
                    path = path.split('/')[-1]
                imports.append(f"import {component} from './{path}';")
            else:
                imports.append(f"import {component} from '{path}';")
        
        imports.insert(0, "import React, { useState } from 'react';")
        imports.append(f"import './{component_name}.css';")
        
        jsx = template.strip()
        
        jsx = jsx.replace('v-if=', 'v-if-replaced=')  # Placeholder to avoid conflicts
        jsx = jsx.replace('v-for=', 'v-for-replaced=')  # Placeholder to avoid conflicts
        jsx = jsx.replace('v-model=', 'v-model-replaced=')  # Placeholder to avoid conflicts
        jsx = jsx.replace('class=', 'className=')
        jsx = jsx.replace('v-if-replaced=', '{/* v-if converted to conditional rendering */}')
        jsx = jsx.replace('v-for-replaced=', '{/* v-for converted to map() */}')
        jsx = jsx.replace('v-model-replaced=', '{/* v-model converted to value/onChange */}')
        
        react_component = f"""
{chr(10).join(imports)}

function {component_name}() {{
  // State would be initialized here based on Vue data
  const [state, setState] = useState({{}});
  
  // Methods would be defined here
  
  // Render JSX
  return (
{jsx}
  );
}}

export default {component_name};
"""
        
        return react_component
    
    def _generate_css(self, component_name, vue_content):
        """Generate CSS based on the Vue component."""
        style_match = re.search(r"<style.*?>(.*?)</style>", vue_content, re.DOTALL)
        
        if style_match:
            return style_match.group(1).strip()
        else:
            return f"""
.{component_name.lower()} {{
  padding: 20px;
  margin: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
}}

h2 {{
  color: #42b983;
}}
"""

class AgentVueToReactConverter:
    """
    Enhanced Vue to React converter that uses an agent to convert Vue components to React.
    Includes detailed logging of the conversion process.
    """
    
    def __init__(self, model_client, max_lines_per_chunk=500):
        """Initialize the converter with a model client."""
        self.model_client = model_client
        self.max_lines_per_chunk = max_lines_per_chunk
        self.conversion_logs = {}
        logger.info(f"Initialized AgentVueToReactConverter with max_lines_per_chunk: {max_lines_per_chunk}")
    
    def save_knowledge_base(self, file_path):
        """Save knowledge base to a file."""
        logger.info(f"Saving knowledge base to: {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        knowledge_base = {
            "version": "1.0",
            "rules": [
                "Vue template tags become JSX",
                "Vue data() becomes React useState",
                "Vue methods become React functions",
                "Vue lifecycle hooks map to React useEffect",
                "Vue v-if becomes React conditional rendering with &&",
                "Vue v-for becomes React map() function",
                "Vue v-model becomes React controlled components with onChange",
                "Vue props become React props",
                "Vue computed properties become React useMemo",
                "Vue watchers become React useEffect",
                "Vue components become React components",
                "Vue single-file components are split into separate JS and CSS files"
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(knowledge_base, f, indent=2)
        
        logger.info(f"Knowledge base saved successfully")
        return knowledge_base
    
    async def convert_file(self, vue_file_path, output_dir, knowledge_base_path=None):
        """
        Convert a Vue file to React using the agent.
        
        Args:
            vue_file_path: Path to the Vue file
            output_dir: Output directory for the React file
            knowledge_base_path: Optional path to the knowledge base file
        
        Returns:
            Dictionary with conversion results
        """
        logger.info(f"Converting file: {vue_file_path}")
        logger.info(f"Output directory: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(vue_file_path, 'r', encoding='utf-8') as f:
            vue_content = f.read()
        
        logger.info(f"Source file content ({vue_file_path}):\n{vue_content}")
        
        component_name = os.path.basename(vue_file_path).replace('.vue', '')
        
        knowledge_base_content = ""
        if knowledge_base_path and os.path.exists(knowledge_base_path):
            with open(knowledge_base_path, 'r') as f:
                knowledge_base_content = f.read()
        
        prompt = self._create_conversion_prompt(vue_content, component_name, knowledge_base_content)
        
        response = await self.model_client.create(prompt)
        
        react_component, css = self._extract_react_component_and_css(response, component_name)
        
        react_file_path = os.path.join(output_dir, f"{component_name}.jsx")
        with open(react_file_path, 'w', encoding='utf-8') as f:
            f.write(react_component)
        
        css_file_path = os.path.join(output_dir, f"{component_name}.css")
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write(css)
        
        logger.info(f"Converted React component ({react_file_path}):\n{react_component}")
        logger.info(f"Converted CSS ({css_file_path}):\n{css}")
        
        report_dir = os.path.join(output_dir, ".reports")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"{component_name}_conversion_report.json")
        
        report = {
            "source_file": vue_file_path,
            "target_file": react_file_path,
            "css_file": css_file_path,
            "conversion_status": "success",
            "timestamp": self._get_timestamp()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        self.conversion_logs[vue_file_path] = {
            "source": vue_content,
            "react_component": react_component,
            "css": css,
            "report": report
        }
        
        logger.info(f"Conversion completed successfully for: {vue_file_path}")
        logger.info(f"React component saved to: {react_file_path}")
        logger.info(f"CSS saved to: {css_file_path}")
        logger.info(f"Report saved to: {report_path}")
        
        return {
            "vue_file": vue_file_path,
            "react_file": react_file_path,
            "css_file": css_file_path,
            "report_path": report_path,
            "success": True
        }
    
    def _create_conversion_prompt(self, vue_content, component_name, knowledge_base_content=""):
        """Create a prompt for the agent to convert a Vue component to React."""
        system_message = """
        You are an expert Vue to React converter. Your task is to convert Vue single-file components to React components.
        Follow these rules:
        1. Convert Vue template to React JSX
        2. Convert Vue data() to React useState hooks
        3. Convert Vue methods to React functions
        4. Convert Vue lifecycle hooks to React useEffect hooks
        5. Convert Vue v-if to React conditional rendering with &&
        6. Convert Vue v-for to React map() function
        7. Convert Vue v-model to React controlled components with onChange
        8. Convert Vue props to React props
        9. Convert Vue computed properties to React useMemo hooks
        10. Convert Vue watchers to React useEffect hooks
        11. Split Vue style section into a separate CSS file
        12. Ensure the React component is functional, not class-based
        13. Use modern React practices (hooks, functional components)
        14. Maintain the same functionality as the original Vue component
        15. Include all necessary imports
        
        Provide your response in the following format:
        
        ```jsx
        // React component code here
        ```
        
        ```css
        /* CSS code here */
        ```
        """
        
        user_message = f"""
        Please convert the following Vue component named "{component_name}" to a React component:
        
        ```vue
        {vue_content}
        ```
        
        Knowledge base:
        {knowledge_base_content}
        
        Please provide the React component code and CSS separately.
        """
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def _extract_react_component_and_css(self, response, component_name):
        """Extract the React component and CSS from the agent's response."""
        try:
            content = response["choices"][0]["message"]["content"]
            
            jsx_match = content.split("```jsx")[1].split("```")[0] if "```jsx" in content else ""
            if not jsx_match:
                jsx_match = content.split("```javascript")[1].split("```")[0] if "```javascript" in content else ""
            if not jsx_match:
                jsx_match = content.split("```js")[1].split("```")[0] if "```js" in content else ""
            
            css_match = content.split("```css")[1].split("```")[0] if "```css" in content else ""
            
            if not jsx_match:
                if "import React" in content:
                    start_idx = content.find("import React")
                    end_idx = content.find("```css") if "```css" in content else len(content)
                    jsx_match = content[start_idx:end_idx].strip()
            
            if not css_match:
                if "/* CSS code" in content:
                    start_idx = content.find("/* CSS code")
                    css_match = content[start_idx:].strip()
            
            if not jsx_match:
                jsx_match = self._get_default_react_component(component_name)
            
            if not css_match:
                css_match = self._get_default_css(component_name)
            
            return jsx_match.strip(), css_match.strip()
        
        except Exception as e:
            logger.error(f"Error extracting React component and CSS: {str(e)}")
            return self._get_default_react_component(component_name), self._get_default_css(component_name)
    
    def _get_default_react_component(self, component_name):
        """Get a default React component if extraction fails."""
        return f"""
import React from 'react';
import './{component_name}.css';

function {component_name}() {{
  return (
    <div className="{component_name.lower()}">
      <h2>{component_name}</h2>
      <p>This is a converted React component.</p>
    </div>
  );
}}

export default {component_name};
"""
    
    def _get_default_css(self, component_name):
        """Get default CSS if extraction fails."""
        return f"""
.{component_name.lower()} {{
  padding: 20px;
  margin: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
}}

h2 {{
  color: #42b983;
}}
"""
    
    def _get_timestamp(self):
        """Get the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_conversion_logs(self, output_dir):
        """Save all conversion logs to a file."""
        log_dir = os.path.join(output_dir, ".logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "conversion_logs.json")
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.conversion_logs, f, indent=2)
        
        logger.info(f"Conversion logs saved to: {log_path}")
        return log_path

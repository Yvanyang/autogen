from typing import Dict, List

ANALYSIS_AGENT_NAME = "code_analysis_agent"
CONVERSION_AGENT_NAME = "conversion_agent" 
VERIFICATION_AGENT_NAME = "verification_agent"
REPORT_AGENT_NAME = "report_generation_agent"
USER_PROXY_NAME = "user_proxy"

AGENT_DESCRIPTIONS = {
    ANALYSIS_AGENT_NAME: "An agent that analyzes Vue code to understand its functionality before conversion",
    CONVERSION_AGENT_NAME: "An agent that transforms Vue code to React following the knowledge base guidelines",
    VERIFICATION_AGENT_NAME: "An agent that compares pre and post conversion functionality and initiates iterations if needed",
    REPORT_AGENT_NAME: "An agent that generates test reports highlighting areas that need special attention"
}

ANALYSIS_SYSTEM_MESSAGE = """You are a Code Analysis Agent responsible for evaluating Vue components.
Your task is to thoroughly analyze Vue code and identify:
1. Core functionality and features
2. Component structure and relationships
3. State management approach
4. Props and event handling
5. Lifecycle methods used
6. Dependencies and external libraries

You should document this analysis in a structured format that will be used by the Conversion Agent.
"""

CONVERSION_SYSTEM_MESSAGE = """You are a Conversion Agent responsible for transforming Vue code to React.
Follow these guidelines:
1. Use the component mapping and syntax style from the knowledge base
2. Prioritize functional consistency: performance first, methods second, UI third
3. Only implement complete page conversions, not partial conversions
4. Structure the code following React best practices
5. Document any decisions or adjustments made during conversion

Use the analysis provided by the Code Analysis Agent to guide your conversion process.
"""

VERIFICATION_SYSTEM_MESSAGE = """You are a Verification Agent responsible for comparing pre and post conversion functionality.
Your task is to:
1. Compare the Vue and React implementations for functional equivalence
2. Prioritize verification in this order: performance, methods, UI
3. Identify any inconsistencies or potential issues
4. Provide detailed feedback for any functionality differences
5. Recommend specific improvements when issues are found
6. Determine if additional iterations are needed

If functionality differences are detected, provide clear instructions for the Conversion Agent.
"""

REPORT_SYSTEM_MESSAGE = """You are a Report Generation Agent responsible for creating test reports.
Your report should:
1. Summarize the conversion process and results
2. Highlight areas that required special attention
3. Document any known limitations or issues
4. Include metrics on functional consistency
5. Provide recommendations for manual review if needed
6. Organize information in a clear, structured format

Focus on providing actionable insights rather than just listing changes.
"""

VUE_REACT_COMPONENT_MAPPING = {
    "Vue Template": "JSX",
    "v-if": "conditional rendering with {condition && <Component/>}",
    "v-for": "map() function",
    "v-model": "useState and onChange handlers",
    "v-bind:prop or :prop": "prop={value}",
    "v-on:event or @event": "onClick, onChange, etc.",
    "computed": "useMemo hook",
    "methods": "regular functions or useCallback",
    "watch": "useEffect hook",
    "created/mounted": "useEffect(() => {}, [])",
    "beforeDestroy/unmounted": "useEffect cleanup function",
    "data()": "useState hooks",
    "props": "function parameters",
    "components": "import statements",
    "filters": "separate utility functions"
}

SYNTAX_STYLE_GUIDELINES = [
    "Use functional components with hooks instead of class components",
    "Use destructuring for props",
    "Use named exports for components",
    "Use proper code formatting and indentation",
    "Use consistent naming conventions (camelCase for variables, PascalCase for components)",
    "Use ES6+ features where appropriate",
    "Include PropTypes or TypeScript types for props",
    "Organize imports alphabetically",
    "Use meaningful component and variable names"
]

FUNCTIONAL_CONSISTENCY_CHECKS = [
    {
        "priority": 1,
        "category": "Performance",
        "checks": [
            "Rendering optimization",
            "State updates efficiency",
            "Memoization of expensive calculations",
            "Event handler binding approach",
            "Resource loading and management"
        ]
    },
    {
        "priority": 2,
        "category": "Methods",
        "checks": [
            "API calls implementation",
            "Event handlers functionality",
            "Data processing methods",
            "Form submission handling",
            "State manipulation logic"
        ]
    },
    {
        "priority": 3,
        "category": "UI",
        "checks": [
            "Component layout and structure",
            "Styling and appearance",
            "Responsive behavior",
            "Animation and transitions",
            "Accessibility features"
        ]
    }
]

MAX_CONVERSION_ITERATIONS = 3

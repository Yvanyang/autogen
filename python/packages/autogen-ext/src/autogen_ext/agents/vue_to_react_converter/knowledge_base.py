from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import os

from .constants import VUE_REACT_COMPONENT_MAPPING, SYNTAX_STYLE_GUIDELINES, FUNCTIONAL_CONSISTENCY_CHECKS


@dataclass
class ConversionRule:
    """A rule for converting Vue code to React code."""
    vue_pattern: str
    react_pattern: str
    description: str
    example_vue: str
    example_react: str


@dataclass
class KnowledgeBase:
    """Knowledge base for Vue to React conversion."""
    component_mapping: Dict[str, str]
    syntax_guidelines: List[str]
    conversion_rules: List[ConversionRule]
    consistency_checks: List[Dict]
    
    @classmethod
    def create_default(cls) -> 'KnowledgeBase':
        """Create a default knowledge base with predefined rules."""
        conversion_rules = [
            ConversionRule(
                vue_pattern="<template><div>{{ message }}</div></template>",
                react_pattern="return <div>{message}</div>;",
                description="Basic template conversion to JSX",
                example_vue="<template><div>{{ message }}</div></template>",
                example_react="return <div>{message}</div>;"
            ),
            ConversionRule(
                vue_pattern="data() { return { count: 0 } }",
                react_pattern="const [count, setCount] = useState(0);",
                description="Convert data properties to useState hooks",
                example_vue="data() { return { count: 0 } }",
                example_react="const [count, setCount] = useState(0);"
            ),
            ConversionRule(
                vue_pattern="methods: { increment() { this.count++ } }",
                react_pattern="const increment = () => setCount(count + 1);",
                description="Convert methods to functions",
                example_vue="methods: { increment() { this.count++ } }",
                example_react="const increment = () => setCount(count + 1);"
            ),
            ConversionRule(
                vue_pattern="computed: { doubled() { return this.count * 2 } }",
                react_pattern="const doubled = useMemo(() => count * 2, [count]);",
                description="Convert computed properties to useMemo hooks",
                example_vue="computed: { doubled() { return this.count * 2 } }",
                example_react="const doubled = useMemo(() => count * 2, [count]);"
            ),
            ConversionRule(
                vue_pattern="watch: { count(newVal, oldVal) { /* ... */ } }",
                react_pattern="useEffect(() => { /* ... */ }, [count]);",
                description="Convert watchers to useEffect hooks",
                example_vue="watch: { count(newVal, oldVal) { console.log(newVal, oldVal) } }",
                example_react="useEffect(() => { console.log('count changed to', count); }, [count]);"
            ),
            ConversionRule(
                vue_pattern="<div v-if=\"condition\">Content</div>",
                react_pattern="{condition && <div>Content</div>}",
                description="Convert v-if directives to conditional rendering",
                example_vue="<div v-if=\"isVisible\">Now you see me</div>",
                example_react="{isVisible && <div>Now you see me</div>}"
            ),
            ConversionRule(
                vue_pattern="<div v-for=\"item in items\" :key=\"item.id\">{{ item.name }}</div>",
                react_pattern="{items.map(item => <div key={item.id}>{item.name}</div>)}",
                description="Convert v-for directives to map functions",
                example_vue="<div v-for=\"item in items\" :key=\"item.id\">{{ item.name }}</div>",
                example_react="{items.map(item => <div key={item.id}>{item.name}</div>)}"
            ),
            ConversionRule(
                vue_pattern="<input v-model=\"message\">",
                react_pattern="<input value={message} onChange={e => setMessage(e.target.value)} />",
                description="Convert v-model directives to controlled components",
                example_vue="<input v-model=\"message\">",
                example_react="<input value={message} onChange={e => setMessage(e.target.value)} />"
            ),
            ConversionRule(
                vue_pattern="<button @click=\"handleClick\">Click me</button>",
                react_pattern="<button onClick={handleClick}>Click me</button>",
                description="Convert event handlers",
                example_vue="<button @click=\"handleClick\">Click me</button>",
                example_react="<button onClick={handleClick}>Click me</button>"
            ),
            ConversionRule(
                vue_pattern="props: { msg: String, required: true }",
                react_pattern="function Component({ msg }) { /* ... */ }\nComponent.propTypes = { msg: PropTypes.string.isRequired };",
                description="Convert props declaration",
                example_vue="props: { msg: { type: String, required: true } }",
                example_react="function Component({ msg }) { /* ... */ }\nComponent.propTypes = { msg: PropTypes.string.isRequired };"
            ),
        ]
        
        return cls(
            component_mapping=VUE_REACT_COMPONENT_MAPPING,
            syntax_guidelines=SYNTAX_STYLE_GUIDELINES,
            conversion_rules=conversion_rules,
            consistency_checks=FUNCTIONAL_CONSISTENCY_CHECKS
        )
    
    def save_to_file(self, file_path: str) -> None:
        """Save the knowledge base to a JSON file."""
        data = {
            "component_mapping": self.component_mapping,
            "syntax_guidelines": self.syntax_guidelines,
            "conversion_rules": [
                {
                    "vue_pattern": rule.vue_pattern,
                    "react_pattern": rule.react_pattern,
                    "description": rule.description,
                    "example_vue": rule.example_vue,
                    "example_react": rule.example_react
                }
                for rule in self.conversion_rules
            ],
            "consistency_checks": self.consistency_checks
        }
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'KnowledgeBase':
        """Load the knowledge base from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        conversion_rules = [
            ConversionRule(
                vue_pattern=rule["vue_pattern"],
                react_pattern=rule["react_pattern"],
                description=rule["description"],
                example_vue=rule["example_vue"],
                example_react=rule["example_react"]
            )
            for rule in data["conversion_rules"]
        ]
        
        return cls(
            component_mapping=data["component_mapping"],
            syntax_guidelines=data["syntax_guidelines"],
            conversion_rules=conversion_rules,
            consistency_checks=data["consistency_checks"]
        )
        
    def add_rule(self, rule: ConversionRule) -> None:
        """Add a new conversion rule to the knowledge base."""
        self.conversion_rules.append(rule)
        
    def get_rules_by_description(self, description_fragment: str) -> List[ConversionRule]:
        """Get rules that match a description fragment."""
        return [rule for rule in self.conversion_rules 
                if description_fragment.lower() in rule.description.lower()]
                
    def get_rule_for_pattern(self, vue_pattern_fragment: str) -> Optional[ConversionRule]:
        """Get the first rule that matches a Vue pattern fragment."""
        for rule in self.conversion_rules:
            if vue_pattern_fragment.lower() in rule.vue_pattern.lower():
                return rule
        return None

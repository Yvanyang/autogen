"""Repository interaction analyzer agent implementation."""

import os
import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseChatMessage,
    TextMessage,
)
from autogen_core import CancellationToken, Component, ComponentModel
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
)
from pydantic import BaseModel, Field
from typing_extensions import Self

from ._structure_analyzer import RepositoryStructure
from ._component_analyzer import ComponentAnalysis
from ._page_analyzer import PageAnalysis


class Interaction(BaseModel):
    """Interaction details."""
    
    component: str = Field(description="Component where the interaction occurs")
    event: str = Field(description="Event that triggers the interaction")
    handler: str = Field(description="Handler function for the interaction")
    description: str = Field(description="Description of the interaction")
    effects: List[str] = Field(description="Effects of the interaction", default_factory=list)


class InteractionAnalysis(BaseModel):
    """Interaction analysis results."""
    
    interactions: Dict[str, List[Interaction]] = Field(
        description="Dictionary of interactions by page",
        default_factory=dict,
    )
    
    interaction_flows: Dict[str, Dict[str, List[str]]] = Field(
        description="Dictionary of interaction flows by page and component",
        default_factory=dict,
    )
    
    state_changes: Dict[str, Dict[str, List[str]]] = Field(
        description="Dictionary of state changes by page and interaction",
        default_factory=dict,
    )


class InteractionAnalyzerAgentConfig(BaseModel):
    """Configuration for InteractionAnalyzerAgent."""

    name: str
    model_client: ComponentModel
    description: str | None = None


class InteractionAnalyzerAgent(BaseChatAgent, Component[InteractionAnalyzerAgentConfig]):
    """An agent that analyzes repository interactions.
    
    This agent analyzes click handlers and interaction flows in pages and components.
    
    Args:
        name (str): The agent's name
        model_client (ChatCompletionClient): The model to use
        description (str): The agent's description. Defaults to DEFAULT_DESCRIPTION
        repo_path (str): The path to the repository to analyze. Defaults to the current working directory.
    """

    component_config_schema = InteractionAnalyzerAgentConfig
    component_provider_override = "autogen_ext.agents.repo_doc.InteractionAnalyzerAgent"

    DEFAULT_DESCRIPTION = "An agent that analyzes repository interactions."

    DEFAULT_SYSTEM_MESSAGES = [
        SystemMessage(
            content="""
            You are a helpful AI Assistant specialized in analyzing interactions in code repositories.
            You can identify click handlers, interaction flows, and state changes."""
        ),
    ]

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        description: str = DEFAULT_DESCRIPTION,
        repo_path: str = os.getcwd(),
    ) -> None:
        super().__init__(name, description)
        self._model_client = model_client
        self._repo_path = repo_path
        
        self._event_patterns = {
            "click": r"(onClick|handleClick)",
            "change": r"(onChange|handleChange)",
            "submit": r"(onSubmit|handleSubmit)",
            "hover": r"(onHover|onMouseEnter|onMouseLeave)",
            "focus": r"(onFocus|onBlur)",
            "key": r"(onKeyDown|onKeyUp|onKeyPress)",
        }
        
        self._state_patterns = {
            "set_state": r"set(\w+)\(",
            "dispatch": r"dispatch\(\s*\{\s*type:\s*['\"](\w+)['\"]",
            "context": r"(useContext|Context\.Provider)",
        }

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def analyze_interactions(
        self,
        structure: RepositoryStructure,
        component_analysis: ComponentAnalysis,
        page_analysis: PageAnalysis,
        cancellation_token: CancellationToken,
    ) -> InteractionAnalysis:
        """Analyze the repository interactions."""
        interaction_analysis = InteractionAnalysis()
        
        for page_name, page_props in page_analysis.pages.items():
            interactions = await self._analyze_page_interactions(
                page_name, page_props, component_analysis, page_analysis, cancellation_token
            )
            
            if interactions:
                interaction_analysis.interactions[page_name] = interactions
        
        self._analyze_interaction_flows(interaction_analysis, page_analysis)
        
        self._analyze_state_changes(interaction_analysis, page_analysis)
        
        return interaction_analysis

    async def _analyze_page_interactions(
        self,
        page_name: str,
        page_props: Dict[str, str],
        component_analysis: ComponentAnalysis,
        page_analysis: PageAnalysis,
        cancellation_token: CancellationToken,
    ) -> List[Interaction]:
        """Analyze interactions in a page."""
        interactions = []
        file_path = os.path.join(self._repo_path, page_props["file"])
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            page_handlers = self._find_event_handlers(content)
            
            for event_type, handlers in page_handlers.items():
                for handler in handlers:
                    handler_name = handler["name"]
                    
                    handler_impl = self._find_handler_implementation(content, handler_name)
                    
                    effects = self._analyze_handler_effects(handler_impl)
                    
                    interaction = Interaction(
                        component=page_name,
                        event=event_type,
                        handler=handler_name,
                        description=f"{event_type} event handled by {handler_name}",
                        effects=effects,
                    )
                    
                    interactions.append(interaction)
            
            page_components = page_analysis.page_components.get(page_name, [])
            for component_name in page_components:
                component_props = component_analysis.components.get(component_name)
                if component_props:
                    component_handlers = component_props.get("handlers", "")
                    if component_handlers and component_handlers != "No event handlers defined":
                        for handler in component_handlers.split(", "):
                            event_type = "unknown"
                            for event, pattern in self._event_patterns.items():
                                if re.search(pattern, handler):
                                    event_type = event
                                    break
                            
                            interaction = Interaction(
                                component=component_name,
                                event=event_type,
                                handler=handler,
                                description=f"{event_type} event in {component_name} handled by {handler}",
                                effects=["Component state change"],
                            )
                            
                            interactions.append(interaction)
        
        except Exception as e:
            print(f"Error analyzing interactions in {page_name}: {str(e)}")
        
        return interactions

    def _find_event_handlers(self, content: str) -> Dict[str, List[Dict[str, str]]]:
        """Find event handlers in content."""
        handlers = {}
        
        for event_type, pattern in self._event_patterns.items():
            event_handlers = []
            
            jsx_pattern = rf"{pattern}={{([^}}]*)}}"
            for match in re.finditer(jsx_pattern, content):
                handler_expr = match.group(1).strip()
                
                if "=>" in handler_expr:
                    handler = {
                        "name": f"inline_{event_type}_handler",
                        "inline": True,
                        "context": self._find_line_context(content, match.start()),
                    }
                else:
                    handler = {
                        "name": handler_expr,
                        "inline": False,
                        "context": self._find_line_context(content, match.start()),
                    }
                
                event_handlers.append(handler)
            
            func_pattern = rf"(const|function)\s+({pattern}\w*)\s*=?\s*(\(|=>)"
            for match in re.finditer(func_pattern, content):
                handler_name = match.group(2)
                
                handler = {
                    "name": handler_name,
                    "inline": False,
                    "context": self._find_line_context(content, match.start()),
                }
                
                event_handlers.append(handler)
            
            if event_handlers:
                handlers[event_type] = event_handlers
        
        return handlers

    def _find_handler_implementation(self, content: str, handler_name: str) -> str:
        """Find the implementation of a handler function."""
        patterns = [
            rf"(const|function)\s+{handler_name}\s*=\s*(\([^)]*\))?\s*=>\s*{{([^}}]*)}}", # Arrow function with block
            rf"(const|function)\s+{handler_name}\s*=\s*(\([^)]*\))?\s*=>\s*([^;]*);", # Arrow function with expression
            rf"function\s+{handler_name}\s*\([^)]*\)\s*{{([^}}]*)}}", # Function declaration
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(3) if len(match.groups()) > 2 else match.group(0)
        
        return ""

    def _analyze_handler_effects(self, handler_impl: str) -> List[str]:
        """Analyze the effects of a handler implementation."""
        effects = []
        
        if not handler_impl:
            return ["Unknown effects"]
        
        for state_type, pattern in self._state_patterns.items():
            if re.search(pattern, handler_impl):
                if state_type == "set_state":
                    effects.append("Updates component state")
                elif state_type == "dispatch":
                    effects.append("Dispatches action to store")
                elif state_type == "context":
                    effects.append("Updates context")
        
        if re.search(r"(navigate|history\.push|router\.push|Link)", handler_impl):
            effects.append("Navigates to another page")
        
        if re.search(r"(fetch|axios|http|api|request)", handler_impl):
            effects.append("Makes API request")
        
        if re.search(r"(document|window|getElementById|querySelector)", handler_impl):
            effects.append("Manipulates DOM directly")
        
        if re.search(r"(submit|preventDefault|formData)", handler_impl):
            effects.append("Handles form submission")
        
        if not effects:
            effects.append("No detectable effects")
        
        return effects

    def _find_line_context(self, content: str, position: int) -> str:
        """Find the line containing the given position."""
        lines = content.split("\n")
        current_pos = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            if current_pos <= position < current_pos + line_length:
                return line
            current_pos += line_length
        
        return ""

    def _analyze_interaction_flows(self, analysis: InteractionAnalysis, page_analysis: PageAnalysis) -> None:
        """Analyze interaction flows between components and pages."""
        interaction_flows = {}
        
        for page_name, interactions in analysis.interactions.items():
            page_flows = {}
            
            for interaction in interactions:
                component = interaction.component
                
                if component not in page_flows:
                    page_flows[component] = []
                
                for effect in interaction.effects:
                    flow_step = f"{interaction.event} → {effect}"
                    page_flows[component].append(flow_step)
            
            for flow in page_analysis.page_flows:
                if flow.source == page_name:
                    trigger_component = flow.trigger.split("'")[1] if "'" in flow.trigger else page_name
                    
                    if trigger_component not in page_flows:
                        page_flows[trigger_component] = []
                    
                    flow_step = f"Navigation → {flow.target}"
                    page_flows[trigger_component].append(flow_step)
            
            interaction_flows[page_name] = page_flows
        
        analysis.interaction_flows = interaction_flows

    def _analyze_state_changes(self, analysis: InteractionAnalysis, page_analysis: PageAnalysis) -> None:
        """Analyze state changes triggered by interactions."""
        state_changes = {}
        
        for page_name, interactions in analysis.interactions.items():
            page_state_changes = {}
            
            for interaction in interactions:
                interaction_key = f"{interaction.component}.{interaction.handler}"
                
                if interaction_key not in page_state_changes:
                    page_state_changes[interaction_key] = []
                
                state_effects = [
                    effect for effect in interaction.effects
                    if any(keyword in effect.lower() for keyword in ["state", "context", "store", "update"])
                ]
                
                page_state_changes[interaction_key].extend(state_effects)
            
            state_changes[page_name] = page_state_changes
        
        analysis.state_changes = state_changes

    def _to_config(self) -> InteractionAnalyzerAgentConfig:
        """Convert current instance to config object."""
        return InteractionAnalyzerAgentConfig(
            name=self.name,
            model_client=self._model_client.dump_component(),
            description=self.description,
        )

    @classmethod
    def _from_config(cls, config: InteractionAnalyzerAgentConfig) -> Self:
        """Create instance from config object."""
        return cls(
            name=config.name,
            model_client=ChatCompletionClient.load_component(config.model_client),
            description=config.description or cls.DEFAULT_DESCRIPTION,
        )

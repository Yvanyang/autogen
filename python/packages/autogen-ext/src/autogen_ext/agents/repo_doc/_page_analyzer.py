"""Repository page analyzer agent implementation."""

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


class PageFlow(BaseModel):
    """Page navigation flow."""
    
    source: str = Field(description="Source page")
    target: str = Field(description="Target page")
    description: str = Field(description="Description of the navigation")
    trigger: str = Field(description="What triggers the navigation")


class PageAnalysis(BaseModel):
    """Page analysis results."""
    
    pages: Dict[str, Dict[str, str]] = Field(
        description="Dictionary of pages with their properties",
        default_factory=dict,
    )
    
    page_components: Dict[str, List[str]] = Field(
        description="Dictionary of components used in each page",
        default_factory=dict,
    )
    
    page_flows: List[PageFlow] = Field(
        description="List of page navigation flows",
        default_factory=list,
    )
    
    page_parameters: Dict[str, List[str]] = Field(
        description="Dictionary of URL parameters for each page",
        default_factory=dict,
    )
    
    page_routes: Dict[str, str] = Field(
        description="Dictionary of route paths for each page",
        default_factory=dict,
    )


class PageAnalyzerAgentConfig(BaseModel):
    """Configuration for PageAnalyzerAgent."""

    name: str
    model_client: ComponentModel
    description: str | None = None


class PageAnalyzerAgent(BaseChatAgent, Component[PageAnalyzerAgentConfig]):
    """An agent that analyzes repository pages.
    
    This agent analyzes page files to extract components, navigation flows,
    URL parameters, and routing logic.
    
    Args:
        name (str): The agent's name
        model_client (ChatCompletionClient): The model to use
        description (str): The agent's description. Defaults to DEFAULT_DESCRIPTION
        repo_path (str): The path to the repository to analyze. Defaults to the current working directory.
    """

    component_config_schema = PageAnalyzerAgentConfig
    component_provider_override = "autogen_ext.agents.repo_doc.PageAnalyzerAgent"

    DEFAULT_DESCRIPTION = "An agent that analyzes repository pages."

    DEFAULT_SYSTEM_MESSAGES = [
        SystemMessage(
            content="""
            You are a helpful AI Assistant specialized in analyzing pages in code repositories.
            You can identify page components, navigation flows, URL parameters, and routing logic."""
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
        
        self._routing_libraries = [
            "react-router", "next/router", "next/navigation", "vue-router", 
            "angular/router", "svelte-routing", "@reach/router"
        ]
        
        self._navigation_patterns = {
            "link": r"<Link\s+to=['\"]([^'\"]*)['\"]",
            "navigate": r"navigate\(['\"]([^'\"]*)['\"]",
            "push": r"(router|history)\.push\(['\"]([^'\"]*)['\"]",
            "redirect": r"(Redirect|redirect)\s+to=['\"]([^'\"]*)['\"]",
            "href": r"href=['\"]([^'\"]*)['\"]",
        }
        
        self._param_patterns = {
            "path_param": r"/:(\w+)",
            "query_param": r"(\w+)=",
            "use_param": r"use(Params|SearchParams|RouteParams)",
        }

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def analyze_pages(
        self, 
        structure: RepositoryStructure, 
        component_analysis: ComponentAnalysis,
        cancellation_token: CancellationToken
    ) -> PageAnalysis:
        """Analyze the repository pages."""
        page_analysis = PageAnalysis()
        
        for page_file in structure.pages:
            await self._analyze_page_file(
                page_file, page_analysis, component_analysis, cancellation_token
            )
        
        self._analyze_navigation_flows(page_analysis)
        
        return page_analysis

    async def _analyze_page_file(
        self,
        page_file: str,
        analysis: PageAnalysis,
        component_analysis: ComponentAnalysis,
        cancellation_token: CancellationToken,
    ) -> None:
        """Analyze a single page file."""
        file_path = os.path.join(self._repo_path, page_file)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            page_name = os.path.basename(page_file)
            page_name = os.path.splitext(page_name)[0]
            
            page_props = {
                "name": page_name,
                "file": page_file,
                "description": self._extract_page_description(content),
                "route": self._extract_page_route(content, page_file),
                "title": self._extract_page_title(content),
            }
            
            analysis.pages[page_name] = page_props
            
            route_path = page_props["route"]
            if route_path:
                analysis.page_routes[page_name] = route_path
            
            params = self._extract_url_parameters(content, route_path)
            if params:
                analysis.page_parameters[page_name] = params
            
            components = self._extract_page_components(content, component_analysis)
            analysis.page_components[page_name] = components
            
        except Exception as e:
            print(f"Error analyzing page {page_file}: {str(e)}")

    def _extract_page_description(self, content: str) -> str:
        """Extract page description from JSDoc or comments."""
        jsdoc_match = re.search(r"/\*\*\s*([\s\S]*?)\s*\*/", content)
        if jsdoc_match:
            description = jsdoc_match.group(1)
            description = re.sub(r"^\s*\*\s*", "", description, flags=re.MULTILINE)
            description = re.sub(r"@\w+.*$", "", description, flags=re.MULTILINE)
            return description.strip()
        
        comment_match = re.search(r"//\s*(.*?)\s*\n\s*(export|function|class|const)", content)
        if comment_match:
            return comment_match.group(1).strip()
        
        return "No description available"

    def _extract_page_route(self, content: str, page_file: str) -> str:
        """Extract page route from file content or file path."""
        route_patterns = [
            r"path:\s*['\"]([^'\"]*)['\"]",
            r"<Route\s+path=['\"]([^'\"]*)['\"]",
            r"@Route\(['\"]([^'\"]*)['\"]",
        ]
        
        for pattern in route_patterns:
            route_match = re.search(pattern, content)
            if route_match:
                return route_match.group(1)
        
        if "pages" in page_file:
            route_parts = page_file.split("pages/")[1].split(".")
            route = "/" + route_parts[0].replace("/index", "")
            route = re.sub(r"/\[(\w+)\]", r"/:\1", route)
            return route
        
        page_name = os.path.basename(page_file)
        page_name = os.path.splitext(page_name)[0]
        if page_name.lower() == "index":
            return "/"
        else:
            return f"/{page_name.lower()}"

    def _extract_page_title(self, content: str) -> str:
        """Extract page title from content."""
        title_patterns = [
            r"<title>(.*?)</title>",
            r"title=['\"]([^'\"]*)['\"]",
            r"setTitle\(['\"]([^'\"]*)['\"]",
        ]
        
        for pattern in title_patterns:
            title_match = re.search(pattern, content)
            if title_match:
                return title_match.group(1)
        
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content)
        if h1_match:
            return h1_match.group(1)
        
        return "Untitled Page"

    def _extract_url_parameters(self, content: str, route_path: str) -> List[str]:
        """Extract URL parameters from route path and content."""
        params = []
        
        if route_path:
            path_params = re.findall(r":(\w+)", route_path)
            params.extend(path_params)
        
        param_usage_patterns = [
            r"useParams\(\)\.(\w+)",
            r"params\.(\w+)",
            r"searchParams\.get\(['\"](\w+)['\"]",
            r"query\.(\w+)",
        ]
        
        for pattern in param_usage_patterns:
            for match in re.finditer(pattern, content):
                param = match.group(1)
                if param not in params:
                    params.append(param)
        
        return params

    def _extract_page_components(self, content: str, component_analysis: ComponentAnalysis) -> List[str]:
        """Extract components used in the page."""
        components = []
        
        for component_name in component_analysis.components.keys():
            tag_pattern = rf"<{component_name}[ >]"
            if re.search(tag_pattern, content):
                components.append(component_name)
                continue
            
            import_pattern = rf"import\s+{{{component_name}}}\s+from"
            import_pattern_alt = rf"import\s+{component_name}\s+from"
            if re.search(import_pattern, content) or re.search(import_pattern_alt, content):
                if re.search(rf"{component_name}[ (]", content):
                    components.append(component_name)
        
        return components

    def _analyze_navigation_flows(self, analysis: PageAnalysis) -> None:
        """Analyze navigation flows between pages."""
        page_flows = []
        
        route_to_page = {route: page for page, route in analysis.page_routes.items()}
        
        for source_page, props in analysis.pages.items():
            file_path = os.path.join(self._repo_path, props["file"])
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                for nav_type, pattern in self._navigation_patterns.items():
                    for match in re.finditer(pattern, content):
                        target_route = match.group(1) if nav_type == "link" else match.group(2)
                        
                        target_page = None
                        for route, page in route_to_page.items():
                            if target_route == route:
                                target_page = page
                                break
                            
                            route_pattern = re.sub(r":(\w+)", r"[^/]+", route)
                            if re.match(f"^{route_pattern}$", target_route):
                                target_page = page
                                break
                        
                        if target_page and target_page != source_page:
                            line = self._find_line_context(content, match.start())
                            trigger = self._extract_trigger_from_line(line, nav_type)
                            
                            flow = PageFlow(
                                source=source_page,
                                target=target_page,
                                description=f"Navigation from {source_page} to {target_page}",
                                trigger=trigger,
                            )
                            page_flows.append(flow)
            
            except Exception:
                pass
        
        analysis.page_flows = page_flows

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

    def _extract_trigger_from_line(self, line: str, nav_type: str) -> str:
        """Extract the trigger context from a line."""
        if nav_type == "link":
            text_match = re.search(r">([^<]+)<", line)
            if text_match:
                return f"Link with text '{text_match.group(1)}'"
            
            label_match = re.search(r"aria-label=['\"]([^'\"]*)['\"]", line)
            if label_match:
                return f"Link with label '{label_match.group(1)}'"
            
            return "Link element"
        
        elif nav_type in ["navigate", "push"]:
            handler_match = re.search(r"(\w+)={\s*\(\)\s*=>\s*", line)
            if handler_match:
                event = handler_match.group(1)
                return f"Event handler '{event}'"
            
            return f"Programmatic navigation ({nav_type})"
        
        elif nav_type == "redirect":
            return "Automatic redirect"
        
        else:
            return "Navigation trigger"

    def _to_config(self) -> PageAnalyzerAgentConfig:
        """Convert current instance to config object."""
        return PageAnalyzerAgentConfig(
            name=self.name,
            model_client=self._model_client.dump_component(),
            description=self.description,
        )

    @classmethod
    def _from_config(cls, config: PageAnalyzerAgentConfig) -> Self:
        """Create instance from config object."""
        return cls(
            name=config.name,
            model_client=ChatCompletionClient.load_component(config.model_client),
            description=config.description or cls.DEFAULT_DESCRIPTION,
        )

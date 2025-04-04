import os
from typing import List, Dict, Any, Optional
import json

from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.teams.group_chat import TextMentionTermination, MaxMessageTermination

from .constants import (
    ANALYSIS_AGENT_NAME,
    CONVERSION_AGENT_NAME,
    VERIFICATION_AGENT_NAME,
    REPORT_AGENT_NAME,
    USER_PROXY_NAME,
    AGENT_DESCRIPTIONS,
    ANALYSIS_SYSTEM_MESSAGE,
    CONVERSION_SYSTEM_MESSAGE,
    VERIFICATION_SYSTEM_MESSAGE,
    REPORT_SYSTEM_MESSAGE,
    MAX_CONVERSION_ITERATIONS
)
from .tools import CodeAnalysisTool, ConversionTool, VerificationTool, ReportGenerationTool


def create_analysis_agent(model_client: ChatCompletionClient) -> AssistantAgent:
    """Create the Code Analysis Agent."""
    analysis_tools = CodeAnalysisTool.create_tools()
    
    return AssistantAgent(
        name=ANALYSIS_AGENT_NAME,
        description=AGENT_DESCRIPTIONS[ANALYSIS_AGENT_NAME],
        system_message=ANALYSIS_SYSTEM_MESSAGE,
        model_client=model_client,
        tools=analysis_tools
    )


def create_conversion_agent(model_client: ChatCompletionClient) -> AssistantAgent:
    """Create the Conversion Agent."""
    conversion_tools = ConversionTool.create_tools()
    
    return AssistantAgent(
        name=CONVERSION_AGENT_NAME,
        description=AGENT_DESCRIPTIONS[CONVERSION_AGENT_NAME],
        system_message=CONVERSION_SYSTEM_MESSAGE,
        model_client=model_client,
        tools=conversion_tools
    )


def create_verification_agent(model_client: ChatCompletionClient) -> AssistantAgent:
    """Create the Verification Agent."""
    verification_tools = VerificationTool.create_tools()
    
    return AssistantAgent(
        name=VERIFICATION_AGENT_NAME,
        description=AGENT_DESCRIPTIONS[VERIFICATION_AGENT_NAME],
        system_message=VERIFICATION_SYSTEM_MESSAGE,
        model_client=model_client,
        tools=verification_tools
    )


def create_report_agent(model_client: ChatCompletionClient) -> AssistantAgent:
    """Create the Report Generation Agent."""
    report_tools = ReportGenerationTool.create_tools()
    
    return AssistantAgent(
        name=REPORT_AGENT_NAME,
        description=AGENT_DESCRIPTIONS[REPORT_AGENT_NAME],
        system_message=REPORT_SYSTEM_MESSAGE,
        model_client=model_client,
        tools=report_tools
    )


def create_user_proxy() -> UserProxyAgent:
    """Create the User Proxy Agent."""
    return UserProxyAgent(
        name=USER_PROXY_NAME,
        description="A human user that provides Vue code for conversion and reviews the results"
    )


def create_vue_to_react_team(
    model_client: ChatCompletionClient,
    max_iterations: int = MAX_CONVERSION_ITERATIONS
) -> SelectorGroupChat:
    """
    Create a team of agents for Vue to React conversion.
    
    Args:
        model_client: The model client to use for the agents
        max_iterations: Maximum number of conversion iterations
        
    Returns:
        A SelectorGroupChat instance with all the agents
    """
    analysis_agent = create_analysis_agent(model_client)
    conversion_agent = create_conversion_agent(model_client)
    verification_agent = create_verification_agent(model_client)
    report_agent = create_report_agent(model_client)
    user_proxy = create_user_proxy()
    
    max_messages_termination = MaxMessageTermination(max_messages=100)
    text_termination = TextMentionTermination(text="CONVERSION_COMPLETE")
    termination_condition = max_messages_termination | text_termination
    
    selector_prompt = """You are the coordinator of a Vue to React code conversion system. The following roles are available:
{roles}

The conversion process follows these steps:
1. The user_proxy provides Vue code for conversion
2. The code_analysis_agent analyzes the Vue code to understand its functionality
3. The conversion_agent transforms the Vue code to React following the knowledge base guidelines
4. The verification_agent compares the Vue and React implementations for functional equivalence
5. If functionality differences are detected, the conversion_agent makes improvements based on feedback
6. Once the conversion is satisfactory, the report_generation_agent creates a test report

Read the following conversation. Then select the next role from {participants} to play. Only return the role.

{history}

Read the above conversation. Then select the next role from {participants} to play. Only return the role.
"""
    
    team = SelectorGroupChat(
        participants=[analysis_agent, conversion_agent, verification_agent, report_agent, user_proxy],
        selector_prompt=selector_prompt,
        model_client=model_client,
        termination_condition=termination_condition
    )
    
    return team

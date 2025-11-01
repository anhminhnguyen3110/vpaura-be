"""Chat agent for fast general conversation."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from ..agents.base import BaseAgent
from ..llm.llm_factory import LLMFactory, LLMProviderType
from .state.chat_state import ChatState
from ...config.settings import settings


class ChatAgent(BaseAgent):
    """
    Simple chat agent for fast responses.
    
    This agent is optimized for speed:
    - No Think/Plan tools (immediate response)
    - Single LLM node
    - Minimal processing overhead
    
    Use for:
    - General conversation
    - Simple Q&A
    - Quick responses
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Chat Agent.
        
        Args:
            config: Optional configuration dict
        """
        config = config or {}
        
        # Create LLM with OpenRouter support
        self.llm = LLMFactory.create(
            provider_type=LLMProviderType(config.get("llm_provider", settings.LLM_PROVIDER)),
            model=config.get("model", settings.LLM_MODEL),
            temperature=config.get("temperature", settings.LLM_TEMPERATURE),
            max_tokens=config.get("max_tokens", settings.LLM_MAX_TOKENS),
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            enable_guardrail=config.get("enable_guardrail", False),  # Disable by default for chat
        )
        
        super().__init__(agent_type="chat", config=config)
    
    def _build_graph(self) -> StateGraph:
        """
        Build simple chat graph.
        
        Graph: chat_node → END
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(ChatState)
        
        # Single node for chat
        workflow.add_node("chat", self._chat_node)
        
        # Direct path to end
        workflow.set_entry_point("chat")
        workflow.add_edge("chat", END)
        
        return workflow.compile()
    
    async def _chat_node(self, state: ChatState) -> Dict[str, Any]:
        """
        Chat node - generate response.
        
        Args:
            state: Current chat state
            
        Returns:
            Updated state
        """
        self.logger.info("Executing chat node")
        
        try:
            # Build conversation context
            messages = self._build_messages(state)
            
            # Generate response with guardrails (via base LLM provider)
            response = await self.llm.ainvoke(messages)
            
            return {
                "response": response.content if hasattr(response, 'content') else str(response),
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Chat node error: {str(e)}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "error": str(e)
            }
    
    def _build_messages(self, state: ChatState) -> list:
        """
        Build message list for LLM.
        
        Args:
            state: Current chat state
            
        Returns:
            List of LangChain message objects
        """
        messages = []
        
        # Handle LangGraph wrapped state (nested query)
        query_val = state.get("query")
        if isinstance(query_val, dict):
            # Nested state from LangGraph
            actual_query = query_val.get("query")
            history = query_val.get("history", [])
            system_prompt = query_val.get("system_prompt")
        else:
            # Direct state
            actual_query = query_val
            history = state.get("history", [])
            system_prompt = state.get("system_prompt")
        
        # System message
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        # Conversation history as dicts
        if history:
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=msg["content"]))
        
        # Current user query
        if actual_query:
            messages.append(HumanMessage(content=actual_query))
        
        return messages

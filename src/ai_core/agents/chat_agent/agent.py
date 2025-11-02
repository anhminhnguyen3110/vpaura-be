"""Chat agent for fast general conversation."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..base import BaseAgent
from ...llm.llm_factory import LLMFactory, LLMProviderType
from .state import ChatAgentState
from ....config.settings import settings


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
    
    async def execute(
        self,
        query: str,
        history: Optional[list] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute chat agent with system prompt support.
        
        Args:
            query: User query
            history: Conversation history
            system_prompt: System prompt for the LLM
            metadata: Additional metadata
            
        Returns:
            Agent response
        """
        truncated_history = self.truncate_history(history or [])
        
        state: ChatAgentState = {
            "query": query,
            "history": truncated_history,
            "system_prompt": system_prompt,
            "metadata": metadata or {},
        }
        
        return await self._execute_internal(state)
    
    def _build_graph(self) -> StateGraph:
        """
        Build simple chat graph.
        
        Graph: chat_node → END
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(ChatAgentState)
        
        workflow.add_node("chat", self._chat_node)
        
        workflow.set_entry_point("chat")
        workflow.add_edge("chat", END)
        
        return workflow.compile()
    
    async def _chat_node(self, state: ChatAgentState) -> Dict[str, Any]:
        """
        Chat node - generate response.
        
        Args:
            state: Current chat state
            
        Returns:
            Updated state
        """
        self.logger.info("Executing chat node")
        
        try:
            messages = self._build_messages(state)
            
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
    
    def _build_messages(self, state: ChatAgentState) -> list:
        """
        Build message list for LLM.
        
        Args:
            state: Current chat state
            
        Returns:
            List of LangChain message objects
        """
        messages = []
        
        query_val = state.get("query")
        if isinstance(query_val, dict):
            actual_query = query_val.get("query")
            history = query_val.get("history", [])
            system_prompt = query_val.get("system_prompt")
        else:
            actual_query = query_val
            history = state.get("history", [])
            system_prompt = state.get("system_prompt")
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        if history:
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Current user query
        if actual_query:
            messages.append(HumanMessage(content=actual_query))
        
        return messages

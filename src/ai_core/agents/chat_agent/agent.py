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
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        history: Optional[list] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute chat agent with system prompt support.
        
        Args:
            query: User query
            session_id: Session ID for checkpointer (NEW)
            user_id: User ID for tracking (NEW)
            history: Conversation history (legacy, will be deprecated)
            system_prompt: System prompt for the LLM
            metadata: Additional metadata
            
        Returns:
            Agent response
        """
        # Build messages from history + current query
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        # Convert history to messages
        if history:
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Build state with new messages field
        state: ChatAgentState = {
            "messages": messages,
            "session_id": session_id,
            "system_prompt": system_prompt,
            "metadata": metadata or {},
        }
        
        # Build config for graph execution
        config = self._build_graph_config(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        # Execute with config
        return await self._execute_internal(state, config)
    
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
            Updated state with AI message added
        """
        self.logger.info("Executing chat node")
        
        try:
            # Messages already in state with add_messages reducer
            # No need to rebuild - just use directly
            messages = state.get("messages", [])
            
            if not messages:
                raise ValueError("No messages in state")
            
            response = await self.llm.ainvoke(messages)
            
            # Return AI message - add_messages will auto-merge it
            return {
                "messages": [response],
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Chat node error: {str(e)}", exc_info=True)
            
            # Return error message as AI response
            error_msg = AIMessage(
                content="I apologize, but I encountered an error. Please try again."
            )
            return {
                "messages": [error_msg],
                "error": str(e)
            }

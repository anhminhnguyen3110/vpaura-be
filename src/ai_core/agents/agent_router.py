"""Intent detection and automatic agent routing."""

from typing import Dict, Any, Optional
import logging
from langchain_core.messages import HumanMessage

from ..llm import LLMFactory, LLMProviderType
from ...config.settings import settings
from .agent_factory import AgentFactory, AgentType

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Routes user input to appropriate agent.
    
    Features:
    - Auto intent detection using LLM
    - Confidence-based fallback
    - Manual agent selection support
    """
    
    def __init__(self):
        """Initialize router with fast LLM for intent detection."""
        self.llm = LLMFactory.create(
            provider_type=LLMProviderType(settings.LLM_PROVIDER),
            model="gpt-3.5-turbo",  # Fast model for routing
            temperature=0.0,  # Deterministic
            max_tokens=50,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            enable_guardrail=False  # No guardrail for routing
        )
    
    async def detect_intent(self, user_input: str) -> tuple[AgentType, float]:
        """
        Detect which agent to use with confidence score.
        
        Args:
            user_input: User's input text
            
        Returns:
            Tuple of (agent_type, confidence_score)
        """
        prompt = f"""You are an intent classifier. Analyze the user input and determine which agent to use.

Available agents:
- neo4j: For Neo4j database queries, graph analysis, Cypher queries
  Keywords: "query", "database", "graph", "cypher", "find nodes", "relationships", "path"
  Examples: "Find all users connected to John", "Show me the shortest path between A and B"
  
- rag: For document-based question answering, knowledge retrieval, search
  Keywords: "search", "document", "knowledge", "what does X say", "find information"
  Examples: "What does the documentation say about X?", "Search for information about Y"
  
- chat: For general conversation, greetings, simple questions, chitchat
  Keywords: "hello", "hi", "how are you", "thanks", "joke"
  Examples: "Hello", "How are you?", "Tell me a joke", "What's 2+2?"

User input: "{user_input}"

Respond with ONLY the agent name and confidence (0.0-1.0):
Format: <agent> <confidence>
Example: neo4j 0.95"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            intent_str = response.content.strip().lower()
            
            # Parse response
            parts = intent_str.split()
            if len(parts) >= 2:
                agent_str, confidence_str = parts[0], parts[1]
                try:
                    agent_type = AgentType(agent_str)
                    confidence = float(confidence_str)
                    return agent_type, confidence
                except (ValueError, KeyError):
                    pass
            
            # Fallback parsing - just get agent name
            for agent_type in AgentType:
                if agent_type.value in intent_str:
                    return agent_type, 0.5  # Medium confidence
            
            # Default fallback
            logger.warning(f"Could not parse intent from: {intent_str}")
            return AgentType.CHAT, 0.3
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return AgentType.CHAT, 0.0
    
    async def route(
        self, 
        user_input: str, 
        agent_type: Optional[AgentType] = None,
        config: Optional[Dict[str, Any]] = None,
        confidence_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Route to appropriate agent and execute.
        
        Args:
            user_input: User's input text
            agent_type: Optional manual agent selection (overrides auto-detection)
            config: Optional agent configuration
            confidence_threshold: Minimum confidence for auto-routing (default 0.6)
            
        Returns:
            Agent execution result with metadata
        """
        auto_routed = False
        confidence = 1.0
        
        # Auto-detect if not specified
        if agent_type is None:
            detected_type, confidence = await self.detect_intent(user_input)
            
            # Check confidence threshold
            if confidence < confidence_threshold:
                logger.warning(
                    f"Low confidence ({confidence:.2f}) for {detected_type}, "
                    f"defaulting to CHAT agent"
                )
                agent_type = AgentType.CHAT
            else:
                agent_type = detected_type
                auto_routed = True
                logger.info(f"Auto-routed to {agent_type} (confidence: {confidence:.2f})")
        
        # Create and execute agent
        agent = AgentFactory.create(agent_type, config)
        result = await agent.execute({"input": user_input})
        
        # Add routing metadata
        result["_routing"] = {
            "agent_type": agent_type.value,
            "auto_routed": auto_routed,
            "confidence": confidence,
        }
        
        return result

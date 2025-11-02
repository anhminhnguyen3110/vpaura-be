"""Prompts for intent detection and agent routing."""

AGENT_CAPABILITIES = {
    "neo4j": {
        "description": "Specialized for Neo4j graph database operations - querying nodes, relationships, paths, and graph patterns using Cypher",
        "keywords": ["query", "database", "graph", "cypher", "find nodes", "relationships", "path", "connected", "traverse"],
        "examples": [
            "Find all users connected to John",
            "Show me the shortest path between A and B",
            "Get all products in the Electronics category"
        ],
        "use_when": "User needs to query or analyze data in the graph database"
    },
    "rag": {
        "description": "Specialized for document-based knowledge retrieval - searching through documents, extracting information, and answering based on stored knowledge",
        "keywords": ["search", "document", "knowledge", "what does X say", "find information", "according to", "documentation", "read"],
        "examples": [
            "What does the documentation say about authentication?",
            "Search for information about API rate limits",
            "Find details about the payment process"
        ],
        "use_when": "User needs information from documents or knowledge base"
    },
    "chat": {
        "description": "General-purpose conversational agent - handles direct questions, calculations, greetings, and requests that don't require database queries or document retrieval",
        "keywords": ["hello", "hi", "how are you", "thanks", "joke", "calculate", "what is", "explain", "tell me about"],
        "examples": [
            "Hello, how can you help me?",
            "What's 2+2?",
            "Tell me a joke",
            "Explain what machine learning is",
            "How does encryption work?"
        ],
        "use_when": "User asks general questions, greetings, or requests that can be answered directly without external data sources"
    }
}


def get_intent_detection_prompt(user_input: str) -> str:
    """Generate intent detection prompt for routing to appropriate agent.
    
    Args:
        user_input: User's input text
        
    Returns:
        Formatted prompt for LLM
    """
    agent_details = []
    for agent_name, info in AGENT_CAPABILITIES.items():
        keywords_str = ", ".join([f'"{kw}"' for kw in info["keywords"]])
        examples_str = "\n    ".join([f'- "{ex}"' for ex in info["examples"]])
        
        agent_details.append(
            f"**{agent_name.upper()}**\n"
            f"  Description: {info['description']}\n"
            f"  Use When: {info['use_when']}\n"
            f"  Keywords: {keywords_str}\n"
            f"  Examples:\n    {examples_str}"
        )
    
    agents_text = "\n\n".join(agent_details)
    
    return f"""You are an intent classifier that routes user requests to the appropriate specialized agent.

Available Agents:

{agents_text}

User Input: "{user_input}"

Instructions:
1. Analyze the user's intent and keywords carefully
2. Match to the most appropriate agent based on capabilities and use case
3. Assign confidence score (0.0-1.0) based on keyword match and context clarity
4. Respond in the exact format specified below

Required Output Format:
<agent> <confidence>

Example:
neo4j 0.95

Note: Output ONLY the agent name and confidence score, nothing else."""

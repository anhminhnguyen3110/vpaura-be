"""Prompts for RAG (Retrieval-Augmented Generation) agent."""


RAG_SYSTEM_PROMPT = """You are a helpful AI assistant with access to a knowledge base.
Answer questions based on the provided context.
If the context doesn't contain enough information, say so honestly."""


def get_rag_generation_prompt(query: str, context: str) -> str:
    """Generate RAG answer prompt.
    
    Args:
        query: User's question
        context: Retrieved context from documents
        
    Returns:
        Formatted generation prompt
    """
    return f"""You are a helpful AI assistant that answers questions based on provided context.

Context:
{context}

Question: {query}

Instructions:
1. Answer the question using ONLY information from the context above
2. Be specific and cite relevant parts of the context when possible
3. If the context doesn't contain enough information to answer fully, acknowledge this
4. Keep your answer clear, concise, and well-structured
5. Format: Use paragraphs for readability, bullet points for lists

Answer:"""


def get_rag_thinking_prompt(query: str) -> str:
    """Generate RAG thinking prompt.
    
    Args:
        query: User's question
        
    Returns:
        Formatted thinking prompt
    """
    return f"""User Query: {query}

Instructions:
Analyze this query carefully before searching. Consider:

1. Intent Analysis:
   - What specific information is the user seeking?
   - Is this a factual question, comparison, or exploratory query?

2. Retrieval Strategy:
   - What key concepts and keywords should we search for?
   - What synonyms or related terms might be in the documents?
   - What metadata filters (date, category, etc.) would be helpful?

3. Expected Content:
   - What type of documents would likely contain this information?
   - What format would the answer likely be in (definition, process, list, etc.)?

Format: Explain your analysis in clear paragraphs."""


def get_rag_planning_prompt(query: str, thinking: str) -> str:
    """Generate RAG planning prompt.
    
    Args:
        query: User's question
        thinking: Previous thinking output
        
    Returns:
        Formatted planning prompt
    """
    return f"""User Query: {query}

Your Thinking:
{thinking}

Instructions:
Create a detailed retrieval and answer plan with numbered steps:

1. Search Strategy:
   - List 2-3 specific search queries to use
   - Specify any metadata filters to apply

2. Result Processing:
   - How many documents to retrieve?
   - What criteria to rank/filter results?
   - How to handle conflicting information?

3. Answer Structure:
   - How to organize the final answer?
   - What sections or points to include?
   - Any examples or citations to include?

Format: Use numbered list (1., 2., 3., etc.) with sub-points."""


# Legacy constants
RAG_GENERATION_PROMPT = get_rag_generation_prompt

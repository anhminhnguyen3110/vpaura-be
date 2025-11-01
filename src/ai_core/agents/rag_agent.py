"""RAG agent for retrieval-augmented generation."""

from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END

from ..agents.base import BaseAgent
from ..llm.llm_factory import LLMFactory
from .state.chat_state import ChatState
from ..tools.think import ThinkTool
from ..tools.plan import PlanTool
from ..vectorstore.pgvector_store import PgVectorStore
from ..vectorstore.base import Document
from ..vectorstore.embeddings import get_embedding_function


class RAGAgent(BaseAgent):
    """
    RAG (Retrieval-Augmented Generation) agent.
    
    This agent uses a full workflow:
    - Think: Analyze the query
    - Plan: Plan retrieval strategy
    - Retrieve: Fetch relevant documents
    - Rerank: Score and order results
    - Generate: Create answer with context
    - Respond: Format final response
    
    Features:
    - Semantic search over documents
    - Relevance reranking
    - Context-aware generation
    - Metadata filtering
    """
    
    def __init__(
        self,
        llm_provider: Optional[str] = None,
        model: Optional[str] = None,
        vectorstore_config: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        **kwargs
    ):
        """
        Initialize RAG Agent.
        
        Args:
            llm_provider: LLM provider name (default from config)
            model: Model name (default from config)
            vectorstore_config: Vector store configuration
            top_k: Number of documents to retrieve
            **kwargs: Additional configuration
        """
        self.llm = LLMFactory.create(provider=llm_provider, model=model)
        self.vectorstore = PgVectorStore(config=vectorstore_config)
        self.embeddings = get_embedding_function()
        self.think_tool = ThinkTool()
        self.plan_tool = PlanTool()
        self.top_k = top_k
        super().__init__(agent_type="rag", **kwargs)
    
    def _build_graph(self) -> StateGraph:
        """
        Build RAG agent graph.
        
        Graph:
        think → plan → retrieve → rerank → generate → respond → END
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("think", self._think_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("rerank", self._rerank_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("respond", self._respond_node)
        
        # Build workflow
        workflow.set_entry_point("think")
        workflow.add_edge("think", "plan")
        workflow.add_edge("plan", "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "generate")
        workflow.add_edge("generate", "respond")
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    async def _think_node(self, state: ChatState) -> Dict[str, Any]:
        """Think about the retrieval strategy."""
        self.logger.info("Executing think node")
        
        try:
            prompt = f"""
            User Query: {state['query']}
            
            Analyze this query and think about:
            1. What information is the user looking for?
            2. What kind of documents would be relevant?
            3. What are key concepts to search for?
            4. Any metadata filters that might help?
            """
            
            thinking = await self.think_tool.execute(prompt)
            
            return {"thinking": thinking}
            
        except Exception as e:
            self.logger.error(f"Think node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _plan_node(self, state: ChatState) -> Dict[str, Any]:
        """Plan the retrieval strategy."""
        self.logger.info("Executing plan node")
        
        try:
            prompt = f"""
            User Query: {state['query']}
            Thinking: {state.get('thinking', '')}
            
            Create a retrieval plan:
            1. What search queries to use?
            2. What metadata filters to apply?
            3. How to rank/filter results?
            4. How to structure the answer?
            """
            
            plan = await self.plan_tool.execute(prompt)
            
            return {"plan": plan}
            
        except Exception as e:
            self.logger.error(f"Plan node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _retrieve_node(self, state: ChatState) -> Dict[str, Any]:
        """Retrieve relevant documents."""
        self.logger.info("Executing retrieve node")
        
        try:
            query = state["query"]
            
            # Extract metadata filters from state if available
            filter_dict = state.get("metadata_filter")
            
            # Perform similarity search
            documents = await self.vectorstore.similarity_search_with_score(
                query=query,
                k=self.top_k,
                filter_dict=filter_dict
            )
            
            self.logger.info(f"Retrieved {len(documents)} documents")
            
            return {
                "retrieved_docs": documents,
                "retrieval_count": len(documents)
            }
            
        except Exception as e:
            self.logger.error(f"Retrieve node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _rerank_node(self, state: ChatState) -> Dict[str, Any]:
        """Rerank retrieved documents."""
        self.logger.info("Executing rerank node")
        
        try:
            documents = state.get("retrieved_docs", [])
            
            if not documents:
                return {"reranked_docs": []}
            
            # Already sorted by similarity score from retrieval
            # Could add additional reranking logic here (cross-encoder, etc.)
            
            # For now, just take top results and filter by score threshold
            score_threshold = 0.7
            filtered_docs = [
                (doc, score) for doc, score in documents
                if score >= score_threshold
            ]
            
            self.logger.info(
                f"Reranked {len(filtered_docs)} documents "
                f"(filtered from {len(documents)} by score threshold {score_threshold})"
            )
            
            return {"reranked_docs": filtered_docs}
            
        except Exception as e:
            self.logger.error(f"Rerank node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _generate_node(self, state: ChatState) -> Dict[str, Any]:
        """Generate answer with retrieved context."""
        self.logger.info("Executing generate node")
        
        try:
            query = state["query"]
            reranked_docs = state.get("reranked_docs", [])
            
            # Build context from documents
            context_parts = []
            for idx, (doc, score) in enumerate(reranked_docs[:3], 1):
                context_parts.append(
                    f"Document {idx} (relevance: {score:.2f}):\n{doc.content}"
                )
            
            context = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
            
            # Build prompt
            prompt = f"""
            Answer the user's question based on the following context.
            If the context doesn't contain enough information, say so honestly.
            
            Context:
            {context}
            
            Question: {query}
            
            Answer:
            """
            
            messages = [{"role": "user", "content": prompt}]
            answer = await self.llm.ainvoke(messages)
            
            return {
                "answer": answer,
                "context_used": len(context_parts)
            }
            
        except Exception as e:
            self.logger.error(f"Generate node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _respond_node(self, state: ChatState) -> Dict[str, Any]:
        """Format and return final response."""
        self.logger.info("Executing respond node")
        
        if state.get("error"):
            return {
                "response": f"I apologize, but I encountered an error: {state['error']}",
                "error": state["error"]
            }
        
        answer = state.get("answer", "I couldn't generate an answer.")
        context_used = state.get("context_used", 0)
        retrieval_count = state.get("retrieval_count", 0)
        
        # Format response
        response_parts = [answer]
        
        if context_used > 0:
            response_parts.append(
                f"\n\n_Based on {context_used} relevant document(s) "
                f"(retrieved {retrieval_count} total)_"
            )
        else:
            response_parts.append(
                "\n\n_Note: No relevant documents were found in the knowledge base._"
            )
        
        response = "".join(response_parts)
        
        return {
            "response": response,
            "error": None
        }

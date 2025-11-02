"""Debug endpoints for inspecting LangGraph checkpoints and session state.

These endpoints are for debugging and admin purposes only.
Access should be restricted to authenticated admin users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging

from ...database.session import get_db_session
from ...ai_core.agents.agent_factory import AgentFactory, AgentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/session/{session_id}/checkpoints")
async def get_session_checkpoints(
    session_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get checkpoints for a session (thread).
    
    **Admin only** - Returns full checkpoint data including:
    - All messages (user, assistant, tool calls, tool results)
    - Agent reasoning/thinking
    - Retrieved documents (RAG)
    - Cypher queries (Neo4j)
    - Metadata
    
    Args:
        session_id: Session ID
        limit: Max number of checkpoints to return (default: 10)
    
    Returns:
        List of checkpoints with full state
    """
    try:
        result = await db.execute(
            text("""
                SELECT 
                    checkpoint_id,
                    parent_checkpoint_id,
                    type,
                    checkpoint,
                    metadata,
                    (checkpoint->>'ts') as timestamp
                FROM checkpoints
                WHERE thread_id = :thread_id
                ORDER BY checkpoint_id DESC
                LIMIT :limit
            """),
            {"thread_id": str(session_id), "limit": limit}
        )
        
        rows = result.fetchall()
        
        if not rows:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "detail": f"No checkpoints found for session {session_id}",
                    "session_id": str(session_id)
                }
            )
        
        checkpoints = []
        for row in rows:
            checkpoints.append({
                "checkpoint_id": row.checkpoint_id,
                "parent_checkpoint_id": row.parent_checkpoint_id,
                "type": row.type,
                "checkpoint": row.checkpoint,  # Full JSONB data
                "metadata": row.metadata,
                "timestamp": row.timestamp
            })
        
        logger.info(
            "debug_checkpoints_retrieved",
            session_id=str(session_id),
            count=len(checkpoints)
        )
        
        return {
            "session_id": str(session_id),
            "checkpoint_count": len(checkpoints),
            "checkpoints": checkpoints
        }
        
    except Exception as e:
        logger.error(
            "debug_get_checkpoints_failed",
            session_id=str(session_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve checkpoints: {str(e)}"
        )


@router.get("/session/{session_id}/state")
async def get_session_state(
    session_id: int,
    agent_type: AgentType = AgentType.CHAT,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get current graph state for a session.
    
    **Admin only** - Returns the current state from LangGraph's StateSnapshot.
    
    Args:
        session_id: Session ID
        agent_type: Type of agent to use for state retrieval (default: CHAT)
    
    Returns:
        Current graph state with messages, metadata, etc.
    """
    try:
        agent = AgentFactory.create(agent_type)
        
        if agent.graph is None:
            await agent._build_graph_async()
        
        if not agent._checkpointer:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Checkpointer not available for this agent",
                    "agent_type": agent_type.value
                }
            )
        
        from asgiref.sync import sync_to_async
        
        state_snapshot = await sync_to_async(agent.graph.get_state)(
            config={"configurable": {"thread_id": str(session_id)}}
        )
        
        if not state_snapshot.values:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "detail": f"No state found for session {session_id}",
                    "session_id": str(session_id)
                }
            )
        
        state_data = dict(state_snapshot.values)
        
        if "messages" in state_data:
            messages = []
            for msg in state_data["messages"]:
                msg_dict = {
                    "type": msg.type if hasattr(msg, "type") else "unknown",
                    "content": msg.content if hasattr(msg, "content") else str(msg)
                }
                
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "name": tc.get("name"),
                            "args": tc.get("args"),
                            "id": tc.get("id")
                        }
                        for tc in msg.tool_calls
                    ]
                
                if hasattr(msg, "tool_call_id"):
                    msg_dict["tool_call_id"] = msg.tool_call_id
                
                messages.append(msg_dict)
            
            state_data["messages"] = messages
        
        logger.info(
            "debug_state_retrieved",
            session_id=str(session_id),
            agent_type=agent_type.value
        )
        
        return {
            "session_id": str(session_id),
            "agent_type": agent_type.value,
            "state": state_data,
            "next_node": state_snapshot.next,
            "config": state_snapshot.config
        }
        
    except Exception as e:
        logger.error(
            "debug_get_state_failed",
            session_id=str(session_id),
            agent_type=agent_type.value,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve state: {str(e)}"
        )


@router.post("/session/{session_id}/fork")
async def fork_session(
    session_id: int,
    checkpoint_id: Optional[str] = None,
    agent_type: AgentType = AgentType.CHAT,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Fork a session from a specific checkpoint ("what-if" scenarios).
    
    **Admin only** - Creates a new session by branching from a checkpoint.
    This allows exploring alternative conversation paths.
    
    Args:
        session_id: Original session ID
        checkpoint_id: Specific checkpoint to fork from (optional, defaults to latest)
        agent_type: Type of agent (default: CHAT)
    
    Returns:
        New session ID and initial state
    """
    try:
        # Generate new session ID for the fork (will be auto-incremented when created)
        # For now, just return a message that forking is not fully implemented
        
        # Get checkpoint to fork from
        if checkpoint_id:
            # Copy specific checkpoint
            result = await db.execute(
                text("""
                    SELECT checkpoint, metadata
                    FROM checkpoints
                    WHERE thread_id = :thread_id
                    AND checkpoint_id = :checkpoint_id
                """),
                {
                    "thread_id": str(session_id),
                    "checkpoint_id": checkpoint_id
                }
            )
        else:
            # Copy latest checkpoint
            result = await db.execute(
                text("""
                    SELECT checkpoint, metadata
                    FROM checkpoints
                    WHERE thread_id = :thread_id
                    ORDER BY checkpoint_id DESC
                    LIMIT 1
                """),
                {"thread_id": str(session_id)}
            )
        
        row = result.fetchone()
        
        if not row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "detail": f"Checkpoint not found for session {session_id}",
                    "checkpoint_id": checkpoint_id
                }
            )
        
        logger.info(
            "session_fork_requested",
            original_session_id=session_id,
            checkpoint_id=checkpoint_id
        )
        
        return {
            "original_session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "message": "Session forking not fully implemented. This is a placeholder for future fork functionality.",
            "checkpoint_data": row.checkpoint
        }
        
    except Exception as e:
        logger.error(
            "debug_fork_session_failed",
            session_id=str(session_id),
            checkpoint_id=checkpoint_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fork session: {str(e)}"
        )

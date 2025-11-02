"""Neo4j MCP client for Cypher query execution."""

from typing import Dict, Any, Optional, List
import logging
import asyncio
from neo4j import AsyncGraphDatabase, AsyncDriver

from .base import BaseMCPClient
from ...config.settings import settings

logger = logging.getLogger(__name__)


class Neo4jMCPClient(BaseMCPClient):
    """Neo4j MCP client for Cypher execution and schema management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.neo4j_driver: Optional[AsyncDriver] = None
        self.uri = config.get("uri", settings.NEO4J_URI) if config else settings.NEO4J_URI
        self.user = config.get("user", settings.NEO4J_USER) if config else settings.NEO4J_USER
        self.password = config.get("password", settings.NEO4J_PASSWORD) if config else settings.NEO4J_PASSWORD
        self.database = config.get("database", settings.NEO4J_DATABASE) if config else settings.NEO4J_DATABASE
    
    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        logger.info(f"Connecting to Neo4j at {self.uri}")
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            await self.neo4j_driver.verify_connectivity()
            self._connection = {"status": "connected", "uri": self.uri}
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Neo4j."""
        if self.neo4j_driver:
            logger.info("Disconnecting from Neo4j")
            await self.neo4j_driver.close()
            self.neo4j_driver = None
            self._connection = None
    
    async def execute(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute MCP command."""
        params = params or {}
        
        if not self.is_connected:
            await self.connect()
        
        cmd = command.lower()
        if cmd == "run_query":
            return await self.execute_cypher(params.get("query", ""))
        elif cmd == "get_schema":
            return await self.get_schema()
        elif cmd == "explain":
            return await self.explain_query(params.get("query", ""))
        elif cmd == "validate":
            return await self.validate_query(params.get("query", ""))
        else:
            raise ValueError(f"Unknown command: {command}")
    
    async def execute_cypher(self, query: str) -> List[Dict[str, Any]]:
        """Execute Cypher query and return results."""
        if not self.neo4j_driver:
            await self.connect()
        
        logger.info(f"Executing Cypher: {query[:100]}...")
        
        async with self.neo4j_driver.session(database=self.database) as session:
            result = await session.run(query)
            records = await result.data()
            logger.info(f"Query returned {len(records)} records")
            return records
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema from Neo4j."""
        if not self.neo4j_driver:
            await self.connect()
        
        logger.info("Retrieving Neo4j schema")
        
        schema = {
            "node_labels": [],
            "relationship_types": [],
            "property_keys": [],
            "constraints": [],
            "indexes": []
        }
        
        async with self.neo4j_driver.session(database=self.database) as session:
            result = await session.run("CALL db.labels()")
            labels = await result.data()
            schema["node_labels"] = [record["label"] for record in labels]
            
            result = await session.run("CALL db.relationshipTypes()")
            rel_types = await result.data()
            schema["relationship_types"] = [record["relationshipType"] for record in rel_types]
            
            result = await session.run("CALL db.propertyKeys()")
            props = await result.data()
            schema["property_keys"] = [record["propertyKey"] for record in props]
            
            for label in schema["node_labels"][:10]:
                try:
                    result = await session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    count_data = await result.single()
                    if count_data:
                        schema[f"{label}_count"] = count_data["count"]
                except Exception:
                    pass
        
        logger.info(f"Schema retrieved: {len(schema['node_labels'])} labels, {len(schema['relationship_types'])} relationships")
        return schema
    
    async def explain_query(self, query: str) -> Dict[str, Any]:
        """Return EXPLAIN execution plan from Neo4j."""
        if not self.neo4j_driver:
            await self.connect()
        
        logger.info(f"Explaining query: {query[:100]}...")
        
        async with self.neo4j_driver.session(database=self.database) as session:
            result = await session.run(f"EXPLAIN {query}")
            plan = await result.consume()
            
            return {
                "plan": str(plan.plan) if plan.plan else None,
                "profile_info": str(plan.profile) if hasattr(plan, 'profile') else None
            }
    
    async def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate query using EXPLAIN plan."""
        logger.info(f"Validating query using EXPLAIN: {query[:100]}...")
        
        try:
            explain_result = await self.explain_query(query)
            if explain_result and explain_result.get("plan"):
                return {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                    "plan_summary": "Validation passed (based on EXPLAIN plan)."
                }
            else:
                return {
                    "valid": False,
                    "errors": ["Empty plan returned from EXPLAIN."],
                    "warnings": []
                }
        except Exception as e:
            logger.warning(f"EXPLAIN failed: {e}")
            return {
                "valid": False,
                "errors": [f"EXPLAIN failed: {e}"],
                "warnings": []
            }


def get_neo4j_client(config: Optional[Dict[str, Any]] = None) -> Neo4jMCPClient:
    """Return a Neo4j MCP client instance."""
    return Neo4jMCPClient(config)
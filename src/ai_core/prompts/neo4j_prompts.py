"""Prompts for Neo4j agent."""


def get_neo4j_analysis_prompt(query: str, schema: dict) -> str:
    """Generate Neo4j analysis prompt (combines thinking + planning).
    
    Args:
        query: User's query
        schema: Database schema information
        
    Returns:
        Formatted analysis prompt
    """
    node_labels = ', '.join(schema.get('node_labels', []))
    relationships = ', '.join(schema.get('relationship_types', []))
    
    return f"""User Query: {query}

Database Schema:
- Node Labels: {node_labels}
- Relationship Types: {relationships}

Instructions:
Analyze this query comprehensively to prepare for Cypher generation.

1. Intent Understanding:
   - What specific data is the user requesting?
   - Is this a simple lookup, graph traversal, aggregation, or complex pattern?
   - What is the expected output format?

2. Schema Mapping:
   - Which node labels are relevant to this query?
   - What relationships need to be traversed?
   - What properties should be matched or returned?
   - Draw the expected graph pattern mentally

3. Query Strategy:
   - What MATCH patterns are needed?
   - Are WHERE conditions required for filtering?
   - What should the RETURN clause include?
   - Any aggregations (COUNT, COLLECT) or ordering needed?
   - Edge cases to consider (null values, empty results, etc.)?

Format: Provide a clear analysis covering all three sections above."""


def get_neo4j_generation_prompt(query: str, analysis: dict, schema: dict) -> str:
    """Generate Neo4j Cypher generation prompt.
    
    Args:
        query: User's query
        analysis: Analysis output from previous step
        schema: Database schema
        
    Returns:
        Formatted generation prompt
    """
    analysis_text = analysis.get('analysis', '') if isinstance(analysis, dict) else str(analysis)
    node_labels = schema.get('node_labels', [])
    relationships = schema.get('relationship_types', [])
    
    return f"""You are a Neo4j Cypher query generator with access to MCP tools.

User Query: {query}

Your Analysis:
{analysis_text}

Available Schema:
- Node Labels: {node_labels}
- Relationship Types: {relationships}

Instructions:
1. Generate a syntactically correct Cypher query based on your analysis
2. Use proper variable naming (lowercase, descriptive)
3. Include appropriate WHERE clauses for filtering
4. Return only the data requested by the user
5. Ensure the query is efficient and follows Neo4j best practices
6. You can use MCP tools if needed for schema exploration or validation

Required Output Format:
Return ONLY the Cypher query without any explanation, comments, or markdown.

Example:
MATCH (u:User)-[:KNOWS]->(f:User) WHERE u.name = 'Alice' RETURN f.name

Your Cypher Query:"""

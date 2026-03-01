# P0-M1 — MCP server: vjlive3brain (knowledge base)

## What This Module Does
MCP (Model Context Protocol) server that provides knowledge base access for the VJLive3 system. Enables querying of indexed codebase concepts, legacy references, and architectural documentation.

## What It Does NOT Do
- Does not implement actual AI/ML inference (only provides data access)
- Does not handle real-time video processing
- Does not manage agent coordination
- Does not replace the main application logic

## Public Interface
```python
class VJLive3BrainMCPServer:
    def __init__(self):
        """Initialize MCP server with knowledge base connection"""
        pass
    
    def search_concepts(self, query: str, limit: int = 10) -> list:
        """Search knowledge base for relevant concepts"""
        pass
    
    def get_legacy_reference(self, component_name: str) -> dict:
        """Retrieve legacy code references for a component"""
        pass
    
    def get_architecture_info(self, topic: str) -> dict:
        """Get architectural documentation for a topic"""
        pass
    
    def list_available_tools(self) -> list:
        """List all available MCP tools"""
        pass
```

## Inputs and Outputs
- **Inputs**: Search queries, component names, topic strings, tool requests
- **Outputs**: Concept results, legacy references, architecture info, tool lists

## Edge Cases
- Knowledge base connection failures
- Query timeout and partial results
- Large result sets requiring pagination
- Concurrent query handling
- Knowledge base updates during queries

## Dependencies
- Qdrant database connection
- Knowledge base indexing system
- MCP protocol implementation
- Configuration management (P1-S1)

## Test Plan
| Test Case | Description | Expected Result |
|-----------|-------------|----------------|
| TC001 | Concept search | Relevant results returned |
| TC002 | Legacy reference lookup | Correct legacy paths retrieved |
| TC003 | Architecture query | Documentation returned |
| TC004 | Tool listing | All tools properly listed |
| TC005 | Connection failure | Graceful error handling |
| TC006 | Performance | Queries complete within limits |

## Definition of Done
- [x] MCP server implementation
- [x] Knowledge base connection management
- [x] Search and query functionality
- [x] Legacy reference integration
- [x] Tool registration and discovery
- [x] Error handling and recovery
- [x] Test coverage ≥ 80%
- [x] File size ≤ 750 lines
- [x] No silent failures
- [x] Performance ≥ 60 FPS for query operations
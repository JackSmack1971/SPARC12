"""
sparc_mcp_server.py
==================

MCP Server wrapper for the ContextPortalSPARCServer that exposes all functionality
through the Model Context Protocol for integration with Roo Code and other MCP clients.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Sequence

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Import your specialized server
from specialized_mcp_server import ContextPortalSPARCServer


class SPARCMCPServer:
    """MCP Server wrapper for SPARC Context Portal functionality."""
    
    def __init__(self):
        self.server = Server("sparc-context-portal")
        self.context_server: Optional[ContextPortalSPARCServer] = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register all MCP handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List all available SPARC context tools."""
            return [
                # Phase management tools
                types.Tool(
                    name="sparc_get_current_phase",
                    description="Get the current SPARC development phase",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="sparc_transition_phase",
                    description="Transition to the next SPARC phase",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "confirm": {
                                "type": "boolean",
                                "description": "Confirm the phase transition"
                            }
                        },
                        "required": ["confirm"]
                    }
                ),
                
                # Context management tools
                types.Tool(
                    name="sparc_get_product_context",
                    description="Retrieve the current product context",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="sparc_update_product_context",
                    description="Update product context with new information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "object",
                                "description": "Full context object to replace current content"
                            },
                            "patch_content": {
                                "type": "object", 
                                "description": "Partial updates to merge with existing content"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="sparc_get_active_context",
                    description="Get the current active session context",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="sparc_update_active_context",
                    description="Update active session context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "object"},
                            "patch_content": {"type": "object"}
                        }
                    }
                ),
                
                # Decision logging tools
                types.Tool(
                    name="sparc_log_decision",
                    description="Log an architectural or design decision",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Brief summary of the decision"
                            },
                            "rationale": {
                                "type": "string", 
                                "description": "Detailed rationale for the decision"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags for categorizing the decision"
                            }
                        },
                        "required": ["summary", "rationale"]
                    }
                ),
                types.Tool(
                    name="sparc_get_decisions",
                    description="Retrieve logged decisions with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of decisions to return"
                            },
                            "tags_include_all": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags that must all be present"
                            },
                            "tags_include_any": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "Tags where at least one must be present"
                            }
                        }
                    }
                ),
                
                # Progress tracking tools
                types.Tool(
                    name="sparc_log_progress",
                    description="Log progress on a task or milestone",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Description of the progress item"
                            },
                            "status": {
                                "type": "string", 
                                "description": "Status: pending, in_progress, completed, blocked"
                            },
                            "parent_id": {
                                "type": "integer",
                                "description": "ID of parent progress item for hierarchical tracking"
                            }
                        },
                        "required": ["description", "status"]
                    }
                ),
                types.Tool(
                    name="sparc_get_progress",
                    description="Retrieve progress items with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status_filter": {
                                "type": "string",
                                "description": "Filter by status"
                            },
                            "parent_id_filter": {
                                "type": "integer",
                                "description": "Filter by parent ID"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum items to return"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="sparc_update_progress",
                    description="Update an existing progress item",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "progress_id": {
                                "type": "integer",
                                "description": "ID of progress item to update"
                            },
                            "status": {"type": "string"},
                            "description": {"type": "string"},
                            "parent_id": {"type": "integer"}
                        },
                        "required": ["progress_id"]
                    }
                ),
                
                # System patterns tools
                types.Tool(
                    name="sparc_log_system_pattern",
                    description="Log a reusable system pattern or architectural approach",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the pattern"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the pattern"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags for categorizing the pattern"
                            }
                        },
                        "required": ["name", "description"]
                    }
                ),
                types.Tool(
                    name="sparc_get_system_patterns",
                    description="Retrieve system patterns with optional tag filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tags_include_all": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "limit": {"type": "integer"}
                        }
                    }
                ),
                
                # Search and RAG tools
                types.Tool(
                    name="sparc_semantic_search",
                    description="Perform semantic search across all project context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query text"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5
                            },
                            "filter_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Limit search to specific item types"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="sparc_rag_assist",
                    description="Get RAG-powered assistance for a query, optimized for current SPARC mode",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Question or request for assistance"
                            },
                            "mode": {
                                "type": "string",
                                "description": "Current SPARC mode (e.g., sparc-architect, sparc-code-implementer)"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of context items to retrieve",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                
                # Synchronization tools
                types.Tool(
                    name="sparc_sync_from_memory_bank",
                    description="Import data from SPARC12 memory bank files into database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_bank_path": {
                                "type": "string",
                                "description": "Path to memory-bank directory"
                            }
                        },
                        "required": ["memory_bank_path"]
                    }
                ),
                types.Tool(
                    name="sparc_sync_to_memory_bank",
                    description="Export database content to SPARC12 memory bank files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_bank_path": {
                                "type": "string",
                                "description": "Path to memory-bank directory"
                            }
                        },
                        "required": ["memory_bank_path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls."""
            if not self.context_server:
                return [types.TextContent(
                    type="text",
                    text="Error: Context server not initialized. Please set workspace_id first."
                )]
            
            try:
                result = await self._execute_tool(name, arguments)
                return [types.TextContent(
                    type="text", 
                    text=json.dumps(result, indent=2, default=str)
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
    
    async def _execute_tool(self, name: str, args: dict) -> Any:
        """Execute a specific tool call."""
        server = self.context_server
        
        # Phase management
        if name == "sparc_get_current_phase":
            return {"current_phase": server.get_current_phase()}
        
        elif name == "sparc_transition_phase":
            if args.get("confirm", False):
                old_phase = server.get_current_phase()
                server.transition_to_next_phase()
                new_phase = server.get_current_phase()
                return {
                    "transitioned": True,
                    "from_phase": old_phase,
                    "to_phase": new_phase
                }
            return {"error": "Phase transition not confirmed"}
        
        # Context management
        elif name == "sparc_get_product_context":
            return server.get_product_context() or {}
        
        elif name == "sparc_update_product_context":
            server.update_product_context(
                content=args.get("content"),
                patch_content=args.get("patch_content")
            )
            return {"updated": True}
        
        elif name == "sparc_get_active_context":
            return server.get_active_context() or {}
        
        elif name == "sparc_update_active_context":
            server.update_active_context(
                content=args.get("content"),
                patch_content=args.get("patch_content")
            )
            return {"updated": True}
        
        # Decision logging
        elif name == "sparc_log_decision":
            decision_id = server.log_decision(
                summary=args["summary"],
                rationale=args["rationale"],
                tags=args.get("tags")
            )
            return {"decision_id": decision_id, "logged": True}
        
        elif name == "sparc_get_decisions":
            decisions = server.get_decisions(
                limit=args.get("limit"),
                tags_filter_include_all=args.get("tags_include_all"),
                tags_filter_include_any=args.get("tags_include_any")
            )
            return {"decisions": decisions, "count": len(decisions)}
        
        # Progress tracking
        elif name == "sparc_log_progress":
            progress_id = server.log_progress(
                description=args["description"],
                status=args["status"],
                parent_id=args.get("parent_id")
            )
            return {"progress_id": progress_id, "logged": True}
        
        elif name == "sparc_get_progress":
            progress = server.get_progress(
                status_filter=args.get("status_filter"),
                parent_id_filter=args.get("parent_id_filter"),
                limit=args.get("limit")
            )
            return {"progress": progress, "count": len(progress)}
        
        elif name == "sparc_update_progress":
            server.update_progress(
                progress_id=args["progress_id"],
                status=args.get("status"),
                description=args.get("description"),
                parent_id=args.get("parent_id")
            )
            return {"updated": True}
        
        # System patterns
        elif name == "sparc_log_system_pattern":
            pattern_id = server.log_system_pattern(
                name=args["name"],
                description=args["description"],
                tags=args.get("tags")
            )
            return {"pattern_id": pattern_id, "logged": True}
        
        elif name == "sparc_get_system_patterns":
            patterns = server.get_system_patterns(
                tags_filter_include_all=args.get("tags_include_all"),
                limit=args.get("limit")
            )
            return {"patterns": patterns, "count": len(patterns)}
        
        # Search and RAG
        elif name == "sparc_semantic_search":
            results = server.semantic_search(
                query_text=args["query"],
                top_k=args.get("top_k", 5),
                filter_item_types=args.get("filter_types")
            )
            return {"results": results, "count": len(results)}
        
        elif name == "sparc_rag_assist":
            results = server.rag_assist(
                query=args["query"],
                mode=args.get("mode"),
                top_k=args.get("top_k", 5)
            )
            return {
                "relevant_context": results,
                "count": len(results),
                "mode": args.get("mode"),
                "query": args["query"]
            }
        
        # Synchronization
        elif name == "sparc_sync_from_memory_bank":
            server.sync_from_memory_bank(args["memory_bank_path"])
            return {"imported": True, "from": args["memory_bank_path"]}
        
        elif name == "sparc_sync_to_memory_bank":
            server.sync_to_memory_bank(args["memory_bank_path"])
            return {"exported": True, "to": args["memory_bank_path"]}
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    def initialize_workspace(self, workspace_path: str):
        """Initialize the context server for a specific workspace."""
        self.context_server = ContextPortalSPARCServer(workspace_path)
    
    async def run(self, workspace_path: str):
        """Run the MCP server."""
        self.initialize_workspace(workspace_path)
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="sparc-context-portal",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python sparc_mcp_server.py <workspace_path>")
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    server = SPARCMCPServer()
    asyncio.run(server.run(workspace_path))

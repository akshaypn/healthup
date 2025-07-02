import asyncio
import logging
import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio
from . import schemas

logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manager for MCP servers using OpenAI agents"""
    
    def __init__(self, mcp_config: schemas.MCPServerConfig):
        self.mcp_config = mcp_config
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self._server: Optional[MCPServer] = None
    
    async def start_server(self):
        """Start the MCP server"""
        try:
            # Create MCP server with filesystem tools
            self._server = MCPServerStdio(
                name="HealthUp Filesystem Server",
                params={
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
                },
            )
            await self._server.__aenter__()
            logger.info("MCP server started successfully")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the MCP server"""
        if self._server:
            try:
                await self._server.__aexit__(None, None, None)
                logger.info("MCP server stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping MCP server: {e}")
    
    @asynccontextmanager
    async def get_server(self):
        """Context manager for MCP server"""
        if not self._server:
            await self.start_server()
        try:
            yield self._server
        finally:
            # Don't stop the server here, let the manager handle it
            pass
    
    async def run_agent_with_mcp(self, prompt: str, tools: Optional[list] = None) -> Dict[str, Any]:
        """Run an OpenAI agent with MCP server tools"""
        if not self._server:
            await self.start_server()
        
        # Create agent with MCP server
        agent = Agent(
            name="HealthUp Assistant",
            instructions="""You are a helpful health and nutrition assistant. 
            Use the available tools to help users with their health goals, 
            food logging, and nutrition analysis.""",
            mcp_servers=[self._server],
        )
        
        # Add additional tools if provided
        if tools:
            agent.tools.extend(tools)
        
        try:
            with trace("MCP Agent Execution"):
                result = await Runner.run(agent, prompt)
            
            return {
                "success": True,
                "text": result.final_output,
                "agent_name": agent.name,
                "trace_id": getattr(result, 'trace_id', None)
            }
        except Exception as e:
            logger.error(f"Error running agent with MCP: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    async def search_filesystem(self, query: str) -> Dict[str, Any]:
        """Search the filesystem using MCP server"""
        prompt = f"""
Search the filesystem for information related to: {query}

Please provide a comprehensive search and return relevant files and their contents.
"""
        
        return await self.run_agent_with_mcp(prompt)
    
    async def analyze_user_data(self, user_id: str, data_type: str) -> Dict[str, Any]:
        """Analyze user data using MCP server"""
        prompt = f"""
Analyze the user data for user ID: {user_id}
Data type: {data_type}

Please provide insights and recommendations based on the available data.
"""
        
        return await self.run_agent_with_mcp(prompt)
    
    async def generate_nutrition_report(self, food_data: list) -> Dict[str, Any]:
        """Generate nutrition report using MCP server"""
        food_summary = "\n".join([f"- {item}" for item in food_data])
        
        prompt = f"""
Generate a comprehensive nutrition report for the following food items:

{food_summary}

Please provide:
1. Nutritional analysis
2. Health recommendations
3. Meal planning suggestions
4. Any relevant health insights
"""
        
        return await self.run_agent_with_mcp(prompt)

# Global MCP server manager instance
_mcp_manager: Optional[MCPServerManager] = None

def get_mcp_manager(mcp_config: schemas.MCPServerConfig) -> MCPServerManager:
    """Get or create MCP server manager instance"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPServerManager(mcp_config)
    return _mcp_manager

async def initialize_mcp_server(mcp_config: schemas.MCPServerConfig):
    """Initialize the MCP server"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPServerManager(mcp_config)
        await _mcp_manager.start_server()
    return _mcp_manager

async def shutdown_mcp_server():
    """Shutdown the MCP server"""
    global _mcp_manager
    if _mcp_manager:
        await _mcp_manager.stop_server()
        _mcp_manager = None

# Legacy compatibility functions
@asynccontextmanager
async def get_mcp_client(mcp_config: schemas.MCPServerConfig):
    """Legacy function for backward compatibility"""
    manager = get_mcp_manager(mcp_config)
    async with manager.get_server() as server:
        yield MCPClientWrapper(server, manager)

class MCPClientWrapper:
    """Wrapper for MCP client to maintain backward compatibility"""
    
    def __init__(self, server: MCPServer, manager: MCPServerManager):
        self.server = server
        self.manager = manager
    
    async def _call_model_with_fallback(self, prompt: str, response_schema=None, tools=None) -> Dict[str, Any]:
        """Call model with fallback for backward compatibility"""
        result = await self.manager.run_agent_with_mcp(prompt, tools)
        
        if result["success"] and response_schema:
            try:
                # Try to parse the response according to the schema
                import json
                import re
                
                text = result["text"]
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_data = json.loads(json_str)
                    return {
                        "success": True,
                        "text": text,
                        "parsed": response_schema(**parsed_data)
                    }
                else:
                    # Try to parse the entire response as JSON
                    parsed_data = json.loads(text)
                    return {
                        "success": True,
                        "text": text,
                        "parsed": response_schema(**parsed_data)
                    }
            except Exception as e:
                logger.warning(f"Failed to parse response according to schema: {e}")
                return {
                    "success": True,
                    "text": text,
                    "parsed": None
                }
        
        return result 
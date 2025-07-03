import asyncio
import logging
import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from . import schemas
from openai import OpenAI

logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manager for MCP servers using OpenAI directly"""
    
    def __init__(self, mcp_config: schemas.MCPServerConfig):
        self.mcp_config = mcp_config
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=self.openai_api_key)
    
    async def run_ai_analysis(self, prompt: str, tools: Optional[list] = None) -> Dict[str, Any]:
        """Run AI analysis using OpenAI directly"""
        try:
            # Use OpenAI's chat completion for analysis
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful health and nutrition assistant. Use the available tools to help users with their health goals, food logging, and nutrition analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return {
                "success": True,
                "text": response.choices[0].message.content,
                "model": "gpt-4",
                "usage": response.usage.dict() if response.usage else None
            }
        except Exception as e:
            logger.error(f"Error running AI analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    async def search_filesystem(self, query: str) -> Dict[str, Any]:
        """Search the filesystem using AI analysis"""
        prompt = f"""
Search the filesystem for information related to: {query}

Please provide a comprehensive search and return relevant files and their contents.
"""
        
        return await self.run_ai_analysis(prompt)
    
    async def analyze_user_data(self, user_id: str, data_type: str) -> Dict[str, Any]:
        """Analyze user data using AI analysis"""
        prompt = f"""
Analyze the user data for user ID: {user_id}
Data type: {data_type}

Please provide insights and recommendations based on the available data.
"""
        
        return await self.run_ai_analysis(prompt)
    
    async def generate_nutrition_report(self, food_data: list) -> Dict[str, Any]:
        """Generate nutrition report using AI analysis"""
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
        
        return await self.run_ai_analysis(prompt)

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
    return _mcp_manager

async def shutdown_mcp_server():
    """Shutdown the MCP server"""
    global _mcp_manager
    if _mcp_manager:
        _mcp_manager = None

# Legacy compatibility functions
@asynccontextmanager
async def get_mcp_client(mcp_config: schemas.MCPServerConfig):
    """Legacy function for backward compatibility"""
    manager = get_mcp_manager(mcp_config)
    yield MCPClientWrapper(mcp_config)

class MCPClientWrapper:
    """Wrapper for OpenAI client to maintain compatibility with food parser"""
    
    def __init__(self, mcp_config: schemas.MCPServerConfig):
        self.mcp_config = mcp_config
        self.client = OpenAI()
    
    def responses(self):
        """Return a responses object that mimics the OpenAI responses API"""
        return ResponsesWrapper(self.client)

class ResponsesWrapper:
    """Wrapper for OpenAI responses API"""
    
    def __init__(self, client):
        self.client = client
    
    def create(self, **kwargs):
        """Create a response using OpenAI chat completion"""
        try:
            # Extract the prompt from kwargs
            prompt = kwargs.get('prompt', '')
            
            # Use chat completion instead of responses
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful health and nutrition assistant. Analyze the provided information and respond appropriately."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Return a mock response object that mimics the expected interface
            class MockResponse:
                def __init__(self, content):
                    self.content = content
                    self.text = content
                    self.output_text = content  # Add the missing attribute
                
                def json(self):
                    return {"text": self.content}
            
            return MockResponse(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error in MCP response creation: {e}")
            # Return a mock error response
            class MockErrorResponse:
                def __init__(self, error):
                    self.error = error
                    self.text = f"Error: {error}"
                
                def json(self):
                    return {"error": str(self.error)}
            
            return MockErrorResponse(str(e))

def get_mcp_client(mcp_config: schemas.MCPServerConfig) -> MCPClientWrapper:
    """Get MCP client wrapper"""
    return MCPClientWrapper(mcp_config) 
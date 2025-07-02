#!/usr/bin/env python3
"""
Simple MCP Server Example for HealthUp Food Parsing

This is a basic implementation of an MCP server that provides tools for:
- Google search (mock)
- Nutrition extraction
- Food input parsing

To run this server:
python mcp_server_example.py

The server will start on http://localhost:8001
"""

import asyncio
import os
import shutil

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio


async def run(mcp_server: MCPServer):
    agent = Agent(
        name="HealthUp Assistant",
        instructions="""You are a helpful health and nutrition assistant for the HealthUp application. 
        Use the available tools to help users with their health goals, food logging, and nutrition analysis.
        You can read files from the filesystem to understand user data and provide personalized recommendations.""",
        mcp_servers=[mcp_server],
    )

    # List the files it can read
    message = "Read the files and list them."
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

    # Ask about user data
    message = "What health data files are available for analysis?"
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

    # Ask for nutrition recommendations
    message = "Look at the available health data and suggest nutrition improvements."
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)


async def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")

    # Create sample files directory if it doesn't exist
    os.makedirs(samples_dir, exist_ok=True)

    async with MCPServerStdio(
        name="HealthUp Filesystem Server",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
    ) as server:
        trace_id = gen_trace_id()
        with trace(workflow_name="HealthUp MCP Filesystem Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run(server)


if __name__ == "__main__":
    # Let's make sure the user has npx installed
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed. Please install it with `npm install -g npx`.")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")

    asyncio.run(main()) 
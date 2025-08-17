import asyncio
import json
from typing import Optional, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ollama
from dotenv import load_dotenv


load_dotenv()


class MCPClient:
    def __init__(self):
        self.sessions: Optional[List[ClientSession]] = []
        self.exit_stack = AsyncExitStack()
        self.ollama_client = ollama.Client(host="http://localhost:11434")

    @staticmethod
    def convert_tools_format(tools) -> dict:
        """Convert tools to the required format for the Ollama API."""
        converted = []

        for tool in tools:
            converted_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            converted.append(converted_tool)

        return converted
    
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport

        loc_session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        self.sessions.append(loc_session)

        await self.sessions[-1].initialize()

        _available_tools = []
        for sess in self.sessions:
            response = await sess.list_tools()
            _available_tools.extend(response.tools)
        print("\nConnected to all servers with tools:", [tool.name for tool in _available_tools])

    async def connect_to_servers(self, server_script_paths: List[str]):
        for server_script_path in server_script_paths:
            await self.connect_to_server(server_script_path)

        # List available tools
        for idx, loc in enumerate(self.sessions):
            response = await loc.list_tools()
            loc_tools = response.tools
            print(
                f"\nConnected to {server_script_paths[idx]} server with tools:",
                [tool.name for tool in loc_tools],
            )
    
    async def process_query(self, query: str, model: str = "gpt-oss:20b") -> str:
        """
        Send `query` to the local Ollama model.  
        If the model asks to use a tool, call the Python function and feed
        the result back as a "tool" message.  Return the final answer.
        """
        messages = [{"role": "user", "content": query}]

        available_tools = []
        for sess in self.sessions:
            response = await sess.list_tools()
            available_tools.extend(MCPClient.convert_tools_format(response.tools))
        
        print(f"Available tools: {available_tools}")
        while True:
            print(f"Message to model: {messages}")
            response = self.ollama_client.chat(
                model=model,
                messages=messages,
                tools=available_tools,
                stream=False,
            )
            
            print(f"Model response: {response}")
            tool_calls = response.message.get("tool_calls") or []

            if tool_calls:
                print(f"Tool calls: {tool_calls}")
                # For simplicity we assume a single tool call per round
                call = tool_calls[0].function
                tool_name = call.get("name")
                tool_args = call.get("arguments", "{}")

                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    print("JSON LOAD ERROR")
                    tool_args = {}
                except TypeError:
                    pass
                except Exception as e:
                    raise e

                # Dispatch to the Python function
                result = await self.session.call_tool(tool_name, tool_args)
                print(f"""Tool response: {result}""")
                messages.append(
                    {"role": "tool", "name": tool_name, "content": str(result)}
                )
                
            else:
                # The model has produced a final answer
                print(f"Final response: {response}")
                return response.get("message", {}).get("content", "")

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_servers(sys.argv[1:])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())

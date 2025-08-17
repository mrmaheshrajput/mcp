# Model Context Protocol (MCP) Examples

A comprehensive collection of MCP servers and clients demonstrating how to build production-ready AI agents that can connect to external systems dynamically.

## 📖 About This Repository

This repository contains all the code examples from the article ["Master Model Context Protocol: Build AI Agents That Connect to Anything"](http://medium.com/mrmaheshrajput/). The examples progress from simple "Hello World" servers to multi-server production architectures.

Model Context Protocol (MCP) is Anthropic's open standard for connecting AI assistants to external data sources and tools. Instead of hardcoding tools for each AI application, MCP enables dynamic discovery and connection to various systems.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Ollama (for local LLM) or API keys for OpenAI/Anthropic

### Installation

```bash
git clone https://github.com/yourusername/mcp-examples
cd mcp-examples

# Install dependencies
pip install -r requirements.txt

# Or with uv (recommended)
uv pip install -r requirements.txt
```

## 📁 Files Overview

### MCP Servers

- `simple_mcp_server.py` - Basic MCP server with a single datetime tool. Perfect starting point for understanding MCP concepts.
- `weather_server.py` - Weather API integration server using the National Weather Service API. Demonstrates external API integration and error handling.
- `observability_server_functions.py` - Mock observability server with system metrics, alerts, and resources. Shows advanced MCP features like resources and multiple tools.

### MCP Clients

- `weather_client.py` - Single-server MCP client that connects to the weather server. Demonstrates basic client-server communication with Ollama.
- `multi_client.py` - Advanced client that can connect to multiple MCP servers simultaneously. Shows how to orchestrate tools from different servers.

### Configuration

`requirements.txt` - All Python dependencies needed to run the examples.

## 🛠 Usage Examples

### 1. Simple MCP Server

Test with MCP Inspector:

```bash
bashmcp dev simple_mcp_server.py
```

### 2. Weather Server & Client

Start the weather client (automatically starts server):
```bash
python weather_client.py weather_server.py
```

Example interaction:

```
You: What's the weather forecast for San Francisco?
Assistant: [Calls weather API and returns forecast]
```

### 3. Multi-Server Client

Connect to multiple servers:
```bash
python multi_client.py weather_server.py observability_server_functions.py
```

Example interaction:
```
You: Check the weather in NYC and show me CPU metrics
Assistant: [Uses both weather and observability tools]
```

## 🏗 Architecture

```
[User] ↔ [MCP Client] ↔ [MCP Server] ↔ [External System]
```

- **Host**: Machine running the MCP Client
- **Client**: Session object maintaining 1-to-1 connection with MCP Server
- **Server**: MCP server exposing tools, resources, and prompts
- **External System**: APIs, databases, filesystems, etc.


## 🤝 Contributing
Feel free to submit issues, fork the repository, and create pull requests for improvements.

## 📄 License
MIT License - see LICENSE file for details.

***

⭐ If this repository helped you understand MCP, please give it a star!
# Docker MCP Labs

Hands-on labs for learning how to build and consume Model Context Protocol (MCP) servers and clients.

The repository progresses from basic Docker and local MCP concepts to remote MCP servers, OAuth, tool discovery, LLM tool selection, and multi-server workflows.

## Current Topics

- Docker fundamentals
- Python MCP servers
- MCP clients
- Tool discovery
- Tool calling
- LLM-driven tool selection
- Remote MCP servers
- Streamable HTTP
- OAuth authentication
- GitHub MCP Server
- Multi-server routing
- Cross-server workflows

## Lab Progression

The labs are organized sequentially.

Early labs focus on Docker and local MCP servers.

Later labs focus on:

- consuming existing MCP servers
- discovering exposed tools
- calling remote tools
- letting an LLM select tools
- connecting multiple MCP servers
- routing tool calls to the correct server
- chaining outputs between MCP servers

## Environment

Primary lab environment:

- Ubuntu on AWS EC2
- Python virtual environments
- Ollama
- Qwen
- MCP Python SDK
- VS Code Remote SSH

## Goal

The goal of this repository is to build practical experience with MCP architecture and real-world tool integrations, with an emphasis on understanding how LLMs interact with MCP servers and external systems.

# Agent World framework integration examples

These examples demonstrate a deliberate architecture choice: external agent
frameworks connect to Agent World through MCP rather than becoming part of the
simulation authority.

The examples are intentionally small. Their first job is to prove discovery of
the same bounded Agent World tool surface.

## Start Agent World locally

For Streamable HTTP clients:

```bash
python -m examples.agent_world_arena.mcp_server --transport streamable-http
```

Default URL:

```text
http://127.0.0.1:8765/mcp
```

For clients that prefer to launch MCP as a child process, use stdio:

```bash
python -m examples.agent_world_arena.mcp_server --transport stdio
```

Do not type anything into the stdio server manually; the MCP host owns stdin and
stdout.

## OpenAI Agents SDK

Install:

```bash
pip install openai-agents
```

Run:

```bash
python examples/agent_world_arena/integrations/openai_agents_mcp.py
```

This discovery example does not make an OpenAI model call.

## AutoGen

Install the MCP extension:

```bash
pip install -U "autogen-ext[mcp]"
```

Run:

```bash
python examples/agent_world_arena/integrations/autogen_mcp.py
```

This uses AutoGen's `McpWorkbench` with Streamable HTTP.

## LangChain / LangGraph ecosystem

Install:

```bash
pip install -U langchain-mcp-adapters
```

Run:

```bash
python examples/agent_world_arena/integrations/langchain_mcp.py
```

This loads Agent World tools through `MultiServerMCPClient`. A LangGraph or
LangChain agent can then consume those tools without changing Agent World.

## CrewAI

Current CrewAI MCP tooling documents stdio and the older SSE transport. Agent
World therefore uses stdio for the CrewAI example rather than adding new
infrastructure on deprecated SSE.

Install:

```bash
pip install -U "crewai-tools[mcp]"
```

Run:

```bash
python examples/agent_world_arena/integrations/crewai_stdio.py
```

The CrewAI adapter launches Agent World as a child MCP process.

## Runtime-proof status

The Agent World core and MCP server are tested separately in HAL CI.

These framework examples are kept dependency-optional so the core does not
inherit every framework's dependency graph. Syntax is compiled in the Agent
World workflow. A future interoperability matrix job should install each
framework in an isolated environment, connect to a live local Agent World MCP
server, assert the expected tool set, and record framework/version receipts.

## Security rule

Framework examples must never add credentials to the server URL, committed
files, participant manifests, or replay output. When remote authentication is
added, pass credentials through the framework's supported header/auth mechanism
and scope them to one participant identity.

import asyncio
import base64
import os

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from k8s_agent_sandbox import SandboxClient
from dotenv import load_dotenv

load_dotenv()

langfuse = get_client()
langfuse_handler = CallbackHandler()


@tool
def execute_python(code: str) -> str:
    """Execute Python code in an isolated Kubernetes sandbox and return its output."""
    sb = SandboxClient()
    sandbox = sb.create_sandbox(warmpool="python-sandbox-pool", namespace="default")
    try:
        encoded = base64.b64encode(code.encode()).decode()
        sandbox.commands.run(f"sh -c 'echo {encoded} | base64 -d > /workspace/run.py'")
        result = sandbox.commands.run("sh -c 'python3 /workspace/run.py'")
        return result.stdout if result.exit_code == 0 else f"ERROR: {result.stderr}"
    finally:
        sandbox.terminate()


SYSTEM_PROMPT = """You are a coding agent. You have GitHub tools (e.g. get_file_contents) to fetch
file contents from a repository, and execute_python to run Python code in a sandbox.

When asked to run a file from a GitHub repo:
1. Use get_file_contents to fetch the file's contents as text.
2. Pass that exact code as the `code` argument to execute_python."""


async def main():
    mcp_client = MultiServerMCPClient({
        "github": {
            "url": "http://localhost:8089/mcp",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']}"
            },
        }
    })
    github_tools = await mcp_client.get_tools()
    tools = github_tools + [execute_python]

    llm = ChatOllama(model="qwen2.5:7b-instruct", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: MessagesState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    app = graph.compile()

    result = await app.ainvoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content="Fetch main.py from kunaljha5/agent-sandbox-hello-world and run it."),
            ]
        },
        config={"callbacks": [langfuse_handler]},
    )
    print("=== FINAL ANSWER ===")
    print(result["messages"][-1].content)

    langfuse.flush()


if __name__ == "__main__":
    asyncio.run(main())

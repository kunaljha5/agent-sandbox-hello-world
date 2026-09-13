# Local AI Code Execution Agent with Ollama, LangGraph, GitHub MCP, and Kubernetes Agent Sandbox

Run an AI coding agent completely on your local machine.

This project combines **Ollama**, **LangGraph**, **GitHub MCP Server**, **Langfuse**, and **Kubernetes Agent Sandbox** to safely execute AI-generated Python code inside an isolated Kubernetes sandbox running on **minikube**.

The agent can:

- Read public GitHub repositories through GitHub MCP.
- Fetch source files from GitHub using a Personal Access Token.
- Start an isolated sandbox in Kubernetes.
- Execute Python code inside the sandbox.
- Return stdout and stderr back to the LLM.
- Trace every LLM and tool call using Langfuse.

---

## Architecture

```text
User Prompt
      │
      ▼
Ollama (qwen2.5:7b-instruct)
      │
      ▼
LangGraph Agent
      │
      ├── GitHub MCP Tool
      │       │
      │       ▼
      │   GitHub Repository
      │
      └── execute_python Tool
              │
              ▼
 Kubernetes Agent Sandbox
              │
              ▼
 Python Sandbox Pod
              │
              ▼
 stdout / stderr
              │
              ▼
      LangGraph Response
```

---

## Tech Stack

| Component | Purpose |
|----------|---------|
| Ollama | Local LLM runtime |
| LangGraph | AI agent orchestration |
| LangChain | Tool integration |
| GitHub MCP Server | GitHub access through MCP |
| Kubernetes Agent Sandbox | Secure Python execution |
| Minikube | Local Kubernetes cluster |
| Langfuse | LLM and tool tracing |

---

## Features

- Fully local AI coding agent.
- No OpenAI API required.
- GitHub MCP integration.
- Kubernetes-native sandbox execution.
- Langfuse observability.
- Every execution runs in a fresh sandbox.

---

## Project Structure

```text
.
├── main.py
├── sandbox-template.yaml
├── sandbox-warmpool.yaml
├── requirements.txt
├── docs/
│   └── index.md
└── README.md
```

---

## Quick Start

### 1. Start Minikube

```bash
minikube start
kubectl config use-context minikube
```

Verify:

```bash
minikube status
```

### 2. Install Agent Sandbox

```bash
VERSION=$(curl -s https://api.github.com/repos/kubernetes-sigs/agent-sandbox/releases/latest | jq -r '.tag_name')

kubectl apply -f \
https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${VERSION}/sandbox-with-extensions.yaml
```

Wait until the controller is ready.

### 3. Deploy Sandbox Router

```bash
kubectl apply -f sandbox_router.yaml

kubectl set env deployment/sandbox-router-deployment \
-n agent-sandbox-system \
ALLOW_UNAUTHENTICATED_ROUTER=true
```

### 4. Create Sandbox Template

```bash
kubectl apply -f sandbox-template.yaml
```

### 5. Create Warm Pool

```bash
kubectl apply -f sandbox-warmpool.yaml
```

Verify:

```bash
kubectl get sandboxes -A
kubectl get pvc
```

---

## Run GitHub MCP Server

Start the MCP server with Docker.

```bash
docker run -d \
  --name github-mcp \
  -p 8089:8089 \
  ghcr.io/github/github-mcp-server
```

Verify:

```bash
docker ps | grep github-mcp
```

---

## Environment Variables

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxxx

export LANGFUSE_PUBLIC_KEY=pk_xxxxxxxxx
export LANGFUSE_SECRET_KEY=sk_xxxxxxxxx
export LANGFUSE_HOST=http://localhost:3000
```

---

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Run the Agent

```bash
python main.py
```

Example prompt:

> Fetch `main.py` from `kunaljha5/agent-sandbox-hello-world` and run it.

The agent will:

1. Ask GitHub MCP for the file.
2. Fetch the file contents.
3. Create a sandbox.
4. Write the file into `/workspace`.
5. Execute Python.
6. Return the output.

---

## How the Sandbox Works

Each execution creates a new sandbox from the warm pool.

```text
Warm Pool
    │
    ▼
SandboxClaim
    │
    ▼
Python Sandbox Pod
    │
    ▼
Execute /workspace/run.py
    │
    ▼
Destroy Sandbox
```

This keeps execution isolated from your local machine.

---

## Langfuse Tracing

Langfuse records:

- User prompt.
- System prompt.
- Tool calls.
- GitHub MCP requests.
- Sandbox execution.
- Final response.

This makes debugging and observability much easier.

---
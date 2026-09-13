import base64
from k8s_agent_sandbox import SandboxClient

def execute_python(code: str, warmpool: str = "python-sandbox-pool") -> str:
    sb = SandboxClient()
    sandbox = sb.create_sandbox(warmpool=warmpool, namespace="default")
    try:
        encoded = base64.b64encode(code.encode()).decode()
        sandbox.commands.run(f"sh -c 'echo {encoded} | base64 -d > /workspace/run.py'")
        result = sandbox.commands.run("sh -c 'python3 /workspace/run.py'")
        return result.stdout if result.exit_code == 0 else f"ERROR: {result.stderr}"
    finally:
        sandbox.terminate()

print(execute_python("print('hello from sandbox')\nprint(2 + 2)"))

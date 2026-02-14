
import pkgutil
import langchain.agents

print("Submodules in langchain.agents:")
for loader, module_name, is_pkg in pkgutil.walk_packages(langchain.agents.__path__):
    print(module_name)

try:
    from langchain.agents.agent import AgentExecutor
    print("\nFound AgentExecutor in langchain.agents.agent")
except ImportError as e:
    print(f"\nCould not import AgentExecutor from langchain.agents.agent: {e}")

try:
    from langchain.agents import create_tool_calling_agent
    print("Found create_tool_calling_agent in langchain.agents")
except ImportError:
    print("create_tool_calling_agent NOT in langchain.agents")

try:
    from langchain.agents.tool_calling_agent import create_tool_calling_agent
    print("Found create_tool_calling_agent in langchain.agents.tool_calling_agent")
except ImportError:
    print("create_tool_calling_agent NOT in langchain.agents.tool_calling_agent")

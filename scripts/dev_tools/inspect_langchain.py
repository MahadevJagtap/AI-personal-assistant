
import langchain.agents
print(dir(langchain.agents))
try:
    from langchain.agents import create_tool_calling_agent
    print("Found create_tool_calling_agent")
except ImportError:
    print("create_tool_calling_agent NOT FOUND in langchain.agents")

try:
    from langchain.agents import AgentExecutor
    print("Found AgentExecutor")
except ImportError:
    print("AgentExecutor NOT FOUND in langchain.agents")

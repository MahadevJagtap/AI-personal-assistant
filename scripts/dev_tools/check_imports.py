
import sys
try:
    import langchain
    print(f"langchain: {langchain.__version__} ({langchain.__file__})")
except ImportError:
    print("langchain not installed")

try:
    import langchain_community
    print(f"langchain_community: {langchain_community.__version__} ({langchain_community.__file__})")
except ImportError:
    print("langchain_community not installed")

try:
    import langchain_core
    print(f"langchain_core: {langchain_core.__version__} ({langchain_core.__file__})")
except ImportError:
    print("langchain_core not installed")

try:
    from langchain.chains import LLMChain
    print("Successfully imported LLMChain from langchain.chains")
except ImportError as e:
    print(f"Failed to import LLMChain from langchain.chains: {e}")

try:
    from langchain.prompts import PromptTemplate
    print("Successfully imported PromptTemplate from langchain.prompts")
except ImportError as e:
    print(f"Failed to import PromptTemplate from langchain.prompts: {e}")

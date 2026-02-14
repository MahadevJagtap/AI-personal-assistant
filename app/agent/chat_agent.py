
import os
import logging
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from app.agent.registry import get_all_tools
from app.agent.memory import AgentMemory
from huggingface_hub import InferenceClient

from app.config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ChatAgent:
    """
    Agent that uses Gemini (primary) or Hugging Face (fallback) to process queries.
    """
    def __init__(self):
        self.config = Config
        self.google_api_key = self.config.GEMINI_API_KEY
        self.llm = None
        self.tools = []
        self.tool_map = {}
        self.memory = AgentMemory() # SQLite backed memory
        self.fallback_llm = None
        self.hf_token = self.config.HUGGINGFACE_API_TOKEN
        
        self._initialize_agent()

    def _initialize_agent(self):
        """Initializes the Agent with Tools and LLM."""
        # Set environment variable for langchain integration
        if self.google_api_key:
            os.environ["GOOGLE_API_KEY"] = self.google_api_key
        else:
            logger.error("GEMINI_API_KEY not found in config.")
            return

        try:
            # 1. Setup LLM
            # Note: We bind tools later or here.
            base_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-lite",
                google_api_key=self.google_api_key,
                temperature=0.7,
                max_retries=2,
                convert_system_message_to_human=True
            )

            # 2. Get Tools
            self.tools = get_all_tools()
            self.tool_map = {t.name: t for t in self.tools}

            # 3. Bind Tools
            self.llm = base_llm.bind_tools(self.tools)
            
            # 4. Fallback configuration (using InferenceClient)
            self.hf_client = None
            if self.hf_token:
                self.hf_client = InferenceClient(api_key=self.hf_token)
                self.hf_model = "mistralai/Mistral-7B-Instruct-v0.2"
                logger.info(f"Fallback configured with InferenceClient for {self.hf_model}")
            
            logger.info("ChatAgent initialized and tools bound successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize ChatAgent: {e}")

    def run(self, user_input: str) -> str:
        """
        Runs the agent loop:
        1. Load History
        2. Append User Input
        3. Loop:
           - Invoke LLM
           - If tool calls -> Execute -> Append ToolOutput -> Continue
           - If text -> Append AIMessage -> Break
        4. Save final state to Memory
        """
        if not self.llm:
            return "Agent not initialized correctly."

        # 1. Load History (Core Messages)
        # We need to construct a list of messages for the LLM
        # memory.buffer_messages is a list of BaseMessage (Human/AI)
        # We might need to copy it to avoid modifying the buffer in-place during the loop until finalized?
        # Actually, for the loop, we work with a transient list extending history.
        
        messages = list(self.memory.buffer_messages)
        
        # Add System Prompt with explicit tool instructions
        system_prompt = SystemMessage(content="""You are a highly capable AI Personal Assistant.
You have access to a variety of tools:
- Google Calendar (calendar_tool): Use this for 'list', 'create', 'update', and 'delete' actions on the user's Google Calendar. This is the preferred way to manage meetings.
- Local Scheduler (schedule_meeting, list_meetings, delete_meeting): Use these for local JSON-based meeting management (secondary).
- Email (send_email_tool): Use this to send emails.
- Memory: You automatically remember past context.

When asked to list or manage meetings/events, ALWAYS check Google Calendar using `calendar_tool` first.
If a tool is available for a task, you MUST use it rather than saying you don't have access. 
After a tool call, you will receive the output. Analyze it and provide a clear final answer to the user.""")
        messages.insert(0, system_prompt)

        # 2. Add User Message
        user_msg = HumanMessage(content=user_input)
        messages.append(user_msg)

        # 3. Execution Loop
        final_response = ""
        max_turns = 5 # Safety break
        turn = 0
        
        while turn < max_turns:
            turn += 1
            try:
                # Invoke LLM
                ai_msg = self.llm.invoke(messages)
            except Exception as e:
                logger.error(f"Gemini Invocation Failed: {e}")
                
                # Check for quota error specifically to inform user
                error_msg = str(e)
                is_quota_error = "429" in error_msg or "quota" in error_msg.lower()
                
                # Try Fallback if available
                if self.hf_client:
                    logger.info(f"Attempting fallback to Hugging Face (Mistral-7B)...")
                    try:
                        # 1. Try Chat Completion (Modern API)
                        try:
                            response = self.hf_client.chat.completions.create(
                                model=self.hf_model,
                                messages=[
                                    {"role": "system", "content": system_prompt.content},
                                    {"role": "user", "content": user_input}
                                ],
                                max_tokens=500,
                                temperature=0.7
                            )
                            if response.choices and len(response.choices) > 0:
                                response_content = response.choices[0].message.content.strip()
                                prefix = "⚠️ **[Gemini Quota Reached - Using Fallback]**\n\n" if is_quota_error else "⚠️ **[System Fallback Active]**\n\n"
                                return f"{prefix}{response_content}"
                        except Exception as chat_e:
                            logger.warning(f"HF Chat API failed: {chat_e}. Trying text_generation...")
                            
                            # 2. Try Text Generation (Alternative)
                            prompt = f"System: {system_prompt.content}\nUser: {user_input}\nAssistant:"
                            hf_text = self.hf_client.text_generation(
                                prompt,
                                model="google/flan-t5-large",
                                max_new_tokens=200
                            )
                            if hf_text:
                                prefix = "⚠️ **[Emergency Fallback Mode]** "
                                return f"{prefix}{hf_text.strip()}"
                                
                    except Exception as hf_e:
                        logger.error(f"All Hugging Face attempts failed: {hf_e}")
                
                if is_quota_error:
                    return "I've reached my Gemini API limit for now, and my backup brain is also unavailable. Please try again in a few minutes."
                return "I'm having trouble connecting to my brain right now. Please check my API configuration."

            messages.append(ai_msg)

            # Check for tool calls
            if ai_msg.tool_calls:
                logger.info(f"Tool Calls Detected: {len(ai_msg.tool_calls)}")
                
                for tool_call in ai_msg.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call["id"]
                    
                    logger.info(f"Executing {tool_name} with {tool_args}")
                    
                    if tool_name in self.tool_map:
                        tool_instance = self.tool_map[tool_name]
                        try:
                            # Execute Tool
                            # Tool invoke can take dict or specific args depending on definition
                            tool_output = tool_instance.invoke(tool_args)
                        except Exception as e:
                            tool_output = f"Error executing tool: {e}"
                        
                        # Create Tool Message
                        tool_msg = ToolMessage(content=str(tool_output), tool_call_id=tool_id)
                        messages.append(tool_msg)
                        logger.info(f"Tool Output: {str(tool_output)[:50]}...")
                    else:
                        logger.warning(f"Tool {tool_name} not found.")
                        tool_msg = ToolMessage(content=f"Error: Tool {tool_name} not found.", tool_call_id=tool_id)
                        messages.append(tool_msg)
                
                # Loop continues to let LLM generate response based on tool outputs
                continue 
            
            # No tool calls, this is the final response
            content = ai_msg.content
            if isinstance(content, str):
                final_response = content
            elif isinstance(content, list):
                # Combine all text blocks
                text_parts = []
                for block in content:
                    if isinstance(block, str):
                        text_parts.append(block)
                    elif isinstance(block, dict):
                        if block.get("type") == "text" and "text" in block:
                            text_parts.append(block["text"])
                final_response = " ".join(text_parts).strip()
            else:
                final_response = str(content)
            
            # If final_response is empty but we reached here, it might be a model quirk
            if not final_response.strip():
                final_response = "Execution complete."
                
            break

        
        # 4. Save to Memory
        # We save the original User Input and the FINAL AI Response.
        # Intermediate tool calls are usually transient in simple memory, 
        # or we save the whole chain. 
        # The `AgentMemory` class implemented earlier (`add_to_memory`) takes (user_msg, ai_msg).
        # It doesn't support list of tool messages yet. 
        # For this requirement ("Store conversation in memory"), 
        # saving the final turn is standard for simple chat history.
        # If we want full trace, we'd need to update Memory schema.
        # Let's stick to saving the user input and final answer.
        
        self.memory.add_to_memory(user_input, final_response)
        
        return final_response

# Singleton instance
chat_agent = ChatAgent()

def run_agent(user_input: str) -> str:
    """Public interface for the unified agent."""
    return chat_agent.run(user_input)

if __name__ == "__main__":
    # Test block
    print("--- Testing Unified Agent (Manual Loop) ---")
    q = "What tools do you have available?"
    print(f"User: {q}")
    res = run_agent(q)
    print(f"Agent: {res}")

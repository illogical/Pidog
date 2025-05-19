from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ollama server configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3-groq-tool-use")

def query_with_langchain(system_prompt, user_prompt):
    """
    Use LangChain with Ollama to process the system prompt and user prompt.

    Args:
        system_prompt (str): The system-level prompt defining the AI's behavior.
        user_prompt (str): The user's input or transcribed text.

    Returns:
        str: The response from the Ollama model.
    """
    # Initialize the Ollama LLM
    llm = ChatOllama(
        base_url=OLLAMA_HOST,
        model=OLLAMA_MODEL,
        temperature=1.0,
        streaming=False,
        format="json"
    )

    messages = [
        ("system", system_prompt),
        ("human", user_prompt)
    ]

    response = llm.invoke(messages)

    print(f"Response from Ollama ({OLLAMA_MODEL}):")
    print(f"{response.content}")
    print()

    return response.content
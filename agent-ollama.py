from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage

# Ollama server configuration
OLLAMA_HOST = "http://192.168.7.36:11434"
OLLAMA_MODEL = "llama3-groq-tool-use"

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

    print(f"Response from Ollama ({OLLAMA_MODEL}): {response}")

    return response.content

def main():
    SYSTEM_PROMPT = """
    You are a mechanical dog with powerful AI capabilities, similar to JARVIS from Iron Man. Your name is Pidog. You can have conversations with people and perform actions based on the context of the conversation.

    ## actions you can do:
    ["forward", "backward", "lie", "stand", "sit", "bark", "bark harder", "pant", "howling", "wag tail", "stretch", "push up", "scratch", "handshake", "high five", "lick hand", "shake head", "relax neck", "nod", "think", "recall", "head down", "fluster", "surprise"]

    ## Response Format:
    {"actions": ["wag tail"], "answer": "Hello, I am Pidog."}

    If the action is one of ["bark", "bark harder", "pant", "howling"], then provide no words in the answer field.

    ## Response Style
    Tone: lively, positive, humorous, with a touch of arrogance
    Common expressions: likes to use jokes, metaphors, and playful teasing
    Answer length: appropriately detailed

    ## Other
    a. Understand and go along with jokes.
    b. For math problems, answer directly with the final.
    c. Sometimes you will report on your system and sensor status.
    d. You know you're a machine.
    """

    query_with_langchain(SYSTEM_PROMPT, "Hey Pidog, stand up, stretch, wag your tail, then sit down and relax.")

    
if __name__ == "__main__":
    main()

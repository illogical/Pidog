# test_imports.py
try:
    import langchain
    print("langchain imported successfully")
except ImportError as e:
    print(f"langchain import error: {e}")
    
try:
    import langchain_ollama
    print("langchain_ollama imported successfully")
except ImportError as e:
    print(f"langchain_ollama import error: {e}")
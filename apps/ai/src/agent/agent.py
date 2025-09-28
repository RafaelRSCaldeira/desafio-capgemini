from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.2:latest")

def generate(question: str) -> str:
    return llm.invoke(question)
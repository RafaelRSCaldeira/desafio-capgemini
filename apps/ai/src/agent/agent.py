from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.tools import Tool
from typing import Dict, Any

from src.tools.csv_analyzer import analyze_csv

# Configuração do modelo
model = ChatOllama(model="llama3.2")

# Configuração do workflow
workflow = StateGraph(state_schema=MessagesState)

# Tools disponíveis
tools = [analyze_csv]
model_with_tools = model.bind_tools(tools)

def call_model(state: MessagesState):
    """Função que processa mensagens e pode usar tools"""
    system_prompt = (
        "You are a helpful assistant. You can analyze CSV files using the analyze_csv tool. "
        "When users ask about CSV data, use the tool with either file_url or file_path parameter. "
        "Answer all questions to the best of your ability."
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def generate(message: str) -> str:
    """Função simples para compatibilidade com o main.py atual"""
    response = model.invoke(message)
    return response

# Configuração do workflow (se quiser usar StateGraph)
workflow.add_node("agent", call_model)
workflow.add_edge(START, "agent")
workflow.set_entry_point("agent")

# Compilar o workflow
app = workflow.compile()
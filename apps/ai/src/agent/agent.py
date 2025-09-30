from langgraph.graph import START, StateGraph, END # Adicionado END para clareza
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from langchain_ollama import ChatOllama

from src.tools.rag import search_rag
from src.tools.web_search import web_search

sys_msg_content = """You are a helpful assistant.
You have access to the following tools: 'search_rag' and 'web_search'.
Use them when you need to find information to answer the user's question.
Respond with a tool call when necessary.
You must always use the search_rag tool before using the web_search tool.
If the retrieved information is not relevant, use the web_search tool to find more information."""
sys_msg = SystemMessage(content=sys_msg_content)

llm = ChatOllama(model="qwen3:latest", temperature=0)
tools = [search_rag, web_search]
llm_with_tools = llm.bind_tools(tools)

def assistant(state: MessagesState):
    result = llm_with_tools.invoke(state["messages"])
    return {"messages": [result]}

builder = StateGraph(MessagesState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")
graph = builder.compile()

def extract_thinking(message: str):
    message = message.replace("<think>", "")
    think, answer = message.split("</think>")
    return think, answer

def generate(message: str) -> str:
    initial_state = {"messages": [sys_msg, HumanMessage(content=message)]}
    final_state = graph.invoke(initial_state)
    print(final_state)
    answer = final_state["messages"][-1].content
    return extract_thinking(answer)
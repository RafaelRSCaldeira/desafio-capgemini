from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

search = DuckDuckGoSearchResults(output_format="list", num_results=10)

@tool
def web_search(query: str) -> str:
    """Search the web for the most relevant information."""
    return search.invoke(query)
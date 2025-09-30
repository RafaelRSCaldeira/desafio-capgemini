from langchain_community.tools import DuckDuckGoSearchResults

search = DuckDuckGoSearchResults(output_format="list")

def web_search(query: str) -> str:
    """Search the web for the most relevant information."""
    return search.invoke(query)
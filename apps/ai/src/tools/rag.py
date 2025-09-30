import os
import requests
from typing import Dict, Any
from langchain_core.tools import tool

def _get_rag_service_url() -> str:
    """Obtém a URL do serviço RAG a partir das variáveis de ambiente."""
    return os.getenv("RAG_SERVICE_URL", "http://localhost:8080")

def _make_rag_request(query: str, k: int = 10) -> Dict[str, Any]:
    """Faz requisição para o serviço RAG com tratamento de erros."""
    url = f"{_get_rag_service_url()}/rag/similar"
    payload = {
        "text": query,
        "k": k
    }
    
    timeout = int(os.getenv("RAG_TIMEOUT", "30"))
    
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        raise Exception(f"Não foi possível conectar ao serviço RAG em {url}")
    except requests.exceptions.Timeout:
        raise Exception(f"Timeout ao acessar o serviço RAG (>{timeout}s)")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Erro HTTP do serviço RAG: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"Erro inesperado ao acessar o serviço RAG: {str(e)}")

@tool
def search_rag(query: str, k: int = 10) -> str:
    """
    Search the RAG database for the most relevant information.
    
    Args:
        query: Text to search for
        k: Number of results to return (default: 10)
    
    Returns:
        Formatted string with search results
    """
    try:
        result = _make_rag_request(query, k)
        results = result.get("results", [])
        
        if not results:
            return "Nenhum resultado encontrado para a consulta."
        
        # Formatar resultados
        formatted_results = []
        for i, item in enumerate(results, 1):
            value = item.get("value", "N/A")
            file = item.get("file", "N/A")
            formatted_results.append(f"{i}. {value} (fonte: {file})")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Erro na busca RAG: {str(e)}"

@tool
def rag_health_check() -> str:
    """Check if the RAG service is healthy and responding."""
    url = f"{_get_rag_service_url()}/rag/health/"
    timeout = int(os.getenv("RAG_TIMEOUT", "10"))
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == 201:
            return "✅ Serviço RAG está funcionando corretamente."
        else:
            return f"⚠️ Serviço RAG respondeu com status inesperado: {data}"
            
    except requests.exceptions.ConnectionError:
        return f"❌ Não foi possível conectar ao serviço RAG em {url}"
    except requests.exceptions.Timeout:
        return f"⏰ Timeout ao verificar o serviço RAG (>{timeout}s)"
    except Exception as e:
        return f"❌ Erro ao verificar o serviço RAG: {str(e)}"
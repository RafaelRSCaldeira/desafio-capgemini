#!/usr/bin/env python3
"""
Exemplo de uso das ferramentas RAG com LangChain.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.rag import search_rag, rag_health_check


def test_rag_tools():
    """Testa as ferramentas RAG."""
    print("=== Testando Ferramentas RAG ===\n")
    
    # Configurar variáveis de ambiente para teste local
    os.environ.setdefault("RAG_SERVICE_HOST", "localhost")
    os.environ.setdefault("RAG_SERVICE_PORT", "8080")
    os.environ.setdefault("RAG_SERVICE_PROTOCOL", "http")
    os.environ.setdefault("RAG_TIMEOUT", "10")
    
    # Testar saúde do serviço
    print("1. Verificando saúde do serviço RAG...")
    health_result = rag_health_check()
    print(health_result)
    print()
    
    # Testar busca
    print("2. Testando busca por 'smartphone'...")
    search_result = search_rag("smartphone", k=3)
    print(search_result)
    print()
    
    # Testar busca por tecnologia
    print("3. Testando busca por 'inteligência artificial'...")
    search_result = search_rag("inteligência artificial", k=2)
    print(search_result)
    print()
    
    # Testar busca por produtos
    print("4. Testando busca por 'produtos eletrônicos'...")
    search_result = search_rag("produtos eletrônicos", k=2)
    print(search_result)


def test_with_langchain_agent():
    """Exemplo de uso com agente LangChain."""
    try:
        from langchain.agents import initialize_agent, AgentType
        from langchain.llms import OpenAI
        
        print("\n=== Exemplo com Agente LangChain ===")
        
        # Configurar LLM (substitua pela sua chave API)
        llm = OpenAI(temperature=0)
        
        # Obter ferramentas RAG
        tools = [search_rag, rag_health_check]
        
        # Criar agente
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        
        # Exemplo de pergunta
        question = "Encontre informações sobre smartphones disponíveis"
        print(f"Pergunta: {question}")
        print("Resposta do agente:")
        response = agent.run(question)
        print(response)
        
    except ImportError:
        print("LangChain não instalado. Instale com: pip install langchain openai")
    except Exception as e:
        print(f"Erro ao criar agente: {e}")


if __name__ == "__main__":
    test_rag_tools()
    test_with_langchain_agent()

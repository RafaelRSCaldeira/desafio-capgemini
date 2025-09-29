"""
Exemplo de como interagir com a função call_model e usar o tool de CSV
"""
from src.agent.agent import call_model, app
from langchain_core.messages import HumanMessage

def exemplo_uso_simples():
    """Exemplo básico usando call_model diretamente"""
    print("=== Exemplo 1: Uso simples do call_model ===")
    
    # Estado inicial com mensagem do usuário
    state = {
        "messages": [HumanMessage(content="Olá! Como você pode me ajudar?")]
    }
    
    # Chama o modelo
    result = call_model(state)
    print("Resposta:", result["messages"][0].content)
    print()

def exemplo_uso_com_csv():
    """Exemplo usando o tool de CSV"""
    print("=== Exemplo 2: Uso com análise de CSV ===")
    
    # Estado com pergunta sobre CSV
    state = {
        "messages": [
            HumanMessage(content="Analise o arquivo CSV em /data/vendas.csv e me diga quais são os top 5 produtos por vendas")
        ]
    }
    
    # Chama o modelo (que pode usar o tool)
    result = call_model(state)
    print("Resposta:", result["messages"][0].content)
    print()

def exemplo_uso_workflow():
    """Exemplo usando o workflow completo"""
    print("=== Exemplo 3: Uso do workflow completo ===")
    
    # Estado inicial
    state = {
        "messages": [HumanMessage(content="Preciso analisar dados de vendas de um CSV")]
    }
    
    # Executa o workflow
    result = app.invoke(state)
    print("Resposta do workflow:", result["messages"][-1].content)
    print()

def exemplo_tool_direto():
    """Exemplo usando o tool diretamente"""
    print("=== Exemplo 4: Uso direto do tool de CSV ===")
    
    from src.tools.csv_analyzer import analyze_csv
    
    # Simula análise de um CSV local
    result = analyze_csv.invoke({
        "file_path": "/data/exemplo.csv",
        "question": "Quantas linhas tem este arquivo?"
    })
    
    print("Resultado da análise:", result)
    print()

if __name__ == "__main__":
    print("Exemplos de uso do call_model e tools de CSV\n")
    
    try:
        exemplo_uso_simples()
        # exemplo_uso_com_csv()
        # exemplo_uso_workflow()
        # exemplo_tool_direto()
    except Exception as e:
        print(f"Erro: {e}")
        print("Certifique-se de que o Ollama está rodando e o modelo 'llama3' está disponível")

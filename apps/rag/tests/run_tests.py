#!/usr/bin/env python3
"""
Script para executar todos os testes do sistema RAG.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_unittest_tests():
    """Executa os testes unittest."""
    print("=" * 60)
    print("EXECUTANDO TESTES UNITTEST")
    print("=" * 60)
    
    try:
        # Executar testes unittest
        result = subprocess.run([
            sys.executable, "-m", "unittest", 
            "test_rag_client.TestRAGClient", "-v"
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Erro ao executar testes unittest: {e}")
        return False

def run_pytest_tests():
    """Executa os testes pytest."""
    print("\n" + "=" * 60)
    print("EXECUTANDO TESTES PYTEST")
    print("=" * 60)
    
    try:
        # Executar testes pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_rag_pytest.py", "-v", "--tb=short"
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Erro ao executar testes pytest: {e}")
        return False

def run_all_tests():
    """Executa todos os testes."""
    print("INICIANDO EXECUÇÃO DE TODOS OS TESTES")
    print("=" * 60)
    
    unittest_success = run_unittest_tests()
    pytest_success = run_pytest_tests()
    
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    print(f"Testes unittest: {'PASSOU' if unittest_success else 'FALHOU'}")
    print(f"Testes pytest: {'PASSOU' if pytest_success else 'FALHOU'}")
    
    overall_success = unittest_success and pytest_success
    print(f"Resultado geral: {'TODOS OS TESTES PASSARAM' if overall_success else 'ALGUNS TESTES FALHARAM'}")
    
    return overall_success

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

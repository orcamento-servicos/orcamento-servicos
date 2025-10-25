#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se as APIs estão funcionando
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_api_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Testa um endpoint da API"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code == expected_status:
            return True
        else:
            print(f"❌ Erro: Esperado {expected_status}, recebido {response.status_code}")
            if response.text:
                print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Erro de conexão (servidor não está rodando?)")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Erro: {e}")
        return False

def main():
    print("🧪 Testando APIs do Sistema de Orçamentos...")
    print("=" * 50)
    
    # Testa endpoints básicos
    endpoints = [
        ("/api", "GET"),
        ("/api/auth/verificar", "GET"),
        ("/api/servicos/", "GET"),
        ("/api/clientes/", "GET"),
        ("/api/orcamentos/", "GET"),
        ("/api/agendamentos/", "GET"),
    ]
    
    success_count = 0
    total_tests = len(endpoints)
    
    for endpoint, method in endpoints:
        if test_api_endpoint(endpoint, method):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 Resultado: {success_count}/{total_tests} testes passaram")
    
    if success_count == total_tests:
        print("🎉 Todas as APIs estão funcionando!")
    else:
        print("⚠️  Algumas APIs podem ter problemas")
    
    print("\n💡 Para testar funcionalidades completas:")
    print("1. Execute: python src/main.py")
    print("2. Acesse: http://localhost:5000")
    print("3. Faça login e teste as funcionalidades")

if __name__ == "__main__":
    main()

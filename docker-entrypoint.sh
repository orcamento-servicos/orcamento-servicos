#!/bin/sh

# Imprime as mensagens personalizadas no console
echo ""
echo "----------------------------------------------------"
echo "🚀 Iniciando o Sistema de Orçamentos de Serviços..."
echo "✅ Aplicação pronta! Acesse em: http://localhost:5000"
echo "----------------------------------------------------"
echo ""

# 'exec' inicia o Gunicorn. Isso é importante para que o Gunicorn
# se torne o processo principal do contêiner.
exec gunicorn --bind 0.0.0.0:5000 src.main:app
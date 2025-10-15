#!/bin/sh

# Imprime as mensagens personalizadas no console
echo ""
echo "===================================================="
echo "🚀 Sistema de Orcamentos de Servicos"
echo "===================================================="
echo ""
echo "✅ Aplicacao iniciada com sucesso!"
echo ""
echo "🔗 Como acessar a API:"
echo "   API: http://localhost:5000"
echo ""
echo "📋 Dicas para testar a API:"
echo "   - Acesse http://localhost:5000 no navegador"
echo "   - Utilize uma ferramenta como Postman ou curl"
echo ""
echo "🛑 Para parar: Ctrl+C"
echo "===================================================="
echo ""

# 'exec' inicia o Gunicorn com configurações otimizadas
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --preload \
  src.main:app
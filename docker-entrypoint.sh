#!/bin/bash

# ========================================
# DOCKER ENTRYPOINT - Sistema de Orçamentos
# Script de inicialização otimizado
# ========================================

set -e  # Para em caso de erro

echo ""
echo "===================================================="
echo "🚀 Sistema de Orçamentos de Serviços"
echo "===================================================="
echo ""
echo "📊 Inicializando sistema..."
echo ""

# Aguarda um momento para garantir que tudo está pronto
sleep 2

# Verifica se o diretório do banco existe
if [ ! -d "/app/src/database" ]; then
    echo "📁 Criando diretório do banco de dados..."
    mkdir -p /app/src/database
fi

# Inicializa o banco de dados
echo "🗄️  Inicializando banco de dados..."
python -c "
import sys
import os
sys.path.insert(0, '/app')

try:
    from src.main import app, db
    with app.app_context():
        db.create_all()
        print('✅ Banco de dados inicializado com sucesso!')
        print('📊 Tabelas criadas: usuario, cliente, servico, orcamento, agendamento, etc.')
except Exception as e:
    print(f'❌ Erro ao inicializar banco: {e}')
    sys.exit(1)
"

# Verifica se a inicialização foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "✅ Sistema inicializado com sucesso!"
else
    echo "❌ Erro na inicialização do sistema"
    exit 1
fi

echo ""
echo "🌐 Iniciando servidor web..."
echo "🔗 API disponível em: http://localhost:5000"
echo "📱 Interface web: http://localhost:5000"
echo "📋 Documentação da API: http://localhost:5000/api"
echo ""
echo "🛑 Para parar: Ctrl+C"
echo "===================================================="
echo ""

# Aguarda o banco de dados PostgreSQL (se DATABASE_URL estiver definida)
echo ""
echo "⏳ Aguardando conexão com o banco de dados PostgreSQL..."

if [ -n "${DATABASE_URL}" ]; then
    # Extrai as variáveis da DATABASE_URL no formato: postgresql://user:pass@host:port/dbname
    export PGPASSWORD=$(echo $DATABASE_URL | awk -F':' '{print $3}' | awk -F'@' '{print $1}')
    DB_USER=$(echo $DATABASE_URL | awk -F'//' '{print $2}' | awk -F':' '{print $1}')
    DB_HOST=$(echo $DATABASE_URL | awk -F'@' '{print $2}' | awk -F':' '{print $1}')
    DB_NAME=$(echo $DATABASE_URL | awk -F'/' '{print $4}')

    # Loop de espera usando pg_isready
    until pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
        echo "Banco de dados indisponível. Tentando novamente em 2s..."
        sleep 2
    done

    echo "✅ Conexão com o PostgreSQL estabelecida!"
else
    echo "DATABASE_URL não definida; pulando espera por PostgreSQL (usar fallback SQLite)."
fi

# Inicia o Gunicorn com configurações otimizadas
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --worker-class sync \
    --worker-connections 1000 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    src.main:app
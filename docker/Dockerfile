# ========================================
# DOCKERFILE - Sistema de Orçamentos
# Versão otimizada com todas as dependências
# ========================================

# Use uma imagem base oficial do Python 3.11
FROM python:3.11-slim

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_APP=src.main:app

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    pango1.0-tools \
    libpangocairo-1.0-0 \
    sqlite3 \
    postgresql-client \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copia o arquivo de dependências primeiro (para cache do Docker)
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto
COPY . .

# Copia e torna executável o script de entrada
# Agora o script está dentro da pasta docker/ no repositório; durante build (context: .) usamos esse caminho
COPY docker/docker-entrypoint.sh .
# Remove possíveis CRLF do arquivo (salva compatibilidade com ambientes Windows)
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Cria diretórios necessários
RUN mkdir -p /app/src/database \
    && mkdir -p /app/logs

# Define permissões corretas
RUN chmod -R 755 /app

# Expõe a porta
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api || exit 1

# Comando para iniciar a aplicação
CMD ["./docker-entrypoint.sh"]

# Use uma imagem base oficial do Python. A versão 'slim' é mais leve.
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Instala as dependências de sistema necessárias para o WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    pango1.0-tools \
    libpangocairo-1.0-0 \
    --no-install-recommends

# Copia o arquivo de dependências do Python primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do seu projeto para o diretório de trabalho no contêiner
COPY . .

# --- ALTERAÇÕES AQUI ---
# 1. Copia o script de inicialização para o contêiner
COPY docker-entrypoint.sh .

# 2. Torna o script executável
RUN chmod +x docker-entrypoint.sh
# --- FIM DAS ALTERAÇÕES ---

# Expõe a porta que o seu aplicativo usa
EXPOSE 5000

# 3. Comando para iniciar a aplicação usando o nosso novo script
CMD ["./docker-entrypoint.sh"]
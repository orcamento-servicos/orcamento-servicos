# Sistema de Orçamentos de Serviços - API Backend

## 📋 Resumo do Sistema

Sistema completo de gerenciamento de orçamentos de serviços com API REST em Flask. Permite cadastrar clientes, serviços, criar orçamentos interativos, converter em vendas e gerar PDFs. Inclui autenticação, logs de auditoria e múltiplos endereços por cliente.

**Funcionalidades principais:**
- 🔐 Autenticação de usuários
- 👥 CRUD de clientes e endereços
- 🛠️ CRUD de serviços
- 📋 Criação e gerenciamento de orçamentos
- 💰 Conversão de orçamentos em vendas
- 📄 Geração de PDFs (opcional)e
- 📊 Logs de auditoria


## 📋 Próximas Tarefas para o Backend

### 🚀 Funcionalidades Prioritárias
1. **Validação de Dados**
   - Implementar validação mais robusta nos endpoints
   - Adicionar validação de CPF/CNPJ para clientes
   - Validação de formato de email e telefone

2. **Segurança**
   - Implementar rate limiting
   - Adicionar CORS configurável
   - Melhorar validação de senhas
   - Implementar JWT como alternativa aos cookies

3. **Relatórios e Analytics**
   - Dashboard com métricas de vendas
   - Relatórios de performance por período
   - Exportação de dados em Excel/CSV

4. **Notificações**
   - Sistema de notificações por email
   - Alertas de orçamentos vencidos
   - Notificações de mudança de status

### 🛠️ Melhorias Técnicas
5. **Banco de Dados**
   - Migrar para PostgreSQL em produção
   - Implementar migrations
   - Adicionar índices para performance

6. **API**
   - Implementar paginação em todos os endpoints
   - Adicionar filtros avançados
   - Implementar cache com Redis
   - Documentação automática com Swagger

7. **Testes**
   - Implementar testes unitários
   - Testes de integração
   - Testes de performance
   - CI/CD pipeline

8. **Monitoramento**
   - Logs estruturados
   - Métricas de performance
   - Health checks
   - Alertas automáticos

### 📱 Funcionalidades Avançadas
9. **Integrações**
   - Integração com sistemas de pagamento
   - Integração com ERPs
   - API para aplicativo mobile

10. **Automação**
    - Geração automática de orçamentos recorrentes
    - Workflow de aprovação configurável
    - Templates de orçamento personalizáveis

## 🚀 Executando com Docker Compose

Instruções rápidas para rodar a aplicação com PostgreSQL via Docker Compose (recomendado):

1. Copie o arquivo de exemplo e edite valores sensíveis (opcional):

```powershell
cp .env.example .env
# Edite .env se precisar (ex.: SECRET_KEY)
```

2. Build e subir os containers:

```powershell
docker compose up --build
```

3. Subir em background:

```powershell
docker compose up -d --build
```

4. Ver logs:

```powershell
docker compose logs -f backend db
```

Notas:
- Se quiser usar SQLite localmente, comente `DATABASE_URL` no `.env` e a aplicação usará o arquivo `src/database/app.db` como fallback.
- Para produção, recomendo configurar variáveis reais (SECRET_KEY, POSTGRES_PASSWORD) e usar migrations (Alembic) em vez de `db.create_all()`.

---

## 🗂️ Organização dos arquivos Docker

Todos os arquivos relacionados ao Docker agora ficam na pasta `docker/`:
- `docker/Dockerfile` — arquivo principal de build
- `docker/docker-entrypoint.sh` — script de inicialização

O `docker-compose.yml` na raiz já está configurado para usar o Dockerfile dentro da pasta `docker/`.

Se você encontrar arquivos antigos como `dockerfile` ou `docker-entrypoint.sh` na raiz, pode removê-los com segurança.

## 📦 Sobre requirements

- Use `requirements.txt` para dependências de produção.
- Use `requirements-local.txt` (ou crie `requirements-dev.txt`) para dependências extras de desenvolvimento.

---

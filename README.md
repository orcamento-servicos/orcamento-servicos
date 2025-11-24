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

docker compose up --build
docker compose up -d --build
docker compose logs -f backend db
## ▶️ Executando localmente (sem Docker)

Se você prefere rodar a aplicação diretamente no Windows (sem Docker), siga estas instruções rápidas.

1) Crie um ambiente virtual e ative (PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2) Instale dependências:

```powershell
pip install -r requirements.txt
```

3) Crie o arquivo de variáveis de ambiente a partir do exemplo e edite se necessário:

```powershell
Copy-Item .env.example .env
# Abra .env e ajuste SECRET_KEY, SMTP_* e (opcional) DATABASE_URL
```

Observações sobre o banco de dados:
- Por padrão a aplicação usa a variável `DATABASE_URL`. Se não definida, ela cairá para um SQLite local (`sqlite:///banco.db`).
- Se quiser usar um Postgres local/hosted, defina `DATABASE_URL` no formato: `postgresql://user:password@host:5432/dbname`.

4) Execute a aplicação:

```powershell
python .\src\main.py
```

5) Acesse a API pelo navegador em: http://localhost:5000

Notas de produção:
- Em produção, configure variáveis reais (SECRET_KEY, credenciais do banco e SMTP) e use migrations (Alembic) em vez de confiar apenas em `db.create_all()` no startup.

---

## 📦 Sobre requirements

- Use `requirements.txt` para dependências de produção.
- Use `requirements-local.txt` (ou crie `requirements-dev.txt`) para dependências extras de desenvolvimento.

---

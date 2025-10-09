# Sistema de Orçamentos de Serviços

Um sistema completo para gerenciamento de orçamentos de serviços, desenvolvido em Flask com interface de API REST.

## 📋 Funcionalidades Implementadas

### 🔐 Autenticação e Usuários
- **Cadastro de usuários** com validação de dados
- **Login/Logout** com sessões seguras
- **Recuperação de senha** via token temporário
- **Verificação de autenticação** em tempo real
- **Logs de acesso** para auditoria

### 👥 Gestão de Clientes
- **CRUD completo** de clientes
- **Múltiplos endereços** por cliente
- **Endereço padrão** configurável
- **Validações** de dados obrigatórios
- **Proteção** contra exclusão de clientes com orçamentos

### 🛠️ Gestão de Serviços
- **CRUD completo** de serviços
- **Valores monetários** com precisão decimal
- **Validações** de dados e valores
- **Proteção** contra exclusão de serviços em uso

### 📊 Gestão de Orçamentos
- **Criação prática** de orçamentos (sem JSON complexo)
- **Adição gradual** de itens um por vez
- **Edição em tempo real** de quantidades
- **Remoção fácil** de itens indesejados
- **Cálculo automático** de valores totais
- **Controle de status** (Em Andamento, Pendente, Aprovado, Recusado, Concluído)
- **Listagem completa** com filtros
- **Detalhamento** de orçamentos específicos
- **Geração de PDF** profissional
- **Envio por email** (configurável)

### 💰 Gestão de Vendas
- **Conversão** de orçamentos aprovados em vendas
- **Código único** para cada venda
- **Snapshot** dos itens no momento da venda
- **Listagem** com filtros por data e cliente
- **Paginação** de resultados

### 📍 Endereços
- **Múltiplos endereços** por cliente
- **Endereço padrão** configurável
- **CRUD completo** de endereços
- **Validações** de dados

## 🏗️ Arquitetura do Sistema

### Backend (Flask)
- **Framework**: Flask com SQLAlchemy
- **Banco de dados**: SQLite (desenvolvimento)
- **Autenticação**: Flask-Login
- **API**: REST com JSON
- **PDF**: WeasyPrint (opcional)
- **Containerização**: Docker com Gunicorn

### Frontend estático
- **Framework**: Nenhum — interface construída com HTML, CSS e JavaScript puros
- **Finalidade**: prototipação visual até a implementação das telas dinâmicas
- **Localização**: arquivos em `src/static/`

### Estrutura de Pastas
```
orcamento-servicos-main/
├── src/                 # Código fonte da aplicação
│   ├── main.py          # Aplicação principal
│   ├── models/
│   │   └── models.py    # Modelos do banco de dados
│   ├── routes/
│   │   ├── auth.py      # Autenticação
│   │   ├── clientes.py  # Gestão de clientes
│   │   ├── servicos.py  # Gestão de serviços
│   │   ├── orcamentos.py # Gestão de orçamentos
│   │   └── vendas.py    # Gestão de vendas
│   ├── static/          # Interface temporária (testes)
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
│   └── database/        # Banco SQLite (criado automaticamente)
├── Dockerfile           # Configuração do container
├── docker-entrypoint.sh # Script de inicialização
├── .dockerignore        # Arquivos ignorados no build
├── requirements.txt     # Dependências Python
└── README.md           # Documentação
```

### Modelos de Dados
- **Usuario**: Usuários do sistema
- **Cliente**: Clientes da empresa
- **Servico**: Serviços oferecidos
- **Orcamento**: Orçamentos criados
- **OrcamentoServicos**: Relação orçamento-serviços
- **Venda**: Vendas convertidas de orçamentos
- **VendaItem**: Itens das vendas
- **Endereco**: Endereços dos clientes
- **LogsAcesso**: Logs de auditoria
- **PasswordResetToken**: Tokens de recuperação

## 🚀 Como Executar

### **Opção 1: Docker (Recomendado)**

#### Pré-requisitos
- Docker instalado
- Docker Compose (opcional)

#### 1. Construir e Executar com Docker
```bash
# Construir a imagem
docker build -t orcamento-servicos .

# Executar o container
docker run -p 5000:5000 orcamento-servicos
```

#### 2. Acessar o Sistema
- **Interface web**: http://localhost:5000
- **API**: http://localhost:5000/api/

### **Opção 2: Execução Local**

#### Pré-requisitos
- Python 3.11+
- pip (gerenciador de pacotes Python)

#### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

#### 2. Executar o Sistema
```bash
python src/main.py
```

#### 3. Acessar o Sistema
- **Interface web**: http://localhost:5000
- **API**: http://localhost:5000/api/

## 🚀 Fluxo Prático de Criação de Orçamentos

### **Método Recomendado (Sem JSON Complexo)**

1. **Iniciar Orçamento**
   ```bash
   POST /api/orcamentos/iniciar
   {
     "id_cliente": 1
   }
   ```

2. **Adicionar Itens Gradualmente**
   ```bash
   POST /api/orcamentos/123/adicionar-item
   {
     "id_servico": 5,
     "quantidade": 2
   }
   ```

3. **Atualizar Quantidades (se necessário)**
   ```bash
   PUT /api/orcamentos/123/atualizar-quantidade/5
   {
     "quantidade": 3
   }
   ```

4. **Remover Itens (se necessário)**
   ```bash
   DELETE /api/orcamentos/123/remover-item/5
   ```

5. **Finalizar Orçamento**
   ```bash
   POST /api/orcamentos/123/finalizar
   ```

### **Vantagens do Novo Fluxo**
- ✅ **Simples**: Apenas 2 campos por requisição
- ✅ **Intuitivo**: Adiciona um item por vez
- ✅ **Flexível**: Pode editar/remover a qualquer momento
- ✅ **Visual**: Vê o total sendo calculado em tempo real
- ✅ **Seguro**: Orçamento fica "Em Andamento" até finalizar

## 📚 Endpoints da API

### Autenticação (`/api/auth/`)
- `POST /register` - Cadastrar usuário
- `POST /login` - Fazer login
- `POST /logout` - Fazer logout
- `GET /verificar` - Verificar se está logado
- `POST /forgot-password` - Solicitar recuperação de senha
- `POST /reset-password` - Redefinir senha

### Clientes (`/api/clientes/`)
- `GET /` - Listar clientes
- `GET /<id>` - Buscar cliente específico
- `POST /` - Cadastrar cliente
- `PUT /<id>` - Atualizar cliente
- `DELETE /<id>` - Excluir cliente
- `GET /<id>/enderecos` - Listar endereços do cliente
- `POST /<id>/enderecos` - Criar endereço
- `PUT /<id>/enderecos/<id_endereco>` - Atualizar endereço
- `DELETE /<id>/enderecos/<id_endereco>` - Excluir endereço
- `PUT /<id>/enderecos/<id_endereco>/definir-padrao` - Definir endereço padrão

### Serviços (`/api/servicos/`)
- `GET /` - Listar serviços
- `GET /<id>` - Buscar serviço específico
- `POST /` - Cadastrar serviço
- `PUT /<id>` - Atualizar serviço
- `DELETE /<id>` - Excluir serviço

### Orçamentos (`/api/orcamentos/`)
- `GET /` - Listar orçamentos
- `GET /<id>` - Detalhar orçamento
- `POST /` - Criar orçamento (método tradicional com JSON)
- `PUT /<id>/status` - Atualizar status
- `POST /<id>/converter-venda` - Converter em venda
- `GET /<id>/pdf` - Gerar PDF
- `POST /<id>/enviar-email` - Enviar por email

#### **Novos Endpoints Práticos (Recomendados)**
- `POST /iniciar` - Iniciar orçamento temporário
- `POST /<id>/adicionar-item` - Adicionar item individual
- `DELETE /<id>/remover-item/<id_servico>` - Remover item específico
- `PUT /<id>/atualizar-quantidade/<id_servico>` - Atualizar quantidade
- `POST /<id>/finalizar` - Finalizar orçamento

### Vendas (`/api/vendas/`)
- `GET /` - Listar vendas (com filtros)
- `GET /<id>` - Detalhar venda

## 🐳 Docker

### **Configuração do Container**
- **Imagem base**: Python 3.11-slim
- **Servidor**: Gunicorn (produção)
- **Porta**: 5000
- **Dependências**: WeasyPrint com bibliotecas do sistema

### **Arquivos Docker**
- `Dockerfile`: Configuração da imagem
- `docker-entrypoint.sh`: Script de inicialização
- `.dockerignore`: Arquivos ignorados no build

### **Vantagens do Docker**
- ✅ **Isolamento**: Ambiente consistente
- ✅ **Portabilidade**: Funciona em qualquer sistema
- ✅ **Dependências**: Instalação automática do WeasyPrint
- ✅ **Produção**: Gunicorn para melhor performance
- ✅ **Simplicidade**: Um comando para executar

### **Comandos Docker Úteis**
```bash
# Construir a imagem
docker build -t orcamento-servicos .

# Executar o container
docker run -p 5000:5000 orcamento-servicos

# Executar em background
docker run -d -p 5000:5000 --name orcamento-app orcamento-servicos

# Ver logs do container
docker logs orcamento-app

# Parar o container
docker stop orcamento-app

# Remover o container
docker rm orcamento-app

# Remover a imagem
docker rmi orcamento-servicos
```

## 🔧 Configurações

### Variáveis de Ambiente (Opcionais)
```bash
SECRET_KEY=sua-chave-secreta-aqui
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASS=sua-senha-app
SMTP_FROM=seu-email@gmail.com
SMTP_TLS=true
```

### Banco de Dados
- **Desenvolvimento**: SQLite (criado automaticamente)
- **Produção**: PostgreSQL (configuração necessária)

## 📝 Notas Importantes

### Interface Temporária
Os arquivos na pasta `static/` são apenas para testes locais e podem ser removidos em produção.

### Geração de PDF
- Requer instalação do WeasyPrint
- Funciona sem dependências externas (outras funcionalidades)

### Logs de Auditoria
- Todas as ações são registradas automaticamente
- Inclui informações de usuário, ação e timestamp

### Segurança
- Senhas são criptografadas com hash
- Tokens de recuperação têm expiração
- Validações de dados em todas as entradas

## 🐛 Solução de Problemas

### **Docker**

#### Erro ao construir a imagem
```bash
# Limpar cache do Docker
docker system prune -a

# Reconstruir sem cache
docker build --no-cache -t orcamento-servicos .
```

#### Erro de permissão no script
```bash
# Verificar se o script está executável
chmod +x docker-entrypoint.sh
```

#### Container não inicia
```bash
# Verificar logs
docker logs orcamento-app

# Verificar se a porta está em uso
netstat -tulpn | grep :5000
```

### **Execução Local**

#### Erro de Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Erro de Banco de Dados
- Verifique se a pasta `src/database/` existe
- O banco SQLite é criado automaticamente

#### Erro de PDF
- Instale o WeasyPrint: `pip install WeasyPrint`
- Ou use apenas as funcionalidades de API

## 📈 Próximos Passos

### **Em Desenvolvimento**
- [ ] Interface web completa (Roberto)
- [ ] Agendamento de Serviços
- [ ] Relatórios e Estatísticas
- [ ] Configuração completa de email

### **Melhorias Técnicas**
- [ ] Migração para PostgreSQL
- [ ] Testes automatizados
- [ ] Documentação da API (Swagger)
- [ ] Docker Compose para desenvolvimento
- [ ] CI/CD pipeline

## 👥 Desenvolvimento

Sistema desenvolvido para gerenciamento completo de orçamentos de serviços, com foco em simplicidade e funcionalidade.

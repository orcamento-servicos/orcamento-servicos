# Sistema de Orçamentos de Serviços

Backend em Flask com autenticação, CRUD de clientes, serviços e orçamentos, incluindo geração de PDF e atualização de status.

## Requisitos
- Python 3.11+
- Pip
- (Opcional) Docker

## Instalação (local)
1. Crie um ambiente virtual (recomendado)
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode o servidor:
   ```bash
   python -m src.main
   ```
4. Acesse `http://localhost:5000`

### Observações WeasyPrint (Windows)
- Tente `pip install weasyprint` caso falhe no `requirements.txt`.
- Pode exigir bibliotecas de renderização (GTK/Cairo). Se tiver dificuldades, use Docker.

## Uso com Docker
Construir a imagem e subir o container:
```bash
docker build -t orcamento-servicos .
docker run -p 5000:5000 --name orcamento-servicos orcamento-servicos
```

## Fluxo de Teste Rápido
Existem duas formas simples: pela página de testes (`/`) e por cliente REST (Postman/Insomnia).

### A) Testar pela página de testes (recomendado para validação rápida)
1. Inicie o servidor: `python -m src.main` e acesse `http://localhost:5000`.
2. Na seção “Autenticação”, faça login (se ainda não tiver usuário, registre primeiro via Postman ou crie direto no banco).
3. Na seção “Adicionar Novo Cliente”, cadastre um cliente e verifique ele na lista abaixo.
4. Cadastre dois serviços (via Postman ou usando as rotas diretamente):
   - Exemplo 1:
     ```json
     { "nome": "Pintura", "descricao": "Pintura de sala", "valor": 250 }
     ```
   - Exemplo 2:
     ```json
     { "nome": "Limpeza", "descricao": "Limpeza pós-obra", "valor": 150 }
     ```
5. Na seção “Orçamentos” da página de testes:
   - Informe o ID do cliente.
   - Em “Itens em JSON”, cole um array com itens (itens duplicados são somados automaticamente):
     ```json
     [
       { "id_servico": 1, "quantidade": 1 },
       { "id_servico": 1, "quantidade": 3 },
       { "id_servico": 2, "quantidade": 2 }
     ]
     ```
   - Clique em “Criar Orçamento” e veja a resposta no quadro de saída.
   - “Listar Orçamentos” mostrará todos com seus itens.
   - Para “Detalhar”, informe o ID do orçamento e clique em “Detalhar”.
   - Para “Atualizar Status”, informe o ID e escolha um status: `Pendente`, `Aprovado`, `Recusado` ou `Concluído`.
   - Para baixar o PDF, informe o ID e clique em “Baixar PDF”. O arquivo será salvo como `orcamento_{id}.pdf`.

Observações:
- É necessário estar logado para acessar as rotas (sessão via cookies do navegador).
- Se o PDF falhar no Windows por dependências do WeasyPrint, utilize Docker ou instale as bibliotecas requeridas.

### B) Testar pelo Postman/Insomnia
1. Importe a coleção:
   - Postman: `docs/postman_collection.json`
   - Insomnia: `docs/insomnia_collection.yaml`
2. Registrar usuário (POST `/api/auth/register`):
   ```json
   { "nome": "Admin", "email": "admin@teste.com", "senha": "123456" }
   ```
3. Login (POST `/api/auth/login`):
   ```json
   { "email": "admin@teste.com", "senha": "123456" }
   ```
   O cliente guardará a sessão por cookie automaticamente (habilite “Enable cookies”).
4. Criar cliente (POST `/api/clientes/`):
   ```json
   { "nome": "Cliente X", "telefone": "11999999999", "email": "cliente@x.com", "endereco": "Rua A, 123" }
   ```
5. Criar serviços (POST `/api/servicos/`):
   ```json
   { "nome": "Pintura", "descricao": "Pintura de sala", "valor": 250 }
   ```
   ```json
   { "nome": "Limpeza", "descricao": "Limpeza pós-obra", "valor": 150 }
   ```
6. Criar orçamento (POST `/api/orcamentos/`):
   ```json
   {
     "id_cliente": 1,
     "itens": [
       { "id_servico": 1, "quantidade": 1 },
       { "id_servico": 1, "quantidade": 3 },
       { "id_servico": 2, "quantidade": 2 }
     ]
   }
   ```
7. Listar orçamentos (GET `/api/orcamentos/`).
8. Detalhar orçamento (GET `/api/orcamentos/{id}`).
9. Atualizar status (PUT `/api/orcamentos/{id}/status`):
   ```json
   { "status": "Aprovado" }
   ```
   Status válidos: `Pendente`, `Aprovado`, `Recusado`, `Concluído`.
10. Gerar PDF (GET `/api/orcamentos/{id}/pdf`).

Erros comuns e dicas:
- 401 Não autenticado: faça login novamente.
- Validação de itens: `id_servico` deve existir e `quantidade` deve ser inteiro ≥ 1.
- Itens duplicados no POST são somados automaticamente antes do cálculo.

## Coleções de Teste
- Postman: `docs/postman_collection.json`
- Insomnia: `docs/insomnia_collection.yaml`

## Padrões do Projeto
- Código em português, indentação com espaços.
- Blueprints em `src/routes/`.
- Modelos em `src/models/models.py`.

## Notas
- O banco SQLite é criado em `src/database/app.db` ao iniciar.
- Se alterar modelos, pode ser necessário apagar o `app.db` para recriar.


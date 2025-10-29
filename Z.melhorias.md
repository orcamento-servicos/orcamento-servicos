# Melhorias Sugeridas para o Projeto Orçamento de Serviços

## 1. Experiência do Usuário (UX/UI)
- [ ] Adicionar feedback visual de carregamento (spinners/loaders) em todas as requisições assíncronas.
- [ ] Exibir mensagens de erro detalhadas e amigáveis para o usuário.
- [ ] Permitir visualização e edição do perfil em modal, sem sair da tela principal.
- [FAZER] Implementar tema escuro/claro com alternância.
- [ ] Melhorar responsividade para dispositivos móveis.
- [ ] Adicionar pré-visualização da imagem de perfil antes do upload.
- [ ] Exibir notificações (toasts) para ações rápidas (sucesso/erro).

## 2. Segurança
- [ ] Forçar HTTPS em produção.
- [ ] Limitar tamanho e tipo de arquivos no upload de avatar.
- [ ] Implementar proteção contra CSRF nas rotas sensíveis.
- [ ] Adicionar verificação de força de senha no cadastro e troca de senha.
- [ ] Bloquear conta após múltiplas tentativas de login inválidas.

## 3. Backend/API
- [FAZER] Implementar paginação e filtros nas listagens (clientes, orçamentos, serviços).
- [ ] Adicionar logs detalhados de todas as ações críticas (edição, exclusão, login, etc).
- [ ] Permitir atualização parcial do perfil (PATCH além de PUT).
- [ ] Adicionar testes automatizados (unitários e de integração) para rotas e modelos.
- [ ] Implementar versionamento da API.
- [ ] Permitir múltiplos perfis de usuário (admin, operador, cliente, etc).

## 4. Funcionalidades
- [ ] Permitir anexar arquivos (ex: comprovantes, contratos) aos orçamentos.
- [ ] Adicionar busca global (clientes, orçamentos, serviços) com autocomplete.
- [ ] Permitir exportação de dados em CSV/Excel.
- [ ] Adicionar dashboard com gráficos de desempenho (orçamentos aprovados, vendas, etc).
- [ ] Implementar notificações por e-mail para eventos importantes (orçamento aprovado, serviço agendado, etc).
- [FAZER] Permitir login social (Google, Microsoft, etc).
- [ ] Adicionar histórico de alterações nos orçamentos e perfis.

## 5. Infraestrutura e DevOps
- [ ] Adicionar Dockerfile e docker-compose para facilitar deploy.
- [ ] Configurar CI/CD para testes e deploy automático.
- [ ] Permitir configuração de variáveis sensíveis via painel admin (sem editar .env).
- [ ] Documentar todas as rotas da API (Swagger/OpenAPI).

## 6. Código e Organização
- [ ] Refatorar código JS para módulos ES6 e reaproveitamento de funções.
- [ ] Separar lógica de frontend em componentes reutilizáveis.
- [ ] Adicionar comentários e docstrings detalhados em todas as funções e métodos.
- [ ] Padronizar nomes de arquivos e pastas (case, idioma, etc).

---

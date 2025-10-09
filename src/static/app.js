(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2600);
  }

  function setOutput(id, data) {
    const el = $(id);
    el.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  }

  async function api(method, url, body, opts = {}) {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      credentials: 'include',
      body: body ? JSON.stringify(body) : undefined,
    });
    const isJson = (res.headers.get('content-type') || '').includes('application/json');
    const data = isJson ? await res.json() : await res.text();
    if (!res.ok) throw { status: res.status, data };
    return data;
  }

  // Tabs
  $$('.tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      $$('.tab').forEach((b) => b.classList.remove('active'));
      $$('.tabpane').forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      const id = btn.dataset.tab;
      $('#' + id).classList.add('active');
    });
  });

  // Atalhos de mudança de aba
  $$('[data-tab-target]').forEach((trigger) => {
    trigger.addEventListener('click', () => {
      const target = trigger.dataset.tabTarget;
      const tabBtn = $(`.tab[data-tab="${target}"]`);
      if (tabBtn) tabBtn.click();
    });
  });

  // Sessão
  async function refreshSession() {
    try {
      const d = await api('GET', '/api/auth/verificar');
      if (d.logado) {
        $('#userStatus').textContent = `Logado: ${d.usuario.nome} (${d.usuario.email})`;
        $('#btnLogout').disabled = false;
      } else {
        $('#userStatus').textContent = 'Não autenticado';
        $('#btnLogout').disabled = true;
      }
    } catch (e) {
      $('#userStatus').textContent = 'Sessão desconhecida';
      $('#btnLogout').disabled = true;
    }
  }

  $('#btnLogout').addEventListener('click', async () => {
    try {
      await api('POST', '/api/auth/logout');
      toast('Sessão encerrada');
      refreshSession();
    } catch (e) {
      toast('Falha ao sair');
    }
  });

  // Auth
  $('#btnRegistrar').addEventListener('click', async () => {
    try {
      const body = { nome: $('#regNome').value, email: $('#regEmail').value, senha: $('#regSenha').value };
      const d = await api('POST', '/api/auth/register', body);
      setOutput('#authOutput', d);
      toast('Usuário registrado');
    } catch (e) {
      setOutput('#authOutput', e.data);
      toast('Erro ao registrar');
    }
  });
  $('#btnLogin').addEventListener('click', async () => {
    try {
      const body = { email: $('#loginEmail').value, senha: $('#loginSenha').value };
      const d = await api('POST', '/api/auth/login', body);
      setOutput('#authOutput', d);
      toast('Login realizado');
      refreshSession();
    } catch (e) {
      setOutput('#authOutput', e.data);
      toast('Erro ao logar');
    }
  });
  $('#btnVerificar').addEventListener('click', async () => {
    try {
      const d = await api('GET', '/api/auth/verificar');
      setOutput('#authOutput', d);
    } catch (e) {
      setOutput('#authOutput', e.data);
    }
  });

  // Clientes
  $('#btnCriarCliente').addEventListener('click', async () => {
    try {
      const body = { nome: $('#cliNome').value, telefone: $('#cliTelefone').value, email: $('#cliEmail').value, endereco: $('#cliEndereco').value };
      const d = await api('POST', '/api/clientes/', body);
      setOutput('#clientesOutput', d);
      toast('Cliente criado');
    } catch (e) {
      setOutput('#clientesOutput', e.data);
      toast('Erro ao criar cliente');
    }
  });
  $('#btnListarClientes').addEventListener('click', async () => {
    try {
      const d = await api('GET', '/api/clientes/');
      setOutput('#clientesOutput', d);
    } catch (e) {
      setOutput('#clientesOutput', e.data);
    }
  });
  $('#btnBuscarCliente').addEventListener('click', async () => {
    const id = $('#cliIdBusca').value;
    if (!id) return toast('Informe o ID');
    try {
      const d = await api('GET', `/api/clientes/${id}`);
      setOutput('#clientesOutput', d);
    } catch (e) {
      setOutput('#clientesOutput', e.data);
    }
  });

  // Endereços
  $('#btnCriarEndereco').addEventListener('click', async () => {
    const cid = $('#endCliId').value;
    if (!cid) return toast('Informe ID Cliente');
    try {
      const body = {
        logradouro: $('#endLogradouro').value,
        numero: $('#endNumero').value,
        complemento: $('#endComplemento').value,
        bairro: $('#endBairro').value,
        cidade: $('#endCidade').value,
        uf: $('#endUf').value,
        cep: $('#endCep').value,
        apelido: $('#endApelido').value,
        is_padrao: $('#endPadrao').checked,
      };
      const d = await api('POST', `/api/clientes/${cid}/enderecos`, body);
      setOutput('#enderecosOutput', d);
      toast('Endereço criado');
    } catch (e) {
      setOutput('#enderecosOutput', e.data);
    }
  });
  $('#btnListarEnderecos').addEventListener('click', async () => {
    const cid = $('#endCliId').value;
    if (!cid) return toast('Informe ID Cliente');
    try {
      const d = await api('GET', `/api/clientes/${cid}/enderecos`);
      setOutput('#enderecosOutput', d);
    } catch (e) {
      setOutput('#enderecosOutput', e.data);
    }
  });
  $('#btnAtualizarEndereco').addEventListener('click', async () => {
    const cid = $('#endCliId').value;
    const eid = $('#endId').value;
    if (!cid || !eid) return toast('Informe ID Cliente e ID Endereço');
    try {
      const body = {
        logradouro: $('#endLogradouro').value,
        numero: $('#endNumero').value,
        complemento: $('#endComplemento').value,
        bairro: $('#endBairro').value,
        cidade: $('#endCidade').value,
        uf: $('#endUf').value,
        cep: $('#endCep').value,
        apelido: $('#endApelido').value,
        is_padrao: $('#endPadrao').checked,
      };
      const d = await api('PUT', `/api/clientes/${cid}/enderecos/${eid}`, body);
      setOutput('#enderecosOutput', d);
      toast('Endereço atualizado');
    } catch (e) {
      setOutput('#enderecosOutput', e.data);
    }
  });
  $('#btnExcluirEndereco').addEventListener('click', async () => {
    const cid = $('#endCliId').value;
    const eid = $('#endId').value;
    if (!cid || !eid) return toast('Informe ID Cliente e ID Endereço');
    try {
      const d = await api('DELETE', `/api/clientes/${cid}/enderecos/${eid}`);
      setOutput('#enderecosOutput', d);
      toast('Endereço excluído');
    } catch (e) {
      setOutput('#enderecosOutput', e.data);
    }
  });
  $('#btnDefinirPadrao').addEventListener('click', async () => {
    const cid = $('#endCliId').value;
    const eid = $('#endId').value;
    if (!cid || !eid) return toast('Informe ID Cliente e ID Endereço');
    try {
      const d = await api('PUT', `/api/clientes/${cid}/enderecos/${eid}/definir-padrao`);
      setOutput('#enderecosOutput', d);
      toast('Padrão definido');
    } catch (e) {
      setOutput('#enderecosOutput', e.data);
    }
  });

  // Serviços
  $('#btnCriarServico').addEventListener('click', async () => {
    try {
      const body = { nome: $('#srvNome').value, descricao: $('#srvDescricao').value, valor: $('#srvValor').value };
      const d = await api('POST', '/api/servicos/', body);
      setOutput('#servicosOutput', d);
      toast('Serviço criado');
    } catch (e) {
      setOutput('#servicosOutput', e.data);
    }
  });
  $('#btnListarServicos').addEventListener('click', async () => {
    try {
      const d = await api('GET', '/api/servicos/');
      setOutput('#servicosOutput', d);
    } catch (e) {
      setOutput('#servicosOutput', e.data);
    }
  });
  $('#btnBuscarServico').addEventListener('click', async () => {
    const id = $('#srvIdBusca').value;
    if (!id) return toast('Informe o ID');
    try {
      const d = await api('GET', `/api/servicos/${id}`);
      setOutput('#servicosOutput', d);
    } catch (e) {
      setOutput('#servicosOutput', e.data);
    }
  });

  // Orçamentos
  $('#btnCriarOrcamento').addEventListener('click', async () => {
    try {
      const itens = JSON.parse($('#orcItens').value || '[]');
      const body = { id_cliente: parseInt($('#orcIdCliente').value), itens };
      const idEnd = $('#orcIdEndereco').value;
      if (idEnd) body.id_endereco = parseInt(idEnd);
      const d = await api('POST', '/api/orcamentos/', body);
      setOutput('#orcamentosOutput', d);
      toast('Orçamento criado');
    } catch (e) {
      setOutput('#orcamentosOutput', e.data);
    }
  });
  $('#btnListarOrcamentos').addEventListener('click', async () => {
    try {
      const d = await api('GET', '/api/orcamentos/');
      setOutput('#orcamentosOutput', d);
    } catch (e) {
      setOutput('#orcamentosOutput', e.data);
    }
  });
  $('#btnDetalharOrcamento').addEventListener('click', async () => {
    const id = $('#orcIdBusca').value;
    if (!id) return toast('Informe ID do orçamento');
    try {
      const d = await api('GET', `/api/orcamentos/${id}`);
      setOutput('#orcamentosOutput', d);
    } catch (e) {
      setOutput('#orcamentosOutput', e.data);
    }
  });
  $('#btnAtualizarStatus').addEventListener('click', async () => {
    const id = $('#orcIdBusca').value;
    if (!id) return toast('Informe ID do orçamento');
    try {
      const body = { status: $('#orcStatusNovo').value };
      const d = await api('PUT', `/api/orcamentos/${id}/status`, body);
      setOutput('#orcamentosOutput', d);
      toast('Status atualizado');
    } catch (e) {
      setOutput('#orcamentosOutput', e.data);
    }
  });
  $('#btnBaixarPDF').addEventListener('click', async () => {
    const id = $('#orcIdBusca').value;
    if (!id) return toast('Informe ID do orçamento');
    try {
      const res = await fetch(`/api/orcamentos/${id}/pdf`, { credentials: 'include' });
      if (!res.ok) throw await res.json();
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `orcamento_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast('PDF baixado');
    } catch (e) {
      setOutput('#orcamentosOutput', e);
    }
  });
  $('#btnEnviarEmail').addEventListener('click', async () => {
    const id = $('#orcIdBusca').value;
    const emails = ($('#orcEmails').value || '').split(',').map((s) => s.trim()).filter(Boolean);
    const mensagem = $('#orcMensagem').value;
    if (!id || emails.length === 0) return toast('Informe ID e emails');
    try {
      const d = await api('POST', `/api/orcamentos/${id}/enviar-email`, { emails, mensagem });
      setOutput('#orcamentosOutput', d);
      toast('E-mail enviado');
    } catch (e) {
      setOutput('#orcamentosOutput', e.data);
    }
  });
  $('#btnConverterVenda').addEventListener('click', async () => {
    const id = $('#orcIdBusca').value;
    if (!id) return toast('Informe ID do orçamento');
    try {
      const d = await api('POST', `/api/orcamentos/${id}/converter-venda`);
      setOutput('#orcamentosOutput', d);
      toast('Convertido em venda');
    } catch (e) {
      setOutput('#orcamentosOutput', e.data);
    }
  });

  // Vendas
  $('#btnListarVendas').addEventListener('click', async () => {
    try {
      const qs = new URLSearchParams();
      if ($('#vIdCliente').value) qs.set('id_cliente', $('#vIdCliente').value);
      if ($('#vIdOrcamento').value) qs.set('id_orcamento', $('#vIdOrcamento').value);
      if ($('#vDataIni').value) qs.set('data_ini', $('#vDataIni').value);
      if ($('#vDataFim').value) qs.set('data_fim', $('#vDataFim').value);
      const d = await api('GET', `/api/vendas/?${qs.toString()}`);
      setOutput('#vendasOutput', d);
    } catch (e) {
      setOutput('#vendasOutput', e.data);
    }
  });
  $('#btnDetalharVenda').addEventListener('click', async () => {
    const id = $('#vIdVenda').value;
    if (!id) return toast('Informe ID da venda');
    try {
      const d = await api('GET', `/api/vendas/${id}`);
      setOutput('#vendasOutput', d);
    } catch (e) {
      setOutput('#vendasOutput', e.data);
    }
  });

  // Recuperação de senha
  $('#btnForgot').addEventListener('click', async () => {
    try {
      const d = await api('POST', '/api/auth/forgot-password', { email: $('#recEmail').value });
      setOutput('#senhaOutput', d);
      toast('Solicitado');
    } catch (e) {
      setOutput('#senhaOutput', e.data);
    }
  });
  $('#btnReset').addEventListener('click', async () => {
    try {
      const d = await api('POST', '/api/auth/reset-password', { token: $('#recToken').value, nova_senha: $('#recNovaSenha').value });
      setOutput('#senhaOutput', d);
      toast('Senha redefinida');
    } catch (e) {
      setOutput('#senhaOutput', e.data);
    }
  });

  // Init
  refreshSession();
})();
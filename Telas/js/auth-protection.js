// ========================================
// PROTEÇÃO DE ROTAS - VERIFICAÇÃO DE AUTENTICAÇÃO
// Sistema de Orçamentos de Serviços
// ========================================

// Configuração da API
const API_BASE_URL = '/api';

/**
 * Verifica se o usuário está autenticado
 * @returns {Promise<boolean>} true se autenticado, false caso contrário
 */
async function verificarAutenticacao() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/verificar`, {
      method: 'GET',
      credentials: 'include'
    });

    if (response.ok) {
      const data = await response.json();
      return data.logado === true;
    }
    return false;
  } catch (error) {
    console.error('Erro ao verificar autenticação:', error);
    return false;
  }
}

/**
 * Redireciona para a tela de login
 */
function redirecionarParaLogin() {
  window.location.href = '/';
}

/**
 * Protege uma página verificando autenticação
 * Deve ser chamada quando a página carrega
 */
async function protegerPagina() {
  const estaAutenticado = await verificarAutenticacao();
  
  if (!estaAutenticado) {
    console.log('Usuário não autenticado. Redirecionando para login...');
    redirecionarParaLogin();
    return false;
  }
  
  console.log('Usuário autenticado. Acesso liberado.');
  return true;
}

/**
 * Função para fazer logout
 */
async function fazerLogout() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include'
    });

    if (response.ok) {
      console.log('Logout realizado com sucesso');
      redirecionarParaLogin();
    } else {
      console.error('Erro ao fazer logout');
      // Mesmo com erro, redireciona para login
      redirecionarParaLogin();
    }
  } catch (error) {
    console.error('Erro na requisição de logout:', error);
    // Mesmo com erro, redireciona para login
    redirecionarParaLogin();
  }
}

/**
 * Adiciona listener para botões de logout
 * Procura por elementos com data-logout="true"
 */
function configurarLogout() {
  // Procura por botões/links de logout
  const logoutElements = document.querySelectorAll('[data-logout="true"]');
  
  logoutElements.forEach(element => {
    element.addEventListener('click', function(e) {
      e.preventDefault();
      fazerLogout();
    });
  });

  // Também procura por links que apontam para TelaLogin.html
  const loginLinks = document.querySelectorAll('a[href*="TelaLogin.html"]');
  loginLinks.forEach(link => {
    // Se não tem data-logout="true", assume que é logout
    if (!link.hasAttribute('data-logout') || link.getAttribute('data-logout') !== 'true') {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        fazerLogout();
      });
    }
  });
}

// Auto-executa quando o script é carregado
document.addEventListener('DOMContentLoaded', function() {
  // Configura os listeners de logout
  configurarLogout();
  
  // Se estamos em uma página protegida (não é login nem registro), verifica autenticação
  const currentPath = window.location.pathname;
  const isLoginPage = currentPath.includes('TelaLogin.html');
  const isRegisterPage = currentPath.includes('TelaRegistrar.html');
  const isPublicPage = currentPath.includes('TelaSobre.html') || 
                      currentPath.includes('TelaContato.html') ||
                      currentPath.includes('TelaEsqueceuSenha.html');
  
  if (!isLoginPage && !isRegisterPage && !isPublicPage) {
    protegerPagina();
  }
});

// ====== Gerenciamento Global do Perfil do Usuário ======
let dadosUsuarioGlobal = null;

/**
 * Carrega os dados do perfil do usuário
 * @returns {Promise<object>} Dados do usuário
 */
async function carregarDadosUsuario() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/profile`, { 
      credentials: 'include' 
    });
    if (!response.ok) throw new Error('Erro ao carregar perfil');
    const data = await response.json();
    dadosUsuarioGlobal = data.usuario;
    atualizarInterfaceUsuario();
    return data.usuario;
  } catch (error) {
    console.error('Erro ao carregar dados do usuário:', error);
    return null;
  }
}

/**
 * Atualiza a interface com os dados do usuário
 */
function atualizarInterfaceUsuario() {
  if (!dadosUsuarioGlobal) return;
  
  // Atualiza nome do usuário onde houver elemento com id="nomeTopo"
  const elementosNome = document.querySelectorAll('[id="nomeTopo"]');
  elementosNome.forEach(el => {
    el.textContent = dadosUsuarioGlobal.nome || 'Usuário';
  });
  
  // Atualiza status do usuário onde houver elemento com id="statusTopo"
  const elementosStatus = document.querySelectorAll('[id="statusTopo"]');
  elementosStatus.forEach(el => {
    el.textContent = dadosUsuarioGlobal.status || 'Online';
  });
  
  // Atualiza avatar do usuário onde houver elementos com id="avatarPreview" ou id="avatarLarge"
  let avatarUrl = dadosUsuarioGlobal.avatar_url;
  // Se não tem avatar personalizado, usa imagem padrão absoluta
  if (!avatarUrl || typeof avatarUrl !== 'string' || avatarUrl.trim() === '') {
    avatarUrl = '/imagens/usuario.jpg';
  }
  // Garante que o caminho seja absoluto (evita problemas de path relativo)
  if (avatarUrl && !avatarUrl.startsWith('/')) {
    avatarUrl = '/' + avatarUrl.replace(/^\/+/, '');
  }
  const elementosAvatar = document.querySelectorAll('[id="avatarPreview"], [id="avatarLarge"]');
  elementosAvatar.forEach(el => {
    el.style.backgroundImage = `url('${avatarUrl}')`;
    // Corrige avatar quebrado: tenta carregar, se falhar, usa imagem padrão absoluta
    const img = new window.Image();
    img.onerror = () => {
      el.style.backgroundImage = `url('/imagens/usuario.jpg')`;
    };
    img.src = avatarUrl;
  });
}

// Carrega os dados do usuário quando o script é inicializado
document.addEventListener('DOMContentLoaded', carregarDadosUsuario);

// ====== Tema Escuro/Claro (Dark/Light Mode) ======

// Alternância de tema robusta
function alternarTema() {
  const html = document.querySelector('html');
  const temaAtual = html.classList.contains('dark') ? 'dark' : 'light';
  const novoTema = temaAtual === 'dark' ? 'light' : 'dark';
  if (novoTema === 'dark') {
    html.classList.add('dark');
    console.log('[Tema] Ativado modo escuro');
  } else {
    html.classList.remove('dark');
    console.log('[Tema] Ativado modo claro');
  }
  localStorage.setItem('temaPreferido', novoTema);
  atualizarIconeTema();
  console.log('[Tema] Classe dark no <html>?', html.classList.contains('dark'));
}

function aplicarTemaSalvo() {
  const temaSalvo = localStorage.getItem('temaPreferido');
  const html = document.querySelector('html');
  if (temaSalvo === 'dark') {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }
  atualizarIconeTema();
}

function atualizarIconeTema() {
  const btn = document.getElementById('btnTema');
  if (!btn) return;
  const html = document.querySelector('html');
  const isDark = html.classList.contains('dark');
  if (isDark) {
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12.79A9 9 0 1111.21 3a7 7 0 109.79 9.79z" /></svg>';
    btn.title = 'Alternar para tema claro';
  } else {
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m8.66-13.66l-.71.71M4.05 19.07l-.71.71M21 12h-1M4 12H3m16.66 6.66l-.71-.71M4.05 4.93l-.71-.71" /></svg>';
    btn.title = 'Alternar para tema escuro';
  }
}


// Injeta o botão de alternância de tema no canto superior direito absoluto
// Removido botão de alternância de tema conforme solicitado

// ====== Compatibilidade e utilitários globais ======
// Ajusta botões que não possuem `type` explícito para evitar comportamento de submit por omissão
(function ensureButtonTypesAndLogging(){
  try {
    // roda após pequeno delay para garantir que o DOM das páginas single-file já esteja pronto
    window.addEventListener('load', () => {
      const buttons = Array.from(document.querySelectorAll('button'));
      let fixed = 0;
      buttons.forEach(btn => {
        if (!btn.hasAttribute('type')) {
          btn.setAttribute('type', 'button');
          fixed++;
        }
      });
      if (fixed > 0) console.info(`[auth-protection] Ajustados ${fixed} botões sem type para type="button"`);
      console.debug('[auth-protection] script carregado. Número total de botões na página:', buttons.length);
    });
  } catch (e) {
    console.error('[auth-protection] Erro ao ajustar botões:', e);
  }
})();

// Pequeno utilitário para logar respostas de fetch para debugging rápido (opcional)
window.debugFetchResponse = async function(response) {
  try {
    console.log('[debugFetch] status', response.status, 'ok', response.ok);
    const ct = response.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      const data = await response.clone().json();
      console.log('[debugFetch] json', data);
      return data;
    } else {
      const txt = await response.clone().text();
      console.log('[debugFetch] text', txt.substring(0, 200));
      return txt;
    }
  } catch (err) {
    console.error('[debugFetch] erro ao ler resposta:', err);
    return null;
  }
};

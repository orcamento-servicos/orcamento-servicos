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

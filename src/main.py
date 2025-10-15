# ========================================
# ARQUIVO PRINCIPAL DO SISTEMA
# Sistema de Orçamentos de Serviços
# ========================================

import os
import sys

# Configuração necessária para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Carrega variáveis de ambiente do arquivo .env (se existir)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Arquivo .env carregado com sucesso!")
except ImportError:
    print("python-dotenv não instalado. Instale com: pip install python-dotenv")
    print("   Usando variáveis de ambiente do sistema...")
except Exception as e:
    print(f"Erro ao carregar .env: {e}")

# Importações do Flask e extensões
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_cors import CORS

# Importações dos nossos módulos
from src.models.models import db, Usuario
from src.routes.auth import auth_bp
from src.routes.clientes import clientes_bp
from src.routes.servicos import servicos_bp
from src.routes.orcamentos import orcamentos_bp
from src.routes.vendas import vendas_bp

# ========================================
# CONFIGURAÇÃO DO FLASK
# ========================================

# Cria a aplicação Flask
app = Flask(__name__)

# Configura CORS para permitir requisições do frontend
CORS(app, origins=["http://localhost:3000"])

# Chave secreta para sessões (lida do ambiente; define padrão apenas em dev)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-nao-usar-em-producao')

# ========================================
# CONFIGURAÇÃO DO LOGIN
# ========================================

# Inicializa o gerenciador de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.fazer_login'  # Rota para login
login_manager.login_message = 'Você precisa fazer login para acessar esta página.'

# Função que carrega o usuário pela sessão
@login_manager.user_loader
def carregar_usuario(id_usuario):
    """
    Função obrigatória do Flask-Login
    Carrega o usuário pelo ID armazenado na sessão
    """
    return Usuario.query.get(int(id_usuario))

# ========================================
# REGISTRO DAS ROTAS
# ========================================

# Registra os grupos de rotas (blueprints)
app.register_blueprint(auth_bp, url_prefix='/api/auth')        # Rotas de login/logout
app.register_blueprint(clientes_bp, url_prefix='/api/clientes') # Rotas de clientes
app.register_blueprint(servicos_bp, url_prefix='/api/servicos') # Rotas de serviços
app.register_blueprint(orcamentos_bp, url_prefix='/api/orcamentos') # Rotas de orçamentos
app.register_blueprint(vendas_bp, url_prefix='/api/vendas') # Rotas de vendas

# ========================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ========================================

# Caminho para o arquivo do banco SQLite
caminho_banco = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{caminho_banco}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desabilita avisos desnecessários

# Inicializa o banco de dados
db.init_app(app)

# Cria as tabelas se não existirem
with app.app_context():
    db.create_all()
    print("Banco de dados inicializado!")

# ========================================
# ROTA PRINCIPAL DA API
# ========================================

@app.route('/')
def api_info():
    """
    Informações sobre a API
    """
    return jsonify({
        'mensagem': 'Sistema de Orçamentos de Serviços - API',
        'versao': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'clientes': '/api/clientes/',
            'servicos': '/api/servicos/',
            'orcamentos': '/api/orcamentos/',
            'vendas': '/api/vendas/'
        }
    })

# ========================================
# INICIALIZAÇÃO DO SERVIDOR
# ========================================

if __name__ == '__main__':
    print("Iniciando o Sistema de Orçamentos de Serviços...")
    print("Acesse: http://localhost:5000")
    print("Para parar: Ctrl+C")
    
    # Inicia o servidor Flask
    # host='0.0.0.0' permite acesso de outros computadores na rede
    # debug=True reinicia automaticamente quando o código muda
    app.run(host='0.0.0.0', port=5000, debug=True)
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
from flask import Flask, jsonify, send_from_directory, send_file
from flask_login import LoginManager
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import inspect, text

# Importações dos nossos módulos
from src.models.models import db, Usuario
from src.routes.auth import auth_bp
from src.routes.clientes import clientes_bp
from src.routes.servicos import servicos_bp
from src.routes.orcamentos import orcamentos_bp
from src.routes.vendas import vendas_bp
from src.routes.agendamentos import agendamentos_bp
from src.routes.empresas import empresas_bp

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
app.register_blueprint(agendamentos_bp, url_prefix='/api/agendamentos') # Rotas de agendamentos
app.register_blueprint(empresas_bp, url_prefix='/api/empresas') # Rotas de empresas

# ========================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ========================================

# Caminho para o banco SQLite (usado apenas se DATABASE_URL não estiver definida)
caminho_banco_fallback = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
fallback_uri = f"sqlite:///{caminho_banco_fallback}"

# Usa a DATABASE_URL do ambiente (PostgreSQL no Docker) ou o fallback (SQLite local)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///banco.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco de dados
db.init_app(app)

# Inicializa o Flask-Migrate
migrate = Migrate(app, db)

# Cria as tabelas se não existirem
def garantir_schema_atualizado():
    """Garante que colunas novas existam na tabela empresas, corrigindo o banco automaticamente."""
    try:
        inspector = inspect(db.engine)
        # Verifica se a tabela existe antes de tentar ler colunas
        if 'empresas' in inspector.get_table_names():
            colunas = [col['name'] for col in inspector.get_columns('empresas')]
            
            with db.engine.connect() as conn:
                # --- CORREÇÃO 1: id_usuario (O erro que você está enfrentando) ---
                if 'id_usuario' not in colunas:
                    print("⚠️ Detectada falta de 'id_usuario'. Tentando corrigir...")
                    # Adiciona a coluna. Nota: Se já existirem empresas, elas ficarão com id_usuario=NULL inicialmente
                    conn.execute(text("ALTER TABLE empresas ADD COLUMN id_usuario INTEGER REFERENCES usuario(id_usuario)"))
                    conn.commit()
                    print("✅ Coluna 'id_usuario' adicionada com sucesso!")

                # --- CORREÇÃO 2: logo (Sua correção original) ---
                if 'logo' not in colunas:
                    print("⚠️ Detectada falta de 'logo'. Tentando corrigir...")
                    conn.execute(text("ALTER TABLE empresas ADD COLUMN logo VARCHAR(255)"))
                    conn.commit()
                    print("✅ Coluna 'logo' adicionada com sucesso!")
                    
    except Exception as e:
        print(f"❌ Aviso: Não foi possível sincronizar colunas manualmente: {e}")

# ========================================
# ROTA PRINCIPAL DA API
# ========================================

@app.route('/api')
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
            'vendas': '/api/vendas/',
            'agendamentos': '/api/agendamentos/'
        }
    })

# ========================================
# ROTAS PARA SERVIR O FRONTEND (TEMPLATES REORGANIZADOS)
# ========================================

# Diretórios preferenciais (reorganizados dentro de src/)
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


@app.route('/')
def index():
    """Serve a página inicial (login) — procura primeiro em src/templates, senão cai para Telas/ antiga."""
    candidate = os.path.join(TEMPLATES_DIR, 'TelaLogin.html')
    if os.path.exists(candidate):
        return send_file(candidate)
    # fallback para estrutura antiga (Telas/)
    return send_file(os.path.join(os.path.dirname(__file__), '..', 'Telas', 'TelaLogin.html'))


@app.route('/<path:filename>')
def serve_html(filename):
    """Serve arquivos HTML do frontend; procura em src/templates, depois em src/templates/MenuPrincipal, e por fim no diretório Telas/"""
    # Se não tem extensão, assume .html
    if '.' not in filename:
        filename += '.html'

    # 1) procurar em src/templates
    file_path = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)

    # 2) procurar em src/templates/MenuPrincipal
    menu_path = os.path.join(TEMPLATES_DIR, 'MenuPrincipal', filename)
    if os.path.exists(menu_path):
        return send_file(menu_path)

    # 3) fallback para estrutura antiga (Telas/)
    telas_path = os.path.join(os.path.dirname(__file__), '..', 'Telas')
    file_path = os.path.join(telas_path, filename)
    if os.path.exists(file_path):
        return send_file(file_path)

    menu_path = os.path.join(telas_path, 'MenuPrincipal', filename)
    if os.path.exists(menu_path):
        return send_file(menu_path)

    return jsonify({'erro': 'Página não encontrada'}), 404


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve arquivos estáticos (CSS, JS, imagens).
    Procura primeiro em src/static (recomendado), senão cai para Telas/ (estrutura antiga).
    """
    # 1) src/static
    if os.path.exists(STATIC_DIR):
        try:
            return send_from_directory(STATIC_DIR, filename)
        except Exception:
            pass

    # 2) fallback para Telas/
    static_path = os.path.join(os.path.dirname(__file__), '..', 'Telas')
    return send_from_directory(static_path, filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve arquivos JavaScript; prioriza src/static/js, depois Telas/js"""
    # 1) src/static/js
    js_src = os.path.join(STATIC_DIR, 'js')
    if os.path.exists(js_src):
        try:
            return send_from_directory(js_src, filename)
        except Exception:
            pass

    # 2) fallback Telas/js
    js_path = os.path.join(os.path.dirname(__file__), '..', 'Telas', 'js')
    return send_from_directory(js_path, filename)


@app.route('/Imagens/<path:filename>')
def serve_images(filename):
    """Serve imagens; prioriza src/static/Imagens, depois Telas/Imagens"""
    imgs_src = os.path.join(STATIC_DIR, 'Imagens')
    if os.path.exists(imgs_src):
        try:
            return send_from_directory(imgs_src, filename)
        except Exception:
            pass

    images_path = os.path.join(os.path.dirname(__file__), '..', 'Telas', 'Imagens')
    return send_from_directory(images_path, filename)


@app.route('/avatar/<filename>')
def avatar_file(filename):
    """Serve arquivos de avatar; procura na pasta padrão de avatares."""
    # Caminho absoluto para a pasta de avatares
    base_dir = os.path.dirname(os.path.abspath(__file__))
    avatar_dir = os.path.normpath(os.path.join(base_dir, '..', 'static', 'uploads', 'avatars'))
    return send_from_directory(avatar_dir, filename)

# ========================================
# INICIALIZAÇÃO DO SERVIDOR
# ========================================

# No final do arquivo, atualize o bloco de inicialização:
if __name__ != '__main__':
    # Este bloco roda quando o Gunicorn inicia (Produção no Render)
    with app.app_context():
        try:
            db.create_all()
            garantir_schema_atualizado() # <--- Chama a nova função de correção aqui
            print("Banco de dados verificado e inicializado!")
        except Exception as e:
            print(f"Erro na inicialização do banco: {e}")

if __name__ == '__main__':
    print("Acesse pelo link: http://localhost:5000")
    # Este bloco roda apenas em desenvolvimento local
    with app.app_context():
        db.create_all()
        garantir_schema_atualizado()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
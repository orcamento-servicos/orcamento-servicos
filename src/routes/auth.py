# ========================================
# ROTAS DE AUTENTICAÇÃO
# Sistema de Orçamentos de Serviços
# ========================================

# Importações necessárias
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from src.models.models import db, Usuario, LogsAcesso, PasswordResetToken
from datetime import datetime, timedelta
import secrets
import os
from src.utils.email_utils import send_email, get_smtp_config

# Cria um blueprint (grupo de rotas) para autenticação
auth_bp = Blueprint('auth', __name__)

# ========================================
# ROTA: CADASTRAR USUÁRIO
# POST /api/auth/register
# ========================================
@auth_bp.route('/register', methods=['POST'])
def cadastrar_usuario():
    """
    Cadastra um novo usuário no sistema
    Recebe: nome, email, senha, perfil (opcional)
    Retorna: dados do usuário criado ou erro
    """
    try:
        # Pega os dados enviados pelo cliente (JSON)
        dados = request.get_json()
        
        # Verifica se foram enviados dados
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        # Extrai os campos necessários
        nome = dados.get('nome')
        email = dados.get('email')
        senha = dados.get('senha')
        perfil = dados.get('perfil', 'admin')  # Se não informar, será 'admin'
        
        # Validações básicas
        if not nome or not email or not senha:
            return jsonify({'erro': 'Nome, email e senha são obrigatórios'}), 400
        
        if len(nome) > 80:
            return jsonify({'erro': 'Nome muito longo (máximo 80 caracteres)'}), 400
        
        if len(email) > 50:
            return jsonify({'erro': 'Email muito longo (máximo 50 caracteres)'}), 400
        
        if len(senha) < 6:
            return jsonify({'erro': 'Senha deve ter pelo menos 6 caracteres'}), 400
        
        # Verifica se o email já está sendo usado
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            return jsonify({'erro': 'Este email já está cadastrado'}), 400
        
        # Cria um novo usuário
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            perfil=perfil
        )
        # Criptografa e salva a senha
        novo_usuario.definir_senha(senha)
        
        # Salva no banco de dados
        db.session.add(novo_usuario)
        db.session.commit()
        
        # Registra a ação no log
        log = LogsAcesso(
            id_usuario=novo_usuario.id_usuario,
            acao='Usuário cadastrado no sistema',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        # Retorna sucesso
        return jsonify({
            'mensagem': 'Usuário cadastrado com sucesso!',
            'usuario': novo_usuario.para_dict()
        }), 201
        
    except Exception as e:
        # Se deu erro, desfaz as alterações no banco
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: FAZER LOGIN
# POST /api/auth/login
# ========================================
@auth_bp.route('/login', methods=['POST'])
def fazer_login():
    """
    Faz login do usuário no sistema
    Recebe: email, senha
    Retorna: dados do usuário logado ou erro
    """
    try:
        # Pega os dados enviados
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        email = dados.get('email')
        senha = dados.get('senha')
        
        # Verifica se email e senha foram informados
        if not email or not senha:
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400
        
        # Busca o usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verifica se o usuário existe e se a senha está correta
        if not usuario or not usuario.verificar_senha(senha):
            return jsonify({'erro': 'Email ou senha incorretos'}), 401
        
        # Faz o login (cria a sessão)
        login_user(usuario)
        
        # Registra o login no log
        log = LogsAcesso(
            id_usuario=usuario.id_usuario,
            acao='Login realizado',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        # Retorna sucesso
        return jsonify({
            'mensagem': 'Login realizado com sucesso!',
            'usuario': usuario.para_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: FAZER LOGOUT
# POST /api/auth/logout
# ========================================
@auth_bp.route('/logout', methods=['POST'])
@login_required  # Só funciona se o usuário estiver logado
def fazer_logout():
    """
    Faz logout do usuário (encerra a sessão)
    """
    try:
        # Registra o logout no log antes de sair
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao='Logout realizado',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        # Faz o logout (encerra a sessão)
        logout_user()
        
        return jsonify({'mensagem': 'Logout realizado com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: VERIFICAR SE ESTÁ LOGADO
# GET /api/auth/verificar
# ========================================
@auth_bp.route('/verificar', methods=['GET'])
def verificar_login():
    """
    Verifica se o usuário está logado
    Retorna: dados do usuário se logado, ou status de não logado
    """
    try:
        if current_user.is_authenticated:
            # Usuário está logado
            return jsonify({
                'logado': True,
                'usuario': current_user.para_dict()
            }), 200
        else:
            # Usuário não está logado
            return jsonify({'logado': False}), 200
            
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: SOLICITAR RECUPERAÇÃO DE SENHA
# POST /api/auth/forgot-password
# ========================================
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        dados = request.get_json() or {}
        email = (dados.get('email') or '').strip()
        # Resposta idempotente: sempre 200
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            # Gera token seguro e registra com expiração de 1h
            token = secrets.token_urlsafe(32)
            expires = datetime.utcnow() + timedelta(hours=1)
            prt = PasswordResetToken(
                id_usuario=usuario.id_usuario,
                token=token,
                expires_at=expires
            )
            db.session.add(prt)
            db.session.commit()

            # Log
            try:
                log = LogsAcesso(
                    id_usuario=usuario.id_usuario,
                    acao='Solicitação de recuperação de senha',
                    data_hora=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                db.session.rollback()

            # Em produção, o token deve ser enviado por e-mail com link seguro.
            # Tentamos enviar o e-mail; se falhar, ainda retornamos 200 para não vazar existência de contas.
            frontend = os.environ.get('FRONTEND_URL', 'http://localhost:5000')
            reset_path = os.environ.get('RESET_PATH', '/TelaResetSenha.html')
            reset_link = f"{frontend.rstrip('/')}{reset_path}?token={token}"
            assunto = 'Recuperação de senha - Orçamento Serviços'
            corpo = f"Olá {usuario.nome},\n\nRecebemos uma solicitação para redefinir sua senha. Acesse o link abaixo para criar uma nova senha (válido por 1 hora):\n\n{reset_link}\n\nSe você não solicitou, ignore esta mensagem.\n\nAtenciosamente,\nEquipe"

            try:
                ok, msg = send_email(subject=assunto, body=corpo, to=[usuario.email])
                if not ok:
                    # registra no log, mas não falha a resposta para o cliente (idempotência)
                    try:
                        log = LogsAcesso(
                            id_usuario=usuario.id_usuario,
                            acao=f'Falha ao enviar email de recuperação para {usuario.email}: {msg}',
                            data_hora=datetime.utcnow()
                        )
                        db.session.add(log)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
            except Exception:
                # qualquer erro de envio não impede a resposta (mantemos idempotência)
                try:
                    log = LogsAcesso(
                        id_usuario=usuario.id_usuario,
                        acao=f'Exceção ao tentar enviar email de recuperação para {usuario.email}',
                        data_hora=datetime.utcnow()
                    )
                    db.session.add(log)
                    db.session.commit()
                except Exception:
                    db.session.rollback()

            return jsonify({'mensagem': 'Se o email existir, enviaremos instruções.', 'token_teste': token}), 200

        return jsonify({'mensagem': 'Se o email existir, enviaremos instruções.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: RESET DE SENHA
# POST /api/auth/reset-password
# body: { token, nova_senha }
# ========================================
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        dados = request.get_json() or {}
        token = (dados.get('token') or '').strip()
        nova = (dados.get('nova_senha') or '').strip()
        if not token or not nova:
            return jsonify({'erro': 'token e nova_senha são obrigatórios'}), 400
        if len(nova) < 6:
            return jsonify({'erro': 'Senha deve ter pelo menos 6 caracteres'}), 400

        prt = PasswordResetToken.query.filter_by(token=token).first()
        if not prt or prt.used_at is not None or prt.expires_at < datetime.utcnow():
            return jsonify({'erro': 'Token inválido ou expirado'}), 400

        usuario = Usuario.query.get_or_404(prt.id_usuario)
        usuario.definir_senha(nova)
        prt.used_at = datetime.utcnow()

        db.session.commit()

        # Log
        try:
            log = LogsAcesso(
                id_usuario=usuario.id_usuario,
                acao='Senha redefinida por token',
                data_hora=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify({'mensagem': 'Senha redefinida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: OBTER PERFIL DO USUÁRIO
# GET /api/auth/profile
# ========================================
@auth_bp.route('/profile', methods=['GET'])
@login_required
def obter_perfil():
    """
    Obtém os dados do perfil do usuário logado
    Retorna: dados do usuário ou erro
    """
    try:
        return jsonify({
            'usuario': current_user.para_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: ATUALIZAR PERFIL DO USUÁRIO
# PUT /api/auth/profile
# ========================================
@auth_bp.route('/profile', methods=['PUT'])
@login_required
def atualizar_perfil():
    """
    Atualiza as informações do perfil do usuário logado
    Recebe: FormData com nome, email, telefone, status e avatar (opcional)
    Retorna: dados do usuário atualizado ou erro
    """
    try:
        # Pega os dados do formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        status = request.form.get('status', 'Online')
        
        # Validações básicas
        if not nome or not email:
            return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
        
        if len(nome) > 80:
            return jsonify({'erro': 'Nome muito longo (máximo 80 caracteres)'}), 400
        
        if len(email) > 50:
            return jsonify({'erro': 'Email muito longo (máximo 50 caracteres)'}), 400
        
        # Verifica se o email já está sendo usado por outro usuário
        usuario_existente = Usuario.query.filter(
            Usuario.email == email,
            Usuario.id_usuario != current_user.id_usuario
        ).first()
        
        if usuario_existente:
            return jsonify({'erro': 'Este email já está sendo usado por outro usuário'}), 400
        
        # Processa upload de avatar se houver
        if 'avatar' in request.files:
            arquivo = request.files['avatar']
            if arquivo and arquivo.filename:
                # Gera um nome único para o arquivo
                extensao = arquivo.filename.rsplit('.', 1)[1].lower()
                nome_arquivo = f'avatar_{current_user.id_usuario}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.{extensao}'
                
                # Salva o arquivo
                caminho = os.path.join('static', 'uploads', 'avatars', nome_arquivo)
                os.makedirs(os.path.dirname(caminho), exist_ok=True)
                arquivo.save(caminho)
                
                # Atualiza a URL do avatar
                current_user.avatar_url = f'/avatar/{nome_arquivo}'
        
        # Atualiza os dados do usuário
        current_user.nome = nome
        current_user.email = email
        current_user.telefone = telefone
        current_user.status = status
        
        # Salva no banco de dados
        db.session.commit()
        
        # Registra a ação no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao='Perfil atualizado',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        # Retorna sucesso
        return jsonify({
            'mensagem': 'Perfil atualizado com sucesso!',
            'usuario': current_user.para_dict()
        }), 200
        
    except Exception as e:
        # Se deu erro, desfaz as alterações no banco
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: ALTERAR SENHA
# PUT /api/auth/change-password
# ========================================
@auth_bp.route('/change-password', methods=['PUT'])
@login_required
def alterar_senha():
    """
    Permite ao usuário alterar sua própria senha
    Recebe: senha_atual, nova_senha
    Retorna: mensagem de sucesso ou erro
    """
    try:
        # Pega os dados enviados pelo cliente (JSON)
        dados = request.get_json()
        
        # Verifica se foram enviados dados
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        # Extrai os campos
        senha_atual = dados.get('senha_atual')
        nova_senha = dados.get('nova_senha')
        
        # Validações básicas
        if not senha_atual or not nova_senha:
            return jsonify({'erro': 'Senha atual e nova senha são obrigatórias'}), 400
        
        if len(nova_senha) < 6:
            return jsonify({'erro': 'Nova senha deve ter pelo menos 6 caracteres'}), 400
        
        # Verifica se a senha atual está correta
        if not current_user.verificar_senha(senha_atual):
            return jsonify({'erro': 'Senha atual incorreta'}), 401
        
        # Define a nova senha
        current_user.definir_senha(nova_senha)
        
        # Salva no banco de dados
        db.session.commit()
        
        # Registra a ação no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao='Senha alterada',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        # Retorna sucesso
        return jsonify({
            'mensagem': 'Senha alterada com sucesso!'
        }), 200
        
    except Exception as e:
        # Se deu erro, desfaz as alterações no banco
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


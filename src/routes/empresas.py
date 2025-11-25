# ========================================
# CRUD DE EMPRESAS
# Sistema de Orçamentos de Serviços
# ========================================

import os
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from src.models.models import db, Empresa, LogsAcesso
from datetime import datetime

empresas_bp = Blueprint('empresas', __name__)


def _salvar_logo(logo_file):
    if not logo_file or not logo_file.filename:
        return ''
    logos_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'logos')
    logos_dir = os.path.abspath(logos_dir)
    os.makedirs(logos_dir, exist_ok=True)
    filename = secure_filename(logo_file.filename)
    file_path = os.path.join(logos_dir, filename)
    try:
        logo_file.save(file_path)
        return f'logos/{filename}'
    except Exception:
        return ''

# ========================================
# ROTA: LISTAR TODAS AS EMPRESAS
# GET /api/empresas/
# ========================================
@empresas_bp.route('/', methods=['GET'])
@login_required
def listar_empresas():
    try:
        empresas = Empresa.query.all()
        lista_empresas = [empresa.para_dict() for empresa in empresas]
        return jsonify({
            'empresas': lista_empresas,
            'total': len(lista_empresas)
        }), 200
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: CADASTRAR NOVA EMPRESA
# POST /api/empresas/
# ========================================
@empresas_bp.route('/', methods=['POST'])
@login_required
def cadastrar_empresa():
    try:
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            nome = request.form.get('nome')
            cnpj = request.form.get('cnpj')
            telefone = request.form.get('telefone')
            endereco = request.form.get('endereco')
            email = request.form.get('email')
            logo_file = request.files.get('logo')
        else:
            dados = request.get_json()
            if not dados:
                return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
            nome = dados.get('nome')
            cnpj = dados.get('cnpj')
            telefone = dados.get('telefone')
            endereco = dados.get('endereco')
            email = dados.get('email')
            logo_file = None

        nome = (nome or '').strip()
        cnpj_numeros = ''.join(filter(str.isdigit, (cnpj or '')))
        telefone_numeros = ''.join(filter(str.isdigit, (telefone or '')))
        endereco = (endereco or '').strip()
        email = (email or '').strip()

        if not nome:
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        if len(cnpj_numeros) != 14:
            return jsonify({'erro': 'CNPJ inválido. Informe 14 dígitos.'}), 400
        if len(telefone_numeros) != 11:
            return jsonify({'erro': 'Telefone inválido. Informe 11 dígitos.'}), 400
        if not email:
            return jsonify({'erro': 'E-mail é obrigatório.'}), 400

        # Evita duplicidade de CNPJ com mensagem amigável
        empresa_existente = Empresa.query.filter_by(cnpj=cnpj_numeros).first()
        if empresa_existente:
            return jsonify({'erro': 'CNPJ já cadastrado.'}), 400

        logo_path = _salvar_logo(logo_file)

        nova_empresa = Empresa(
            nome=nome,
            cnpj=cnpj_numeros,
            telefone=telefone_numeros,
            endereco=endereco,
            email=email,
            logo=logo_path
        )
        db.session.add(nova_empresa)
        db.session.commit()

        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Empresa cadastrada: {nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'mensagem': 'Empresa cadastrada com sucesso!',
            'empresa': nova_empresa.para_dict()
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'erro': 'Não foi possível salvar. Verifique se o CNPJ já está cadastrado.'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: EXCLUIR EMPRESA
# DELETE /api/empresas/<id_empresa>
# ========================================
@empresas_bp.route('/<int:id_empresa>', methods=['DELETE'])
@login_required
def excluir_empresa(id_empresa):
    try:
        empresa = Empresa.query.get_or_404(id_empresa)
        db.session.delete(empresa)
        db.session.commit()
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Empresa excluída: {empresa.nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'mensagem': 'Empresa excluída com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: OBTER EMPRESA POR ID
# GET /api/empresas/<id_empresa>
# ========================================
@empresas_bp.route('/<int:id_empresa>', methods=['GET'])
@login_required
def obter_empresa(id_empresa):
    try:
        empresa = Empresa.query.get_or_404(id_empresa)
        return jsonify({'empresa': empresa.para_dict()}), 200
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: ATUALIZAR EMPRESA
# PUT /api/empresas/<id_empresa>
# ========================================
@empresas_bp.route('/<int:id_empresa>', methods=['PUT'])
@login_required
def atualizar_empresa(id_empresa):
    try:
        empresa = Empresa.query.get_or_404(id_empresa)

        if request.content_type and request.content_type.startswith('multipart/form-data'):
            nome = request.form.get('nome', empresa.nome)
            cnpj = request.form.get('cnpj', empresa.cnpj)
            telefone = request.form.get('telefone', empresa.telefone)
            endereco = request.form.get('endereco', empresa.endereco)
            email = request.form.get('email', empresa.email)
            logo_file = request.files.get('logo')
        else:
            dados = request.get_json() or {}
            nome = dados.get('nome', empresa.nome)
            cnpj = dados.get('cnpj', empresa.cnpj)
            telefone = dados.get('telefone', empresa.telefone)
            endereco = dados.get('endereco', empresa.endereco)
            email = dados.get('email', empresa.email)
            logo_file = None

        nome = (nome or '').strip()
        cnpj_numeros = ''.join(filter(str.isdigit, (cnpj or '')))
        telefone_numeros = ''.join(filter(str.isdigit, (telefone or '')))
        endereco = (endereco or '').strip()
        email = (email or '').strip()

        if not nome:
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        if len(cnpj_numeros) != 14:
            return jsonify({'erro': 'CNPJ inválido. Informe 14 dígitos.'}), 400
        if len(telefone_numeros) != 11:
            return jsonify({'erro': 'Telefone inválido. Informe 11 dígitos.'}), 400
        if not email:
            return jsonify({'erro': 'E-mail é obrigatório.'}), 400

        if cnpj_numeros != empresa.cnpj:
            existe = Empresa.query.filter(Empresa.cnpj == cnpj_numeros, Empresa.id_empresa != id_empresa).first()
            if existe:
                return jsonify({'erro': 'CNPJ já cadastrado.'}), 400

        if logo_file and logo_file.filename:
            novo_logo = _salvar_logo(logo_file)
            if novo_logo:
                empresa.logo = novo_logo

        empresa.nome = nome
        empresa.cnpj = cnpj_numeros
        empresa.telefone = telefone_numeros
        empresa.endereco = endereco
        empresa.email = email

        db.session.commit()

        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Empresa atualizada: {empresa.nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'mensagem': 'Empresa atualizada com sucesso!', 'empresa': empresa.para_dict()}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'erro': 'Não foi possível salvar. Verifique se o CNPJ já está cadastrado.'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# CRUD DE SERVIÇOS
# Sistema de Orçamentos de Serviços
# ========================================

# Importações necessárias
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models.models import db, Servico, LogsAcesso
from datetime import datetime
from decimal import Decimal

# Cria um blueprint para as rotas de serviços
servicos_bp = Blueprint('servicos', __name__)

# ========================================
# ROTA: LISTAR TODOS OS SERVIÇOS
# GET /api/servicos/
# ========================================
@servicos_bp.route('/', methods=['GET'])
@login_required
def listar_servicos():
    """
    Lista todos os serviços cadastrados
    Retorna: lista com todos os serviços
    """
    try:
        # Busca todos os serviços no banco
        servicos = Servico.query.filter_by(id_usuario=current_user.id_usuario).all()
        
        # Converte para formato JSON
        lista_servicos = [servico.para_dict() for servico in servicos]
        
        return jsonify({
            'servicos': lista_servicos,
            'total': len(lista_servicos)
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: BUSCAR UM SERVIÇO ESPECÍFICO
# GET /api/servicos/<id>
# ========================================
@servicos_bp.route('/<int:id_servico>', methods=['GET'])
@login_required
def buscar_servico(id_servico):
    """
    Busca um serviço específico pelo ID
    Parâmetro: id_servico (número)
    Retorna: dados do serviço ou erro se não encontrar
    """
    try:
        # Busca o serviço pelo ID
        servico = Servico.query.filter_by(id_servicos=id_servico, id_usuario=current_user.id_usuario).first_or_404()
        
        return jsonify({
            'servico': servico.para_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: CADASTRAR NOVO SERVIÇO
# POST /api/servicos/
# ========================================
@servicos_bp.route('/', methods=['POST'])
@login_required
def cadastrar_servico():
    """
    Cadastra um novo serviço
    Recebe: nome (obrigatório), descricao (opcional), valor (obrigatório)
    Retorna: dados do serviço criado ou erro
    """
    try:
        # Pega os dados enviados
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        # Extrai os campos
        nome = dados.get('nome')
        descricao = dados.get('descricao')
        valor = dados.get('valor')
        
        # Validações básicas
        if not nome:
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        
        if len(nome) > 80:
            return jsonify({'erro': 'Nome muito longo (máximo 80 caracteres)'}), 400
        
        if descricao and len(descricao) > 255:
            return jsonify({'erro': 'Descrição muito longa (máximo 255 caracteres)'}), 400
        
        if not valor:
            return jsonify({'erro': 'Valor é obrigatório'}), 400
        
        # Valida o valor (deve ser um número positivo)
        try:
            valor_decimal = Decimal(str(valor))
            if valor_decimal < 0:
                return jsonify({'erro': 'Valor deve ser positivo'}), 400
        except (ValueError, TypeError):
            return jsonify({'erro': 'Valor deve ser um número válido'}), 400
        
        # Cria o novo serviço
        novo_servico = Servico(
            nome=nome,
            descricao=descricao,
            valor=valor_decimal,
            id_usuario=current_user.id_usuario
        )
        
        # Salva no banco
        db.session.add(novo_servico)
        db.session.commit()
        
        # Registra no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Serviço cadastrado: {nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Serviço cadastrado com sucesso!',
            'servico': novo_servico.para_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: ATUALIZAR SERVIÇO
# PUT /api/servicos/<id>
# ========================================
@servicos_bp.route('/<int:id_servico>', methods=['PUT'])
@login_required
def atualizar_servico(id_servico):
    """
    Atualiza os dados de um serviço existente
    Parâmetro: id_servico (número)
    Recebe: campos a serem atualizados
    Retorna: dados do serviço atualizado ou erro
    """
    try:
        # Busca o serviço
        servico = Servico.query.filter_by(id_servicos=id_servico, id_usuario=current_user.id_usuario).first_or_404()
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        # Atualiza apenas os campos enviados
        if 'nome' in dados:
            nome = dados['nome']
            if not nome:
                return jsonify({'erro': 'Nome não pode ser vazio'}), 400
            if len(nome) > 80:
                return jsonify({'erro': 'Nome muito longo (máximo 80 caracteres)'}), 400
            servico.nome = nome
        
        if 'descricao' in dados:
            descricao = dados['descricao']
            if descricao and len(descricao) > 255:
                return jsonify({'erro': 'Descrição muito longa (máximo 255 caracteres)'}), 400
            servico.descricao = descricao
        
        if 'valor' in dados:
            valor = dados['valor']
            try:
                valor_decimal = Decimal(str(valor))
                if valor_decimal < 0:
                    return jsonify({'erro': 'Valor deve ser positivo'}), 400
                servico.valor = valor_decimal
            except (ValueError, TypeError):
                return jsonify({'erro': 'Valor deve ser um número válido'}), 400
        
        # Salva as alterações
        db.session.commit()
        
        # Registra no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Serviço atualizado: {servico.nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Serviço atualizado com sucesso!',
            'servico': servico.para_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: EXCLUIR SERVIÇO
# DELETE /api/servicos/<id>
# ========================================
@servicos_bp.route('/<int:id_servico>', methods=['DELETE'])
@login_required
def excluir_servico(id_servico):
    """
    Exclui um serviço do sistema
    Parâmetro: id_servico (número)
    Retorna: mensagem de sucesso ou erro
    
    ATENÇÃO: Não permite excluir serviço que está em orçamentos
    """
    try:
        # Busca o serviço
        servico = Servico.query.filter_by(id_servicos=id_servico, id_usuario=current_user.id_usuario).first_or_404()
        nome_servico = servico.nome
        
        # Verifica se o serviço está sendo usado em orçamentos
        if servico.orcamento_servicos:
            return jsonify({
                'erro': 'Não é possível excluir serviço que está sendo usado em orçamentos'
            }), 400
        
        # Exclui o serviço
        db.session.delete(servico)
        db.session.commit()
        
        # Registra no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Serviço excluído: {nome_servico}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Serviço "{nome_servico}" excluído com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


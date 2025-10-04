# ========================================
# CRUD DE CLIENTES
# Sistema de Orçamentos de Serviços
# ========================================

# Importações necessárias
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models.models import db, Cliente, LogsAcesso, Endereco
from datetime import datetime

# Cria um blueprint para as rotas de clientes
clientes_bp = Blueprint('clientes', __name__)

# ========================================
# ROTA: LISTAR TODOS OS CLIENTES
# GET /api/clientes/
# ========================================
@clientes_bp.route('/', methods=['GET'])
@login_required  # Só funciona se estiver logado
def listar_clientes():
    """
    Lista todos os clientes cadastrados
    Retorna: lista com todos os clientes
    """
    try:
        # Busca todos os clientes no banco
        clientes = Cliente.query.all()
        
        # Converte para formato JSON
        lista_clientes = [cliente.para_dict() for cliente in clientes]
        
        return jsonify({
            'clientes': lista_clientes,
            'total': len(lista_clientes)
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: BUSCAR UM CLIENTE ESPECÍFICO
# GET /api/clientes/<id>
# ========================================
@clientes_bp.route('/<int:id_cliente>', methods=['GET'])
@login_required
def buscar_cliente(id_cliente):
    """
    Busca um cliente específico pelo ID
    Parâmetro: id_cliente (número)
    Retorna: dados do cliente ou erro se não encontrar
    """
    try:
        # Busca o cliente pelo ID (retorna erro 404 se não encontrar)
        cliente = Cliente.query.get_or_404(id_cliente)
        
        return jsonify({
            'cliente': cliente.para_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: CADASTRAR NOVO CLIENTE
# POST /api/clientes/
# ========================================
@clientes_bp.route('/', methods=['POST'])
@login_required
def cadastrar_cliente():
    """
    Cadastra um novo cliente
    Recebe: nome (obrigatório), telefone, email, endereco (opcionais)
    Retorna: dados do cliente criado ou erro
    """
    try:
        # Pega os dados enviados
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        # Extrai os campos
        nome = dados.get('nome')
        telefone = dados.get('telefone')
        email = dados.get('email')
        endereco = dados.get('endereco')
        
        # Validações
        if not nome:
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        
        if len(nome) > 80:
            return jsonify({'erro': 'Nome muito longo (máximo 80 caracteres)'}), 400
        
        if telefone and len(telefone) > 11:
            return jsonify({'erro': 'Telefone muito longo (máximo 11 caracteres)'}), 400
        
        if email and len(email) > 50:
            return jsonify({'erro': 'Email muito longo (máximo 50 caracteres)'}), 400
        
        if endereco and len(endereco) > 55:
            return jsonify({'erro': 'Endereço muito longo (máximo 55 caracteres)'}), 400
        
        # Cria o novo cliente
        novo_cliente = Cliente(
            nome=nome,
            telefone=telefone,
            email=email,
            endereco=endereco
        )
        
        # Salva no banco
        db.session.add(novo_cliente)
        db.session.commit()
        
        # Registra no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Cliente cadastrado: {nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Cliente cadastrado com sucesso!',
            'cliente': novo_cliente.para_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: ATUALIZAR CLIENTE
# PUT /api/clientes/<id>
# ========================================
@clientes_bp.route('/<int:id_cliente>', methods=['PUT'])
@login_required
def atualizar_cliente(id_cliente):
    """
    Atualiza os dados de um cliente existente
    Parâmetro: id_cliente (número)
    Recebe: campos a serem atualizados
    Retorna: dados do cliente atualizado ou erro
    """
    try:
        # Busca o cliente
        cliente = Cliente.query.get_or_404(id_cliente)
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
            cliente.nome = nome
        
        if 'telefone' in dados:
            telefone = dados['telefone']
            if telefone and len(telefone) > 11:
                return jsonify({'erro': 'Telefone muito longo (máximo 11 caracteres)'}), 400
            cliente.telefone = telefone
        
        if 'email' in dados:
            email = dados['email']
            if email and len(email) > 50:
                return jsonify({'erro': 'Email muito longo (máximo 50 caracteres)'}), 400
            cliente.email = email
        
        if 'endereco' in dados:
            endereco = dados['endereco']
            if endereco and len(endereco) > 55:
                return jsonify({'erro': 'Endereço muito longo (máximo 55 caracteres)'}), 400
            cliente.endereco = endereco
        
        # Salva as alterações
        db.session.commit()
        
        # Registra no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Cliente atualizado: {cliente.nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Cliente atualizado com sucesso!',
            'cliente': cliente.para_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: EXCLUIR CLIENTE
# DELETE /api/clientes/<id>
# ========================================
@clientes_bp.route('/<int:id_cliente>', methods=['DELETE'])
@login_required
def excluir_cliente(id_cliente):
    """
    Exclui um cliente do sistema
    Parâmetro: id_cliente (número)
    Retorna: mensagem de sucesso ou erro
    
    ATENÇÃO: Não permite excluir cliente que tem orçamentos
    """
    try:
        # Busca o cliente
        cliente = Cliente.query.get_or_404(id_cliente)
        nome_cliente = cliente.nome
        
        # Verifica se o cliente tem orçamentos
        if cliente.orcamentos:
            return jsonify({
                'erro': 'Não é possível excluir cliente que possui orçamentos cadastrados'
            }), 400
        
        # Exclui o cliente
        db.session.delete(cliente)
        db.session.commit()
        
        # Registra no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Cliente excluído: {nome_cliente}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Cliente "{nome_cliente}" excluído com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ENDEREÇOS DO CLIENTE (múltiplos endereços)
# ========================================

@clientes_bp.route('/<int:id_cliente>/enderecos', methods=['GET'])
@login_required
def listar_enderecos(id_cliente):
    try:
        cliente = Cliente.query.get_or_404(id_cliente)
        enderecos = [e.para_dict() for e in cliente.enderecos]
        return jsonify({'enderecos': enderecos, 'total': len(enderecos)}), 200
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


@clientes_bp.route('/<int:id_cliente>/enderecos', methods=['POST'])
@login_required
def criar_endereco(id_cliente):
    try:
        Cliente.query.get_or_404(id_cliente)
        dados = request.get_json() or {}

        logradouro = (dados.get('logradouro') or '').strip()
        if not logradouro:
            return jsonify({'erro': 'logradouro é obrigatório'}), 400

        end = Endereco(
            id_cliente=id_cliente,
            logradouro=logradouro,
            numero=dados.get('numero'),
            complemento=dados.get('complemento'),
            bairro=dados.get('bairro'),
            cidade=dados.get('cidade'),
            uf=dados.get('uf'),
            cep=dados.get('cep'),
            apelido=dados.get('apelido'),
            is_padrao=bool(dados.get('is_padrao', False)),
        )
        if end.is_padrao:
            Endereco.query.filter_by(id_cliente=id_cliente, is_padrao=True).update({'is_padrao': False})
        db.session.add(end)
        db.session.commit()

        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Endereço criado para cliente {id_cliente}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'mensagem': 'Endereço criado com sucesso!', 'endereco': end.para_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


@clientes_bp.route('/<int:id_cliente>/enderecos/<int:id_endereco>', methods=['PUT'])
@login_required
def atualizar_endereco(id_cliente, id_endereco):
    try:
        end = Endereco.query.filter_by(id_cliente=id_cliente, id_endereco=id_endereco).first_or_404()
        dados = request.get_json() or {}

        if 'logradouro' in dados:
            logradouro = (dados.get('logradouro') or '').strip()
            if not logradouro:
                return jsonify({'erro': 'logradouro não pode ser vazio'}), 400
            end.logradouro = logradouro
        if 'numero' in dados:
            end.numero = dados.get('numero')
        if 'complemento' in dados:
            end.complemento = dados.get('complemento')
        if 'bairro' in dados:
            end.bairro = dados.get('bairro')
        if 'cidade' in dados:
            end.cidade = dados.get('cidade')
        if 'uf' in dados:
            uf = dados.get('uf')
            end.uf = uf[:2] if uf else None
        if 'cep' in dados:
            end.cep = dados.get('cep')
        if 'apelido' in dados:
            end.apelido = dados.get('apelido')
        if 'is_padrao' in dados:
            is_padrao = bool(dados.get('is_padrao'))
            if is_padrao:
                Endereco.query.filter_by(id_cliente=id_cliente, is_padrao=True).update({'is_padrao': False})
            end.is_padrao = is_padrao

        db.session.commit()

        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Endereço atualizado {id_endereco} do cliente {id_cliente}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'mensagem': 'Endereço atualizado com sucesso!', 'endereco': end.para_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


@clientes_bp.route('/<int:id_cliente>/enderecos/<int:id_endereco>', methods=['DELETE'])
@login_required
def excluir_endereco(id_cliente, id_endereco):
    try:
        end = Endereco.query.filter_by(id_cliente=id_cliente, id_endereco=id_endereco).first_or_404()
        db.session.delete(end)
        db.session.commit()

        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Endereço excluído {id_endereco} do cliente {id_cliente}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'mensagem': 'Endereço excluído com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


@clientes_bp.route('/<int:id_cliente>/enderecos/<int:id_endereco>/definir-padrao', methods=['PUT'])
@login_required
def definir_endereco_padrao(id_cliente, id_endereco):
    try:
        Endereco.query.filter_by(id_cliente=id_cliente, is_padrao=True).update({'is_padrao': False})
        end = Endereco.query.filter_by(id_cliente=id_cliente, id_endereco=id_endereco).first_or_404()
        end.is_padrao = True
        db.session.commit()

        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Endereço {id_endereco} definido como padrão do cliente {id_cliente}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'mensagem': 'Endereço definido como padrão com sucesso!', 'endereco': end.para_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


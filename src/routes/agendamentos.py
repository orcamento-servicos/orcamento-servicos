# ========================================
# ROTAS DE AGENDAMENTOS
# Sistema de Orçamentos de Serviços
# ========================================

# Importações necessárias
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models.models import db, Agendamento, Servico, LogsAcesso
from datetime import datetime

# Cria um blueprint (grupo de rotas) para agendamentos
agendamentos_bp = Blueprint('agendamentos', __name__)

# ========================================
# ROTA: LISTAR AGENDAMENTOS
# GET /api/agendamentos/
# ========================================
@agendamentos_bp.route('/', methods=['GET'])
@login_required
def listar_agendamentos():
    """
    Lista todos os agendamentos do usuário logado
    Query params opcionais: status, busca
    Retorna: lista de agendamentos ou erro
    """
    try:
        # Parâmetros de filtro
        status_filtro = request.args.get('status')
        busca = request.args.get('busca', '').strip().lower()
        
        # Query base
        query = Agendamento.query.filter_by(id_usuario=current_user.id_usuario)
        
        # Aplica filtro de status se fornecido
        if status_filtro:
            query = query.filter_by(status=status_filtro)
        
        # Aplica filtro de busca se fornecido
        if busca:
            query = query.join(Servico).filter(
                db.or_(
                    Servico.nome.ilike(f'%{busca}%'),
                    Agendamento.observacoes.ilike(f'%{busca}%')
                )
            )
        
        # Ordena por data/hora (mais próximos primeiro)
        agendamentos = query.order_by(Agendamento.data_hora.asc()).all()
        
        # Converte para JSON
        agendamentos_json = [ag.para_dict() for ag in agendamentos]
        
        return jsonify({
            'agendamentos': agendamentos_json,
            'total': len(agendamentos_json)
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: CRIAR AGENDAMENTO
# POST /api/agendamentos/
# ========================================
@agendamentos_bp.route('/', methods=['POST'])
@login_required
def criar_agendamento():
    """
    Cria um novo agendamento
    Recebe: id_servico, data_hora, observacoes (opcional)
    Retorna: dados do agendamento criado ou erro
    """
    try:
        # Pega os dados enviados pelo cliente (JSON)
        dados = request.get_json()
        
        # Verifica se foram enviados dados
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        # Extrai os campos necessários
        id_servico = dados.get('id_servico')
        data_hora_str = dados.get('data_hora')
        observacoes = dados.get('observacoes', '')
        
        # Validações básicas
        if not id_servico:
            return jsonify({'erro': 'ID do serviço é obrigatório'}), 400
        
        if not data_hora_str:
            return jsonify({'erro': 'Data e hora são obrigatórias'}), 400
        
        # Verifica se o serviço existe
        servico = Servico.query.get(id_servico)
        if not servico:
            return jsonify({'erro': 'Serviço não encontrado'}), 404
        
        # Converte a string de data/hora para datetime
        try:
            data_hora = datetime.fromisoformat(data_hora_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'erro': 'Formato de data/hora inválido'}), 400
        
        # Verifica se a data não é no passado
        if data_hora < datetime.utcnow():
            return jsonify({'erro': 'Não é possível agendar para datas passadas'}), 400
        
        # Cria um novo agendamento
        novo_agendamento = Agendamento(
            id_servico=id_servico,
            id_usuario=current_user.id_usuario,
            data_hora=data_hora,
            valor=servico.valor,  # Valor do serviço na época do agendamento
            observacoes=observacoes,
            status='Agendado'
        )
        
        # Salva no banco de dados
        db.session.add(novo_agendamento)
        db.session.commit()
        
        # Registra a ação no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Agendamento criado: {servico.nome} para {data_hora.strftime("%d/%m/%Y %H:%M")}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        # Retorna sucesso
        return jsonify({
            'mensagem': 'Agendamento criado com sucesso!',
            'agendamento': novo_agendamento.para_dict()
        }), 201
        
    except Exception as e:
        # Se deu erro, desfaz as alterações no banco
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: ATUALIZAR STATUS DO AGENDAMENTO
# PUT /api/agendamentos/<id>/status
# ========================================
@agendamentos_bp.route('/<int:id_agendamento>/status', methods=['PUT'])
@login_required
def atualizar_status_agendamento(id_agendamento):
    """
    Atualiza o status de um agendamento
    Recebe: status (Concluído, Cancelado, Agendado)
    Retorna: dados do agendamento atualizado ou erro
    """
    try:
        # Pega os dados enviados
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        novo_status = dados.get('status')
        
        # Validações
        if not novo_status:
            return jsonify({'erro': 'Status é obrigatório'}), 400
        
        status_validos = ['Agendado', 'Concluído', 'Cancelado']
        if novo_status not in status_validos:
            return jsonify({'erro': f'Status inválido. Use: {", ".join(status_validos)}'}), 400
        
        # Busca o agendamento
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        # Atualiza o status
        status_anterior = agendamento.status
        agendamento.status = novo_status
        agendamento.updated_at = datetime.utcnow()
        
        # Salva no banco
        db.session.commit()
        
        # Registra a ação no log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Status do agendamento alterado: {status_anterior} → {novo_status}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        # Retorna sucesso
        return jsonify({
            'mensagem': f'Status alterado para {novo_status} com sucesso!',
            'agendamento': agendamento.para_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: OBTER DETALHES DO AGENDAMENTO / ATUALIZAR / EXCLUIR
# /api/agendamentos/<id_agendamento>
# ========================================
@agendamentos_bp.route('/<int:id_agendamento>', methods=['GET'])
@login_required
def obter_agendamento(id_agendamento):
    """
    Obtém os detalhes de um agendamento específico
    Retorna: dados do agendamento ou erro
    """
    try:
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        return jsonify({'agendamento': agendamento.para_dict()}), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


@agendamentos_bp.route('/<int:id_agendamento>', methods=['PUT'])
@login_required
def atualizar_agendamento(id_agendamento):
    """
    Atualiza os detalhes completos de um agendamento
    Recebe: data_hora, status, observacoes, endereco, tecnico, id_cliente, 
            lembrete_cliente, lembrete_tecnico, solicitar_confirmacao, recorrencia
    Retorna: dados do agendamento atualizado ou erro
    """
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        # Busca o agendamento
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        # Atualiza campos permitidos
        if 'data_hora' in dados and dados['data_hora']:
            try:
                data_hora = datetime.fromisoformat(dados['data_hora'].replace('Z', '+00:00'))
                agendamento.data_hora = data_hora
            except ValueError:
                return jsonify({'erro': 'Formato de data/hora inválido'}), 400
        
        if 'status' in dados:
            status_validos = ['Agendado', 'Confirmado', 'Em Andamento', 'Concluído', 'Cancelado']
            if dados['status'] not in status_validos:
                return jsonify({'erro': f'Status inválido. Use: {", ".join(status_validos)}'}), 400
            agendamento.status = dados['status']
        
        if 'observacoes' in dados:
            agendamento.observacoes = dados.get('observacoes', '')
        
        # Campos adicionais (armazenados como observações ou em novos campos se necessário)
        # Para agora, vamos apenas registrar no histórico
        if 'endereco' in dados:
            endereco_info = f"\n[Endereço: {dados['endereco']}]" if dados['endereco'] else ""
            if endereco_info and endereco_info not in (agendamento.observacoes or ''):
                agendamento.observacoes = (agendamento.observacoes or '') + endereco_info
        
        if 'tecnico' in dados:
            tecnico_info = f"\n[Técnico: {dados['tecnico']}]" if dados['tecnico'] else ""
            if tecnico_info and tecnico_info not in (agendamento.observacoes or ''):
                agendamento.observacoes = (agendamento.observacoes or '') + tecnico_info
        
        # Atualiza timestamp
        agendamento.updated_at = datetime.utcnow()
        
        # Salva
        db.session.commit()
        
        # Registra log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Agendamento atualizado: {agendamento.servico.nome if agendamento.servico else "N/A"}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Agendamento atualizado com sucesso!',
            'agendamento': agendamento.para_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


@agendamentos_bp.route('/<int:id_agendamento>', methods=['DELETE'])
@login_required
def excluir_agendamento(id_agendamento):
    """
    Exclui definitivamente um agendamento do usuário logado.
    """
    try:
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()

        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404

        servico_nome = agendamento.servico.nome if agendamento.servico else None

        db.session.delete(agendamento)
        db.session.commit()

        # Loga a exclusão
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Agendamento excluído: {servico_nome or agendamento.id_agendamento}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'mensagem': 'Agendamento excluído com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

# ========================================
# ROTA: EXCLUIR AGENDAMENTO
# DELETE /api/agendamentos/<id>
# ========================================
@agendamentos_bp.route('/<int:id_agendamento>', methods=['DELETE'])
@login_required
def excluir_agendamento(id_agendamento):
    """
    Exclui um agendamento
    Retorna: mensagem de sucesso ou erro
    """
    try:
        # Busca o agendamento
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        # Registra a ação no log antes de excluir
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Agendamento excluído: {agendamento.servico.nome if agendamento.servico else "N/A"}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        
        # Remove o agendamento
        db.session.delete(agendamento)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Agendamento excluído com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

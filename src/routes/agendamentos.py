# ========================================
# ROTAS DE AGENDAMENTOS
# ========================================

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models.models import db, Agendamento, Servico, LogsAcesso
from datetime import datetime

agendamentos_bp = Blueprint('agendamentos', __name__)

@agendamentos_bp.route('/', methods=['GET'])
@login_required
def listar_agendamentos():
    try:
        status_filtro = request.args.get('status')
        busca = request.args.get('busca', '').strip().lower()
        query = Agendamento.query.filter_by(id_usuario=current_user.id_usuario)
        
        if status_filtro:
            query = query.filter_by(status=status_filtro)
        if busca:
            query = query.join(Servico).filter(
                db.or_(
                    Servico.nome.ilike(f'%{busca}%'),
                    Agendamento.observacoes.ilike(f'%{busca}%')
                )
            )
        agendamentos = query.order_by(Agendamento.data_hora.asc()).all()
        agendamentos_json = [ag.para_dict() for ag in agendamentos]
        
        return jsonify({
            'agendamentos': agendamentos_json,
            'total': len(agendamentos_json)
        }), 200
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

@agendamentos_bp.route('/', methods=['POST'])
@login_required
def criar_agendamento():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        id_servico = dados.get('id_servico')
        data_hora_str = dados.get('data_hora')
        observacoes = dados.get('observacoes', '')
        
        if not id_servico:
            return jsonify({'erro': 'ID do serviço é obrigatório'}), 400
        
        if not data_hora_str:
            return jsonify({'erro': 'Data e hora são obrigatórias'}), 400
        
        servico = Servico.query.get(id_servico)
        if not servico:
            return jsonify({'erro': 'Serviço não encontrado'}), 404
        
        try:
            data_hora = datetime.fromisoformat(data_hora_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'erro': 'Formato de data/hora inválido'}), 400
        
        if data_hora < datetime.utcnow():
            return jsonify({'erro': 'Não é possível agendar para datas passadas'}), 400
        
        novo_agendamento = Agendamento(
            id_servico=id_servico,
            id_usuario=current_user.id_usuario,
            data_hora=data_hora,
            valor=servico.valor,
            observacoes=observacoes,
            status='Agendado'
        )
        
        db.session.add(novo_agendamento)
        db.session.commit()
        
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Agendamento criado: {servico.nome} para {data_hora.strftime("%d/%m/%Y %H:%M")}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Agendamento criado com sucesso!',
            'agendamento': novo_agendamento.para_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

@agendamentos_bp.route('/<int:id_agendamento>/status', methods=['PUT'])
@login_required
def atualizar_status_agendamento(id_agendamento):
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        novo_status = dados.get('status')
        if not novo_status:
            return jsonify({'erro': 'Status é obrigatório'}), 400
        
        status_validos = ['Agendado', 'Concluído', 'Cancelado']
        if novo_status not in status_validos:
            return jsonify({'erro': f'Status inválido. Use: {", ".join(status_validos)}'}), 400
        
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        status_anterior = agendamento.status
        agendamento.status = novo_status
        agendamento.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Status do agendamento alterado: {status_anterior} → {novo_status}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Status alterado para {novo_status} com sucesso!',
            'agendamento': agendamento.para_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

@agendamentos_bp.route('/<int:id_agendamento>', methods=['GET'])
@login_required
def obter_agendamento(id_agendamento):
    try:
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        return jsonify({
            'agendamento': agendamento.para_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500

@agendamentos_bp.route('/<int:id_agendamento>', methods=['PUT'])
@login_required
def atualizar_agendamento(id_agendamento):
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400
        
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
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
        
        if 'endereco' in dados:
            endereco_info = f"\n[Endereço: {dados['endereco']}]" if dados['endereco'] else ""
            if endereco_info and endereco_info not in (agendamento.observacoes or ''):
                agendamento.observacoes = (agendamento.observacoes or '') + endereco_info
        
        if 'tecnico' in dados:
            tecnico_info = f"\n[Técnico: {dados['tecnico']}]" if dados['tecnico'] else ""
            if tecnico_info and tecnico_info not in (agendamento.observacoes or ''):
                agendamento.observacoes = (agendamento.observacoes or '') + tecnico_info
        
        agendamento.updated_at = datetime.utcnow()
        db.session.commit()
        
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
    try:
        agendamento = Agendamento.query.filter_by(
            id_agendamento=id_agendamento,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Agendamento excluído: {agendamento.servico.nome if agendamento.servico else "N/A"}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        
        db.session.delete(agendamento)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Agendamento excluído com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500
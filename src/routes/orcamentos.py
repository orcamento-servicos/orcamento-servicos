# ========================================
# ROTAS DE ORÇAMENTOS (RF003, RF004, RF005, RF006)
# Sistema de Orçamentos de Serviços
# ========================================

# Importações necessárias
from flask import Blueprint, request, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
import os
import base64
import secrets
import smtplib
from email.message import EmailMessage

from src.models.models import (
    db,
    Cliente,
    Servico,
    Orcamento,
    OrcamentoServicos,
    LogsAcesso,
    Venda,
    VendaItem,
)

try:
    from weasyprint import HTML, CSS  # Sugestão conforme RNF004
    WEASYPRINT_AVAILABLE = True
except Exception:
    # Mantém a API funcional mesmo sem o pacote para outras rotas
    WEASYPRINT_AVAILABLE = False


# Cria um blueprint para as rotas de orçamentos
orcamentos_bp = Blueprint('orcamentos', __name__)


# ========================================
# ROTA: CRIAR ORÇAMENTO
# POST /api/orcamentos/
# RF003: Criação de orçamentos selecionando cliente e múltiplos serviços
# ========================================
@orcamentos_bp.route('/', methods=['POST'])
@login_required
def criar_orcamento():
    """
    Cria um novo orçamento a partir de um cliente e uma lista de serviços.
    Payload esperado (JSON):
    {
      "id_cliente": number,
      "itens": [
        {"id_servico": number, "quantidade": number >= 1}, ...
      ]
    }
    Calcula automaticamente o valor total somando (quantidade × valor_unitario) por item.
    Registra log de acesso na criação.
    """
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400

        id_cliente = dados.get('id_cliente')
        itens = dados.get('itens', [])

        # Validações básicas
        if not id_cliente:
            return jsonify({'erro': 'id_cliente é obrigatório'}), 400
        if not isinstance(itens, list) or len(itens) == 0:
            return jsonify({'erro': 'Lista de itens é obrigatória e não pode ser vazia'}), 400

        # Verifica cliente
        cliente = Cliente.query.get_or_404(id_cliente)

        # Agrega itens duplicados somando quantidades e valida IDs e quantidades
        mapa_quantidades = {}
        for item in itens:
            id_servico = item.get('id_servico')
            quantidade = item.get('quantidade', 1)
            if not id_servico:
                return jsonify({'erro': 'Cada item deve conter id_servico'}), 400
            if not isinstance(quantidade, int):
                return jsonify({'erro': 'quantidade deve ser inteiro válido'}), 400
            if quantidade < 1:
                return jsonify({'erro': 'quantidade deve ser maior ou igual a 1'}), 400
            mapa_quantidades[id_servico] = mapa_quantidades.get(id_servico, 0) + quantidade

        # Monta os itens com dados do serviço atual e calcula totais
        valor_total = Decimal('0.00')
        itens_calculados = []
        for id_servico, quantidade_total in mapa_quantidades.items():
            servico = Servico.query.get_or_404(id_servico)
            valor_unitario = Decimal(str(servico.valor))
            subtotal = (valor_unitario * quantidade_total)
            valor_total += subtotal
            itens_calculados.append({
                'id_servico': servico.id_servicos,
                'quantidade': quantidade_total,
                'valor_unitario': valor_unitario,
                'subtotal': subtotal
            })

        # Cria o orçamento
        novo_orcamento = Orcamento(
            id_cliente=cliente.id_cliente,
            id_usuario=current_user.id_usuario,
            data_criacao=datetime.utcnow(),
            valor_total=valor_total
        )
        db.session.add(novo_orcamento)
        db.session.flush()  # Gera id_orcamento para relacionar itens

        # Cria os itens do orçamento
        for ic in itens_calculados:
            item_orc = OrcamentoServicos(
                id_orcamento=novo_orcamento.id_orcamento,
                id_servico=ic['id_servico'],
                quantidade=ic['quantidade'],
                valor_unitario=ic['valor_unitario'],
                subtotal=ic['subtotal']
            )
            db.session.add(item_orc)

        # Salva tudo
        db.session.commit()

        # Log de criação
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Orçamento criado (ID {novo_orcamento.id_orcamento}) para cliente {cliente.nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        # Monta resposta detalhada
        itens_resp = []
        for rel in OrcamentoServicos.query.filter_by(id_orcamento=novo_orcamento.id_orcamento).all():
            itens_resp.append(rel.para_dict())

        return jsonify({
            'mensagem': 'Orçamento criado com sucesso!',
            'orcamento': novo_orcamento.para_dict(),
            'itens': itens_resp
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: LISTAR ORÇAMENTOS
# GET /api/orcamentos/
# RF004: Listagem de todos os orçamentos
# ========================================
@orcamentos_bp.route('/', methods=['GET'])
@login_required
def listar_orcamentos():
    """
    Lista todos os orçamentos com informações de cliente, data, serviços, valor total e status.
    """
    try:
        orcamentos = Orcamento.query.order_by(Orcamento.data_criacao.desc()).all()
        resultado = []
        for o in orcamentos:
            itens = [rel.para_dict() for rel in o.orcamento_servicos]
            resultado.append({
                'orcamento': o.para_dict(),
                'itens': itens
            })
        return jsonify({'orcamentos': resultado, 'total': len(resultado)}), 200
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: DETALHAR UM ORÇAMENTO
# GET /api/orcamentos/<id_orcamento>
# RF005: Buscar orçamento específico
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>', methods=['GET'])
@login_required
def detalhar_orcamento(id_orcamento):
    """
    Retorna um orçamento específico e seus itens.
    """
    try:
        orcamento = Orcamento.query.get_or_404(id_orcamento)
        itens = [rel.para_dict() for rel in orcamento.orcamento_servicos]
        return jsonify({'orcamento': orcamento.para_dict(), 'itens': itens}), 200
    except Exception as e:
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: ATUALIZAR STATUS DO ORÇAMENTO
# PUT /api/orcamentos/<id_orcamento>/status
# Atualiza o campo status do orçamento
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/status', methods=['PUT'])
@login_required
def atualizar_status_orcamento(id_orcamento):
    """
    Atualiza o status de um orçamento. Recebe JSON { "status": "Aprovado" }.
    Valores aceitos: "Pendente", "Aprovado", "Recusado", "Concluído".
    Retorna o orçamento atualizado.
    """
    try:
        dados = request.get_json()
        if not dados or 'status' not in dados:
            return jsonify({'erro': 'Campo "status" é obrigatório'}), 400

        status_novo = str(dados.get('status', '')).strip()
        status_validos = {"Pendente", "Aprovado", "Recusado", "Concluído"}
        if status_novo not in status_validos:
            return jsonify({'erro': 'Status inválido. Use: Pendente, Aprovado, Recusado, Concluído'}), 400

        orcamento = Orcamento.query.get_or_404(id_orcamento)
        orcamento.status = status_novo
        db.session.commit()

        # Log da alteração de status
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Status do orçamento {orcamento.id_orcamento} atualizado para {status_novo}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        itens = [rel.para_dict() for rel in orcamento.orcamento_servicos]
        return jsonify({'mensagem': 'Status atualizado com sucesso!', 'orcamento': orcamento.para_dict(), 'itens': itens}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: CONVERTER ORÇAMENTO EM VENDA
# POST /api/orcamentos/<id_orcamento>/converter-venda
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/converter-venda', methods=['POST'])
@login_required
def converter_em_venda(id_orcamento):
    try:
        orcamento = Orcamento.query.get_or_404(id_orcamento)

        if orcamento.status != 'Aprovado':
            return jsonify({'erro': 'Apenas orçamentos Aprovados podem ser convertidos em venda'}), 400

        # Evita conversão duplicada
        existente = Venda.query.filter_by(id_orcamento=orcamento.id_orcamento).first()
        if existente:
            return jsonify({'erro': 'Este orçamento já foi convertido em venda', 'venda': existente.para_dict()}), 409

        # Gera código de venda curto e único
        codigo = secrets.token_hex(6)

        venda = Venda(
            id_orcamento=orcamento.id_orcamento,
            id_cliente=orcamento.id_cliente,
            id_usuario=current_user.id_usuario,
            data_venda=datetime.utcnow(),
            codigo_venda=codigo,
            valor_total=orcamento.valor_total,
        )
        db.session.add(venda)
        db.session.flush()

        # Copia snapshot dos itens
        relacoes = OrcamentoServicos.query.filter_by(id_orcamento=orcamento.id_orcamento).all()
        for rel in relacoes:
            vi = VendaItem(
                id_venda=venda.id_venda,
                id_servico=rel.id_servico,
                quantidade=rel.quantidade,
                valor_unitario=rel.valor_unitario,
                subtotal=rel.subtotal,
            )
            db.session.add(vi)

        db.session.commit()

        # Log
        try:
            log = LogsAcesso(
                id_usuario=current_user.id_usuario,
                acao=f'Orçamento {orcamento.id_orcamento} convertido em venda {venda.codigo_venda}',
                data_hora=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        itens = [i.para_dict() for i in venda.itens]
        return jsonify({'mensagem': 'Conversão realizada com sucesso!', 'venda': venda.para_dict(), 'itens': itens}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: GERAR PDF DO ORÇAMENTO
# GET /api/orcamentos/<id_orcamento>/pdf
# RF006: Geração de PDF
# RNF004: Documento legível e estruturado
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/pdf', methods=['GET'])
@login_required
def gerar_pdf_orcamento(id_orcamento):
    """
    Gera um PDF formatado com dados do cliente, serviços selecionados e valor total.
    Requer WeasyPrint instalado no ambiente.
    """
    try:
        if not WEASYPRINT_AVAILABLE:
            return jsonify({'erro': 'Geração de PDF indisponível: WeasyPrint não instalado'}), 503

        orcamento = Orcamento.query.get_or_404(id_orcamento)
        cliente = orcamento.cliente
        itens = orcamento.orcamento_servicos

        # Função auxiliar para formatar moeda em pt-BR
        def formatar_brl(valor_decimal):
            valor = float(valor_decimal)
            txt = f"{valor:,.2f}"
            txt = txt.replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"R$ {txt}"

        # Tenta embutir logo se existir em src/static/logo.png
        logo_data_uri = ''
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            logo_path = os.path.join(base_dir, 'static', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                    logo_data_uri = f"data:image/png;base64,{b64}"
        except Exception:
            logo_data_uri = ''

        EMPRESA_NOME = 'Sua Empresa Ltda.'
        EMPRESA_ENDERECO = 'Rua Exemplo, 123 - Cidade/UF'
        EMPRESA_CONTATO = 'contato@empresa.com | (11) 0000-0000'

        # HTML com header/footer e estilos
        html_conteudo = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <style>
                @page {{
                    size: A4;
                    margin: 20mm 15mm 20mm 15mm;
                    @top-center {{ content: element(header); }}
                    @bottom-center {{ content: 'Página ' counter(page) ' de ' counter(pages); font-size: 10px; color: #666; }}
                }}
                body {{ font-family: Arial, sans-serif; font-size: 12px; color: #222; }}
                header.header {{ padding-bottom: 8px; border-bottom: 2px solid #333; }}
                .header-content {{ display: flex; align-items: center; gap: 12px; }}
                .logo {{ height: 40px; }}
                .empresa {{ font-size: 14px; font-weight: bold; }}
                .sub {{ font-size: 11px; color: #555; }}
                h1 {{ font-size: 18px; margin: 14px 0 6px 0; }}
                .meta {{ margin: 0 0 8px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                th {{ background: #f5f5f5; }}
                .right {{ text-align: right; }}
                .total {{ margin-top: 12px; font-weight: bold; text-align: right; }}
                thead {{ display: table-header-group; }}
                tr {{ page-break-inside: avoid; }}
            </style>
        </head>
        <body>
            <header class="header" style="position: running(header);">
                <div class="header-content">
                    {f'<img class="logo" src="{logo_data_uri}">' if logo_data_uri else ''}
                    <div>
                        <div class="empresa">{EMPRESA_NOME}</div>
                        <div class="sub">{EMPRESA_ENDERECO}</div>
                        <div class="sub">{EMPRESA_CONTATO}</div>
                    </div>
                </div>
            </header>

            <h1>Orçamento #{orcamento.id_orcamento}</h1>
            <p class="meta"><strong>Data:</strong> {orcamento.data_criacao.strftime('%d/%m/%Y %H:%M')}</p>
            <p class="meta"><strong>Status:</strong> {orcamento.status}</p>
            <p class="meta"><strong>Cliente:</strong> {cliente.nome} — {cliente.telefone or '-'} | {cliente.email or '-'}</p>
            <p class="meta"><strong>Endereço:</strong> {cliente.endereco or '-'}</p>

            <table>
                <thead>
                    <tr>
                        <th>Serviço</th>
                        <th>Descrição</th>
                        <th class="right">Qtd.</th>
                        <th class="right">Valor Unitário</th>
                        <th class="right">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"<tr><td>{rel.servico.nome}</td><td>{rel.servico.descricao or '-'}</td><td class='right'>{rel.quantidade}</td><td class='right'>{formatar_brl(rel.valor_unitario)}</td><td class='right'>{formatar_brl(rel.subtotal)}</td></tr>"
                        for rel in itens
                    ])}
                </tbody>
            </table>

            <p class='total'>Valor Total: {formatar_brl(orcamento.valor_total)}</p>
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html_conteudo).write_pdf()

        # Log de sucesso
        try:
            log = LogsAcesso(
                id_usuario=current_user.id_usuario,
                acao=f'PDF gerado para orçamento {orcamento.id_orcamento}',
                data_hora=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=orcamento_{orcamento.id_orcamento}.pdf'
        return response
    except Exception as e:
        # Log de falha
        try:
            log = LogsAcesso(
                id_usuario=current_user.id_usuario,
                acao=f'Falha ao gerar PDF do orçamento {id_orcamento}: {str(e)}',
                data_hora=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'erro': f'Erro ao gerar PDF: {str(e)}'}), 500






# ========================================
# ROTAS PARA ORÇAMENTO EM ANDAMENTO (MAIS PRÁTICAS)
# ========================================

# ========================================
# ROTA: INICIAR ORÇAMENTO
# POST /api/orcamentos/iniciar
# Cria um orçamento temporário para adicionar itens gradualmente
# ========================================
@orcamentos_bp.route('/iniciar', methods=['POST'])
@login_required
def iniciar_orcamento():
    """
    Inicia um novo orçamento temporário para um cliente.
    Recebe: { "id_cliente": number }
    Retorna: dados do orçamento temporário criado
    """
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400

        id_cliente = dados.get('id_cliente')
        if not id_cliente:
            return jsonify({'erro': 'id_cliente é obrigatório'}), 400

        # Verifica cliente
        cliente = Cliente.query.get_or_404(id_cliente)

        # Cria orçamento temporário
        orcamento_temp = Orcamento(
            id_cliente=cliente.id_cliente,
            id_usuario=current_user.id_usuario,
            data_criacao=datetime.utcnow(),
            valor_total=Decimal('0.00'),
            status='Em Andamento'  # Status especial para orçamentos em construção
        )
        db.session.add(orcamento_temp)
        db.session.commit()

        # Log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Orçamento temporário iniciado (ID {orcamento_temp.id_orcamento}) para cliente {cliente.nome}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'mensagem': 'Orçamento iniciado! Agora você pode adicionar itens.',
            'orcamento': orcamento_temp.para_dict(),
            'itens': []
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: ADICIONAR ITEM AO ORÇAMENTO
# POST /api/orcamentos/<id_orcamento>/adicionar-item
# Adiciona um item individual ao orçamento
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/adicionar-item', methods=['POST'])
@login_required
def adicionar_item_orcamento(id_orcamento):
    """
    Adiciona um item ao orçamento em andamento.
    Recebe: { "id_servico": number, "quantidade": number }
    Retorna: orçamento atualizado com o novo item
    """
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400

        id_servico = dados.get('id_servico')
        quantidade = dados.get('quantidade', 1)

        # Validações
        if not id_servico:
            return jsonify({'erro': 'id_servico é obrigatório'}), 400
        if not isinstance(quantidade, int) or quantidade < 1:
            return jsonify({'erro': 'quantidade deve ser um número inteiro maior que 0'}), 400

        # Busca orçamento e serviço
        orcamento = Orcamento.query.get_or_404(id_orcamento)
        servico = Servico.query.get_or_404(id_servico)

        # Verifica se é um orçamento em andamento
        if orcamento.status != 'Em Andamento':
            return jsonify({'erro': 'Apenas orçamentos em andamento podem receber itens'}), 400

        # Verifica se o serviço já está no orçamento
        item_existente = OrcamentoServicos.query.filter_by(
            id_orcamento=id_orcamento, 
            id_servico=id_servico
        ).first()

        if item_existente:
            # Se já existe, soma a quantidade
            item_existente.quantidade += quantidade
            item_existente.subtotal = item_existente.quantidade * item_existente.valor_unitario
        else:
            # Se não existe, cria novo item
            valor_unitario = Decimal(str(servico.valor))
            subtotal = valor_unitario * quantidade
            
            novo_item = OrcamentoServicos(
                id_orcamento=id_orcamento,
                id_servico=id_servico,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                subtotal=subtotal
            )
            db.session.add(novo_item)

        # Recalcula valor total
        itens = OrcamentoServicos.query.filter_by(id_orcamento=id_orcamento).all()
        valor_total = sum(item.subtotal for item in itens)
        orcamento.valor_total = valor_total

        db.session.commit()

        # Log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Item adicionado ao orçamento {id_orcamento}: {servico.nome} (qtd: {quantidade})',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        # Retorna orçamento atualizado
        itens_resp = [item.para_dict() for item in itens]
        return jsonify({
            'mensagem': f'Item "{servico.nome}" adicionado com sucesso!',
            'orcamento': orcamento.para_dict(),
            'itens': itens_resp
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: REMOVER ITEM DO ORÇAMENTO
# DELETE /api/orcamentos/<id_orcamento>/remover-item/<id_servico>
# Remove um item específico do orçamento
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/remover-item/<int:id_servico>', methods=['DELETE'])
@login_required
def remover_item_orcamento(id_orcamento, id_servico):
    """
    Remove um item específico do orçamento em andamento.
    """
    try:
        # Busca orçamento
        orcamento = Orcamento.query.get_or_404(id_orcamento)
        
        if orcamento.status != 'Em Andamento':
            return jsonify({'erro': 'Apenas orçamentos em andamento podem ter itens removidos'}), 400

        # Busca e remove o item
        item = OrcamentoServicos.query.filter_by(
            id_orcamento=id_orcamento, 
            id_servico=id_servico
        ).first()

        if not item:
            return jsonify({'erro': 'Item não encontrado no orçamento'}), 404

        nome_servico = item.servico.nome
        db.session.delete(item)

        # Recalcula valor total
        itens_restantes = OrcamentoServicos.query.filter_by(id_orcamento=id_orcamento).all()
        valor_total = sum(item.subtotal for item in itens_restantes)
        orcamento.valor_total = valor_total

        db.session.commit()

        # Log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Item removido do orçamento {id_orcamento}: {nome_servico}',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        # Retorna orçamento atualizado
        itens_resp = [item.para_dict() for item in itens_restantes]
        return jsonify({
            'mensagem': f'Item "{nome_servico}" removido com sucesso!',
            'orcamento': orcamento.para_dict(),
            'itens': itens_resp
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: ATUALIZAR QUANTIDADE DO ITEM
# PUT /api/orcamentos/<id_orcamento>/atualizar-quantidade/<id_servico>
# Atualiza a quantidade de um item específico
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/atualizar-quantidade/<int:id_servico>', methods=['PUT'])
@login_required
def atualizar_quantidade_item(id_orcamento, id_servico):
    """
    Atualiza a quantidade de um item específico no orçamento.
    Recebe: { "quantidade": number }
    """
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Nenhum dado foi enviado'}), 400

        quantidade = dados.get('quantidade')
        if not isinstance(quantidade, int) or quantidade < 1:
            return jsonify({'erro': 'quantidade deve ser um número inteiro maior que 0'}), 400

        # Busca orçamento e item
        orcamento = Orcamento.query.get_or_404(id_orcamento)
        
        if orcamento.status != 'Em Andamento':
            return jsonify({'erro': 'Apenas orçamentos em andamento podem ter quantidades alteradas'}), 400

        item = OrcamentoServicos.query.filter_by(
            id_orcamento=id_orcamento, 
            id_servico=id_servico
        ).first()

        if not item:
            return jsonify({'erro': 'Item não encontrado no orçamento'}), 404

        # Atualiza quantidade e subtotal
        item.quantidade = quantidade
        item.subtotal = item.quantidade * item.valor_unitario

        # Recalcula valor total
        itens = OrcamentoServicos.query.filter_by(id_orcamento=id_orcamento).all()
        valor_total = sum(item.subtotal for item in itens)
        orcamento.valor_total = valor_total

        db.session.commit()

        # Log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Quantidade atualizada no orçamento {id_orcamento}: {item.servico.nome} (nova qtd: {quantidade})',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        # Retorna orçamento atualizado
        itens_resp = [item.para_dict() for item in itens]
        return jsonify({
            'mensagem': f'Quantidade atualizada para {quantidade}!',
            'orcamento': orcamento.para_dict(),
            'itens': itens_resp
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: FINALIZAR ORÇAMENTO
# POST /api/orcamentos/<id_orcamento>/finalizar
# Finaliza o orçamento e define o status como Pendente
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/finalizar', methods=['POST'])
@login_required
def finalizar_orcamento(id_orcamento):
    """
    Finaliza um orçamento em andamento, definindo status como Pendente.
    """
    try:
        orcamento = Orcamento.query.get_or_404(id_orcamento)
        
        if orcamento.status != 'Em Andamento':
            return jsonify({'erro': 'Apenas orçamentos em andamento podem ser finalizados'}), 400

        # Verifica se tem itens
        itens = OrcamentoServicos.query.filter_by(id_orcamento=id_orcamento).all()
        if not itens:
            return jsonify({'erro': 'Orçamento deve ter pelo menos um item para ser finalizado'}), 400

        # Muda status para Pendente
        orcamento.status = 'Pendente'
        db.session.commit()

        # Log
        log = LogsAcesso(
            id_usuario=current_user.id_usuario,
            acao=f'Orçamento {id_orcamento} finalizado e enviado para aprovação',
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        # Retorna orçamento finalizado
        itens_resp = [item.para_dict() for item in itens]
        return jsonify({
            'mensagem': 'Orçamento finalizado com sucesso! Status alterado para Pendente.',
            'orcamento': orcamento.para_dict(),
            'itens': itens_resp
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro no servidor: {str(e)}'}), 500


# ========================================
# ROTA: ENVIAR PDF POR E-MAIL
# POST /api/orcamentos/<id_orcamento>/enviar-email
# body: { "emails": ["a@b.com"], "mensagem": "..." }
# Requer configuração SMTP via variáveis de ambiente
# ========================================
@orcamentos_bp.route('/<int:id_orcamento>/enviar-email', methods=['POST'])
@login_required
def enviar_email_orcamento(id_orcamento):
    try:
        dados = request.get_json() or {}
        emails = dados.get('emails') or []
        mensagem = dados.get('mensagem') or ''
        if not isinstance(emails, list) or len(emails) == 0:
            return jsonify({'erro': 'Informe uma lista de emails'}), 400

        if not WEASYPRINT_AVAILABLE:
            return jsonify({'erro': 'Geração de PDF indisponível: WeasyPrint não instalado'}), 503

        orcamento = Orcamento.query.get_or_404(id_orcamento)
        # Reusa o HTML da função anterior para gerar o PDF
        cliente = orcamento.cliente
        itens = orcamento.orcamento_servicos

        def formatar_brl(valor_decimal):
            valor = float(valor_decimal)
            txt = f"{valor:,.2f}"
            txt = txt.replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"R$ {txt}"

        logo_data_uri = ''
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            logo_path = os.path.join(base_dir, 'static', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                    logo_data_uri = f"data:image/png;base64,{b64}"
        except Exception:
            logo_data_uri = ''

        EMPRESA_NOME = 'Sua Empresa Ltda.'
        EMPRESA_ENDERECO = 'Rua Exemplo, 123 - Cidade/UF'
        EMPRESA_CONTATO = 'contato@empresa.com | (11) 0000-0000'

        html_conteudo = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <style>
                @page {{ size: A4; margin: 20mm 15mm 20mm 15mm; }}
                body {{ font-family: Arial, sans-serif; font-size: 12px; color: #222; }}
                header.header {{ padding-bottom: 8px; border-bottom: 2px solid #333; }}
            </style>
        </head>
        <body>
            <header class="header">
                {f'<img style="height:40px" src="{logo_data_uri}">' if logo_data_uri else ''}
                <div><div style="font-weight:bold">{EMPRESA_NOME}</div><div>{EMPRESA_ENDERECO}</div><div>{EMPRESA_CONTATO}</div></div>
            </header>
            <h1>Orçamento #{orcamento.id_orcamento}</h1>
            <p><strong>Cliente:</strong> {cliente.nome}</p>
            <table style="width:100%; border-collapse:collapse" border="1" cellpadding="6">
                <tr><th>Serviço</th><th>Descrição</th><th>Qtd</th><th>Unitário</th><th>Subtotal</th></tr>
                {''.join([
                    f"<tr><td>{rel.servico.nome}</td><td>{rel.servico.descricao or '-'}</td><td>{rel.quantidade}</td><td>{formatar_brl(rel.valor_unitario)}</td><td>{formatar_brl(rel.subtotal)}</td></tr>"
                    for rel in itens
                ])}
            </table>
            <p style="text-align:right; font-weight:bold">Valor Total: {formatar_brl(orcamento.valor_total)}</p>
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html_conteudo).write_pdf()

        # Config SMTP
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        smtp_tls = os.environ.get('SMTP_TLS', 'true').lower() == 'true'
        remetente = os.environ.get('SMTP_FROM', smtp_user)
        if not (smtp_host and smtp_user and smtp_pass and remetente):
            return jsonify({'erro': 'SMTP não configurado (defina SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM)'}), 500

        msg = EmailMessage()
        msg['From'] = remetente
        msg['To'] = ', '.join(emails)
        msg['Subject'] = f'Orçamento #{orcamento.id_orcamento}'
        corpo = mensagem or f'Segue em anexo o orçamento #{orcamento.id_orcamento}.'
        msg.set_content(corpo)
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f'orcamento_{orcamento.id_orcamento}.pdf')

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            if smtp_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        # Log
        try:
            log = LogsAcesso(
                id_usuario=current_user.id_usuario,
                acao=f'E-mail enviado com orçamento {orcamento.id_orcamento} para {len(emails)} destinatário(s)',
                data_hora=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify({'mensagem': 'E-mail enviado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao enviar e-mail: {str(e)}'}), 500


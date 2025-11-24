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
from src.utils.email_utils import send_email, get_smtp_config

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
    Usa ReportLab para gerar o PDF.
    """
    try:
        # Busca dados do orçamento
        orcamento = Orcamento.query.get_or_404(id_orcamento)
        cliente = orcamento.cliente
        itens = orcamento.orcamento_servicos

        def formatar_brl(valor_decimal):
            valor = float(valor_decimal)
            txt = f"{valor:,.2f}"
            txt = txt.replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"R$ {txt}"

        # Primeiro tenta usar WeasyPrint (HTML -> PDF) para um layout rico
        if WEASYPRINT_AVAILABLE:
            # Tenta carregar logo da empresa em static (qualquer formato suportado)
            logo_data_uri = ''
            try:
                base_dir = os.path.dirname(os.path.dirname(__file__))
                # procura por logo.png, logo.jpg ou logo.svg
                for fname in ('logo.png', 'logo.jpg', 'logo.svg'):
                    logo_path = os.path.join(base_dir, 'static', fname)
                    if os.path.exists(logo_path):
                        with open(logo_path, 'rb') as f:
                            b64 = base64.b64encode(f.read()).decode('utf-8')
                            mime = 'image/png' if fname.endswith('.png') else ('image/jpeg' if fname.endswith('.jpg') else 'image/svg+xml')
                            logo_data_uri = f"data:{mime};base64,{b64}"
                        break
            except Exception:
                logo_data_uri = ''

            EMPRESA_NOME = os.environ.get('EMPRESA_NOME', 'ORCATECH')
            EMPRESA_ENDERECO = os.environ.get('EMPRESA_ENDERECO', '')
            EMPRESA_CONTATO = os.environ.get('EMPRESA_CONTATO', '')

            html_conteudo = f"""
            <html>
            <head>
                <meta charset='utf-8'>
                <style>
                    @page {{ size: A4; margin: 18mm 12mm; }}
                    :root {{ --accent: #0b57a4; --text: #222; --muted: #666; }}
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: var(--text); font-size:12px; }}
                    header.header {{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding-bottom:10px; border-bottom:2px solid #eee; }}
                    header.header .company {{ text-align:right; font-size:11px; color:var(--muted); }}
                    header.header img {{ height:72px; object-fit:contain; }}
                    h1 {{ text-align:center; color:var(--accent); margin:12px 0 6px 0; font-size:20px; }}
                    .meta {{ display:flex; justify-content:space-between; margin-bottom:12px; gap:12px; font-size:11px; color:var(--muted); }}
                    .box {{ border:2px solid var(--accent); border-radius:14px; padding:10px; margin-bottom:12px; }}
                    table.items {{ width:100%; border-collapse:collapse; margin-top:6px; }}
                    table.items th {{ background:var(--accent); color:#fff; padding:8px 6px; font-weight:600; font-size:11px; text-align:left; }}
                    table.items td {{ padding:8px 6px; border-bottom:1px solid #eee; vertical-align:top; font-size:11px; }}
                    table.items tr:nth-child(even) td {{ background:#fbfbfb; }}
                    .total {{ margin-top:8px; text-align:right; font-size:13px; font-weight:700; color:var(--accent); }}
                    footer {{ margin-top:18px; font-size:10px; color:var(--muted); text-align:center; }}
                </style>
            </head>
            <body>
                <header class="header">
                    <div class="logo">{f'<img src="{logo_data_uri}"/>' if logo_data_uri else ''}</div>
                    <div class="company">
                        <div style="font-weight:700; color:var(--text)">{EMPRESA_NOME}</div>
                        <div>{EMPRESA_ENDERECO}</div>
                        <div>{EMPRESA_CONTATO}</div>
                    </div>
                </header>
                <div class="box">
                    <div style="display:flex; justify-content:space-between;">
                        <div><strong>Data:</strong> {orcamento.data_criacao.strftime('%d/%m/%Y %H:%M')}</div>
                        <div><strong>Orçamento:</strong> #{orcamento.id_orcamento}</div>
                    </div>
                    <div style="margin-top:8px"><strong>Cliente:</strong> {cliente.nome}</div>
                    <div style="margin-top:4px"><strong>Endereço:</strong> {cliente.endereco or ''}</div>
                </div>
                <h1>Itens</h1>
                <table class="items" cellpadding="0" cellspacing="0">
                    <thead>
                        <tr><th style="width:60px; text-align:center">Qtd</th><th>Descrição do Item</th><th style="width:120px; text-align:right">Valor Unit.</th><th style="width:140px; text-align:right">Valor Total</th></tr>
                    </thead>
                    <tbody>
                    {''.join([
                        f"<tr><td style='text-align:center'>{rel.quantidade}</td><td>{rel.servico.nome}<br/><small>{(rel.servico.descricao or '')}</small></td><td style='text-align:right'>{formatar_brl(rel.valor_unitario)}</td><td style='text-align:right'>{formatar_brl(rel.subtotal)}</td></tr>"
                        for rel in itens
                    ])}
                    </tbody>
                </table>
                <div class="total">TOTAL GERAL: {formatar_brl(orcamento.valor_total)}</div>
                <footer>Assinatura: ____________________________________________</footer>
            </body>
            </html>
            """

            try:
                from weasyprint import HTML
                pdf_bytes = HTML(string=html_conteudo).write_pdf()
            except Exception as e:
                return jsonify({'erro': f'WeasyPrint falhou ao gerar o PDF: {str(e)}'}), 500

        else:
            # Fallback: tenta usar ReportLab (versão já estilizada)
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.utils import ImageReader
            from io import BytesIO

            # Configuração do documento
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)

            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=12, alignment=1)
            normal_style = styles["Normal"]
            normal_style.fontSize = 10
            small_style = ParagraphStyle('Small', parent=normal_style, fontSize=9)

            # Cabeçalho
            EMPRESA_NOME = os.environ.get('EMPRESA_NOME', 'ORCATECH')
            EMPRESA_ENDERECO = os.environ.get('EMPRESA_ENDERECO', '')
            EMPRESA_CONTATO = os.environ.get('EMPRESA_CONTATO', '')

            elements = []
            elements.append(Paragraph(f"Orçamento #{orcamento.id_orcamento}", title_style))
            elements.append(Paragraph(f"Cliente: {cliente.nome}", normal_style))
            elements.append(Spacer(1, 12))

            table_data = [['Serviço', 'Descrição', 'Qtd.', 'Valor Unit.', 'Subtotal']]
            for item in itens:
                table_data.append([
                    item.servico.nome,
                    item.servico.descricao or '-',
                    str(item.quantidade),
                    formatar_brl(item.valor_unitario),
                    formatar_brl(item.subtotal)
                ])
            table_data.append(['', '', '', 'Total:', formatar_brl(orcamento.valor_total)])

            col_widths = [4*cm, 8*cm, 2*cm, 3*cm, 3*cm]
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1773cf')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (2, 1), (4, -2), 'RIGHT'),
                ('INNERGRID', (0, 0), (-1, -2), 0.25, colors.grey),
                ('BOX', (0, 0), (-1, -2), 0.25, colors.grey),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()

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
    """
    Envia orçamento por e-mail com PDF em anexo.
    Valida configuração SMTP, trata erros específicos e registra logs detalhados.
    """
    try:
        # Validação dos dados de entrada
        dados = request.get_json() or {}
        emails = dados.get('emails') or []
        mensagem = dados.get('mensagem') or ''
        
        if not isinstance(emails, list) or len(emails) == 0:
            return jsonify({'erro': 'Informe uma lista de emails válida'}), 400

        # Busca o orçamento
        orcamento = Orcamento.query.get_or_404(id_orcamento)
        cliente = orcamento.cliente
        itens = orcamento.orcamento_servicos

        # Validação da configuração SMTP (não falha imediatamente — apenas validaremos ao enviar)
        smtp_cfg = get_smtp_config()
        if not smtp_cfg['host'] or not smtp_cfg['user'] or not smtp_cfg['password']:
            return jsonify({'erro': 'Serviço de e-mail não configurado no servidor (variáveis SMTP ausentes)'}), 503

        # Função auxiliar para formatar valores em BRL
        def formatar_brl(valor_decimal):
            valor = float(valor_decimal)
            txt = f"{valor:,.2f}"
            txt = txt.replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"R$ {txt}"

        # Tenta carregar logo da empresa
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

        # Dados da empresa (configuráveis via variáveis de ambiente)
        EMPRESA_NOME = os.environ.get('EMPRESA_NOME', 'Sua Empresa Ltda.')
        EMPRESA_ENDERECO = os.environ.get('EMPRESA_ENDERECO', 'Rua Exemplo, 123 - Cidade/UF')
        EMPRESA_CONTATO = os.environ.get('EMPRESA_CONTATO', 'contato@empresa.com | (11) 0000-0000')

        # Gera HTML do orçamento (estilizado)
        html_conteudo = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <style>
                @page {{ size: A4; margin: 18mm 12mm; }}
                :root {{ --accent: #1773cf; --text: #222; --muted: #666; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: var(--text); font-size:12px; }}
                header.header {{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding-bottom:10px; border-bottom:2px solid #eee; }}
                header.header .company {{ text-align:right; font-size:11px; color:var(--muted); }}
                header.header img {{ height:64px; object-fit:contain; }}
                h1 {{ text-align:center; color:var(--accent); margin:18px 0 6px 0; font-size:20px; }}
                .meta {{ display:flex; justify-content:space-between; margin-bottom:12px; gap:12px; font-size:11px; color:var(--muted); }}
                table.items {{ width:100%; border-collapse:collapse; margin-top:6px; }}
                table.items th {{ background:var(--accent); color:#fff; padding:8px 6px; font-weight:600; font-size:11px; text-align:left; }}
                table.items td {{ padding:8px 6px; border-bottom:1px solid #eee; vertical-align:top; font-size:11px; }}
                table.items tr:nth-child(even) td {{ background:#fbfbfb; }}
                .total {{ margin-top:8px; text-align:right; font-size:13px; font-weight:700; color:var(--accent); }}
                footer {{ margin-top:18px; font-size:10px; color:var(--muted); text-align:center; }}
            </style>
        </head>
        <body>
            <header class="header">
                <div class="logo">{f'<img src="{logo_data_uri}"/>' if logo_data_uri else ''}</div>
                <div class="company">
                    <div style="font-weight:700; color:var(--text)">{EMPRESA_NOME}</div>
                    <div>{EMPRESA_ENDERECO}</div>
                    <div>{EMPRESA_CONTATO}</div>
                </div>
            </header>
            <h1>Orçamento #{orcamento.id_orcamento}</h1>
            <div class="meta">
                <div class="cliente"><strong>Cliente:</strong> {cliente.nome} {f'<br/>{cliente.email}' if cliente.email else ''} {f'<br/>{cliente.telefone}' if cliente.telefone else ''}</div>
                <div class="info"><strong>Data:</strong> {orcamento.data_criacao.strftime('%d/%m/%Y %H:%M')}<br/><strong>Status:</strong> {orcamento.status}</div>
            </div>
            <table class="items" cellpadding="0" cellspacing="0">
                <thead>
                    <tr><th>Serviço</th><th>Descrição</th><th style="width:60px; text-align:center">Qtd</th><th style="width:100px; text-align:right">Unitário</th><th style="width:120px; text-align:right">Subtotal</th></tr>
                </thead>
                <tbody>
                {''.join([
                    f"<tr><td>{rel.servico.nome}</td><td>{(rel.servico.descricao or '-')}</td><td style='text-align:center'>{rel.quantidade}</td><td style='text-align:right'>{formatar_brl(rel.valor_unitario)}</td><td style='text-align:right'>{formatar_brl(rel.subtotal)}</td></tr>"
                    for rel in itens
                ])}
                </tbody>
            </table>
            <div class="total">Valor Total: {formatar_brl(orcamento.valor_total)}</div>
            <footer>Este documento é uma proposta de serviço e não constitui fatura. Obrigado por escolher {EMPRESA_NOME}.</footer>
        </body>
        </html>
        """

        # Gera PDF: tenta WeasyPrint e, se não disponível ou falhar, usa ReportLab
        pdf_bytes = None
        if WEASYPRINT_AVAILABLE:
            try:
                from weasyprint import HTML as _HTML
                pdf_bytes = _HTML(string=html_conteudo).write_pdf()
            except Exception:
                pdf_bytes = None

        if not pdf_bytes:
            # fallback ReportLab (pega do mesmo bloco existente no endpoint de geração de PDF)
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from io import BytesIO

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=8, alignment=1)
            normal_style = styles['Normal']
            normal_style.fontSize = 10

            elements = []
            elements.append(Paragraph(f"Orçamento #{orcamento.id_orcamento}", title_style))
            elements.append(Paragraph(f"Cliente: {cliente.nome}", normal_style))
            elements.append(Spacer(1, 8))

            table_data = [['Serviço', 'Descrição', 'Qtd.', 'Valor Unit.', 'Subtotal']]
            for item in itens:
                table_data.append([
                    item.servico.nome,
                    item.servico.descricao or '-',
                    str(item.quantidade),
                    formatar_brl(item.valor_unitario),
                    formatar_brl(item.subtotal)
                ])
            table_data.append(['', '', '', 'Total:', formatar_brl(orcamento.valor_total)])

            col_widths = [4*cm, 8*cm, 2*cm, 3*cm, 3*cm]
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1773cf')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (2, 1), (4, -2), 'RIGHT'),
                ('INNERGRID', (0, 0), (-1, -2), 0.25, colors.grey),
                ('BOX', (0, 0), (-1, -2), 0.25, colors.grey),
            ]))
            elements.append(table)
            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()

        # Envia e-mail com anexo via utilitário compartilhado
        attachments = [{'filename': f'orcamento_{orcamento.id_orcamento}.pdf', 'content': pdf_bytes, 'maintype': 'application', 'subtype': 'pdf'}]
        corpo = mensagem or f'Segue em anexo o orçamento #{orcamento.id_orcamento}.'
        ok, msg = send_email(subject=f'Orçamento #{orcamento.id_orcamento}', body=corpo, to=emails, attachments=attachments)
        if not ok:
            # registra log detalhado e devolve erro apropriado
            try:
                log = LogsAcesso(
                    id_usuario=current_user.id_usuario,
                    acao=f'Falha ao enviar e-mail do orçamento {orcamento.id_orcamento}: {msg}',
                    data_hora=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                db.session.rollback()

            # traduz mensagens comuns em códigos HTTP
            if 'Autenticação' in msg or 'Autenticação SMTP' in msg:
                return jsonify({'erro': 'Falha na autenticação do servidor de e-mail. Verifique as credenciais SMTP.'}), 401
            if 'conex' in msg.lower():
                return jsonify({'erro': 'Não foi possível conectar ao servidor de e-mail. Verifique as configurações SMTP.'}), 503
            return jsonify({'erro': f'Erro ao enviar e-mail: {msg}'}), 502

        # Log de sucesso com detalhes dos destinatários
        try:
            emails_str = ', '.join(emails)
            log = LogsAcesso(
                id_usuario=current_user.id_usuario,
                acao=f'E-mail enviado com sucesso: orçamento {orcamento.id_orcamento} para {len(emails)} destinatário(s) - {emails_str}',
                data_hora=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify({
            'mensagem': 'E-mail enviado com sucesso!',
            'destinatarios': emails,
            'total_destinatarios': len(emails)
        }), 200

    except Exception as e:
        # Log de erro geral
        try:
            log = LogsAcesso(
                id_usuario=current_user.id_usuario,
                acao=f'Erro geral ao enviar e-mail do orçamento {id_orcamento}: {str(e)}',
                data_hora=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500


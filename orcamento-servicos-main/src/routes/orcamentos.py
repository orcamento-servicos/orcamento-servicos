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

from src.models.models import (
    db,
    Cliente,
    Servico,
    Orcamento,
    OrcamentoServicos,
    LogsAcesso,
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






# ========================================
# ROTAS DE VENDAS
# ========================================

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy.orm import joinedload
from datetime import datetime

from src.models.models import (
    db,
    Venda,
    VendaItem,
    Orcamento,
)

vendas_bp = Blueprint("vendas", __name__)


def _paginate(query):
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 10))
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 10
    except Exception:
        page, size = 1, 10
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total, page, size


# ========================================
# LISTAR VENDAS
# GET /api/vendas/
# Filtros: data_ini, data_fim, id_cliente, id_orcamento
# ========================================
@vendas_bp.route("/", methods=["GET"])
@login_required
def listar_vendas():
    try:
        q = Venda.query.options(joinedload(Venda.itens))

        id_cliente = request.args.get("id_cliente")
        id_orcamento = request.args.get("id_orcamento")
        data_ini = request.args.get("data_ini")
        data_fim = request.args.get("data_fim")

        if id_cliente:
            q = q.filter(Venda.id_cliente == int(id_cliente))
        if id_orcamento:
            q = q.filter(Venda.id_orcamento == int(id_orcamento))
        if data_ini:
            try:
                di = datetime.fromisoformat(data_ini)
                q = q.filter(Venda.data_venda >= di)
            except Exception:
                pass
        if data_fim:
            try:
                df = datetime.fromisoformat(data_fim)
                q = q.filter(Venda.data_venda <= df)
            except Exception:
                pass

        q = q.order_by(Venda.data_venda.desc())
        vendas, total, page, size = _paginate(q)

        resp = []
        for v in vendas:
            resp.append(
                {
                    "venda": v.para_dict(),
                    "itens": [i.para_dict() for i in v.itens],
                }
            )

        return (
            jsonify({"vendas": resp, "total": total, "page": page, "size": size}),
            200,
        )
    except Exception as e:
        return jsonify({"erro": f"Erro no servidor: {str(e)}"}), 500


# ========================================
# DETALHAR VENDA
# GET /api/vendas/<id_venda>
# ========================================
@vendas_bp.route("/<int:id_venda>", methods=["GET"])
@login_required
def detalhar_venda(id_venda):
    try:
        venda = Venda.query.options(joinedload(Venda.itens)).get_or_404(id_venda)
        return (
            jsonify(
                {
                    "venda": venda.para_dict(),
                    "itens": [i.para_dict() for i in venda.itens],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"erro": f"Erro no servidor: {str(e)}"}), 500

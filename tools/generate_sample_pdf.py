#!/usr/bin/env python3
"""Gera um PDF de exemplo do orçamento para revisão.
Usa WeasyPrint (HTML->PDF) quando disponível, caso contrário usa ReportLab como fallback.
Salva em tmp/orcamento_exemplo.pdf
"""
import os
import base64
from datetime import datetime

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tmp')
os.makedirs(OUT_PATH, exist_ok=True)
OUT_FILE = os.path.join(OUT_PATH, 'orcamento_exemplo.pdf')

# Dados de exemplo
cliente = {
    'nome': 'João da Silva',
    'endereco': 'Rua das Flores, 123 - Centro',
    'email': 'joao@example.com',
    'telefone': '(11) 99999-0000'
}

itens = [
    {'nome': 'Montagem de móvel', 'descricao': 'Montagem de guarda-roupa 3 portas', 'qtd': 1, 'unit': 350.0, 'subtotal': 350.0},
    {'nome': 'Conserto de eletro', 'descricao': 'Troca de placa', 'qtd': 1, 'unit': 220.0, 'subtotal': 220.0},
]

total = sum(i['subtotal'] for i in itens)

def formatar_brl(v):
    txt = f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {txt}"

def try_weasy(html, out_file):
    try:
        from weasyprint import HTML
    except Exception as e:
        return False, f'WeasyPrint não disponível: {e}'

    try:
        HTML(string=html).write_pdf(out_file)
        return True, 'OK'
    except Exception as e:
        return False, f'Erro WeasyPrint: {e}'

def try_reportlab(out_file):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except Exception as e:
        return False, f'ReportLab não disponível: {e}'

    buffer = out_file
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('DLZ TECH', ParagraphStyle('h1', parent=styles['Heading1'], alignment=1)))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Cliente: {cliente['nome']}", styles['Normal']))
    elements.append(Spacer(1, 12))

    table_data = [['Qtd', 'Descrição do Item', 'Valor Unit.', 'Valor Total']]
    for it in itens:
        table_data.append([str(it['qtd']), it['nome'] + '\n' + it['descricao'], formatar_brl(it['unit']), formatar_brl(it['subtotal'])])
    table_data.append(['', '', 'TOTAL GERAL', formatar_brl(total)])

    table = Table(table_data, colWidths=[50, 300, 90, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1773cf')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
    ]))
    elements.append(table)
    doc.build(elements)
    return True, 'OK'

def main():
    # Monta HTML parecido com o template do app
    base_dir = os.path.dirname(os.path.dirname(__file__))
    logo_uri = ''
    for fname in ('logo.png','logo.jpg','logo.svg'):
        p = os.path.join(base_dir, 'static', fname)
        if os.path.exists(p):
            with open(p, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
                if fname.endswith('.svg'):
                    mime = 'image/svg+xml'
                elif fname.endswith('.png'):
                    mime = 'image/png'
                else:
                    mime = 'image/jpeg'
                logo_uri = f'data:{mime};base64,{b64}'
            break

    html = f"""
    <html><head><meta charset='utf-8'><style>
    body{{font-family:Arial,Helvetica,sans-serif;font-size:12px}}
    header{{display:flex;justify-content:space-between;align-items:center}}
    .box{{border:2px solid #0b57a4;border-radius:12px;padding:10px;margin:12px 0}}
    table{{width:100%;border-collapse:collapse;margin-top:8px}}
    th{{background:#0b57a4;color:#fff;padding:8px}}
    td{{border:1px solid #ddd;padding:8px}}
    .total{{text-align:right;margin-top:8px;font-weight:700}}
    footer{{margin-top:20px}}
    </style></head><body>
    <header>{f'<img src="{logo_uri}" style="height:72px"/>' if logo_uri else '<div style="font-size:28px;font-weight:700">DLZ TECH</div>'}<div style="text-align:right">Rua da Matriz, 81<br/>9 89760615<br/>Romualdo</div></header>
    <div class='box'><div>Data: ____________________________</div><div>Telefone: ______________________</div><div>Endereço: ______________________</div><div>Cliente: _______________________</div></div>
    <h3>Itens</h3>
    <table><thead><tr><th style='width:60px'>QUANT.</th><th>DESCRIÇÃO DO ITEM</th><th style='width:120px'>VALOR UN.</th><th style='width:140px'>VALOR TOTAL</th></tr></thead><tbody>"""
    for it in itens:
        html += f"<tr><td style='text-align:center'>{it['qtd']}</td><td>{it['nome']}<br/><small>{it['descricao']}</small></td><td style='text-align:right'>{formatar_brl(it['unit'])}</td><td style='text-align:right'>{formatar_brl(it['subtotal'])}</td></tr>"
    # add empty rows to simulate the mock
    for _ in range(10):
        html += "<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>"
    html += f"</tbody></table><div class='total'>TOTAL GERAL: {formatar_brl(total)}</div><footer>Assinatura: ____________________________________________</footer></body></html>"

    ok, msg = try_weasy(html, OUT_FILE)
    if ok:
        print('PDF gerado com WeasyPrint em', OUT_FILE)
        return

    print('Weasy falhou ou não disponível:', msg)
    # Fallback reportlab
    ok2, msg2 = try_reportlab(OUT_FILE)
    if ok2:
        print('PDF gerado com ReportLab em', OUT_FILE)
    else:
        print('Falha ao gerar PDF:', msg2)

if __name__ == '__main__':
    main()

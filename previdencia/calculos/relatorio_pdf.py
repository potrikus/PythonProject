from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def formatar_moeda(valor):
    if valor in (None, ""):
        return "Não informado"

    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return str(valor)

    texto = f"{numero:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")

    return f"R$ {texto}"

def formatar_data(data):
    if not data:
        return "Não informada"

    return data.strftime("%d/%m/%Y")


def valor_resultado(resultado, chave, padrao="Não informado"):
    valor = resultado.get(chave, padrao)
    return str(valor) if valor not in (None, "") else padrao


def cabecalho_rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6c757d"))
    canvas.drawString(
        2 * cm,
        1.2 * cm,
        "Previdência - Relatório de simulação",
    )
    canvas.drawRightString(
        A4[0] - 2 * cm,
        1.2 * cm,
        f"Página {doc.page}",
    )
    canvas.restoreState()


def gerar_relatorio_simulacao(response, simulacao):
    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1f4e79"),
        spaceAfter=8,
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#6c757d"),
        spaceAfter=18,
    )

    secao = ParagraphStyle(
        "Secao",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=10,
        spaceAfter=6,
    )

    normal = ParagraphStyle(
        "NormalCustomizado",
        parent=estilos["Normal"],
        fontSize=9,
        leading=13,
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title=f"Simulação previdenciária - {simulacao.cliente}",
        author="Previdência",
    )

    resultado = simulacao.resultado or {}
    elementos = [
        Paragraph("Relatório de Simulação Previdenciária", titulo),
        Paragraph(
            "Estimativa informativa - não substitui decisão administrativa do INSS.",
            subtitulo,
        ),
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#1f4e79"),
        ),
        Spacer(1, 12),
        Paragraph("Dados do cliente", secao),
    ]

    dados_cliente = [
        ["Cliente", escape(str(simulacao.cliente))],
        ["Data de referência", formatar_data(simulacao.data_referencia)],
        [
            "Filiado antes da reforma",
            "Sim" if simulacao.filiado_antes_reforma else "Não",
        ],
    ]

    elementos.append(criar_tabela(dados_cliente))
    elementos.append(Paragraph("Dados informados", secao))

    dados_simulacao = [
        ["Carência", f"{simulacao.carencia_meses} meses"],
        ["Tempo de contribuição", f"{simulacao.contribuicao_meses} meses"],
        [
            "Tempo de contribuição em 13/11/2019",
            f"{simulacao.contribuicao_em_2019_meses} meses",
        ],
        [
            "Salário médio atualizado",
            formatar_moeda(simulacao.salario_medio_atualizado),
        ],
        [
            "Salário de contribuição",
            formatar_moeda(simulacao.salario_contribuicao),
        ],
        ["Categoria", simulacao.get_categoria_display()],
    ]

    elementos.append(criar_tabela(dados_simulacao))
    elementos.append(Paragraph("Resultado da estimativa", secao))

    dados_resultado = [
        [
            "Benefício estimado",
            formatar_moeda(resultado.get("estimativa_beneficio")),
        ],
        [
            "Contribuição mensal estimada",
            formatar_moeda(resultado.get("contribuicao_mensal")),
        ],
        ["Coeficiente aplicado", valor_resultado(resultado, "coeficiente")],
        [
            "Quantidade de regras elegíveis",
            valor_resultado(resultado, "quantidade_regras_elegiveis", "0"),
        ],
    ]

    elementos.append(criar_tabela(dados_resultado))
    elementos.append(Paragraph("Regras avaliadas", secao))

    regras = resultado.get("regras", [])

    if regras:
        linhas_regras = [
            [
                Paragraph("<b>Regra</b>", normal),
                Paragraph("<b>Situação</b>", normal),
                Paragraph("<b>Justificativa</b>", normal),
            ]
        ]

        for regra in regras:
            elegivel = regra.get("elegivel", False)

            linhas_regras.append(
                [
                    Paragraph(escape(str(regra.get("nome", ""))), normal),
                    Paragraph(
                        "Elegível" if elegivel else "Ainda não elegível",
                        normal,
                    ),
                    Paragraph(
                        escape(str(regra.get("motivo", ""))),
                        normal,
                    ),
                ]
            )

        tabela_regras = Table(
            linhas_regras,
            colWidths=[5.1 * cm, 3.2 * cm, 8.7 * cm],
            repeatRows=1,
        )
        tabela_regras.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#ced4da")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                        colors.white,
                        colors.HexColor("#f8f9fa"),
                    ]),
                ]
            )
        )

        elementos.append(tabela_regras)
    else:
        elementos.append(
            Paragraph(
                "Nenhuma regra foi registrada no resultado desta simulação.",
                normal,
            )
        )

    elementos.extend(
        [
            Spacer(1, 16),
            Paragraph(
                "Observação: este relatório é uma estimativa baseada nos dados "
                "informados. A concessão e o cálculo definitivo dependem da "
                "análise administrativa e documental competente.",
                normal,
            ),
        ]
    )

    documento.build(
        elementos,
        onFirstPage=cabecalho_rodape,
        onLaterPages=cabecalho_rodape,
    )


def criar_tabela(linhas):
    tabela = Table(
        [
            [
                Paragraph(f"<b>{escape(str(rotulo))}</b>", getSampleStyleSheet()["BodyText"]),
                Paragraph(escape(str(valor)), getSampleStyleSheet()["BodyText"]),
            ]
            for rotulo, valor in linhas
        ],
        colWidths=[6.3 * cm, 10.7 * cm],
    )

    tabela.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#ced4da")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf2f8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return tabela
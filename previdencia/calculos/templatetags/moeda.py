from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def moeda_br(valor):
    if valor in (None, ""):
        return ""

    try:
        numero = Decimal(str(valor))

        if not numero.is_finite():
            return ""
    except (InvalidOperation, TypeError, ValueError):
        return str(valor)

    texto = f"{numero:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
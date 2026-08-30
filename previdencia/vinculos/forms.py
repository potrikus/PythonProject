import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError

from .models import Vinculo


class CampoMonetarioBR(forms.DecimalField):
    def prepare_value(self, value):
        if value in self.empty_values:
            return ""

        try:
            valor = Decimal(value).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            return value

        inteiro, centavos = f"{valor:.2f}".split(".")
        inteiro_formatado = f"{int(inteiro):,}".replace(",", ".")

        return f"{inteiro_formatado},{centavos}"

    def to_python(self, value):
        if value in self.empty_values:
            return None

        texto = str(value).strip()
        texto = re.sub(r"^R\$\s*", "", texto, flags=re.IGNORECASE).strip()

        formato_sem_milhar = r"\d{1,4}(?:,\d{2})?"
        formato_com_milhar = r"\d{1,3}(?:\.\d{3})+(?:,\d{2})?"

        if re.fullmatch(r"\d{5,}", texto):
            raise ValidationError(
                "O valor informado é ambíguo. Use o formato brasileiro, "
                "por exemplo: 3.850,00."
            )

        if not re.fullmatch(
            rf"(?:{formato_sem_milhar}|{formato_com_milhar})",
            texto,
        ):
            raise ValidationError(
                "Informe um valor monetário no formato brasileiro, "
                "por exemplo: 3.850,00."
            )

        valor_normalizado = texto.replace(".", "").replace(",", ".")

        try:
            return Decimal(valor_normalizado)
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError(
                "Informe um valor monetário válido, por exemplo: 3.850,00."
            )


class VinculoForm(forms.ModelForm):
    salario = CampoMonetarioBR(
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "decimal",
                "autocomplete": "off",
                "placeholder": "3.850,00",
                "data-moeda-br": "true",
            }
        ),
    )

    class Meta:
        model = Vinculo

        fields = [
            "cliente",
            "empresa",
            "tipo",
            "cargo",
            "data_inicio",
            "data_fim",
            "salario",
            "status",
            "observacoes",
        ]

        widgets = {
            "data_inicio": forms.DateInput(
                attrs={"type": "date"},
            ),
            "data_fim": forms.DateInput(
                attrs={"type": "date"},
            ),
            "observacoes": forms.Textarea(
                attrs={"rows": 4},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        for nome in ("cliente", "empresa", "tipo", "status"):
            self.fields[nome].widget.attrs["class"] = "form-select"

        self.fields["cliente"].queryset = (
            self.fields["cliente"].queryset.order_by("nome")
        )
        self.fields["empresa"].queryset = (
            self.fields["empresa"].queryset.order_by("razao_social")
        )
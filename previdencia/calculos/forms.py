import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Simulacao


class CampoMonetarioBR(forms.DecimalField):
    """
    Campo monetário brasileiro.

    Aceita:
        3850
        3850,50
        3.850,00
        R$ 3.850,00

    Rejeita:
        385000

    Valores inteiros com cinco ou mais dígitos devem usar o
    separador brasileiro, como 385.000,00.
    """

    def prepare_value(self, value):
        """Formata valores já gravados para exibição: 3.850,00."""
        if value in self.empty_values:
            return ""

        try:
            valor = Decimal(value).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            return value

        sinal = "-" if valor < 0 else ""
        valor = abs(valor)

        inteiro, centavos = f"{valor:.2f}".split(".")
        inteiro_formatado = f"{int(inteiro):,}".replace(",", ".")

        return f"{sinal}{inteiro_formatado},{centavos}"

    def to_python(self, value):
        if value in self.empty_values:
            return None

        texto = str(value).strip()
        texto = re.sub(r"^R\$\s*", "", texto, flags=re.IGNORECASE).strip()

        formato_sem_milhar = r"\d{1,4}(?:,\d{1,2})?"
        formato_com_milhar = r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?"

        if re.fullmatch(r"\d{5,}", texto):
            raise ValidationError(
                "O valor informado é ambíguo. Use o formato brasileiro, "
                "por exemplo: 3.850,00 ou 385.000,00."
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


class SimulacaoForm(forms.ModelForm):
    salario_medio_atualizado = CampoMonetarioBR(
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

    salario_contribuicao = CampoMonetarioBR(
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
        model = Simulacao

        fields = [
            "cliente",
            "data_referencia",
            "filiado_antes_reforma",
            "carencia_meses",
            "contribuicao_meses",
            "contribuicao_em_2019_meses",
            "magisterio_meses",
            "magisterio_em_2019_meses",
            "comprovacao_magisterio",
            "grau_exposicao",
            "exposicao_especial_meses",
            "ppp_comprovado",
            "atividade_rural_meses",
            "tempo_hibrido_meses",
            "comprovacao_rural",
            "grau_deficiencia",
            "deficiencia_meses",
            "deficiencia_reconhecida",
            "salario_medio_atualizado",
            "categoria",
            "salario_contribuicao",
        ]

        widgets = {
            "data_referencia": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        for nome in [
            "cliente",
            "categoria",
            "grau_exposicao",
            "grau_deficiencia",
        ]:
            self.fields[nome].widget.attrs["class"] = "form-select"

        for nome in [
            "filiado_antes_reforma",
            "ppp_comprovado",
            "comprovacao_rural",
            "comprovacao_magisterio",
            "deficiencia_reconhecida",
        ]:
            self.fields[nome].widget.attrs["class"] = "form-check-input"

        for nome in [
            "exposicao_especial_meses",
            "atividade_rural_meses",
            "tempo_hibrido_meses",
            "magisterio_meses",
            "magisterio_em_2019_meses",
            "deficiencia_meses",
        ]:
            self.fields[nome].required = False

        if not self.instance.pk:
            self.fields["data_referencia"].initial = timezone.localdate()

    def clean(self):
        cleaned = super().clean()

        campos_zero = [
            "exposicao_especial_meses",
            "atividade_rural_meses",
            "tempo_hibrido_meses",
            "magisterio_meses",
            "magisterio_em_2019_meses",
            "deficiencia_meses",
        ]

        for nome in campos_zero:
            cleaned[nome] = cleaned.get(nome) or 0

        contribuicao = cleaned.get("contribuicao_meses") or 0
        contribuicao_2019 = (
            cleaned.get("contribuicao_em_2019_meses") or 0
        )

        if contribuicao_2019 > contribuicao:
            self.add_error(
                "contribuicao_em_2019_meses",
                "O tempo em 2019 não pode superar o tempo total informado.",
            )

        exposicao = cleaned.get("exposicao_especial_meses") or 0
        grau_exposicao = cleaned.get("grau_exposicao")

        if exposicao and not grau_exposicao:
            self.add_error(
                "grau_exposicao",
                "Selecione o grau de exposição.",
            )

        magisterio = cleaned.get("magisterio_meses") or 0
        magisterio_2019 = cleaned.get("magisterio_em_2019_meses") or 0

        if magisterio_2019 > magisterio:
            self.add_error(
                "magisterio_em_2019_meses",
                "O tempo de magistério em 2019 não pode superar "
                "o total informado.",
            )

        deficiencia = cleaned.get("deficiencia_meses") or 0
        grau_deficiencia = cleaned.get("grau_deficiencia")

        if deficiencia and not grau_deficiencia:
            self.add_error(
                "grau_deficiencia",
                "Selecione o grau de deficiência reconhecido.",
            )

        return cleaned
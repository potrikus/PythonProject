from django import forms
from django.utils import timezone

from .models import Simulacao


class SimulacaoForm(forms.ModelForm):

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
                attrs={
                    "type": "date",
                }
            ),

            "salario_medio_atualizado": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "salario_contribuicao": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["cliente"].widget.attrs["class"] = "form-select"

        self.fields["categoria"].widget.attrs["class"] = "form-select"

        self.fields["grau_exposicao"].widget.attrs["class"] = "form-select"

        self.fields["grau_deficiencia"].widget.attrs["class"] = "form-select"

        campos_opcionais = [
            "exposicao_especial_meses",
            "atividade_rural_meses",
            "tempo_hibrido_meses",
            "magisterio_meses",
            "magisterio_em_2019_meses",
            "deficiencia_meses",
        ]

        for nome in campos_opcionais:
            self.fields[nome].required = False

        campos_checkbox = [
            "filiado_antes_reforma",
            "ppp_comprovado",
            "comprovacao_rural",
            "comprovacao_magisterio",
            "deficiencia_reconhecida",
        ]

        for nome in campos_checkbox:
            self.fields[nome].widget.attrs[
                "class"
            ] = "form-check-input"

        if not self.instance.pk:
            self.fields[
                "data_referencia"
            ].initial = timezone.localdate()

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

        contribuicao = cleaned.get(
            "contribuicao_meses"
        ) or 0

        contribuicao_2019 = cleaned.get(
            "contribuicao_em_2019_meses"
        ) or 0

        if contribuicao_2019 > contribuicao:
            self.add_error(
                "contribuicao_em_2019_meses",
                "O tempo em 2019 não pode superar "
                "o tempo total informado."
            )

        exposicao = cleaned.get(
            "exposicao_especial_meses"
        ) or 0

        grau_exposicao = cleaned.get(
            "grau_exposicao"
        )

        if exposicao and not grau_exposicao:
            self.add_error(
                "grau_exposicao",
                "Selecione o grau de exposição."
            )

        magisterio = cleaned.get(
            "magisterio_meses"
        ) or 0

        magisterio_2019 = cleaned.get(
            "magisterio_em_2019_meses"
        ) or 0

        if magisterio_2019 > magisterio:
            self.add_error(
                "magisterio_em_2019_meses",
                "O tempo de magistério em 2019 "
                "não pode superar o total informado."
            )

        deficiencia = cleaned.get(
            "deficiencia_meses"
        ) or 0

        grau_deficiencia = cleaned.get(
            "grau_deficiencia"
        )

        if deficiencia and not grau_deficiencia:
            self.add_error(
                "grau_deficiencia",
                "Selecione o grau de deficiência reconhecido."
            )

        return cleaned
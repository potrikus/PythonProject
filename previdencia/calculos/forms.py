from django import forms
from django.utils import timezone

from .models import Simulacao


class SimulacaoForm(forms.ModelForm):
    class Meta:
        model = Simulacao
        fields = ["cliente", "data_referencia", "filiado_antes_reforma", "carencia_meses", "contribuicao_meses", "contribuicao_em_2019_meses", "magisterio_meses", "magisterio_em_2019_meses", "comprovacao_magisterio", "grau_exposicao", "exposicao_especial_meses", "ppp_comprovado", "atividade_rural_meses", "tempo_hibrido_meses", "comprovacao_rural", "grau_deficiencia", "deficiencia_meses", "deficiencia_reconhecida", "salario_medio_atualizado", "categoria", "salario_contribuicao"]
        widgets = {"data_referencia": forms.DateInput(attrs={"type": "date"}), "salario_medio_atualizado": forms.NumberInput(attrs={"step": "0.01", "min": "0"}), "salario_contribuicao": forms.NumberInput(attrs={"step": "0.01", "min": "0"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["cliente"].widget.attrs["class"] = "form-select"
        self.fields["categoria"].widget.attrs["class"] = "form-select"
        self.fields["exposicao_especial_meses"].required = False
        self.fields["atividade_rural_meses"].required = False
        self.fields["tempo_hibrido_meses"].required = False
        self.fields["magisterio_meses"].required = False
        self.fields["magisterio_em_2019_meses"].required = False
        self.fields["deficiencia_meses"].required = False
        self.fields["filiado_antes_reforma"].widget.attrs["class"] = "form-check-input"
        self.fields["ppp_comprovado"].widget.attrs["class"] = "form-check-input"
        self.fields["comprovacao_rural"].widget.attrs["class"] = "form-check-input"
        self.fields["comprovacao_magisterio"].widget.attrs["class"] = "form-check-input"
        self.fields["deficiencia_reconhecida"].widget.attrs["class"] = "form-check-input"
        if not self.instance.pk:
            self.fields["data_referencia"].initial = timezone.localdate()

    def clean(self):
        cleaned = super().clean()
        cleaned["exposicao_especial_meses"] = cleaned.get("exposicao_especial_meses") or 0
        cleaned["atividade_rural_meses"] = cleaned.get("atividade_rural_meses") or 0
        cleaned["tempo_hibrido_meses"] = cleaned.get("tempo_hibrido_meses") or 0
        cleaned["magisterio_meses"] = cleaned.get("magisterio_meses") or 0
        cleaned["magisterio_em_2019_meses"] = cleaned.get("magisterio_em_2019_meses") or 0
        cleaned["deficiencia_meses"] = cleaned.get("deficiencia_meses") or 0
        if cleaned.get("contribuicao_em_2019_meses", 0) > cleaned.get("contribuicao_meses", 0):
            self.add_error("contribuicao_em_2019_meses", "O tempo em 2019 não pode superar o tempo total informado.")
        if cleaned.get("exposicao_especial_meses", 0) and not cleaned.get("grau_exposicao"):
            self.add_error("grau_exposicao", "Selecione o grau de exposição para avaliar a aposentadoria especial.")
        if cleaned.get("magisterio_em_2019_meses", 0) > cleaned.get("magisterio_meses", 0):
            self.add_error("magisterio_em_2019_meses", "O tempo de magistério em 2019 não pode superar o total informado.")
        if cleaned.get("deficiencia_meses", 0) and not cleaned.get("grau_deficiencia"):
            self.add_error("grau_deficiencia", "Selecione o grau de deficiência reconhecido.")
        return cleaned

from django import forms

from .models import Vinculo


class VinculoForm(forms.ModelForm):
    class Meta:
        model = Vinculo
        fields = ["cliente", "empresa", "tipo", "cargo", "data_inicio", "data_fim", "salario", "status", "observacoes"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
            "salario": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        for nome in ("cliente", "empresa", "tipo", "status"):
            self.fields[nome].widget.attrs["class"] = "form-select"
        self.fields["cliente"].queryset = self.fields["cliente"].queryset.order_by("nome")
        self.fields["empresa"].queryset = self.fields["empresa"].queryset.order_by("razao_social")

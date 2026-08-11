import re

from django import forms

from .models import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            "razao_social", "nome_fantasia", "cnpj", "inscricao_estadual", "telefone", "email",
            "cep", "endereco", "numero", "complemento", "bairro", "cidade", "estado", "observacoes",
        ]
        widgets = {
            "estado": forms.TextInput(attrs={"maxlength": 2, "style": "text-transform: uppercase;"}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_cnpj(self):
        cnpj = re.sub(r"\D", "", self.cleaned_data["cnpj"])
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            raise forms.ValidationError("Informe um CNPJ válido com 14 dígitos.")
        for tamanho in (12, 13):
            pesos = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2) if tamanho == 12 else (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
            total = sum(int(cnpj[indice]) * peso for indice, peso in enumerate(pesos))
            digito = 0 if total % 11 < 2 else 11 - total % 11
            if int(cnpj[tamanho]) != digito:
                raise forms.ValidationError("Informe um CNPJ válido.")
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    def clean_estado(self):
        return self.cleaned_data["estado"].upper()

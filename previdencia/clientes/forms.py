import re

from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome", "cpf", "rg", "nascimento", "sexo", "estado_civil", "telefone", "celular", "email",
            "cep", "endereco", "numero", "complemento", "bairro", "cidade", "estado", "pis", "beneficio", "observacoes",
        ]
        widgets = {
            "nascimento": forms.DateInput(attrs={"type": "date"}),
            "estado": forms.TextInput(attrs={"maxlength": 2, "style": "text-transform: uppercase;"}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["sexo"].widget.attrs["class"] = "form-select"
        self.fields["estado_civil"].widget.attrs["class"] = "form-select"

    def clean_cpf(self):
        cpf = re.sub(r"\D", "", self.cleaned_data["cpf"])
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            raise forms.ValidationError("Informe um CPF válido com 11 dígitos.")
        for posicao in (9, 10):
            soma = sum(int(cpf[indice]) * (posicao + 1 - indice) for indice in range(posicao))
            digito = (soma * 10 % 11) % 10
            if int(cpf[posicao]) != digito:
                raise forms.ValidationError("Informe um CPF válido.")
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    def clean_estado(self):
        return self.cleaned_data["estado"].upper()

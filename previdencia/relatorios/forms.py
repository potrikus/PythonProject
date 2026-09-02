from django import forms

from clientes.models import Cliente


class RelatorioClienteForm(forms.Form):
    busca = forms.CharField(
        required=False,
        label="Buscar cliente",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nome ou CPF",
            }
        ),
    )

    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by("nome"),
        required=False,
        label="Cliente",
        empty_label="Todos os clientes",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
from django import forms

from clientes.models import Cliente


class RelatorioClienteForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by("nome"),
        label="Cliente",
        empty_label="Selecione um cliente",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
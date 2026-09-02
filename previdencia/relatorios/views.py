from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from calculos.models import Simulacao
from clientes.models import Cliente
from vinculos.models import Vinculo

from .forms import RelatorioClienteForm


def lista(request):
    form = RelatorioClienteForm(request.GET or None)

    simulacoes = (
        Simulacao.objects
        .select_related("cliente")
        .order_by("-criado_em")
    )

    if form.is_valid():
        busca = form.cleaned_data["busca"].strip()
        cliente = form.cleaned_data["cliente"]

        if busca:
            simulacoes = simulacoes.filter(
                Q(cliente__nome__icontains=busca)
                | Q(cliente__cpf__icontains=busca)
            )

        if cliente:
            simulacoes = simulacoes.filter(cliente=cliente)

    return render(
        request,
        "relatorios/lista.html",
        {
            "form": form,
            "simulacoes": simulacoes,
            "quantidade_simulacoes": simulacoes.count(),
        },
    )


def previdenciario(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    vinculos = (
        Vinculo.objects
        .select_related("empresa")
        .filter(cliente=cliente)
    )

    simulacoes = (
        Simulacao.objects
        .filter(cliente=cliente)
        .order_by("-criado_em")
    )

    melhor_regra = None

    if simulacoes.exists():
        ultima = simulacoes.first()

        for regra in ultima.resultado.get("regras", []):
            if regra.get("elegivel"):
                melhor_regra = regra
                break

    return render(
        request,
        "relatorios/previdenciario.html",
        {
            "cliente": cliente,
            "vinculos": vinculos,
            "simulacoes": simulacoes,
            "melhor_regra": melhor_regra,
        },
    )
from django.shortcuts import get_object_or_404, render

from clientes.models import Cliente
from vinculos.models import Vinculo
from calculos.models import Simulacao

from .forms import RelatorioClienteForm


def lista(request):
    form = RelatorioClienteForm(request.GET or None)

    if form.is_valid():
        cliente = form.cleaned_data["cliente"]

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
                "vinculos": Vinculo.objects.select_related("empresa").filter(
                    cliente=cliente
                ),
                "simulacoes": simulacoes,
                "melhor_regra": melhor_regra,
            },
        )

    return render(
        request,
        "relatorios/lista.html",
        {"form": form},
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
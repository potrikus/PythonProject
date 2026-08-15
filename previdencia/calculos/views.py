from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SimulacaoForm
from .models import Simulacao
from .services import calcular_contribuicao, simular


def lista(request):

    simulacoes = (
        Simulacao.objects
        .select_related("cliente")
        .all()
    )

    return render(
        request,
        "calculos/lista.html",
        {
            "simulacoes": simulacoes,
        },
    )


def nova(request):

    form = SimulacaoForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        simulacao = form.save(
            commit=False
        )

        simulacao.resultado = simular(
            cliente=simulacao.cliente,
            referencia=simulacao.data_referencia,
            carencia=simulacao.carencia_meses,
            meses_contribuicao=simulacao.contribuicao_meses,
            meses_2019=simulacao.contribuicao_em_2019_meses,
            filiado_antes=simulacao.filiado_antes_reforma,
            media=simulacao.salario_medio_atualizado,

            grau_exposicao=simulacao.grau_exposicao,
            exposicao_meses=simulacao.exposicao_especial_meses,
            ppp_comprovado=simulacao.ppp_comprovado,

            rural_meses=simulacao.atividade_rural_meses,
            hibrido_meses=simulacao.tempo_hibrido_meses,
            comprovacao_rural=simulacao.comprovacao_rural,

            magisterio_meses=simulacao.magisterio_meses,
            magisterio_2019_meses=(
                simulacao.magisterio_em_2019_meses
            ),
            comprovacao_magisterio=(
                simulacao.comprovacao_magisterio
            ),

            grau_deficiencia=simulacao.grau_deficiencia,
            deficiencia_meses=simulacao.deficiencia_meses,
            deficiencia_reconhecida=(
                simulacao.deficiencia_reconhecida
            ),
        )

        contribuicao = calcular_contribuicao(
            simulacao.salario_contribuicao,
            simulacao.categoria,
        )

        simulacao.resultado[
            "contribuicao_mensal"
        ] = (
            str(contribuicao)
            if contribuicao is not None
            else None
        )

        simulacao.save()

        messages.success(
            request,
            "Simulação calculada e salva com sucesso."
        )

        return redirect(
            "calculos:detalhe",
            pk=simulacao.pk,
        )

    return render(
        request,
        "calculos/form.html",
        {
            "form": form,
        },
    )


def detalhe(request, pk):

    simulacao = get_object_or_404(
        Simulacao.objects.select_related("cliente"),
        pk=pk,
    )

    return render(
        request,
        "calculos/detalhe.html",
        {
            "simulacao": simulacao,
        },
    )
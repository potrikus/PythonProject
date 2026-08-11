from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SimulacaoForm
from .models import Simulacao
from .services import calcular_contribuicao, simular


def lista(request):
    simulacoes = Simulacao.objects.select_related("cliente")
    return render(request, "calculos/lista.html", {"simulacoes": simulacoes})


def nova(request):
    form = SimulacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        simulacao = form.save(commit=False)
        simulacao.resultado = simular(simulacao.cliente, simulacao.data_referencia, simulacao.carencia_meses, simulacao.contribuicao_meses, simulacao.contribuicao_em_2019_meses, simulacao.filiado_antes_reforma, simulacao.salario_medio_atualizado, simulacao.grau_exposicao, simulacao.exposicao_especial_meses, simulacao.ppp_comprovado, simulacao.atividade_rural_meses, simulacao.tempo_hibrido_meses, simulacao.comprovacao_rural, simulacao.magisterio_meses, simulacao.magisterio_em_2019_meses, simulacao.comprovacao_magisterio, simulacao.grau_deficiencia, simulacao.deficiencia_meses, simulacao.deficiencia_reconhecida)
        simulacao.resultado["contribuicao_mensal"] = str(calcular_contribuicao(simulacao.salario_contribuicao, simulacao.categoria)) if simulacao.salario_contribuicao else None
        simulacao.save()
        messages.success(request, "Simulação calculada e salva com sucesso.")
        return redirect("calculos:detalhe", pk=simulacao.pk)
    return render(request, "calculos/form.html", {"form": form})


def detalhe(request, pk):
    simulacao = get_object_or_404(Simulacao.objects.select_related("cliente"), pk=pk)
    return render(request, "calculos/detalhe.html", {"simulacao": simulacao})

# Create your views here.

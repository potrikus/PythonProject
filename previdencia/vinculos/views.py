from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import VinculoForm
from .models import Vinculo


def lista(request):
    termo = request.GET.get("q", "").strip()
    vinculos = Vinculo.objects.select_related("cliente", "empresa")
    if termo:
        vinculos = vinculos.filter(Q(cliente__nome__icontains=termo) | Q(empresa__razao_social__icontains=termo) | Q(empresa__nome_fantasia__icontains=termo) | Q(cargo__icontains=termo))
    return render(request, "vinculos/lista.html", {"vinculos": vinculos, "termo": termo})


def cadastrar(request):
    form = VinculoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vínculo cadastrado com sucesso.")
        return redirect("vinculos:lista")
    return render(request, "vinculos/form.html", {"form": form, "titulo": "Novo vínculo"})


def editar(request, pk):
    vinculo = get_object_or_404(Vinculo, pk=pk)
    form = VinculoForm(request.POST or None, instance=vinculo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vínculo atualizado com sucesso.")
        return redirect("vinculos:lista")
    return render(request, "vinculos/form.html", {"form": form, "titulo": "Editar vínculo", "vinculo": vinculo})


def excluir(request, pk):
    vinculo = get_object_or_404(Vinculo, pk=pk)
    if request.method == "POST":
        vinculo.delete()
        messages.success(request, "Vínculo excluído com sucesso.")
        return redirect("vinculos:lista")
    return render(request, "vinculos/confirmar_exclusao.html", {"vinculo": vinculo})

# Create your views here.

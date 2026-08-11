from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmpresaForm
from .models import Empresa


def lista(request):
    termo = request.GET.get("q", "").strip()
    empresas = Empresa.objects.all()
    if termo:
        empresas = empresas.filter(Q(razao_social__icontains=termo) | Q(nome_fantasia__icontains=termo) | Q(cnpj__icontains=termo) | Q(cidade__icontains=termo))
    return render(request, "empresas/lista.html", {"empresas": empresas, "termo": termo})


def cadastrar(request):
    form = EmpresaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Empresa cadastrada com sucesso.")
        return redirect("empresas:lista")
    return render(request, "empresas/form.html", {"form": form, "titulo": "Nova empresa"})


def editar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    form = EmpresaForm(request.POST or None, instance=empresa)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Dados da empresa atualizados com sucesso.")
        return redirect("empresas:lista")
    return render(request, "empresas/form.html", {"form": form, "titulo": "Editar empresa", "empresa": empresa})


def excluir(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == "POST":
        empresa.delete()
        messages.success(request, "Empresa excluída com sucesso.")
        return redirect("empresas:lista")
    return render(request, "empresas/confirmar_exclusao.html", {"empresa": empresa})

# Create your views here.

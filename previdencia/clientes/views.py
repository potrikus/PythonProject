from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm
from .models import Cliente


def home(request):
    return render(request, "dashboard.html")


def lista(request):
    termo = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all()
    if termo:
        clientes = clientes.filter(
            Q(nome__icontains=termo) | Q(cpf__icontains=termo) | Q(cidade__icontains=termo) | Q(email__icontains=termo)
        )
    return render(request, "clientes/lista.html", {"clientes": clientes, "termo": termo})


def cadastrar(request):
    form = ClienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cliente cadastrado com sucesso.")
        return redirect("clientes:lista")
    return render(request, "clientes/form.html", {"form": form, "titulo": "Novo cliente"})


def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Dados do cliente atualizados com sucesso.")
        return redirect("clientes:lista")
    return render(request, "clientes/form.html", {"form": form, "titulo": "Editar cliente", "cliente": cliente})


def excluir(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        cliente.delete()
        messages.success(request, "Cliente excluído com sucesso.")
        return redirect("clientes:lista")
    return render(request, "clientes/confirmar_exclusao.html", {"cliente": cliente})

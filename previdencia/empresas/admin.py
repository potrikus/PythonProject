from django.contrib import admin

from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "cnpj", "telefone", "cidade")
    search_fields = ("razao_social", "nome_fantasia", "cnpj")
    list_filter = ("cidade", "estado")

# Register your models here.

from django.contrib import admin

from .models import Simulacao


@admin.register(Simulacao)
class SimulacaoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "data_referencia", "filiado_antes_reforma", "criado_em")
    list_filter = ("filiado_antes_reforma", "categoria")
    search_fields = ("cliente__nome", "cliente__cpf")

# Register your models here.

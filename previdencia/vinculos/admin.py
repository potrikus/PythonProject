from django.contrib import admin

from .models import Vinculo


@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "empresa", "tipo", "data_inicio", "status")
    list_filter = ("tipo", "status")
    search_fields = ("cliente__nome", "empresa__razao_social", "empresa__nome_fantasia", "cargo")

# Register your models here.

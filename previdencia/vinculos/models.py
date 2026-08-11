from django.core.exceptions import ValidationError
from django.db import models

from clientes.models import Cliente
from empresas.models import Empresa


class Vinculo(models.Model):
    TIPOS = [
        ("CLT", "CLT"),
        ("Autônomo", "Autônomo"),
        ("Doméstico", "Empregado doméstico"),
        ("Rural", "Trabalhador rural"),
        ("Servidor", "Servidor público"),
        ("Outro", "Outro"),
    ]
    STATUS = [("Ativo", "Ativo"), ("Encerrado", "Encerrado")]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="vinculos")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="vinculos")
    tipo = models.CharField(max_length=20, choices=TIPOS)
    cargo = models.CharField(max_length=120, blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    salario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS, default="Ativo")
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_inicio", "cliente__nome"]
        verbose_name = "Vínculo"
        verbose_name_plural = "Vínculos"

    def __str__(self):
        return f"{self.cliente} — {self.empresa}"

    def clean(self):
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError({"data_fim": "A data de fim não pode ser anterior à data de início."})

# Create your models here.

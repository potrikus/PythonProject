from django.db import models


class Cliente(models.Model):

    SEXO = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]

    ESTADO_CIVIL = [
        ("Solteiro", "Solteiro"),
        ("Casado", "Casado"),
        ("Divorciado", "Divorciado"),
        ("Viúvo", "Viúvo"),
        ("União Estável", "União Estável"),
    ]

    nome = models.CharField(
        max_length=200
    )

    cpf = models.CharField(
        max_length=14,
        unique=True
    )

    rg = models.CharField(
        max_length=20,
        blank=True
    )

    nascimento = models.DateField()

    sexo = models.CharField(
        max_length=1,
        choices=SEXO
    )

    estado_civil = models.CharField(
        max_length=20,
        choices=ESTADO_CIVIL,
        blank=True
    )

    telefone = models.CharField(
        max_length=20,
        blank=True
    )

    celular = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    cep = models.CharField(
        max_length=10,
        blank=True
    )

    endereco = models.CharField(
        max_length=200,
        blank=True
    )

    numero = models.CharField(
        max_length=10,
        blank=True
    )

    complemento = models.CharField(
        max_length=100,
        blank=True
    )

    bairro = models.CharField(
        max_length=100,
        blank=True
    )

    cidade = models.CharField(
        max_length=100,
        blank=True
    )

    estado = models.CharField(
        max_length=2,
        blank=True
    )

    pis = models.CharField(
        max_length=20,
        blank=True
    )

    beneficio = models.CharField(
        max_length=30,
        blank=True
    )

    observacoes = models.TextField(
        blank=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nome
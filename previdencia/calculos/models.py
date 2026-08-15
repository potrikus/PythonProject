from django.db import models

from clientes.models import Cliente


class Simulacao(models.Model):

    CATEGORIAS = [
        (
            "EMPREGADO",
            "Empregado, doméstico ou avulso",
        ),
        (
            "INDIVIDUAL",
            "Contribuinte individual (20%)",
        ),
        (
            "SIMPLIFICADO",
            "Facultativo / plano simplificado (11%)",
        ),
        (
            "MEI",
            "MEI / facultativo baixa renda (5%)",
        ),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="simulacoes",
    )

    data_referencia = models.DateField()

    filiado_antes_reforma = models.BooleanField(
        default=False
    )

    carencia_meses = models.PositiveIntegerField(
        help_text="Quantidade de contribuições válidas para carência."
    )

    contribuicao_meses = models.PositiveIntegerField(
        help_text="Tempo total de contribuição em meses."
    )

    contribuicao_em_2019_meses = models.PositiveIntegerField(
        default=0,
        help_text="Tempo de contribuição apurado em 13/11/2019."
    )

    salario_medio_atualizado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Média já atualizada monetariamente pelo CNIS."
    )

    categoria = models.CharField(
        max_length=15,
        choices=CATEGORIAS,
        default="EMPREGADO",
    )

    salario_contribuicao = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    grau_exposicao = models.PositiveSmallIntegerField(
        choices=[
            (15, "15 anos"),
            (20, "20 anos"),
            (25, "25 anos"),
        ],
        blank=True,
        null=True,
    )

    exposicao_especial_meses = models.PositiveIntegerField(
        default=0,
        help_text="Tempo de efetiva exposição, em meses."
    )

    ppp_comprovado = models.BooleanField(
        default=False,
        help_text="PPP/LTCAT válido para os períodos especiais."
    )

    atividade_rural_meses = models.PositiveIntegerField(
        default=0,
        help_text="Meses de atividade rural comprovável."
    )

    tempo_hibrido_meses = models.PositiveIntegerField(
        default=0,
        help_text="Total de meses urbanos e rurais para a modalidade híbrida."
    )

    comprovacao_rural = models.BooleanField(
        default=False,
        help_text="Documentos/autodeclaração rural disponíveis."
    )

    magisterio_meses = models.PositiveIntegerField(
        default=0,
        help_text="Tempo exclusivo de magistério na educação básica, em meses."
    )

    magisterio_em_2019_meses = models.PositiveIntegerField(
        default=0
    )

    comprovacao_magisterio = models.BooleanField(
        default=False
    )

    grau_deficiencia = models.CharField(
        max_length=10,
        choices=[
            ("LEVE", "Leve"),
            ("MODERADA", "Moderada"),
            ("GRAVE", "Grave"),
        ],
        blank=True,
    )

    deficiencia_meses = models.PositiveIntegerField(
        default=0,
        help_text="Tempo de contribuição na condição de pessoa com deficiência."
    )

    deficiencia_reconhecida = models.BooleanField(
        default=False,
        help_text="Grau reconhecido em avaliação médico-social do INSS."
    )

    resultado = models.JSONField(
        default=dict,
        editable=False,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Simulação"
        verbose_name_plural = "Simulações"

    def __str__(self):
        return (
            f"Simulação de {self.cliente} "
            f"em {self.data_referencia:%d/%m/%Y}"
        )
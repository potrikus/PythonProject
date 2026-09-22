from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from calculos.models import Simulacao
from clientes.models import Cliente


class RelatoriosViewsTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.usuario = User.objects.create_user(
            username="teste",
            password="Teste@123456",
        )

        self.client.login(
            username="teste",
            password="Teste@123456",
        )

        self.cliente_maria = Cliente.objects.create(
            nome="Maria da Silva",
            cpf="529.982.247-25",
            nascimento=date(1960, 1, 1),
            sexo="F",
        )

        self.cliente_joao = Cliente.objects.create(
            nome="João Pereira",
            cpf="111.444.777-35",
            nascimento=date(1965, 2, 10),
            sexo="M",
        )

        self.simulacao_maria = Simulacao.objects.create(
            cliente=self.cliente_maria,
            data_referencia=date(2026, 8, 8),
            filiado_antes_reforma=True,
            carencia_meses=180,
            contribuicao_meses=360,
            contribuicao_em_2019_meses=300,
            salario_medio_atualizado=Decimal("3000.00"),
            salario_contribuicao=Decimal("1621.00"),
            resultado={
                "estimativa_beneficio": "2700.00",
                "quantidade_regras_elegiveis": 1,
                "regras": [
                    {
                        "nome": "Aposentadoria programada",
                        "elegivel": True,
                        "motivo": "Requisitos atendidos.",
                    }
                ],
            },
        )

        self.simulacao_joao = Simulacao.objects.create(
            cliente=self.cliente_joao,
            data_referencia=date(2026, 8, 9),
            filiado_antes_reforma=False,
            carencia_meses=180,
            contribuicao_meses=180,
            contribuicao_em_2019_meses=0,
            resultado={
                "quantidade_regras_elegiveis": 0,
                "regras": [],
            },
        )

    def test_lista_exibe_simulacoes(self):
        response = self.client.get(
            reverse("relatorios:lista")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Maria da Silva",
        )

        self.assertContains(
            response,
            "João Pereira",
        )

        self.assertContains(
            response,
            "R$ 2.700,00",
        )

    def test_lista_filtra_por_nome(self):
        response = self.client.get(
            reverse("relatorios:lista"),
            {"busca": "Maria"},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            list(response.context["simulacoes"]),
            [self.simulacao_maria],
        )

        self.assertEqual(
            response.context["quantidade_simulacoes"],
            1,
        )

    def test_lista_filtra_por_cpf(self):
        response = self.client.get(
            reverse("relatorios:lista"),
            {"busca": "111.444.777-35"},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            list(response.context["simulacoes"]),
            [self.simulacao_joao],
        )

        self.assertEqual(
            response.context["quantidade_simulacoes"],
            1,
        )

    def test_lista_filtra_por_cliente(self):
        response = self.client.get(
            reverse("relatorios:lista"),
            {"cliente": self.cliente_maria.pk},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            list(response.context["simulacoes"]),
            [self.simulacao_maria],
        )

        self.assertEqual(
            response.context["quantidade_simulacoes"],
            1,
        )

    def test_relatorio_previdenciario_do_cliente(self):
        response = self.client.get(
            reverse(
                "relatorios:previdenciario",
                args=[self.cliente_maria.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Maria da Silva",
        )

    def test_acesso_sem_login_redireciona_para_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("relatorios:lista")
        )

        self.assertRedirects(
            response,
            "/login/?next=/relatorios/",
        )
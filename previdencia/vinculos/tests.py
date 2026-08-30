from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from empresas.models import Empresa

from .models import Vinculo


class VinculoViewsTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Maria da Silva",
            cpf="529.982.247-25",
            nascimento="1985-05-10",
            sexo="F",
        )

        self.empresa = Empresa.objects.create(
            razao_social="Empresa Exemplo LTDA",
            cnpj="04.252.011/0001-10",
        )

        self.dados = {
            "cliente": self.cliente.pk,
            "empresa": self.empresa.pk,
            "tipo": "CLT",
            "cargo": "Analista",
            "data_inicio": "2020-01-10",
            "salario": "2.500,00",
            "status": "Ativo",
        }

    def test_crud_e_busca(self):
        response = self.client.post(
            reverse("vinculos:cadastrar"),
            self.dados,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Vinculo.objects.count(), 1)
        self.assertRedirects(response, reverse("vinculos:lista"))

        vinculo = Vinculo.objects.get()
        self.assertEqual(vinculo.salario, Decimal("2500.00"))

        response = self.client.get(
            reverse("vinculos:lista"),
            {"q": "Maria"},
        )
        self.assertContains(response, "Analista")

        response = self.client.post(
            reverse("vinculos:editar", args=[vinculo.pk]),
            {
                **self.dados,
                "status": "Encerrado",
                "data_fim": "2021-01-10",
            },
        )
        self.assertRedirects(response, reverse("vinculos:lista"))

        response = self.client.post(
            reverse("vinculos:excluir", args=[vinculo.pk]),
        )
        self.assertRedirects(response, reverse("vinculos:lista"))
        self.assertFalse(Vinculo.objects.exists())

    def test_data_final_anterior_e_invalida(self):
        response = self.client.post(
            reverse("vinculos:cadastrar"),
            {
                **self.dados,
                "data_fim": "2019-12-31",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data de fim")
        self.assertFalse(Vinculo.objects.exists())
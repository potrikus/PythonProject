from django.test import TestCase
from django.urls import reverse

from .models import Cliente


class ClienteViewsTests(TestCase):
    dados_cliente = {
        "nome": "Maria da Silva",
        "cpf": "529.982.247-25",
        "nascimento": "1985-05-10",
        "sexo": "F",
        "cidade": "São Paulo",
        "estado": "sp",
    }

    def test_lista_e_busca(self):
        Cliente.objects.create(**self.dados_cliente)
        response = self.client.get(reverse("clientes:lista"), {"q": "Maria"})
        self.assertContains(response, "Maria da Silva")

    def test_crud_de_cliente(self):
        response = self.client.post(reverse("clientes:cadastrar"), self.dados_cliente)
        self.assertRedirects(response, reverse("clientes:lista"))
        cliente = Cliente.objects.get(cpf="529.982.247-25")
        self.assertEqual(cliente.estado, "SP")

        response = self.client.post(
            reverse("clientes:editar", args=[cliente.pk]),
            {**self.dados_cliente, "nome": "Maria Silva Atualizada"},
        )
        self.assertRedirects(response, reverse("clientes:lista"))
        cliente.refresh_from_db()
        self.assertEqual(cliente.nome, "Maria Silva Atualizada")

        response = self.client.post(reverse("clientes:excluir", args=[cliente.pk]))
        self.assertRedirects(response, reverse("clientes:lista"))
        self.assertFalse(Cliente.objects.filter(pk=cliente.pk).exists())

    def test_cpf_invalido_nao_e_salvo(self):
        response = self.client.post(reverse("clientes:cadastrar"), {**self.dados_cliente, "cpf": "111.111.111-11"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informe um CPF")
        self.assertEqual(Cliente.objects.count(), 0)

# Create your tests here.

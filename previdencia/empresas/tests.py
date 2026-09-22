from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Empresa


class EmpresaViewsTests(TestCase):

    dados_empresa = {
        "razao_social": "Empresa Exemplo LTDA",
        "nome_fantasia": "Empresa Exemplo",
        "cnpj": "04.252.011/0001-10",
        "cidade": "Curitiba",
        "estado": "pr",
    }

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

    def test_lista_e_busca(self):
        Empresa.objects.create(**self.dados_empresa)

        response = self.client.get(
            reverse("empresas:lista"),
            {"q": "Exemplo"},
        )

        self.assertContains(
            response,
            "Empresa Exemplo LTDA",
        )

    def test_crud_de_empresa(self):
        response = self.client.post(
            reverse("empresas:cadastrar"),
            self.dados_empresa,
        )

        self.assertRedirects(
            response,
            reverse("empresas:lista"),
        )

        empresa = Empresa.objects.get(
            cnpj="04.252.011/0001-10"
        )

        self.assertEqual(
            empresa.estado,
            "PR",
        )

        response = self.client.post(
            reverse("empresas:editar", args=[empresa.pk]),
            {
                **self.dados_empresa,
                "razao_social": "Empresa Atualizada LTDA",
            },
        )

        self.assertRedirects(
            response,
            reverse("empresas:lista"),
        )

        response = self.client.post(
            reverse("empresas:excluir", args=[empresa.pk])
        )

        self.assertRedirects(
            response,
            reverse("empresas:lista"),
        )

        self.assertFalse(
            Empresa.objects.filter(
                pk=empresa.pk
            ).exists()
        )

    def test_cnpj_invalido_nao_e_salvo(self):
        response = self.client.post(
            reverse("empresas:cadastrar"),
            {
                **self.dados_empresa,
                "cnpj": "11.111.111/1111-11",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Informe um CNPJ",
        )

        self.assertEqual(
            Empresa.objects.count(),
            0,
        )

    def test_acesso_sem_login_redireciona_para_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("empresas:lista")
        )

        self.assertRedirects(
            response,
            "/login/?next=/empresas/",
        )
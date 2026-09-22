from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AutenticacaoTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.usuario = User.objects.create_user(
            username="teste",
            password="Teste@123456",
        )

    def test_login_com_credenciais_validas(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "teste",
                "password": "Teste@123456",
            },
        )

        self.assertRedirects(
            response,
            "/",
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_login_com_senha_invalida(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "teste",
                "password": "SenhaErrada",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Usuário ou senha inválidos.",
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_usuario_nao_autenticado_e_redirecionado(self):
        response = self.client.get(
            reverse("clientes:lista")
        )

        self.assertRedirects(
            response,
            "/login/?next=/clientes/",
        )

    def test_usuario_autenticado_acessa_sistema(self):
        self.client.login(
            username="teste",
            password="Teste@123456",
        )

        response = self.client.get("/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_logout(self):
        self.client.login(
            username="teste",
            password="Teste@123456",
        )

        response = self.client.post(
            reverse("logout")
        )

        self.assertRedirects(
            response,
            "/login/",
        )

        response = self.client.get(
            reverse("clientes:lista")
        )

        self.assertRedirects(
            response,
            "/login/?next=/clientes/",
        )

    def test_admin_exige_login(self):
        response = self.client.get("/admin/")

        self.assertRedirects(
            response,
            "/admin/login/?next=/admin/",
        )

    def test_usuario_comum_nao_acessa_admin(self):
        self.client.login(
            username="teste",
            password="Teste@123456",
        )

        response = self.client.get("/admin/")

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            response.url.startswith("/admin/login/")
        )

    def test_superusuario_acessa_admin(self):
        User = get_user_model()

        administrador = User.objects.create_superuser(
            username="administrador",
            password="Admin@123456",
            email="admin@example.com",
        )

        self.client.login(
            username="administrador",
            password="Admin@123456",
        )

        response = self.client.get("/admin/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.wsgi_request.user.is_superuser
        )
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente

from .models import Simulacao
from .services import calcular_contribuicao, simular


class CalculosTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Ana Souza",
            cpf="529.982.247-25",
            nascimento=date(1960, 1, 1),
            sexo="F",
        )

    def test_contribuicao_empregado_2026(self):
        self.assertEqual(
            calcular_contribuicao(Decimal("1621.00"), "EMPREGADO"),
            Decimal("121.58"),
        )
        self.assertEqual(
            calcular_contribuicao(Decimal("1621.00"), "MEI"),
            Decimal("81.05"),
        )

    def test_simulacao_programada(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            Decimal("3000"),
        )

        programada = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria programada"
        )

        self.assertTrue(programada["elegivel"])
        self.assertEqual(resultado["estimativa_beneficio"], "2700.00")

    def test_cria_simulacao_pela_rota(self):
        dados = {
            "cliente": self.cliente.pk,
            "data_referencia": "2026-08-08",
            "filiado_antes_reforma": "on",
            "carencia_meses": 180,
            "contribuicao_meses": 360,
            "contribuicao_em_2019_meses": 300,
            "salario_medio_atualizado": "3.000,00",
            "categoria": "EMPREGADO",
            "salario_contribuicao": "1.621,00",
        }

        response = self.client.post(reverse("calculos:nova"), dados)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Simulacao.objects.count(), 1)

        simulacao = Simulacao.objects.get()

        self.assertRedirects(
            response,
            reverse("calculos:detalhe", args=[simulacao.pk]),
        )
        self.assertEqual(
            simulacao.salario_medio_atualizado,
            Decimal("3000.00"),
        )
        self.assertEqual(
            simulacao.salario_contribuicao,
            Decimal("1621.00"),
        )
        self.assertEqual(
            simulacao.resultado["contribuicao_mensal"],
            "121.58",
        )

    def test_especial_transicao_exige_ppp(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            420,
            300,
            True,
            None,
            25,
            300,
            True,
        )

        especial = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria especial — transição"
        )

        self.assertTrue(especial["elegivel"])

        sem_ppp = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            420,
            300,
            True,
            None,
            25,
            300,
            False,
        )

        especial_sem_ppp = next(
            regra
            for regra in sem_ppp["regras"]
            if regra["nome"] == "Aposentadoria especial — transição"
        )

        self.assertFalse(especial_sem_ppp["elegivel"])

    def test_rural_e_hibrida(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            180,
            0,
            False,
            None,
            rural_meses=180,
            hibrido_meses=180,
            comprovacao_rural=True,
        )

        rural = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria por idade rural"
        )
        hibrida = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria por idade híbrida"
        )

        self.assertTrue(rural["elegivel"])
        self.assertTrue(hibrida["elegivel"])

    def test_professor_e_pcd(self):
        professor = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            None,
            magisterio_meses=360,
            magisterio_2019_meses=300,
            comprovacao_magisterio=True,
        )

        regra_professor = next(
            regra
            for regra in professor["regras"]
            if regra["nome"] == "Professor — regra programada"
        )

        self.assertTrue(regra_professor["elegivel"])

        pcd = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            0,
            False,
            None,
            grau_deficiencia="GRAVE",
            deficiencia_meses=240,
            deficiencia_reconhecida=True,
        )

        regra_pcd = next(
            regra
            for regra in pcd["regras"]
            if regra["nome"] == "PCD — por tempo de contribuição"
        )

        self.assertTrue(regra_pcd["elegivel"])
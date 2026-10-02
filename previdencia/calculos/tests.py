from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente

from .models import Simulacao
from .services import calcular_contribuicao, simular, calcular_coeficiente_pcd_idade


class CalculosTests(TestCase):

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

        self.cliente = Cliente.objects.create(
            nome="Ana Souza",
            cpf="529.982.247-25",
            nascimento=date(1960, 1, 1),
            sexo="F",
        )

    def test_pedagio_100_tempo_faltante(self):
        casos = [
            # meses_2019, meses_contribuicao_atual, elegibilidade
            (348, 372, True),
            (336, 396, True),
            (300, 420, True),
        ]

        for meses_2019, meses_contribuicao, esperado in casos:
            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                meses_contribuicao,
                meses_2019,
                True,
                None,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if "100%" in regra["nome"]
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha no pedágio de 100% com "
                f"{meses_2019} meses em 2019 e "
                f"{meses_contribuicao} meses atuais",
            )

    def test_pedagio_100_limite_idade(self):
        casos = [
            (date(1969, 8, 8), True),  # exatamente 57 anos
            (date(1970, 8, 8), False),  # exatamente 56 anos
        ]

        nascimento_original = self.cliente.nascimento

        for nascimento, esperado in casos:
            self.cliente.nascimento = nascimento
            self.cliente.save(update_fields=["nascimento"])

            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                372,
                348,
                True,
                None,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"] == "Transição com pedágio de 100%"
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha no limite de idade do pedágio de 100% "
                f"para nascimento em {nascimento}",
            )

        self.cliente.nascimento = nascimento_original
        self.cliente.save(update_fields=["nascimento"])

    # ========================================================
    # CONTRIBUIÇÃO
    # ========================================================

    def test_contribuicao_empregado_2026(self):
        self.assertEqual(
            calcular_contribuicao(
                Decimal("1621.00"),
                "EMPREGADO",
            ),
            Decimal("121.58"),
        )

        self.assertEqual(
            calcular_contribuicao(
                Decimal("1621.00"),
                "MEI",
            ),
            Decimal("81.05"),
        )

    # ========================================================
    # APOSENTADORIA PROGRAMADA
    # ========================================================

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

        self.assertTrue(
            programada["elegivel"]
        )

        self.assertEqual(
            resultado["estimativa_beneficio"],
            "2700.00",
        )

    # ========================================================
    # ROTA DE NOVA SIMULAÇÃO
    # ========================================================

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

        response = self.client.post(
            reverse("calculos:nova"),
            dados,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            Simulacao.objects.count(),
            1,
        )

        simulacao = Simulacao.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "calculos:detalhe",
                args=[simulacao.pk],
            ),
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
            simulacao.resultado[
                "contribuicao_mensal"
            ],
            "121.58",
        )

    # ========================================================
    # APOSENTADORIA ESPECIAL
    # ========================================================

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
            if regra["nome"]
            == "Aposentadoria especial — transição"
        )

        self.assertTrue(
            especial["elegivel"]
        )

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
            if regra["nome"]
            == "Aposentadoria especial — transição"
        )

        self.assertFalse(
            especial_sem_ppp["elegivel"]
        )

    # ========================================================
    # RURAL E HÍBRIDA
    # ========================================================

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
            if regra["nome"]
            == "Aposentadoria por idade rural"
        )

        hibrida = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Aposentadoria por idade híbrida"
        )

        self.assertTrue(
            rural["elegivel"]
        )

        self.assertTrue(
            hibrida["elegivel"]
        )

    # ========================================================
    # PROFESSOR E PCD
    # ========================================================

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
            if regra["nome"]
            == "Professor — regra programada"
        )

        self.assertTrue(
            regra_professor["elegivel"]
        )

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
            if regra["nome"]
            == "PCD — por tempo de contribuição"
        )

        self.assertTrue(
            regra_pcd["elegivel"]
        )

    # ========================================================
    # NOVOS TESTES
    # ========================================================

    # --------------------------------------------------------
    # TRANSIÇÃO POR PONTOS - 2026
    # --------------------------------------------------------

    def test_transicao_pontos_2026(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            None,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Transição por pontos"
        )

        self.assertTrue(
            regra["elegivel"]
        )

        self.assertIn(
            "93",
            regra["motivo"],
        )

    def test_transicao_pontos_progressao_historica(self):
        casos = [
            (2019, "86"),
            (2020, "87"),
            (2021, "88"),
            (2022, "89"),
            (2023, "90"),
            (2024, "91"),
            (2025, "92"),
            (2026, "93"),
            (2027, "94"),
            (2030, "97"),
            (2032, "99"),
            (2033, "100"),
            (2034, "100"),
        ]

        for ano, pontos_esperados in casos:
            resultado = simular(
                self.cliente,
                date(ano, 8, 8),
                180,
                360,
                300,
                True,
                None,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"] == "Transição por pontos"
            )

            self.assertIn(
                pontos_esperados,
                regra["motivo"],
                f"Falha na progressão de pontos em {ano}",
            )
    # --------------------------------------------------------
    # TRANSIÇÃO POR PONTOS - NÃO ATINGIU
    # --------------------------------------------------------

    def test_transicao_pontos_nao_elegivel(self):
        cliente = Cliente.objects.create(
            nome="Maria Jovem",
            cpf="111.444.777-35",
            nascimento=date(1975, 1, 1),
            sexo="F",
        )

        resultado = simular(
            cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            None,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Transição por pontos"
        )

        self.assertFalse(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # IDADE PROGRESSIVA
    # --------------------------------------------------------

    def test_idade_progressiva_2026(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            None,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Transição por idade progressiva"
        )

        self.assertTrue(
            regra["elegivel"]
        )

        self.assertIn(
            "59.5",
            regra["motivo"],
        )

    def test_idade_progressiva_historica(self):
        casos = [
            (2024, "58.5"),
            (2025, "59.0"),
            (2026, "59.5"),
            (2027, "60.0"),
            (2028, "60.5"),
            (2029, "61.0"),
            (2030, "61.5"),
            (2031, "62"),
            (2032, "62"),
        ]

        for ano, idade_esperada in casos:
            resultado = simular(
                self.cliente,
                date(ano, 8, 8),
                180,
                360,
                300,
                True,
                None,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"] == "Transição por idade progressiva"
            )

            self.assertIn(
                idade_esperada,
                regra["motivo"],
                f"Falha na idade progressiva em {ano}",
            )
    # --------------------------------------------------------
    # PEDÁGIO DE 50% - CASO VÁLIDO
    # --------------------------------------------------------

    def test_pedagio_50_valido(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            372,
            336,
            True,
            None,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Transição com pedágio de 50%"
        )

        self.assertTrue(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # PEDÁGIO DE 50% - EXATAMENTE 24 MESES
    #
    # Deve ser elegível.
    # A regra oficial utiliza "até 24 meses".
    # --------------------------------------------------------

    def test_pedagio_50_exatamente_24_meses(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            372,
            336,
            True,
            None,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Transição com pedágio de 50%"
        )

        self.assertTrue(
            regra["elegivel"]
        )

        self.assertIn(
            "2.00 anos",
            regra["motivo"],
        )

    # --------------------------------------------------------
    # PEDÁGIO DE 50% - MAIS DE 24 MESES
    # --------------------------------------------------------

    def test_pedagio_50_mais_de_24_meses(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            335,
            True,
            None,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Transição com pedágio de 50%"
        )

        self.assertFalse(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # PEDÁGIO DE 100%
    # --------------------------------------------------------

    def test_pedagio_100(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            420,
            300,
            True,
            None,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Transição com pedágio de 100%"
        )

        self.assertTrue(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # DIREITO ADQUIRIDO ESPECIAL
    #
    # O tempo especial deve ser analisado por
    # exposicao_meses, e não por meses_2019.
    # --------------------------------------------------------

    def test_especial_direito_adquirido_usa_exposicao(self):
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

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Aposentadoria especial — direito adquirido"
        )

        self.assertTrue(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # DIREITO ADQUIRIDO ESPECIAL - SEM TEMPO ESPECIAL
    # --------------------------------------------------------

    def test_especial_direito_adquirido_sem_exposicao(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            420,
            300,
            True,
            None,
            25,
            299,
            True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Aposentadoria especial — direito adquirido"
        )

        self.assertFalse(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # ESPECIAL SEM PPP
    # --------------------------------------------------------

    def test_especial_direito_adquirido_sem_ppp(self):
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
            False,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Aposentadoria especial — direito adquirido"
        )

        self.assertFalse(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # PROFESSOR - PONTOS 2026
    # --------------------------------------------------------

    def test_professor_pontos_2026(self):
        casos = [
            # Mulher: 61 + 27 = 88
            (date(1965, 8, 8), "F", 324, 300, True),

            # Mulher: 61 + 26 = 87
            (date(1965, 8, 8), "F", 312, 300, False),

            # Homem: 60 + 38 = 98
            (date(1966, 8, 8), "M", 456, 360, True),

            # Homem: 60 + 37 = 97
            (date(1966, 8, 8), "M", 444, 360, False),
        ]

        for (
                nascimento,
                sexo,
                meses_contribuicao,
                magisterio_meses,
                esperado,
        ) in casos:
            cliente = self.cliente
            cliente.sexo = sexo
            cliente.nascimento = nascimento
            cliente.save()

            resultado = simular(
                cliente,
                date(2026, 8, 8),
                180,
                meses_contribuicao,
                300,
                True,
                None,
                magisterio_meses=magisterio_meses,
                comprovacao_magisterio=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"]
                == "Professor — transição por pontos"
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
            )

    # --------------------------------------------------------
    # PROFESSOR - PEDÁGIO 100%
    # --------------------------------------------------------

    def test_professor_pedagio_100(self):
        resultado = simular(
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

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Professor — pedágio de 100%"
        )

        self.assertTrue(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # PCD - GRAU GRAVE
    # --------------------------------------------------------

    def test_pcd_grave(self):
        resultado = simular(
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

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "PCD — por tempo de contribuição"
        )

        self.assertTrue(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # PCD - SEM RECONHECIMENTO
    # --------------------------------------------------------

    def test_pcd_sem_reconhecimento(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            0,
            False,
            None,
            grau_deficiencia="GRAVE",
            deficiencia_meses=240,
            deficiencia_reconhecida=False,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "PCD — por tempo de contribuição"
        )

        self.assertFalse(
            regra["elegivel"]
        )

    # --------------------------------------------------------
    # CARÊNCIA INSUFICIENTE
    # --------------------------------------------------------

    def test_carencia_insuficiente(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            179,
            360,
            300,
            True,
            None,
        )

        for regra in resultado["regras"]:

            if (
                regra["nome"]
                in (
                    "Aposentadoria programada",
                    "Transição por pontos",
                    "Transição por idade progressiva",
                    "Transição com pedágio de 50%",
                    "Transição com pedágio de 100%",
                )
            ):
                self.assertFalse(
                    regra["elegivel"]
                )

    def test_pedagio_50_limites(self):
        casos = [
            # meses_2019, meses_contribuicao_atual, elegibilidade
            (348, 366, True),  # 29 anos + 1,5 ano = 30,5 anos
            (336, 396, True),  # 28 anos + 3 anos = 33 anos
            (335, 420, False),  # mais de 24 meses faltantes
        ]

        for meses_2019, meses_contribuicao, esperado in casos:
            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                meses_contribuicao,
                meses_2019,
                True,
                None,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if "50%" in regra["nome"]
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha no limite do pedágio de 50% com "
                f"{meses_2019} meses em 2019 e "
                f"{meses_contribuicao} meses atuais",
            )

    def test_aposentadoria_especial_limites_tempo_exposicao(self):
        casos = [
            # grau, exposição em meses, esperado
            ("25", 299, False),
            ("25", 300, True),
            ("20", 239, False),
            ("20", 240, True),
            ("15", 179, False),
            ("15", 180, True),
        ]

        for grau, exposicao_meses, esperado in casos:
            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                360,
                300,
                True,
                None,
                grau_exposicao=grau,
                exposicao_meses=exposicao_meses,
                ppp_comprovado=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if "especial" in regra["nome"].lower()
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha na aposentadoria especial "
                f"grau {grau} com {exposicao_meses} meses de exposição",
            )

    def test_aposentadoria_especial_exige_ppp(self):
        casos = [
            (True, True),
            (False, False),
        ]

        for ppp_comprovado, esperado in casos:
            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                360,
                300,
                True,
                None,
                grau_exposicao="25",
                exposicao_meses=300,
                ppp_comprovado=ppp_comprovado,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if "especial" in regra["nome"].lower()
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha na exigência de PPP "
                f"com ppp_comprovado={ppp_comprovado}",
            )

    def test_aposentadoria_especial_exige_carencia(self):
        casos = [
            (179, False),
            (180, True),
        ]

        for carencia, esperado in casos:
            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                carencia,
                360,
                300,
                True,
                None,
                grau_exposicao="25",
                exposicao_meses=300,
                ppp_comprovado=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if "especial" in regra["nome"].lower()
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha na carência da aposentadoria especial "
                f"com {carencia} meses",
            )

    def test_aposentadoria_especial_transicao_limite_pontos(self):
        casos = [
            (date(1965, 8, 8), "25", True),  # 61 + 25 = 86
            (date(1966, 8, 8), "25", False),  # 60 + 25 = 85
        ]

        nascimento_original = self.cliente.nascimento

        for nascimento, grau, esperado in casos:
            self.cliente.nascimento = nascimento
            self.cliente.save(update_fields=["nascimento"])

            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                300,
                300,
                300,
                True,
                None,
                grau_exposicao=grau,
                exposicao_meses=300,
                ppp_comprovado=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"] == "Aposentadoria especial — transição"
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha no limite de pontos da especial "
                f"para nascimento em {nascimento}",
            )

        self.cliente.nascimento = nascimento_original
        self.cliente.save(update_fields=["nascimento"])

    def test_aposentadoria_especial_direito_adquirido(self):
        casos = [
            # filiado_antes, exposição, carência, PPP, esperado
            (True, 300, 180, True, True),
            (True, 299, 180, True, False),
            (False, 300, 180, True, False),
            (True, 300, 179, True, False),
            (True, 300, 180, False, False),
        ]

        for (
                filiado_antes,
                exposicao_meses,
                carencia,
                ppp_comprovado,
                esperado,
        ) in casos:
            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                carencia,
                360,
                300,
                filiado_antes,
                None,
                grau_exposicao="25",
                exposicao_meses=exposicao_meses,
                ppp_comprovado=ppp_comprovado,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"]
                == "Aposentadoria especial — direito adquirido"
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha no direito adquirido: "
                f"filiado_antes={filiado_antes}, "
                f"exposicao={exposicao_meses}, "
                f"carencia={carencia}, "
                f"ppp={ppp_comprovado}",
            )

    def test_aposentadoria_especial_direito_adquirido_tres_graus(self):
        casos = [
            ("15", 179, False),
            ("15", 180, True),
            ("20", 239, False),
            ("20", 240, True),
            ("25", 299, False),
            ("25", 300, True),
        ]

        for grau, exposicao_meses, esperado in casos:
            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                360,
                300,
                True,
                None,
                grau_exposicao=grau,
                exposicao_meses=exposicao_meses,
                ppp_comprovado=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"]
                == "Aposentadoria especial — direito adquirido"
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha no grau {grau} "
                f"com {exposicao_meses} meses de exposição",
            )

    def test_aposentadoria_especial_transicao_tres_graus(self):
        casos = [
            # grau, idade, contribuição, exposição, esperado
            ("15", 41, 25, 180, True),  # 41 + 25 = 66
            ("15", 40, 25, 180, False),  # 40 + 25 = 65

            ("20", 51, 25, 240, True),  # 51 + 25 = 76
            ("20", 50, 25, 240, False),  # 50 + 25 = 75

            ("25", 61, 25, 300, True),  # 61 + 25 = 86
            ("25", 60, 25, 300, False),  # 60 + 25 = 85
        ]

        nascimento_original = self.cliente.nascimento

        for grau, idade, anos_contribuicao, exposicao_meses, esperado in casos:
            ano_nascimento = 2026 - idade

            self.cliente.nascimento = date(
                ano_nascimento,
                8,
                8,
            )
            self.cliente.save(update_fields=["nascimento"])

            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                anos_contribuicao * 12,
                300,
                True,
                None,
                grau_exposicao=grau,
                exposicao_meses=exposicao_meses,
                ppp_comprovado=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"]
                == "Aposentadoria especial — transição"
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
                f"Falha no grau {grau}: "
                f"idade={idade}, "
                f"contribuição={anos_contribuicao}, "
                f"exposição={exposicao_meses}",
            )

        self.cliente.nascimento = nascimento_original
        self.cliente.save(update_fields=["nascimento"])

    def test_aposentadoria_especial_transicao_exige_filiacao_anterior(self):
        # Filiado antes da reforma:
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            None,
            grau_exposicao="25",
            exposicao_meses=300,
            ppp_comprovado=True,
        )

        regras_transicao = [
            regra
            for regra in resultado["regras"]
            if regra["nome"]
               == "Aposentadoria especial — transição"
        ]

        self.assertEqual(
            len(regras_transicao),
            1,
            "A regra de transição deveria existir para "
            "filiado antes da reforma.",
        )

        # Filiado depois da reforma:
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            False,
            None,
            grau_exposicao="25",
            exposicao_meses=300,
            ppp_comprovado=True,
        )

        regras_transicao = [
            regra
            for regra in resultado["regras"]
            if regra["nome"]
               == "Aposentadoria especial — transição"
        ]

        self.assertEqual(
            len(regras_transicao),
            0,
            "A regra de transição não deveria existir para "
            "filiado após a reforma.",
        )

    def test_aposentadoria_especial_permanente_sem_idade_minima(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            300,
            False,  # filiação após a reforma
            None,
            grau_exposicao="25",
            exposicao_meses=300,
            ppp_comprovado=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria especial — regra permanente"
        )

        self.assertTrue(regra["elegivel"])

    def test_aposentadoria_especial_permanente_nao_exige_60_anos(self):
        self.cliente.nascimento = date(1980, 8, 8)
        self.cliente.save()

        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            300,
            False,
            None,
            grau_exposicao="25",
            exposicao_meses=300,
            ppp_comprovado=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria especial — regra permanente"
        )

        self.assertTrue(regra["elegivel"])

    def test_especial_direito_adquirido_exige_tempo_ate_2019(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            300,
            True,
            None,
            grau_exposicao="25",
            exposicao_meses=300,
            ppp_comprovado=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria especial — direito adquirido"
        )

        self.assertTrue(regra["elegivel"])

    def test_especial_direito_adquirido_nao_usa_tempo_posterior_a_2019(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            None,
            grau_exposicao="25",
            exposicao_meses=360,
            ppp_comprovado=True,
            exposicao_meses_2019=240,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "Aposentadoria especial — direito adquirido"
        )

        self.assertFalse(regra["elegivel"])

        def test_professor_direito_adquirido(self):
            casos = [
                # Mulher: 25 anos completos até 13/11/2019
                (25 * 12, True),

                # Mulher: 24 anos e 11 meses
                (25 * 12 - 1, False),
            ]

            for magisterio_2019_meses, esperado in casos:
                self.cliente.sexo = "F"
                self.cliente.nascimento = date(1960, 1, 1)
                self.cliente.save()

                resultado = simular(
                    self.cliente,
                    date(2026, 8, 8),
                    180,
                    360,
                    300,
                    True,
                    None,
                    magisterio_meses=360,
                    magisterio_2019_meses=magisterio_2019_meses,
                    comprovacao_magisterio=True,
                )

                regra = next(
                    regra
                    for regra in resultado["regras"]
                    if regra["nome"]
                    == "Professor — direito adquirido"
                )

                self.assertEqual(
                    regra["elegivel"],
                    esperado,
                )

    def test_professor_direito_adquirido_homem(self):
        casos = [
            # Homem: 30 anos completos até 13/11/2019
            (30 * 12, True),

            # Homem: 29 anos e 11 meses
            (30 * 12 - 1, False),
        ]

        for magisterio_2019_meses, esperado in casos:
            self.cliente.sexo = "M"
            self.cliente.nascimento = date(1960, 1, 1)
            self.cliente.save()

            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                420,
                300,
                True,
                None,
                magisterio_meses=420,
                magisterio_2019_meses=magisterio_2019_meses,
                comprovacao_magisterio=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"]
                == "Professor — direito adquirido"
            )

            self.assertEqual(
                regra["elegivel"],
                esperado,
            )

    def test_professor_direito_adquirido_nao_usa_tempo_posterior_a_2019(self):
        self.cliente.sexo = "F"
        self.cliente.nascimento = date(1960, 1, 1)
        self.cliente.save()

        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            360,
            300,
            True,
            None,
            magisterio_meses=360,
            magisterio_2019_meses=240,  # 20 anos até 13/11/2019
            comprovacao_magisterio=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"]
            == "Professor — direito adquirido"
        )

        self.assertFalse(
            regra["elegivel"]
        )

    def test_pcd_por_tempo_mulher_grau_grave(self):
        self.cliente.sexo = "F"
        self.cliente.nascimento = date(1980, 1, 1)
        self.cliente.save()

        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            300,
            True,
            None,
            grau_deficiencia="GRAVE",
            deficiencia_meses=240,
            deficiencia_reconhecida=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "PCD — por tempo de contribuição"
        )

        self.assertTrue(regra["elegivel"])

    def test_pcd_por_tempo_mulher_grave_um_mes_a_menos(self):
        self.cliente.sexo = "F"
        self.cliente.nascimento = date(1980, 1, 1)
        self.cliente.save()

        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            299,
            299,
            True,
            None,
            grau_deficiencia="GRAVE",
            deficiencia_meses=239,
            deficiencia_reconhecida=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "PCD — por tempo de contribuição"
        )

        self.assertFalse(regra["elegivel"])

    def test_pcd_por_tempo_homem_tres_graus(self):
        casos = [
            ("GRAVE", 25 * 12),
            ("MODERADA", 29 * 12),
            ("LEVE", 33 * 12),
        ]

        for grau, meses in casos:
            self.cliente.sexo = "M"
            self.cliente.nascimento = date(1970, 1, 1)
            self.cliente.save()

            resultado = simular(
                self.cliente,
                date(2026, 8, 8),
                180,
                meses,
                300,
                True,
                None,
                grau_deficiencia=grau,
                deficiencia_meses=meses,
                deficiencia_reconhecida=True,
            )

            regra = next(
                regra
                for regra in resultado["regras"]
                if regra["nome"] == "PCD — por tempo de contribuição"
            )

            self.assertTrue(
                regra["elegivel"],
                msg=f"Falhou para grau {grau}",
            )

    def test_pcd_por_idade_mulher(self):
        self.cliente.sexo = "F"
        self.cliente.nascimento = date(1971, 8, 8)
        self.cliente.save()

        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            300,
            True,
            None,
            grau_deficiencia="MODERADA",
            deficiencia_meses=180,
            deficiencia_reconhecida=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "PCD — por idade"
        )

        self.assertTrue(regra["elegivel"])

    def test_pcd_por_idade_homem(self):
        self.cliente.sexo = "M"
        self.cliente.nascimento = date(1966, 8, 8)
        self.cliente.save()

        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            180,
            300,
            300,
            True,
            None,
            grau_deficiencia="LEVE",
            deficiencia_meses=180,
            deficiencia_reconhecida=True,
        )

        regra = next(
            regra
            for regra in resultado["regras"]
            if regra["nome"] == "PCD — por idade"
        )

        self.assertTrue(regra["elegivel"])

    def test_pcd_carencia_nao_precisa_ser_na_condicao_deficiencia(self):
        resultado = simular(
            self.cliente,
            date(2026, 8, 8),
            carencia=180,
            meses_contribuicao=300,
            meses_2019=240,
            filiado_antes=True,
            media=Decimal("4000.00"),
            grau_deficiencia="grave",
            deficiencia_meses=240,
            deficiencia_reconhecida=True,
        )

        regras = {
            item["nome"]: item
            for item in resultado["regras"]
        }

        self.assertTrue(
            regras["PCD — por tempo de contribuição"]["elegivel"]
        )

    def test_coeficiente_pcd_idade(self):
        casos = [
            (180, Decimal("0.85")),
            (240, Decimal("0.90")),
            (300, Decimal("0.95")),
            (360, Decimal("1.00")),
            (420, Decimal("1.00")),
        ]

        for meses, esperado in casos:
            with self.subTest(meses=meses):
                resultado = calcular_coeficiente_pcd_idade(
                    meses
                )

                self.assertEqual(
                    resultado,
                    esperado,
                )
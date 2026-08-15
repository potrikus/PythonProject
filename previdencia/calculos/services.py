from decimal import Decimal, ROUND_HALF_UP


# ============================================================
# PARÂMETROS PREVIDENCIÁRIOS - 2026
# ============================================================

PISO_2026 = Decimal("1621.00")
TETO_2026 = Decimal("8475.55")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def meses_entre(inicio, fim):
    """
    Calcula a quantidade completa de meses entre duas datas.
    """

    if not inicio or not fim:
        return 0

    meses = (fim.year - inicio.year) * 12
    meses += fim.month - inicio.month

    if fim.day < inicio.day:
        meses -= 1

    return max(0, meses)


def anos(meses):
    """
    Converte meses para anos decimais.
    """
    return Decimal(meses) / Decimal("12")


def dinheiro(valor):
    """
    Arredondamento monetário padrão.
    """
    if valor is None:
        return None

    return Decimal(valor).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# CONTRIBUIÇÃO AO INSS
# ============================================================

def calcular_contribuicao(salario, categoria):
    """
    Calcula a contribuição mensal estimada para 2026.

    EMPREGADO:
        aplicação progressiva das faixas.

    INDIVIDUAL:
        20% sobre o salário de contribuição,
        limitado ao teto.

    SIMPLIFICADO:
        11% sobre o salário mínimo.

    MEI:
        5% sobre o salário mínimo.
    """

    if salario is None:
        return None

    salario = Decimal(str(salario))

    if salario <= 0:
        return None

    # --------------------------------------------------------
    # MEI / FACULTATIVO BAIXA RENDA
    # --------------------------------------------------------

    if categoria == "MEI":
        return dinheiro(PISO_2026 * Decimal("0.05"))

    # --------------------------------------------------------
    # PLANO SIMPLIFICADO
    # --------------------------------------------------------

    if categoria == "SIMPLIFICADO":
        return dinheiro(PISO_2026 * Decimal("0.11"))

    # --------------------------------------------------------
    # CONTRIBUINTE INDIVIDUAL - 20%
    # --------------------------------------------------------

    if categoria == "INDIVIDUAL":
        base = max(
            PISO_2026,
            min(salario, TETO_2026),
        )

        return dinheiro(base * Decimal("0.20"))

    # --------------------------------------------------------
    # EMPREGADO / DOMÉSTICO / AVULSO
    # --------------------------------------------------------

    base = max(
        Decimal("0"),
        min(salario, TETO_2026),
    )

    faixas = [
        (Decimal("1621.00"), Decimal("0.075")),
        (Decimal("2902.84"), Decimal("0.09")),
        (Decimal("4354.27"), Decimal("0.12")),
        (Decimal("8475.55"), Decimal("0.14")),
    ]

    anterior = Decimal("0")
    total = Decimal("0")

    for limite, aliquota in faixas:

        if base <= anterior:
            break

        parcela = min(base, limite) - anterior

        if parcela > 0:
            total += parcela * aliquota

        anterior = limite

        if base <= limite:
            break

    return dinheiro(total)


# ============================================================
# COEFICIENTE DO BENEFÍCIO
# ============================================================

def calcular_coeficiente(anos_contribuicao, sexo_feminino):
    """
    Regra geral da EC 103/2019:

    60% da média + 2% por ano que ultrapassar:
        mulher: 15 anos
        homem: 20 anos

    O coeficiente fica limitado a 100%.
    """

    anos_contribuicao = Decimal(str(anos_contribuicao))

    divisor = (
        Decimal("15")
        if sexo_feminino
        else Decimal("20")
    )

    excedente = max(
        Decimal("0"),
        anos_contribuicao - divisor,
    )

    coeficiente = (
        Decimal("0.60")
        + Decimal("0.02") * excedente
    )

    return min(
        Decimal("1.00"),
        coeficiente,
    )


# ============================================================
# SIMULAÇÃO PREVIDENCIÁRIA
# ============================================================

def simular(
    cliente,
    referencia,
    carencia,
    meses_contribuicao,
    meses_2019,
    filiado_antes,
    media,
    grau_exposicao=None,
    exposicao_meses=0,
    ppp_comprovado=False,
    rural_meses=0,
    hibrido_meses=0,
    comprovacao_rural=False,
    magisterio_meses=0,
    magisterio_2019_meses=0,
    comprovacao_magisterio=False,
    grau_deficiencia="",
    deficiencia_meses=0,
    deficiencia_reconhecida=False,
):

    # ========================================================
    # DADOS BÁSICOS
    # ========================================================

    sexo_feminino = cliente.sexo == "F"

    idade_meses = meses_entre(
        cliente.nascimento,
        referencia,
    )

    idade_anos = Decimal(idade_meses) / Decimal("12")

    contribuicao_anos = (
        Decimal(meses_contribuicao) / Decimal("12")
    )

    exposicao_anos = (
        Decimal(exposicao_meses) / Decimal("12")
    )

    rural_anos = (
        Decimal(rural_meses) / Decimal("12")
    )

    regras = []

    ano_referencia = referencia.year

    # ========================================================
    # FUNÇÃO PARA ADICIONAR REGRA
    # ========================================================

    def adicionar(nome, elegivel, motivo):
        regras.append(
            {
                "nome": nome,
                "elegivel": bool(elegivel),
                "motivo": motivo,
            }
        )

    # ========================================================
    # REQUISITOS GERAIS
    # ========================================================

    minimo_contribuicao = (
        30 if sexo_feminino else 35
    )

    # ========================================================
    # APOSENTADORIA PROGRAMADA
    # ========================================================

    idade_programada = (
        Decimal("62")
        if sexo_feminino
        else Decimal("65")
    )

    contribuicao_programada = (
        15
        if sexo_feminino or filiado_antes
        else 20
    )

    elegivel_programada = (
        idade_anos >= idade_programada
        and contribuicao_anos >= contribuicao_programada
        and carencia >= 180
    )

    adicionar(
        "Aposentadoria programada",
        elegivel_programada,
        (
            f"Exige {idade_programada} anos de idade, "
            f"{contribuicao_programada} anos de contribuição "
            f"e 180 meses de carência."
        ),
    )

    # ========================================================
    # REGRAS DE TRANSIÇÃO
    # ========================================================

    if filiado_antes:

        # ----------------------------------------------------
        # PONTOS
        # ----------------------------------------------------

        pontos_exigidos = (
            93 if sexo_feminino else 103
        )

        pontos = idade_anos + contribuicao_anos

        elegivel_pontos = (
            contribuicao_anos >= minimo_contribuicao
            and pontos >= pontos_exigidos
            and carencia >= 180
        )

        adicionar(
            "Transição por pontos",
            elegivel_pontos,
            (
                f"Exige {pontos_exigidos} pontos em "
                f"{ano_referencia}, "
                f"{minimo_contribuicao} anos de contribuição "
                f"e 180 meses de carência. "
                f"Pontuação apurada: {pontos:.2f}."
            ),
        )

        # ----------------------------------------------------
        # IDADE PROGRESSIVA
        # ----------------------------------------------------

        idade_progressiva = (
            Decimal("59.5")
            if sexo_feminino
            else Decimal("64.5")
        )

        # Para anos posteriores a 2026:
        # + 6 meses por ano, respeitando os limites finais.

        anos_desde_2026 = max(
            0,
            ano_referencia - 2026,
        )

        idade_progressiva += (
            Decimal("0.5") * anos_desde_2026
        )

        limite_idade = (
            Decimal("62")
            if sexo_feminino
            else Decimal("65")
        )

        idade_progressiva = min(
            idade_progressiva,
            limite_idade,
        )

        elegivel_idade_progressiva = (
            idade_anos >= idade_progressiva
            and contribuicao_anos >= minimo_contribuicao
            and carencia >= 180
        )

        adicionar(
            "Transição por idade progressiva",
            elegivel_idade_progressiva,
            (
                f"Exige {idade_progressiva} anos de idade "
                f"em {ano_referencia}, "
                f"{minimo_contribuicao} anos de contribuição "
                f"e 180 meses de carência."
            ),
        )

        # ----------------------------------------------------
        # PEDÁGIO DE 50%
        # ----------------------------------------------------

        tempo_minimo_2019 = (
            minimo_contribuicao * 12
        )

        falta_2019 = max(
            0,
            tempo_minimo_2019 - meses_2019,
        )

        # Só existe pedágio de 50% para quem faltava
        # no máximo 24 meses em 13/11/2019.

        elegivel_pedagio_50 = (
            falta_2019 <= 24
            and falta_2019 > 0
            and meses_contribuicao
            >= (
                tempo_minimo_2019
                + Decimal(falta_2019) * Decimal("1.5")
            )
            and carencia >= 180
        )

        adicionar(
            "Transição com pedágio de 50%",
            elegivel_pedagio_50,
            (
                "Aplicável somente ao segurado que, "
                "em 13/11/2019, estava a até 24 meses "
                "de completar o tempo mínimo. "
                f"Tempo que faltava informado: {falta_2019} meses. "
                "Não há idade mínima nessa regra."
            ),
        )

        # ----------------------------------------------------
        # PEDÁGIO DE 100%
        # ----------------------------------------------------

        idade_pedagio_100 = (
            Decimal("57")
            if sexo_feminino
            else Decimal("60")
        )

        tempo_total_pedagio_100 = (
            tempo_minimo_2019
            + (falta_2019 * 2)
        )

        elegivel_pedagio_100 = (
            idade_anos >= idade_pedagio_100
            and meses_contribuicao
            >= tempo_total_pedagio_100
            and carencia >= 180
        )

        adicionar(
            "Transição com pedágio de 100%",
            elegivel_pedagio_100,
            (
                f"Exige {idade_pedagio_100} anos de idade, "
                f"{tempo_minimo_2019 // 12} anos de contribuição "
                "mais 100% do tempo que faltava em 13/11/2019, "
                "além de 180 meses de carência. "
                f"Tempo total calculado: "
                f"{tempo_total_pedagio_100 / 12:.2f} anos."
            ),
        )

    # ========================================================
    # APOSENTADORIA ESPECIAL
    # ========================================================

    if grau_exposicao:

        tempos_especiais = {
            15: 15,
            20: 20,
            25: 25,
        }

        idade_minima_especial = {
            15: Decimal("55"),
            20: Decimal("58"),
            25: Decimal("60"),
        }

        pontos_especial_exigidos = {
            15: Decimal("66"),
            20: Decimal("76"),
            25: Decimal("86"),
        }

        tempo_especial_exigido = (
            Decimal(tempos_especiais[grau_exposicao])
        )

        pontos_especial = (
            idade_anos
            + contribuicao_anos
            + exposicao_anos
        )

        # ----------------------------------------------------
        # TRANSIÇÃO
        # ----------------------------------------------------

        if filiado_antes:

            pontos_exigidos_especial = (
                pontos_especial_exigidos[grau_exposicao]
            )

            elegivel_especial_transicao = (
                exposicao_anos
                >= tempo_especial_exigido
                and pontos_especial
                >= pontos_exigidos_especial
                and carencia >= 180
                and ppp_comprovado
            )

            adicionar(
                "Aposentadoria especial — transição",
                elegivel_especial_transicao,
                (
                    f"Exige {tempo_especial_exigido} anos de "
                    "efetiva exposição, "
                    f"{pontos_exigidos_especial} pontos "
                    "(idade + tempo de contribuição + exposição), "
                    "180 meses de carência e PPP/LTCAT válido. "
                    f"Pontuação apurada: "
                    f"{pontos_especial:.2f}. "
                    f"Exposição informada: "
                    f"{exposicao_anos:.2f} anos."
                ),
            )

        # ----------------------------------------------------
        # REGRA PERMANENTE
        # ----------------------------------------------------

        idade_minima = (
            idade_minima_especial[grau_exposicao]
        )

        elegivel_especial_permanente = (
            exposicao_anos
            >= tempo_especial_exigido
            and idade_anos >= idade_minima
            and carencia >= 180
            and ppp_comprovado
        )

        adicionar(
            "Aposentadoria especial — regra permanente",
            elegivel_especial_permanente,
            (
                f"Exige {tempo_especial_exigido} anos de "
                f"efetiva exposição, idade mínima de "
                f"{idade_minima} anos, "
                "180 meses de carência e PPP/LTCAT válido. "
                f"Exposição informada: "
                f"{exposicao_anos:.2f} anos."
            ),
        )

    # ========================================================
    # APOSENTADORIA RURAL
    # ========================================================

    if rural_meses:

        idade_rural = (
            Decimal("55")
            if sexo_feminino
            else Decimal("60")
        )

        elegivel_rural = (
            idade_anos >= idade_rural
            and rural_meses >= 180
            and comprovacao_rural
        )

        adicionar(
            "Aposentadoria por idade rural",
            elegivel_rural,
            (
                f"Exige {idade_rural} anos de idade, "
                "180 meses de atividade rural "
                "e comprovação documental. "
                f"Atividade rural informada: "
                f"{rural_anos:.2f} anos."
            ),
        )

    # ========================================================
    # APOSENTADORIA HÍBRIDA
    # ========================================================

    if hibrido_meses:

        idade_hibrida = (
            Decimal("60")
            if sexo_feminino
            else Decimal("65")
        )

        elegivel_hibrida = (
            idade_anos >= idade_hibrida
            and hibrido_meses >= 180
            and comprovacao_rural
        )

        adicionar(
            "Aposentadoria por idade híbrida",
            elegivel_hibrida,
            (
                f"Exige {idade_hibrida} anos de idade, "
                "180 meses resultantes da soma dos períodos "
                "urbanos e rurais e comprovação da atividade rural. "
                f"Tempo híbrido informado: "
                f"{Decimal(hibrido_meses) / 12:.2f} anos."
            ),
        )

    # ========================================================
    # PROFESSOR
    # ========================================================

    if magisterio_meses:

        tempo_professor = (
            Decimal("25")
            if sexo_feminino
            else Decimal("30")
        )

        anos_magisterio = (
            Decimal(magisterio_meses) / Decimal("12")
        )

        pontos_professor = (
            idade_anos
            + anos_magisterio
        )

        # ----------------------------------------------------
        # PONTOS 2026
        # ----------------------------------------------------

        pontos_professor_2019 = (
            Decimal("81")
            if sexo_feminino
            else Decimal("91")
        )

        pontos_professor = pontos_professor

        pontos_professor_exigidos = min(
            pontos_professor_2019
            + max(0, ano_referencia - 2019),
            Decimal("92")
            if sexo_feminino
            else Decimal("100"),
        )

        # ----------------------------------------------------
        # IDADE PROGRESSIVA PROFESSOR
        # ----------------------------------------------------

        idade_professor_progressiva = (
            Decimal("51")
            if sexo_feminino
            else Decimal("56")
        )

        idade_professor_progressiva += (
            Decimal("0.5")
            * max(0, ano_referencia - 2019)
        )

        idade_professor_progressiva = min(
            idade_professor_progressiva,
            Decimal("57")
            if sexo_feminino
            else Decimal("60"),
        )

        # ----------------------------------------------------
        # PEDÁGIO
        # ----------------------------------------------------

        tempo_professor_2019 = (
            int(tempo_professor) * 12
        )

        falta_professor_2019 = max(
            0,
            tempo_professor_2019
            - magisterio_2019_meses,
        )

        # ----------------------------------------------------
        # REGRA PROGRAMADA
        # ----------------------------------------------------

        idade_programada_professor = (
            Decimal("57")
            if sexo_feminino
            else Decimal("60")
        )

        elegivel_professor_programada = (
            idade_anos >= idade_programada_professor
            and magisterio_meses
            >= tempo_professor_2019
            and carencia >= 180
            and comprovacao_magisterio
        )

        adicionar(
            "Professor — regra programada",
            elegivel_professor_programada,
            (
                f"Exige {idade_programada_professor} anos de idade, "
                f"{tempo_professor} anos de magistério na "
                "educação básica, 180 meses de carência "
                "e comprovação do exercício do magistério."
            ),
        )

        if filiado_antes:

            # ------------------------------------------------
            # PONTOS
            # ------------------------------------------------

            elegivel_professor_pontos = (
                anos_magisterio >= tempo_professor
                and pontos_professor
                >= pontos_professor_exigidos
                and carencia >= 180
                and comprovacao_magisterio
            )

            adicionar(
                "Professor — transição por pontos",
                elegivel_professor_pontos,
                (
                    f"Exige {pontos_professor_exigidos} pontos "
                    f"em {ano_referencia}, "
                    f"{tempo_professor} anos de magistério "
                    "e 180 meses de carência. "
                    f"Pontuação apurada: "
                    f"{pontos_professor:.2f}."
                ),
            )

            # ------------------------------------------------
            # IDADE PROGRESSIVA
            # ------------------------------------------------

            elegivel_professor_idade = (
                idade_anos >= idade_professor_progressiva
                and anos_magisterio >= tempo_professor
                and carencia >= 180
                and comprovacao_magisterio
            )

            adicionar(
                "Professor — idade progressiva",
                elegivel_professor_idade,
                (
                    f"Exige {idade_professor_progressiva} anos "
                    f"de idade em {ano_referencia}, "
                    f"{tempo_professor} anos de magistério "
                    "e 180 meses de carência."
                ),
            )

            # ------------------------------------------------
            # PEDÁGIO 100%
            # ------------------------------------------------

            idade_professor_pedagio = (
                Decimal("52")
                if sexo_feminino
                else Decimal("55")
            )

            tempo_professor_pedagio = (
                tempo_professor_2019
                + falta_professor_2019 * 2
            )

            elegivel_professor_pedagio = (
                idade_anos >= idade_professor_pedagio
                and magisterio_meses
                >= tempo_professor_pedagio
                and carencia >= 180
                and comprovacao_magisterio
            )

            adicionar(
                "Professor — pedágio de 100%",
                elegivel_professor_pedagio,
                (
                    f"Exige {idade_professor_pedagio} anos de idade, "
                    f"{tempo_professor} anos de magistério "
                    "mais o pedágio de 100% do período que "
                    f"faltava em 13/11/2019. "
                    f"Tempo total calculado: "
                    f"{Decimal(tempo_professor_pedagio) / 12:.2f} anos."
                ),
            )

    # ========================================================
    # PESSOA COM DEFICIÊNCIA
    # ========================================================

    if grau_deficiencia:

        tempos_pcd = {
            "GRAVE": {
                "F": 20,
                "M": 25,
            },
            "MODERADA": {
                "F": 24,
                "M": 29,
            },
            "LEVE": {
                "F": 28,
                "M": 33,
            },
        }

        sexo = "F" if sexo_feminino else "M"

        tempo_pcd = Decimal(
            tempos_pcd[grau_deficiencia][sexo]
        )

        # ----------------------------------------------------
        # PCD POR IDADE
        # ----------------------------------------------------

        idade_pcd = (
            Decimal("55")
            if sexo_feminino
            else Decimal("60")
        )

        elegivel_pcd_idade = (
            idade_anos >= idade_pcd
            and deficiencia_meses >= 180
            and carencia >= 180
            and deficiencia_reconhecida
        )

        adicionar(
            "PCD — por idade",
            elegivel_pcd_idade,
            (
                f"Exige {idade_pcd} anos de idade, "
                "15 anos de contribuição na condição de PCD, "
                "180 meses de carência e reconhecimento "
                "da deficiência."
            ),
        )

        # ----------------------------------------------------
        # PCD POR TEMPO
        # ----------------------------------------------------

        elegivel_pcd_tempo = (
            deficiencia_meses
            >= int(tempo_pcd * 12)
            and carencia >= 180
            and deficiencia_reconhecida
        )

        adicionar(
            "PCD — por tempo de contribuição",
            elegivel_pcd_tempo,
            (
                f"Exige {tempo_pcd} anos de contribuição "
                f"na condição de PCD de grau "
                f"{grau_deficiencia.lower()}, "
                "180 meses de carência e reconhecimento "
                "da deficiência."
            ),
        )

    # ========================================================
    # ESTIMATIVA DO BENEFÍCIO
    # ========================================================

    estimativa = None
    coeficiente = None

    if media:

        media_decimal = Decimal(str(media))

        coeficiente = calcular_coeficiente(
            contribuicao_anos,
            sexo_feminino,
        )

        estimativa = dinheiro(
            media_decimal * coeficiente
        )

        # Não ultrapassar o teto
        if estimativa > TETO_2026:
            estimativa = TETO_2026

        # Não deixar abaixo do piso
        if estimativa < PISO_2026:
            estimativa = PISO_2026

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    regras_elegiveis = [
        regra
        for regra in regras
        if regra["elegivel"]
    ]

    return {
        "idade_anos": round(float(idade_anos), 2),

        "anos_contribuicao": round(
            float(contribuicao_anos),
            2,
        ),

        "anos_exposicao": (
            round(float(exposicao_anos), 2)
            if grau_exposicao
            else None
        ),

        "anos_rural": (
            round(float(rural_anos), 2)
            if rural_meses
            else None
        ),

        "regras": regras,

        "regras_elegiveis": regras_elegiveis,

        "quantidade_regras_elegiveis": len(
            regras_elegiveis
        ),

        "coeficiente": (
            str(
                coeficiente.quantize(
                    Decimal("0.0001")
                )
            )
            if coeficiente is not None
            else None
        ),

        "estimativa_beneficio": (
            str(estimativa)
            if estimativa is not None
            else None
        ),

        "contribuicao_mensal": None,
    }
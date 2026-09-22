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
    Retorna a quantidade de meses completos entre duas datas.
    """

    if not inicio or not fim:
        return 0

    meses = (
        (fim.year - inicio.year) * 12
        + (fim.month - inicio.month)
    )

    if fim.day < inicio.day:
        meses -= 1

    return max(0, meses)


def anos(meses):
    """
    Converte meses para anos decimais.
    """

    meses = inteiro(meses)

    return Decimal(meses) / Decimal("12")


def dinheiro(valor):
    """
    Arredonda valor monetário para duas casas.
    """

    if valor is None:
        return None

    return Decimal(str(valor)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def decimal(valor, padrao="0"):
    """
    Conversão segura para Decimal.
    """

    if valor is None:
        return Decimal(padrao)

    try:
        return Decimal(str(valor))
    except (TypeError, ValueError):
        return Decimal(padrao)


def inteiro(valor, padrao=0):
    """
    Conversão segura para inteiro.
    """

    if valor is None:
        return padrao

    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def booleano(valor):
    """
    Converte corretamente valores booleanos.

    Evita:
        bool("False") == True
    """

    if isinstance(valor, bool):
        return valor

    if valor is None:
        return False

    if isinstance(valor, str):

        valor = valor.strip().lower()

        if valor in (
            "false",
            "0",
            "nao",
            "não",
            "no",
            "",
        ):
            return False

        if valor in (
            "true",
            "1",
            "sim",
            "yes",
        ):
            return True

    return bool(valor)


# ============================================================
# CONTRIBUIÇÃO AO INSS
# ============================================================

def calcular_contribuicao(salario, categoria):
    """
    Estimativa da contribuição mensal para 2026.

    Empregado / doméstico / avulso:
        cálculo progressivo.

    Individual:
        20%, limitado entre piso e teto.

    Simplificado:
        11% sobre o salário mínimo.

    MEI:
        5% sobre o salário mínimo.
    """

    if salario is None:
        return None

    salario = decimal(salario)

    if salario <= 0:
        return None

    categoria = str(
        categoria or ""
    ).upper().strip()

    # --------------------------------------------------------
    # MEI
    # --------------------------------------------------------

    if categoria == "MEI":

        return dinheiro(
            PISO_2026 * Decimal("0.05")
        )

    # --------------------------------------------------------
    # PLANO SIMPLIFICADO
    # --------------------------------------------------------

    if categoria == "SIMPLIFICADO":

        return dinheiro(
            PISO_2026 * Decimal("0.11")
        )

    # --------------------------------------------------------
    # CONTRIBUINTE INDIVIDUAL
    # --------------------------------------------------------

    if categoria == "INDIVIDUAL":

        base = max(
            PISO_2026,
            min(
                salario,
                TETO_2026,
            ),
        )

        return dinheiro(
            base * Decimal("0.20")
        )

    # --------------------------------------------------------
    # EMPREGADO / DOMÉSTICO / AVULSO
    # --------------------------------------------------------

    base = max(
        Decimal("0"),
        min(
            salario,
            TETO_2026,
        ),
    )

    faixas = [
        (
            Decimal("1621.00"),
            Decimal("0.075"),
        ),
        (
            Decimal("2902.84"),
            Decimal("0.09"),
        ),
        (
            Decimal("4354.27"),
            Decimal("0.12"),
        ),
        (
            Decimal("8475.55"),
            Decimal("0.14"),
        ),
    ]

    anterior = Decimal("0")
    total = Decimal("0")

    for limite, aliquota in faixas:

        if base <= anterior:
            break

        parcela = (
            min(base, limite)
            - anterior
        )

        if parcela > 0:
            total += parcela * aliquota

        anterior = limite

        if base <= limite:
            break

    return dinheiro(total)


# ============================================================
# COEFICIENTE DO BENEFÍCIO
# ============================================================

def calcular_coeficiente(
    anos_contribuicao,
    sexo_feminino,
    tempo_base=None,
):
    """
    Coeficiente básico:

    60% + 2% por ano excedente.

    Base:
        Mulher: 15 anos
        Homem: 20 anos

    tempo_base pode ser utilizado
    posteriormente para regras específicas.
    """

    anos_contribuicao = decimal(
        anos_contribuicao
    )

    if tempo_base is not None:

        divisor = decimal(
            tempo_base
        )

    else:

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
        + (
            Decimal("0.02")
            * excedente
        )
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
    # NORMALIZAÇÃO
    # ========================================================

    carencia = inteiro(carencia)

    meses_contribuicao = inteiro(
        meses_contribuicao
    )

    meses_2019 = inteiro(
        meses_2019
    )

    exposicao_meses = inteiro(
        exposicao_meses
    )

    rural_meses = inteiro(
        rural_meses
    )

    hibrido_meses = inteiro(
        hibrido_meses
    )

    magisterio_meses = inteiro(
        magisterio_meses
    )

    magisterio_2019_meses = inteiro(
        magisterio_2019_meses
    )

    deficiencia_meses = inteiro(
        deficiencia_meses
    )

    filiado_antes = booleano(
        filiado_antes
    )

    ppp_comprovado = booleano(
        ppp_comprovado
    )

    comprovacao_rural = booleano(
        comprovacao_rural
    )

    comprovacao_magisterio = booleano(
        comprovacao_magisterio
    )

    deficiencia_reconhecida = booleano(
        deficiencia_reconhecida
    )

    # ========================================================
    # SEXO
    # ========================================================

    sexo = str(
        getattr(
            cliente,
            "sexo",
            "",
        ) or ""
    ).upper().strip()

    sexo_feminino = sexo == "F"

    # ========================================================
    # DATAS
    # ========================================================

    nascimento = getattr(
        cliente,
        "nascimento",
        None,
    )

    idade_meses = meses_entre(
        nascimento,
        referencia,
    )

    idade_anos = anos(
        idade_meses
    )

    contribuicao_anos = anos(
        meses_contribuicao
    )

    exposicao_anos = anos(
        exposicao_meses
    )

    rural_anos = anos(
        rural_meses
    )

    ano_referencia = (
        referencia.year
        if referencia
        else 2026
    )

    # ========================================================
    # LISTA DE REGRAS
    # ========================================================

    regras = []

    def adicionar(
        nome,
        elegivel,
        motivo,
    ):
        regras.append(
            {
                "nome": nome,
                "elegivel": bool(elegivel),
                "motivo": motivo,
            }
        )

    # ========================================================
    # TEMPO MÍNIMO
    # ========================================================

    minimo_contribuicao = (
        Decimal("30")
        if sexo_feminino
        else Decimal("35")
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
        Decimal("15")
        if sexo_feminino
        else (
            Decimal("15")
            if filiado_antes
            else Decimal("20")
        )
    )

    elegivel_programada = (
        idade_anos >= idade_programada
        and contribuicao_anos
        >= contribuicao_programada
        and carencia >= 180
    )

    adicionar(
        "Aposentadoria programada",
        elegivel_programada,
        (
            f"Exige {idade_programada} anos "
            "de idade, "
            f"{contribuicao_programada} anos "
            "de contribuição e "
            "180 meses de carência."
        ),
    )

    # ========================================================
    # REGRAS DE TRANSIÇÃO
    # ========================================================

    if filiado_antes:

        # ====================================================
        # TRANSIÇÃO POR PONTOS
        # ====================================================

        pontos_base = (
            Decimal("86")
            if sexo_feminino
            else Decimal("96")
        )

        incremento_pontos = max(
            0,
            ano_referencia - 2019,
        )

        limite_pontos = (
            Decimal("100")
            if sexo_feminino
            else Decimal("105")
        )

        pontos_exigidos = min(
            pontos_base
            + Decimal(incremento_pontos),
            limite_pontos,
        )

        pontos = (
            idade_anos
            + contribuicao_anos
        )

        elegivel_pontos = (
            contribuicao_anos
            >= minimo_contribuicao
            and pontos >= pontos_exigidos
            and carencia >= 180
        )

        adicionar(
            "Transição por pontos",
            elegivel_pontos,
            (
                f"Exige {pontos_exigidos} "
                f"pontos em {ano_referencia}, "
                f"{minimo_contribuicao} anos "
                "de contribuição e "
                "180 meses de carência. "
                f"Pontuação apurada: "
                f"{pontos:.2f}."
            ),
        )

        # ====================================================
        # IDADE PROGRESSIVA
        # ====================================================

        idade_progressiva = (
            Decimal("58.5")
            if sexo_feminino
            else Decimal("63.5")
        )

        anos_desde_2024 = max(
            0,
            ano_referencia - 2024,
        )

        idade_progressiva += (
            Decimal("0.5")
            * Decimal(anos_desde_2024)
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
            idade_anos
            >= idade_progressiva
            and contribuicao_anos
            >= minimo_contribuicao
            and carencia >= 180
        )

        adicionar(
            "Transição por idade progressiva",
            elegivel_idade_progressiva,
            (
                f"Exige {idade_progressiva} "
                f"anos de idade em "
                f"{ano_referencia}, "
                f"{minimo_contribuicao} anos "
                "de contribuição e "
                "180 meses de carência."
            ),
        )

        # ====================================================
        # PEDÁGIO DE 50%
        # ====================================================

        tempo_minimo_2019 = (
            int(minimo_contribuicao)
            * 12
        )

        falta_2019 = max(
            0,
            tempo_minimo_2019
            - meses_2019,
        )

        tempo_pedagio_50 = (
            Decimal(meses_2019)
            + (
                Decimal(falta_2019)
                * Decimal("1.5")
            )
        )

        elegivel_pedagio_50 = (
            falta_2019 > 0
            and falta_2019 <= 24
            and Decimal(meses_contribuicao)
            >= tempo_pedagio_50
            and carencia >= 180
        )

        adicionar(
            "Transição com pedágio de 50%",
            elegivel_pedagio_50,
            (
                "Aplicável somente ao segurado "
                "que, em 13/11/2019, estava "
                "até 24 meses de completar "
                "o tempo mínimo. "
                f"Tempo informado em 2019: "
                f"{meses_2019 / 12:.2f} anos. "
                f"Tempo que faltava: "
                f"{falta_2019 / 12:.2f} anos. "
                f"Tempo total necessário com "
                f"pedágio: "
                f"{tempo_pedagio_50 / 12:.2f} anos. "
                "Não há idade mínima."
            ),
        )

        # ====================================================
        # PEDÁGIO DE 100%
        # ====================================================

        idade_pedagio_100 = (
            Decimal("57")
            if sexo_feminino
            else Decimal("60")
        )

        tempo_pedagio_100 = (
            Decimal(meses_2019)
            + (
                Decimal(falta_2019)
                * Decimal("2")
            )
        )

        elegivel_pedagio_100 = (
            idade_anos
            >= idade_pedagio_100
            and Decimal(meses_contribuicao)
            >= tempo_pedagio_100
            and carencia >= 180
        )

        adicionar(
            "Transição com pedágio de 100%",
            elegivel_pedagio_100,
            (
                f"Exige {idade_pedagio_100} "
                "anos de idade, "
                f"{minimo_contribuicao} "
                "anos de contribuição e "
                "100% do tempo que faltava "
                "em 13/11/2019. "
                f"Tempo informado em 2019: "
                f"{meses_2019 / 12:.2f} anos. "
                f"Tempo que faltava: "
                f"{falta_2019 / 12:.2f} anos. "
                f"Tempo total necessário: "
                f"{tempo_pedagio_100 / 12:.2f} anos."
            ),
        )

    # ========================================================
    # APOSENTADORIA ESPECIAL
    # ========================================================

    if grau_exposicao:

        try:
            grau = int(grau_exposicao)
        except (TypeError, ValueError):
            grau = None

        tempos_especiais = {
            15: Decimal("15"),
            20: Decimal("20"),
            25: Decimal("25"),
        }

        pontos_especiais = {
            15: Decimal("66"),
            20: Decimal("76"),
            25: Decimal("86"),
        }


        if grau in tempos_especiais:

            tempo_especial = (
                tempos_especiais[grau]
            )

            pontos_exigidos = (
                pontos_especiais[grau]
            )



            # =================================================
            # DIREITO ADQUIRIDO
            # =================================================

            direito_adquirido = (
                filiado_antes
                and exposicao_meses
                >= int(
                    tempo_especial
                    * 12
                )
                and carencia >= 180
                and ppp_comprovado
            )

            adicionar(
                "Aposentadoria especial — direito adquirido",
                direito_adquirido,
                (
                    f"Exige {tempo_especial} anos "
                    "de efetiva exposição "
                    "até 13/11/2019, "
                    "180 meses de carência "
                    "e comprovação da exposição "
                    "por PPP/LTCAT. "
                    f"Exposição informada: "
                    f"{exposicao_anos:.2f} anos."
                ),
            )

            # =================================================
            # TRANSIÇÃO ESPECIAL
            # =================================================

            if filiado_antes:

                pontos_especial = (
                        idade_anos
                        + contribuicao_anos
                )

                elegivel_especial_transicao = (
                    exposicao_anos
                    >= tempo_especial
                    and pontos_especial
                    >= pontos_exigidos
                    and carencia >= 180
                    and ppp_comprovado
                )

                adicionar(
                    "Aposentadoria especial — transição",
                    elegivel_especial_transicao,
                    (
                        "Exige {pontos_exigidos} "
                        "pontos, calculados pela "
                        "soma da idade + tempo de "
                        "contribuição, além de "
                        f"{tempo_especial} anos "
                        "de efetiva exposição, "
                        f"{tempo_especial} anos "
                        "de efetiva exposição, "
                        "180 meses de carência "
                        "e PPP/LTCAT válido. "
                        f"Pontuação apurada: "
                        f"{pontos_especial:.2f}. "
                        f"Exposição informada: "
                        f"{exposicao_anos:.2f} anos."
                    ),
                )

            # =================================================
            # REGRA PERMANENTE
            # =================================================

            else:

                elegivel_especial_permanente = (
                    exposicao_anos
                    >= tempo_especial
                    and carencia >= 180
                    and ppp_comprovado
                )

                adicionar(
                    "Aposentadoria especial — regra permanente",
                    elegivel_especial_permanente,
                    (
                        f"Exige {tempo_especial} anos de efetiva exposição, "
                        "180 meses de carência e PPP/LTCAT válido. "
                        "Não considera idade mínima. "
                        f"Exposição informada: {exposicao_anos:.2f} anos."
                    ),
                )

    # ========================================================
    # APOSENTADORIA RURAL
    # ========================================================

    if rural_meses > 0:

        idade_rural = (
            Decimal("55")
            if sexo_feminino
            else Decimal("60")
        )

        elegivel_rural = (
            idade_anos
            >= idade_rural
            and rural_meses >= 180
            and comprovacao_rural
        )

        adicionar(
            "Aposentadoria por idade rural",
            elegivel_rural,
            (
                f"Exige {idade_rural} anos "
                "de idade, 180 meses de "
                "atividade rural e "
                "comprovação documental. "
                f"Atividade rural informada: "
                f"{rural_anos:.2f} anos."
            ),
        )

    # ========================================================
    # APOSENTADORIA HÍBRIDA
    # ========================================================

    if hibrido_meses > 0:

        idade_hibrida = (
            Decimal("60")
            if sexo_feminino
            else Decimal("65")
        )

        elegivel_hibrida = (
            idade_anos
            >= idade_hibrida
            and hibrido_meses >= 180
            and comprovacao_rural
        )

        adicionar(
            "Aposentadoria por idade híbrida",
            elegivel_hibrida,
            (
                f"Exige {idade_hibrida} "
                "anos de idade e "
                "180 meses de carência "
                "considerando os períodos "
                "admitidos na modalidade híbrida, "
                "com comprovação da atividade "
                "rural. "
                f"Tempo híbrido informado: "
                f"{anos(hibrido_meses):.2f} anos."
            ),
        )

    # ========================================================
    # PROFESSOR
    # ========================================================

    if magisterio_meses > 0:

        tempo_professor = (
            Decimal("25")
            if sexo_feminino
            else Decimal("30")
        )

        anos_magisterio = anos(
            magisterio_meses
        )

        pontos_professor = (
            idade_anos
            + anos_magisterio
        )

        # Progressão começa em 2020.
        # Em 2026:
        # Mulher = 93? NÃO.
        # Para professor a base específica
        # é 86/96 em 2019 e cresce 1 ponto/ano.
        pontos_professor_base = (
            Decimal("81")
            if sexo_feminino
            else Decimal("91")
        )

        incremento_professor = max(
            0,
            ano_referencia - 2019,
        )

        limite_pontos_professor = (
            Decimal("100")
            if sexo_feminino
            else Decimal("105")
        )

        pontos_professor_exigidos = min(
            pontos_professor_base
            + Decimal(incremento_professor),
            limite_pontos_professor,
        )

        idade_professor = (
            Decimal("57")
            if sexo_feminino
            else Decimal("60")
        )

        idade_professor_progressiva = (
            Decimal("53.5")
            if sexo_feminino
            else Decimal("58.5")
        )

        anos_desde_2024 = max(
            0,
            ano_referencia - 2024,
        )

        idade_professor_progressiva += (
            Decimal("0.5")
            * Decimal(anos_desde_2024)
        )

        idade_professor_progressiva = min(
            idade_professor_progressiva,
            idade_professor,
        )

        tempo_professor_2019 = (
            int(tempo_professor)
            * 12
        )

        falta_professor_2019 = max(
            0,
            tempo_professor_2019
            - magisterio_2019_meses,
        )

        elegivel_professor_programada = (
            idade_anos
            >= idade_professor
            and magisterio_meses
            >= tempo_professor_2019
            and carencia >= 180
            and comprovacao_magisterio
        )

        adicionar(
            "Professor — regra programada",
            elegivel_professor_programada,
            (
                f"Exige {idade_professor} "
                "anos de idade, "
                f"{tempo_professor} anos "
                "de efetivo exercício "
                "do magistério na educação "
                "básica, 180 meses de carência "
                "e comprovação."
            ),
        )

        if filiado_antes:

            elegivel_professor_pontos = (
                anos_magisterio
                >= tempo_professor
                and pontos_professor
                >= pontos_professor_exigidos
                and carencia >= 180
                and comprovacao_magisterio
            )

            adicionar(
                "Professor — transição por pontos",
                elegivel_professor_pontos,
                (
                    f"Exige {pontos_professor_exigidos} "
                    f"pontos em {ano_referencia}, "
                    f"{tempo_professor} anos "
                    "de efetivo exercício "
                    "do magistério e "
                    "180 meses de carência. "
                    f"Pontuação apurada: "
                    f"{pontos_professor:.2f}."
                ),
            )

            elegivel_professor_idade = (
                idade_anos
                >= idade_professor_progressiva
                and anos_magisterio
                >= tempo_professor
                and carencia >= 180
                and comprovacao_magisterio
            )

            adicionar(
                "Professor — idade progressiva",
                elegivel_professor_idade,
                (
                    f"Exige "
                    f"{idade_professor_progressiva} "
                    "anos de idade em "
                    f"{ano_referencia}, "
                    f"{tempo_professor} anos "
                    "de magistério e "
                    "180 meses de carência."
                ),
            )

            idade_professor_pedagio = (
                Decimal("52")
                if sexo_feminino
                else Decimal("55")
            )

            tempo_professor_pedagio = (
                Decimal(
                    magisterio_2019_meses
                )
                + (
                    Decimal(
                        falta_professor_2019
                    )
                    * Decimal("2")
                )
            )

            elegivel_professor_pedagio = (
                idade_anos
                >= idade_professor_pedagio
                and magisterio_meses
                >= tempo_professor_pedagio
                and carencia >= 180
                and comprovacao_magisterio
            )

            adicionar(
                "Professor — pedágio de 100%",
                elegivel_professor_pedagio,
                (
                    f"Exige "
                    f"{idade_professor_pedagio} "
                    "anos de idade, "
                    f"{tempo_professor} anos "
                    "de magistério e "
                    "100% do tempo que faltava "
                    "em 13/11/2019. "
                    f"Tempo informado em 2019: "
                    f"{magisterio_2019_meses / 12:.2f} anos. "
                    f"Tempo que faltava: "
                    f"{falta_professor_2019 / 12:.2f} anos. "
                    f"Tempo total necessário: "
                    f"{tempo_professor_pedagio / 12:.2f} anos."
                ),
            )

    # ========================================================
    # PESSOA COM DEFICIÊNCIA
    # ========================================================

    if grau_deficiencia:

        grau_pcd = str(
            grau_deficiencia
        ).upper().strip()

        tempos_pcd = {
            "GRAVE": {
                "F": Decimal("20"),
                "M": Decimal("25"),
            },
            "MODERADA": {
                "F": Decimal("24"),
                "M": Decimal("29"),
            },
            "LEVE": {
                "F": Decimal("28"),
                "M": Decimal("33"),
            },
        }

        sexo_pcd = (
            "F"
            if sexo_feminino
            else "M"
        )

        if grau_pcd in tempos_pcd:

            tempo_pcd = (
                tempos_pcd[
                    grau_pcd
                ][sexo_pcd]
            )

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
                    f"Exige {idade_pcd} anos "
                    "de idade, 15 anos "
                    "de contribuição na "
                    "condição de PCD, "
                    "180 meses de carência "
                    "e reconhecimento "
                    "da deficiência."
                ),
            )

            tempo_pcd_meses = int(
                tempo_pcd * 12
            )

            elegivel_pcd_tempo = (
                deficiencia_meses
                >= tempo_pcd_meses
                and carencia >= 180
                and deficiencia_reconhecida
            )

            adicionar(
                "PCD — por tempo de contribuição",
                elegivel_pcd_tempo,
                (
                    f"Exige {tempo_pcd} anos "
                    "de contribuição na "
                    "condição de PCD, "
                    f"grau {grau_pcd.lower()}, "
                    "180 meses de carência "
                    "e reconhecimento "
                    "da deficiência."
                ),
            )

    # ========================================================
    # ESTIMATIVA DO BENEFÍCIO
    # ========================================================

    estimativa = None
    coeficiente = None

    if media is not None:

        media_decimal = decimal(
            media
        )

        if media_decimal > 0:

            coeficiente = (
                calcular_coeficiente(
                    contribuicao_anos,
                    sexo_feminino,
                )
            )

            estimativa = dinheiro(
                media_decimal
                * coeficiente
            )

            if estimativa > TETO_2026:
                estimativa = TETO_2026

            if estimativa < PISO_2026:
                estimativa = PISO_2026

    # ========================================================
    # REGRAS ELEGÍVEIS
    # ========================================================

    regras_elegiveis = [
        regra
        for regra in regras
        if regra["elegivel"]
    ]

    # ========================================================
    # RESULTADO
    # ========================================================

    return {
        "idade_anos": round(
            float(idade_anos),
            2,
        ),

        "anos_contribuicao": round(
            float(contribuicao_anos),
            2,
        ),

        "anos_exposicao": (
            round(
                float(exposicao_anos),
                2,
            )
            if grau_exposicao
            else None
        ),

        "anos_rural": (
            round(
                float(rural_anos),
                2,
            )
            if rural_meses > 0
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
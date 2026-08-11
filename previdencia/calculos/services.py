from datetime import date
from decimal import Decimal, ROUND_HALF_UP


PISO_2026 = Decimal("1621.00")
TETO_2026 = Decimal("8475.55")


def meses_entre(inicio, fim):
    meses = (fim.year - inicio.year) * 12 + fim.month - inicio.month
    return meses - (1 if fim.day < inicio.day else 0)


def calcular_contribuicao(salario, categoria):
    if not salario:
        return None
    salario = Decimal(salario)
    if categoria == "MEI":
        return Decimal("81.05")
    if categoria == "SIMPLIFICADO":
        return Decimal("178.31")
    base = min(salario, TETO_2026)
    if categoria == "INDIVIDUAL":
        return (base * Decimal("0.20")).quantize(Decimal("0.01"), ROUND_HALF_UP)
    faixas = [(Decimal("1621.00"), Decimal("0.075")), (Decimal("2902.84"), Decimal("0.09")), (Decimal("4354.27"), Decimal("0.12")), (TETO_2026, Decimal("0.14"))]
    anterior, total = Decimal("0"), Decimal("0")
    for limite, aliquota in faixas:
        parcela = min(base, limite) - anterior
        if parcela > 0:
            total += parcela * aliquota
        anterior = limite
        if base <= limite:
            break
    return total.quantize(Decimal("0.01"), ROUND_HALF_UP)


def simular(cliente, referencia, carencia, meses_contribuicao, meses_2019, filiado_antes, media, grau_exposicao=None, exposicao_meses=0, ppp_comprovado=False, rural_meses=0, hibrido_meses=0, comprovacao_rural=False, magisterio_meses=0, magisterio_2019_meses=0, comprovacao_magisterio=False, grau_deficiencia="", deficiencia_meses=0, deficiencia_reconhecida=False):
    sexo_feminino = cliente.sexo == "F"
    idade_meses = meses_entre(cliente.nascimento, referencia)
    idade_anos = idade_meses / 12
    anos_contribuicao = meses_contribuicao / 12
    minimo_tempo = 30 if sexo_feminino else 35
    regras = []

    def adicionar(nome, elegivel, motivo):
        regras.append({"nome": nome, "elegivel": elegivel, "motivo": motivo})

    if sexo_feminino:
        idade_permanente, tempo_permanente = 62, 15
    else:
        idade_permanente, tempo_permanente = 65, (15 if filiado_antes else 20)
    adicionar("Aposentadoria programada", idade_anos >= idade_permanente and anos_contribuicao >= tempo_permanente and carencia >= 180, f"Exige {idade_permanente} anos de idade, {tempo_permanente} anos de contribuição e 180 meses de carência.")

    if filiado_antes:
        ano = referencia.year
        pontos_exigidos = min((86 if sexo_feminino else 96) + max(0, ano - 2019), 100 if sexo_feminino else 105)
        pontos = idade_anos + anos_contribuicao
        adicionar("Transição por pontos", anos_contribuicao >= minimo_tempo and pontos >= pontos_exigidos and carencia >= 180, f"Exige {pontos_exigidos} pontos em {ano}, {minimo_tempo} anos de contribuição e 180 meses de carência. Pontuação apurada: {pontos:.2f}.")
        idade_progressiva = min((56 if sexo_feminino else 61) + Decimal("0.5") * max(0, ano - 2019), Decimal("62") if sexo_feminino else Decimal("65"))
        adicionar("Transição por idade progressiva", idade_anos >= float(idade_progressiva) and anos_contribuicao >= minimo_tempo and carencia >= 180, f"Exige {idade_progressiva} anos de idade em {ano}, {minimo_tempo} anos de contribuição e 180 meses de carência.")
        falta_2019 = max(0, minimo_tempo * 12 - meses_2019)
        elegivel_50 = falta_2019 <= 24 and meses_contribuicao * 2 >= minimo_tempo * 24 + falta_2019 * 3 and carencia >= 180
        adicionar("Transição com pedágio de 50%", elegivel_50, f"Aplicável se faltavam até 24 meses em 13/11/2019; faltavam {falta_2019} meses informados.")
        idade_100 = 57 if sexo_feminino else 60
        elegivel_100 = idade_anos >= idade_100 and meses_contribuicao >= minimo_tempo * 12 + falta_2019 and carencia >= 180
        adicionar("Transição com pedágio de 100%", elegivel_100, f"Exige {idade_100} anos de idade, {minimo_tempo} anos mais o pedágio e 180 meses de carência.")

    if grau_exposicao:
        exposicao_anos = exposicao_meses / 12
        pontos_especial = idade_anos + anos_contribuicao + exposicao_anos
        pontos_exigidos = {15: 66, 20: 76, 25: 86}[grau_exposicao]
        requisito_documental = ppp_comprovado
        if filiado_antes:
            adicionar("Aposentadoria especial — transição", exposicao_anos >= grau_exposicao and pontos_especial >= pontos_exigidos and carencia >= 180 and requisito_documental, f"Exige {grau_exposicao} anos de efetiva exposição, {pontos_exigidos} pontos (idade + contribuição + exposição), 180 meses de carência e PPP/LTCAT. Pontuação apurada: {pontos_especial:.2f}.")
        else:
            adicionar("Aposentadoria especial — regra permanente", exposicao_anos >= grau_exposicao and carencia >= 180 and requisito_documental, f"Exige {grau_exposicao} anos de efetiva exposição, 180 meses de carência e PPP/LTCAT. A idade mínima prevista na EC 103 foi declarada inconstitucional pelo STF em junho de 2026; acompanhe eventual regulamentação.")

    if rural_meses or hibrido_meses:
        idade_rural = 55 if sexo_feminino else 60
        idade_hibrida = 60 if sexo_feminino else 65
        adicionar("Aposentadoria por idade rural", idade_anos >= idade_rural and rural_meses >= 180 and comprovacao_rural, f"Exige {idade_rural} anos de idade, 180 meses de atividade rural comprovada e documentação rural/autodeclaração. Atividade rural informada: {rural_meses} meses.")
        adicionar("Aposentadoria por idade híbrida", idade_anos >= idade_hibrida and hibrido_meses >= 180 and comprovacao_rural, f"Exige {idade_hibrida} anos de idade, 180 meses resultantes da soma de períodos urbanos e rurais e prova da atividade rural. Tempo híbrido informado: {hibrido_meses} meses.")

    if magisterio_meses:
        tempo_professor = 25 if sexo_feminino else 30
        pontos_professor = idade_anos + magisterio_meses / 12
        pontos_exigidos = min((81 if sexo_feminino else 91) + max(0, referencia.year - 2019), 92 if sexo_feminino else 100)
        idade_progressiva_professor = min((51 if sexo_feminino else 56) + 0.5 * max(0, referencia.year - 2019), 57 if sexo_feminino else 60)
        falta_professor = max(0, tempo_professor * 12 - magisterio_2019_meses)
        adicionar("Professor — regra programada", idade_anos >= (57 if sexo_feminino else 60) and magisterio_meses >= tempo_professor * 12 and carencia >= 180 and comprovacao_magisterio, f"Exige {(57 if sexo_feminino else 60)} anos de idade, {tempo_professor} anos de magistério, 180 meses de carência e comprovação de educação básica.")
        if filiado_antes:
            adicionar("Professor — transição por pontos", magisterio_meses >= tempo_professor * 12 and pontos_professor >= pontos_exigidos and carencia >= 180 and comprovacao_magisterio, f"Exige {pontos_exigidos} pontos em {referencia.year}, {tempo_professor} anos de magistério e 180 meses de carência. Pontuação apurada: {pontos_professor:.2f}.")
            adicionar("Professor — idade progressiva", idade_anos >= idade_progressiva_professor and magisterio_meses >= tempo_professor * 12 and carencia >= 180 and comprovacao_magisterio, f"Exige {idade_progressiva_professor} anos de idade em {referencia.year}, {tempo_professor} anos de magistério e 180 meses de carência.")
            adicionar("Professor — pedágio de 100%", idade_anos >= (52 if sexo_feminino else 55) and magisterio_meses >= tempo_professor * 12 + falta_professor and carencia >= 180 and comprovacao_magisterio, f"Exige {(52 if sexo_feminino else 55)} anos de idade, {tempo_professor} anos mais o pedágio e 180 meses de carência.")

    if grau_deficiencia:
        tempos_pcd = {"GRAVE": (20, 25), "MODERADA": (24, 29), "LEVE": (28, 33)}
        tempo_pcd = tempos_pcd[grau_deficiencia][0 if sexo_feminino else 1]
        adicionar("PCD — por idade", idade_anos >= (55 if sexo_feminino else 60) and deficiencia_meses >= 180 and carencia >= 180 and deficiencia_reconhecida, f"Exige {(55 if sexo_feminino else 60)} anos de idade, 15 anos na condição de PCD, 180 meses de carência e avaliação médico-social favorável.")
        adicionar("PCD — por tempo de contribuição", deficiencia_meses >= tempo_pcd * 12 and carencia >= 180 and deficiencia_reconhecida, f"Exige {tempo_pcd} anos na condição de PCD de grau {grau_deficiencia.lower()}, 180 meses de carência e avaliação médico-social favorável.")

    estimativa = None
    if media:
        divisor = 15 if sexo_feminino else 20
        coeficiente = min(Decimal("1"), Decimal("0.60") + Decimal("0.02") * max(0, int(anos_contribuicao) - divisor))
        estimativa = (Decimal(media) * coeficiente).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return {"idade_anos": round(idade_anos, 2), "anos_contribuicao": round(anos_contribuicao, 2), "anos_exposicao": round(exposicao_meses / 12, 2) if grau_exposicao else None, "anos_rural": round(rural_meses / 12, 2) if rural_meses else None, "regras": regras, "estimativa_beneficio": str(estimativa) if estimativa is not None else None}

"""
Funcao de criticidade da Questao 2 (gestao de consumo de energia).

Usada tanto pela forca bruta (src/brute_force.py) quanto pelo
divide-and-conquer (src/divide_conquer.py) pra pontuar cada leitura
antes de buscar o intervalo continuo de maior criticidade acumulada.
"""

# quanto o excesso sobre a capacidade pesa na criticidade -- excesso
# conta em dobro, porque estourar a capacidade disponivel e o cenario
# mais critico pro sistema
FATOR_PENALIDADE_EXCESSO = 2.0

# quanto cada nivel de prioridade soma na criticidade (prioridade vai
# de 1 a 3, entao isso soma de 50 a 150)
PESO_PRIORIDADE = 50.0


def calcular_criticidade(leitura: dict) -> float:
    """
    criticidade = consumo + penalidade_por_excesso + peso_da_prioridade

    - penalidade_por_excesso: so existe quando o consumo passa da
      capacidade_disponivel (excesso * FATOR_PENALIDADE_EXCESSO); se
      nao passou, a penalidade e zero.
    - peso_da_prioridade: prioridade * PESO_PRIORIDADE, pra regioes
      mais prioritarias pesarem mais na busca por intervalos criticos.
    """
    consumo = leitura["consumo"]
    capacidade = leitura["capacidade_disponivel"]
    prioridade = leitura["prioridade"]

    excesso = max(0.0, consumo - capacidade)
    penalidade_por_excesso = excesso * FATOR_PENALIDADE_EXCESSO

    peso_da_prioridade = prioridade * PESO_PRIORIDADE

    return consumo + penalidade_por_excesso + peso_da_prioridade

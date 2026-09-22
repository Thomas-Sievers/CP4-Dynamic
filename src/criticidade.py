"""
Funcao de criticidade da Questao 2 (gestao de consumo de energia).

Usada tanto pela forca bruta (src/brute_force.py) quanto pelo
divide-and-conquer (src/divide_conquer.py) pra pontuar cada leitura
antes de buscar o intervalo continuo de maior criticidade acumulada.
"""

# fracao da capacidade disponivel considerada uso seguro. usar a
# capacidade da propria linha como referencia normaliza entre regioes
# diferentes (Centro tem mais capacidade que Leste, por exemplo).
LIMIAR_SEGURO = 0.75

# quanto o excesso sobre 100% da capacidade pesa na criticidade
# excesso conta em dobro, porque estourar a capacidade disponivel é o cenario mais critico pro sistema
FATOR_PENALIDADE_EXCESSO = 2.0


def calcular_criticidade(leitura: dict) -> float:
    """
    criticidade = consumo_relativo + penalidade_por_excesso

    - consumo_relativo: consumo - (capacidade_disponivel * LIMIAR_SEGURO).
      Fica negativo enquanto o consumo estiver dentro da faixa segura
      (ate 75% da capacidade daquela linha) e so vira positivo quando
      passa disso.
    - penalidade_por_excesso: so existe quando o consumo passa de
      100% da capacidade_disponivel (excesso * FATOR_PENALIDADE_EXCESSO
      * prioridade); se nao passou, e zero. A prioridade multiplica o
      excesso -- nao soma nada sozinha -- porque uma regiao so deve
      pesar mais na busca quando ela de fato estoura a capacidade.
    """
    consumo = leitura["consumo"]
    capacidade = leitura["capacidade_disponivel"]
    prioridade = leitura["prioridade"]

    limiar = capacidade * LIMIAR_SEGURO
    consumo_relativo = consumo - limiar

    excesso = max(0.0, consumo - capacidade)
    penalidade_por_excesso = excesso * FATOR_PENALIDADE_EXCESSO * prioridade

    return consumo_relativo + penalidade_por_excesso

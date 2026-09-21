"""
Busca o intervalo continuo de maior criticidade acumulada por
divide-and-conquer (Parte C da Questao 2) -- o classico "subarray de
soma maxima" adaptado pra usar a criticidade em vez da soma pura.
"""

from src.criticidade import calcular_criticidade


def buscar_intervalo_critico_divide_conquer(leituras: list[dict]) -> tuple[int, int, float]:
    """
    Ponto de entrada: calcula a criticidade de cada leitura e chama a
    recursao que faz a busca de verdade.
    """
    if not leituras:
        raise ValueError("lista de leituras vazia")

    scores = [calcular_criticidade(leitura) for leitura in leituras]
    return _buscar(scores, 0, len(scores) - 1)


def _buscar(scores: list[float], esquerda: int, direita: int) -> tuple[int, int, float]:
    """
    Recursao principal. Recebe o pedaco de 'scores' entre os indices
    esquerda e direita (os dois inclusos) e devolve o melhor intervalo
    continuo daquele pedaco: (indice_inicio, indice_fim, criticidade).
    """
    # CASO BASE: sobrou um so elemento, o unico intervalo possivel e
    # ele mesmo.
    if esquerda == direita:
        return esquerda, direita, scores[esquerda]

    # DIVISAO: corta o pedaco ao meio em duas metades.
    meio = (esquerda + direita) // 2

    # SOLUCAO DA METADE ESQUERDA: melhor intervalo que fica inteiro
    # dentro de [esquerda, meio].
    inicio_e, fim_e, criticidade_e = _buscar(scores, esquerda, meio)

    # SOLUCAO DA METADE DIREITA: melhor intervalo que fica inteiro
    # dentro de [meio+1, direita].
    inicio_d, fim_d, criticidade_d = _buscar(scores, meio + 1, direita)

    # CASO QUE ATRAVESSA A DIVISAO: o melhor intervalo pode nao estar
    # inteiro em nenhuma das duas metades -- pode comecar na esquerda
    # e terminar na direita, atravessando o meio. Isso as duas
    # chamadas acima nunca vao achar sozinhas, entao precisa calcular
    # separado.
    inicio_c, fim_c, criticidade_c = _melhor_intervalo_cruzando_o_meio(scores, esquerda, meio, direita)

    # COMBINACAO: o melhor intervalo do pedaco todo e o maior entre os
    # tres candidatos (so esquerda, so direita, ou atravessando).
    if criticidade_e >= criticidade_d and criticidade_e >= criticidade_c:
        return inicio_e, fim_e, criticidade_e
    if criticidade_d >= criticidade_e and criticidade_d >= criticidade_c:
        return inicio_d, fim_d, criticidade_d
    return inicio_c, fim_c, criticidade_c


def _melhor_intervalo_cruzando_o_meio(
    scores: list[float], esquerda: int, meio: int, direita: int
) -> tuple[int, int, float]:
    """
    Acha o melhor intervalo que obrigatoriamente inclui 'meio' e
    'meio + 1' (por isso atravessa a divisao). Funciona em duas
    partes independentes:

    1. Anda de 'meio' pra tras ate 'esquerda', acumulando a soma, e
       guarda o ponto onde essa soma foi maior -- e o melhor sufixo
       terminando em 'meio'.
    2. Anda de 'meio + 1' pra frente ate 'direita', do mesmo jeito --
       e o melhor prefixo comecando em 'meio + 1'.

    O melhor intervalo cruzando o meio e a uniao dessas duas partes.
    """
    soma = 0.0
    melhor_soma_esquerda = float("-inf")
    melhor_inicio = meio
    for i in range(meio, esquerda - 1, -1):
        soma += scores[i]
        if soma > melhor_soma_esquerda:
            melhor_soma_esquerda = soma
            melhor_inicio = i

    soma = 0.0
    melhor_soma_direita = float("-inf")
    melhor_fim = meio + 1
    for j in range(meio + 1, direita + 1):
        soma += scores[j]
        if soma > melhor_soma_direita:
            melhor_soma_direita = soma
            melhor_fim = j

    return melhor_inicio, melhor_fim, melhor_soma_esquerda + melhor_soma_direita


if __name__ == "__main__":
    from src.estruturas import carregar_leituras

    leituras = carregar_leituras()
    inicio, fim, criticidade = buscar_intervalo_critico_divide_conquer(leituras)

    print(f"intervalo critico: indices {inicio} a {fim} ({fim - inicio + 1} leituras)")
    print(f"de {leituras[inicio]['timestamp']} a {leituras[fim]['timestamp']}")
    print(f"criticidade acumulada: {round(criticidade, 2)}")

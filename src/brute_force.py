"""
Busca o intervalo continuo de maior criticidade acumulada por forca
bruta (Parte B da Questao 2).
"""

from src.criticidade import calcular_criticidade


def buscar_intervalo_critico_forca_bruta(leituras: list[dict]) -> tuple[int, int, float]:
    """
    Testa EXPLICITAMENTE todos os intervalos continuos [inicio, fim]
    possiveis dentro de 'leituras': dois loops aninhados, o de fora
    escolhe o inicio e o de dentro escolhe o fim (sempre >= inicio),
    somando a criticidade das leituras entre eles e guardando o
    intervalo com a maior soma encontrada ate agora.

    Retorna (indice_inicio, indice_fim, criticidade_total) do melhor
    intervalo.
    """
    if not leituras:
        raise ValueError("lista de leituras vazia")

    n = len(leituras)
    scores = [calcular_criticidade(leitura) for leitura in leituras]

    melhor_inicio = 0
    melhor_fim = 0
    melhor_criticidade = scores[0]

    for inicio in range(n):
        soma_do_intervalo = 0.0
        for fim in range(inicio, n):
            soma_do_intervalo += scores[fim]
            if soma_do_intervalo > melhor_criticidade:
                melhor_criticidade = soma_do_intervalo
                melhor_inicio = inicio
                melhor_fim = fim

    return melhor_inicio, melhor_fim, melhor_criticidade


if __name__ == "__main__":
    from src.estruturas import carregar_leituras

    leituras = carregar_leituras()
    inicio, fim, criticidade = buscar_intervalo_critico_forca_bruta(leituras)

    print(f"intervalo critico: indices {inicio} a {fim} ({fim - inicio + 1} leituras)")
    print(f"de {leituras[inicio]['timestamp']} a {leituras[fim]['timestamp']}")
    print(f"criticidade acumulada: {round(criticidade, 2)}")

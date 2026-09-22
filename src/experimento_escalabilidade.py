"""
Experimento de escalabilidade da Questao 2 (Parte D): mede tempo,
numero aproximado de operacoes e memoria da forca bruta e do
divide-and-conquer pra tamanhos de entrada crescentes.
"""

import csv
import random
import time
import tracemalloc
from math import log2

from src.brute_force import buscar_intervalo_critico_forca_bruta
from src.divide_conquer import buscar_intervalo_critico_divide_conquer

TAMANHOS = [100, 250, 500, 1000, 2000, 5000]
REPETICOES = 3  # quantas vezes roda cada algoritmo, pra tirar a media do tempo
SEED = 1  # mesma seed do grupo, pra o experimento ser reproduzivel


def gerar_leituras_aleatorias(n: int) -> list[dict]:
    """
    Gera 'n' leituras aleatorias so com os campos que a funcao de
    criticidade usa (consumo, capacidade_disponivel, prioridade). Nao
    precisa ser um dataset realista com datas e regioes -- aqui o
    objetivo e so medir como os algoritmos escalam com o tamanho n.
    """
    leituras = []
    for _ in range(n):
        capacidade = random.uniform(200.0, 800.0)
        consumo = random.uniform(0.5, 1.3) * capacidade
        prioridade = random.randint(1, 3)
        leituras.append(
            {
                "consumo": consumo,
                "capacidade_disponivel": capacidade,
                "prioridade": prioridade,
            }
        )
    return leituras


def medir_tempo_medio(funcao, leituras: list[dict]) -> float:
    """Roda 'funcao' REPETICOES vezes e devolve a media do tempo, em segundos."""
    tempos = []
    for _ in range(REPETICOES):
        inicio = time.perf_counter()
        funcao(leituras)
        fim = time.perf_counter()
        tempos.append(fim - inicio)
    return sum(tempos) / len(tempos)


def medir_pico_de_memoria(funcao, leituras: list[dict]) -> int:
    """Pico de memoria (em bytes) alocada pelo Python durante a chamada."""
    tracemalloc.start()
    funcao(leituras)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico


def operacoes_forca_bruta(n: int) -> int:
    """
    Numero de vezes que o loop de dentro soma uma leitura no
    intervalo: um por par (inicio, fim) com fim >= inicio, que da
    n*(n+1)/2 pares -- bate com o O(n^2) esperado.
    """
    return n * (n + 1) // 2


def operacoes_divide_conquer(n: int) -> int:
    """
    Aproximacao: cada nivel da recursao varre, somando as duas metades
    do caso que atravessa o meio, o equivalente a n elementos no
    total; e tem ~log2(n) niveis ate chegar no caso base -- bate com
    o O(n log n) esperado.
    """
    if n <= 1:
        return 1
    return round(n * log2(n))


def rodar_experimento() -> list[dict]:
    """Roda forca bruta e divide-and-conquer pra cada tamanho em TAMANHOS e junta os resultados."""
    random.seed(SEED)
    resultados = []

    for n in TAMANHOS:
        leituras = gerar_leituras_aleatorias(n)

        tempo_fb = medir_tempo_medio(buscar_intervalo_critico_forca_bruta, leituras)
        tempo_dc = medir_tempo_medio(buscar_intervalo_critico_divide_conquer, leituras)

        memoria_fb = medir_pico_de_memoria(buscar_intervalo_critico_forca_bruta, leituras)
        memoria_dc = medir_pico_de_memoria(buscar_intervalo_critico_divide_conquer, leituras)

        resultados.append(
            {
                "n": n,
                "tempo_forca_bruta_s": round(tempo_fb, 6),
                "tempo_divide_conquer_s": round(tempo_dc, 6),
                "operacoes_forca_bruta": operacoes_forca_bruta(n),
                "operacoes_divide_conquer": operacoes_divide_conquer(n),
                "memoria_forca_bruta_bytes": memoria_fb,
                "memoria_divide_conquer_bytes": memoria_dc,
            }
        )
        print(f"n={n}: forca bruta {round(tempo_fb, 4)}s | divide-and-conquer {round(tempo_dc, 4)}s")

    return resultados


def salvar_resultados(resultados: list[dict], caminho_csv: str = "data/escalabilidade.csv") -> None:
    """Escreve os resultados de rodar_experimento() num csv, uma linha por tamanho de entrada."""
    campos = list(resultados[0].keys())
    with open(caminho_csv, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(resultados)
    print(f"resultados salvos em {caminho_csv}")


if __name__ == "__main__":
    resultados_do_experimento = rodar_experimento()
    salvar_resultados(resultados_do_experimento)

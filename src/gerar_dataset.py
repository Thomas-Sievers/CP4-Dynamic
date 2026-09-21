"""
Cria o dataset sintetico da Questao 2 (gestao de consumo de energia).

"""

import csv
import random
from datetime import datetime, timedelta

SEED = 1  # Seed do grupo

INICIO = datetime(2025, 6, 1, 0, 0) # Define a data de incio do dataset
N_DIAS = 10 # Quantidade de dias do dataset
HORAS_POR_DIA = 24 # Quantidade de horas por dia
N_HORAS = N_DIAS * HORAS_POR_DIA  # 240 leituras por regiao

# cada regiao tem capacidade instalada e prioridade fixas, como numa
# rede eletrica real (ex: regiao com hospitais/industrias tem prioridade mais alta)

REGIOES = ["Norte", "Sul", "Leste", "Oeste", "Centro"]

CONSUMO_BASE = { 
    "Norte": 320.0,
    "Sul": 260.0,
    "Leste": 210.0,
    "Oeste": 280.0,
    "Centro": 400.0,
}

CAPACIDADE_DISPONIVEL = {
    "Norte": 380.0,
    "Sul": 300.0,
    "Leste": 230.0,
    "Oeste": 320.0,
    "Centro": 430.0,
}

PRIORIDADE = { # 1 = baixa, 2 = media, 3 = alta
    "Norte": 3,  
    "Sul": 2,
    "Leste": 1,
    "Oeste": 2,
    "Centro": 3,
}

TARIFA_NORMAL = 0.65  # custo por unidade de consumo em horario normal
TARIFA_PICO = 1.10  # custo por unidade de consumo em horario de pico

HORAS_DE_PICO = set(range(6, 9)) | set(range(18, 22))  # 6h-8h e 18h-21h


def esta_em_horario_de_pico(hora: int) -> bool:
    return hora in HORAS_DE_PICO  # True se a hora cai num horario de pico


def gerar_consumo(regiao: str, hora: int) -> float:
    """
    Consumo = base da regiao + acrescimo em horario de pico + ruido
    aleatorio. De vez em quando ultrapassa a capacidade disponivel de
    proposito, para a funcao de criticidade ter excessos para penalizar.
    """
    base = CONSUMO_BASE[regiao]  # consumo medio da regiao
    acrescimo_pico = base * 0.35 if esta_em_horario_de_pico(hora) else 0.0  # 35% a mais no pico
    ruido = random.gauss(0, base * 0.08)  # Cria um desvio padrão de 8% do consumo base
    return round(base + acrescimo_pico + ruido, 2)


def gerar_custo(consumo: float, hora: int) -> float:
    tarifa = TARIFA_PICO if esta_em_horario_de_pico(hora) else TARIFA_NORMAL  # tarifa muda no pico
    ruido = random.gauss(0, 0.02)  # pequena variacao na tarifa
    return round(consumo * (tarifa + ruido), 2)


def gerar_linhas() -> list[dict]:
    linhas: list[dict] = []
    for indice_hora in range(N_HORAS):  # percorre cada hora do periodo
        timestamp = INICIO + timedelta(hours=indice_hora)
        for regiao in REGIOES:  # uma leitura por regiao em cada hora
            consumo = gerar_consumo(regiao, timestamp.hour)
            custo = gerar_custo(consumo, timestamp.hour)
            linhas.append(
                {
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "regiao": regiao,
                    "consumo": consumo,
                    "capacidade_disponivel": CAPACIDADE_DISPONIVEL[regiao],
                    "prioridade": PRIORIDADE[regiao],
                    "custo": custo,
                }
            )
    return linhas


def main() -> None:
    random.seed(SEED)  # fixa a seed antes de gerar, para odataset ser sempre igual
    linhas: list[dict] = gerar_linhas()

    caminho_saida: str = "data/problema2.csv"
    campos: list[str] = [  # ordem das colunas no csv
        "timestamp",
        "regiao",
        "consumo",
        "capacidade_disponivel",
        "prioridade",
        "custo",
    ]

    with open(caminho_saida, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"{len(linhas)} linhas geradas em {caminho_saida}")


if __name__ == "__main__":
    main()

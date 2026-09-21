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

CAPACIDADE_DISPONIVEL = {  # 2x a base, pra o pico normal (1.35x) ficar bem abaixo da capacidade
    "Norte": 640.0,
    "Sul": 520.0,
    "Leste": 420.0,
    "Oeste": 560.0,
    "Centro": 800.0,
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

# evento critico injetado de proposito: simula uma falha/manutencao
# que derruba a capacidade disponivel de uma regiao por um periodo
# continuo, pra existir um trecho bem definido e pior que o resto.
EVENTO_REGIAO = "Sul"
EVENTO_INICIO_HORA = 100  # indice da hora onde o evento comeca (dia 5)
EVENTO_DURACAO_HORAS = 30  # quase um dia e meio de capacidade reduzida
EVENTO_FATOR_CAPACIDADE = 0.5  # capacidade cai pra metade durante o evento


def esta_no_evento_critico(regiao: str, indice_hora: int) -> bool:
    fim_do_evento = EVENTO_INICIO_HORA + EVENTO_DURACAO_HORAS
    return regiao == EVENTO_REGIAO and EVENTO_INICIO_HORA <= indice_hora < fim_do_evento


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

            capacidade = CAPACIDADE_DISPONIVEL[regiao]
            if esta_no_evento_critico(regiao, indice_hora):
                capacidade = round(capacidade * EVENTO_FATOR_CAPACIDADE, 2)

            linhas.append(
                {
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "regiao": regiao,
                    "consumo": consumo,
                    "capacidade_disponivel": capacidade,
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

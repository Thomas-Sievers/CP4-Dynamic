"""
Figura 3 da Questao 2: tempo de execucao (forca bruta vs
divide-and-conquer) por tamanho de entrada, usando os resultados
salvos em data/escalabilidade.csv (gerados por
src/experimento_escalabilidade.py). Salva em
figures/questao2/escalabilidade.png.
"""

import csv
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

COR_FORCA_BRUTA = "#2a78d6"
COR_DIVIDE_CONQUER = "#eb6834"
COR_TEXTO_PRIMARIO = "#0b0b0b"
COR_TEXTO_SECUNDARIO = "#52514e"
COR_MUTED = "#898781"
COR_GRADE = "#e1e0d9"
COR_EIXO = "#c3c2b7"
COR_SUPERFICIE = "#fcfcfb"

# paragrafo de interpretacao pedido na Parte D, escrito a partir dos
# numeros reais medidos em data/escalabilidade.csv
INTERPRETACAO = (
    "O tempo medido acompanha a analise assintotica esperada. Quando o tamanho "
    "da entrada cresce 50 vezes (de 100 para 5.000 leituras), o tempo da forca "
    "bruta cresce cerca de 2.554 vezes -- proximo de 50^2 = 2.500, exatamente o "
    "comportamento esperado de um algoritmo O(n^2). Ja o divide-and-conquer "
    "cresceu so ~62 vezes no mesmo intervalo, compativel com O(n log n): o "
    "log(n) cresce bem devagar (log2(100) ~ 6,6 e log2(5000) ~ 12,3), entao o "
    "crescimento fica dominado pelo proprio n, nao pelo seu quadrado. Pra "
    "datasets pequenos a diferenca e irrelevante (0,2ms vs 0,16ms pra n=100), "
    "mas a partir de alguns milhares de leituras a forca bruta ja fica "
    "visivelmente mais lenta -- e com n=1.000.000 ela se tornaria inviavel, "
    "enquanto o divide-and-conquer continuaria rapido."
)


def carregar_resultados(caminho_csv: str = "data/escalabilidade.csv") -> list[dict]:
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [
            {
                "n": int(linha["n"]),
                "tempo_forca_bruta_s": float(linha["tempo_forca_bruta_s"]),
                "tempo_divide_conquer_s": float(linha["tempo_divide_conquer_s"]),
            }
            for linha in leitor
        ]


def gerar_figura(caminho_saida: str = "figures/questao2/escalabilidade.png") -> None:
    resultados = carregar_resultados()
    tamanhos = [linha["n"] for linha in resultados]
    tempos_fb = [linha["tempo_forca_bruta_s"] for linha in resultados]
    tempos_dc = [linha["tempo_divide_conquer_s"] for linha in resultados]

    fig, eixo = plt.subplots(figsize=(9, 5.5), facecolor=COR_SUPERFICIE)
    eixo.set_facecolor(COR_SUPERFICIE)

    eixo.plot(tamanhos, tempos_fb, color=COR_FORCA_BRUTA, linewidth=2, marker="o", markersize=6, label="força bruta O(n²)")
    eixo.plot(
        tamanhos,
        tempos_dc,
        color=COR_DIVIDE_CONQUER,
        linewidth=2,
        marker="o",
        markersize=6,
        label="divide-and-conquer O(n log n)",
    )

    eixo.set_xscale("log")
    eixo.set_yscale("log")
    eixo.set_xlabel("tamanho da entrada (n, escala log)", color=COR_TEXTO_SECUNDARIO)
    eixo.set_ylabel("tempo de execução (s, escala log)", color=COR_TEXTO_SECUNDARIO)
    eixo.set_title(
        "Escalabilidade: força bruta vs divide-and-conquer",
        color=COR_TEXTO_PRIMARIO,
        fontsize=13,
        loc="left",
    )

    eixo.set_xticks(tamanhos)
    eixo.xaxis.set_major_formatter(mticker.ScalarFormatter())
    eixo.xaxis.set_minor_formatter(mticker.NullFormatter())
    eixo.tick_params(colors=COR_MUTED)
    eixo.grid(True, which="both", color=COR_GRADE, linewidth=0.7)
    for borda in ["top", "right"]:
        eixo.spines[borda].set_visible(False)
    for borda in ["left", "bottom"]:
        eixo.spines[borda].set_color(COR_EIXO)

    eixo.legend(loc="upper left", frameon=False, labelcolor=COR_TEXTO_SECUNDARIO, fontsize=9)

    fig.tight_layout()
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    fig.savefig(caminho_saida, dpi=150)
    plt.close(fig)

    print(f"figura salva em {caminho_saida}")
    print()
    print("interpretacao:")
    print(INTERPRETACAO)


if __name__ == "__main__":
    gerar_figura()

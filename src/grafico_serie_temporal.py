"""
Figura 1 da Questao 2: serie temporal de consumo por regiao, com o
intervalo critico encontrado pelo divide-and-conquer destacado.
Salva em figures/questao2/serie_temporal.png.
"""

import os
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from src.divide_conquer import buscar_intervalo_critico_divide_conquer
from src.estruturas import agrupar_por_regiao, carregar_leituras

# paleta categorica na mesma ordem de REGIOES (src/gerar_dataset.py),
# validada pro daltonismo -- ver skill de dataviz, references/palette.md
COR_POR_REGIAO = {
    "Norte": "#2a78d6",
    "Sul": "#eb6834",
    "Leste": "#1baf7a",
    "Oeste": "#eda100",
    "Centro": "#e87ba4",
}

COR_FAIXA_CRITICA = "#d03b3b"  # cor de status "critical" (nunca usada nas regioes)
COR_TINTA_PRIMARIA = "#0b0b0b"
COR_TINTA_SECUNDARIA = "#52514e"
COR_MUTED = "#898781"
COR_GRADE = "#e1e0d9"
COR_EIXO = "#c3c2b7"
COR_SUPERFICIE = "#fcfcfb"


def parse_timestamp(texto: str) -> datetime:
    return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")


def _estilizar_eixo(eixo) -> None:
    eixo.set_facecolor(COR_SUPERFICIE)
    eixo.tick_params(colors=COR_MUTED, labelsize=8)
    eixo.grid(True, color=COR_GRADE, linewidth=0.7)
    for borda in ["top", "right"]:
        eixo.spines[borda].set_visible(False)
    for borda in ["left", "bottom"]:
        eixo.spines[borda].set_color(COR_EIXO)


def gerar_figura(caminho_saida: str = "figures/questao2/serie_temporal.png") -> None:
    """
    Grafico em dois paineis pra nao poluir: o de cima mostra so a
    regiao Sul (onde o evento critico aconteceu) nos 10 dias inteiros,
    so pra situar ONDE o intervalo destacado fica no periodo todo. O
    de baixo da zoom nesse periodo (evento +/- 1 dia) com as 5
    regioes, pra dar pra comparar direito sem 10 dias de linhas
    sobrepostas.
    """
    leituras = carregar_leituras()
    por_regiao = agrupar_por_regiao(leituras)

    # acha o intervalo critico no dataset inteiro, pra destacar no grafico
    indice_inicio, indice_fim, criticidade = buscar_intervalo_critico_divide_conquer(leituras)
    inicio_critico = parse_timestamp(leituras[indice_inicio]["timestamp"])
    fim_critico = parse_timestamp(leituras[indice_fim]["timestamp"])

    margem = timedelta(days=1)
    zoom_inicio = inicio_critico - margem
    zoom_fim = fim_critico + margem

    fig, (eixo_visao_geral, eixo_zoom) = plt.subplots(
        2, 1, figsize=(10, 6.5), facecolor=COR_SUPERFICIE, height_ratios=[1, 2.2]
    )

    # painel de cima: visao geral dos 10 dias, so a regiao do evento
    leituras_sul = por_regiao["Sul"]
    tempos_sul = [parse_timestamp(leitura["timestamp"]) for leitura in leituras_sul]
    consumo_sul = [leitura["consumo"] for leitura in leituras_sul]
    eixo_visao_geral.plot(tempos_sul, consumo_sul, color=COR_POR_REGIAO["Sul"], linewidth=1.0)
    eixo_visao_geral.axvspan(inicio_critico, fim_critico, color=COR_FAIXA_CRITICA, alpha=0.18)
    eixo_visao_geral.set_title(
        "Onde o intervalo crítico fica nos 10 dias (região Sul)",
        color=COR_TINTA_SECUNDARIA,
        fontsize=9,
        loc="left",
    )
    eixo_visao_geral.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    _estilizar_eixo(eixo_visao_geral)

    # painel de baixo: zoom no periodo do evento, todas as regioes
    for regiao, cor in COR_POR_REGIAO.items():
        leituras_da_regiao = [
            leitura for leitura in por_regiao[regiao] if zoom_inicio <= parse_timestamp(leitura["timestamp"]) <= zoom_fim
        ]
        tempos = [parse_timestamp(leitura["timestamp"]) for leitura in leituras_da_regiao]
        consumos = [leitura["consumo"] for leitura in leituras_da_regiao]
        eixo_zoom.plot(tempos, consumos, color=cor, linewidth=1.6, marker="o", markersize=2.5, label=regiao)

    # capacidade disponivel do Sul, tracejada -- mostra o corte de
    # capacidade que causou o evento, exatamente onde o consumo do Sul
    # (linha solida laranja) passa por cima dela
    capacidade_sul_zoom = [
        leitura["capacidade_disponivel"]
        for leitura in leituras_sul
        if zoom_inicio <= parse_timestamp(leitura["timestamp"]) <= zoom_fim
    ]
    tempos_sul_zoom = [
        parse_timestamp(leitura["timestamp"])
        for leitura in leituras_sul
        if zoom_inicio <= parse_timestamp(leitura["timestamp"]) <= zoom_fim
    ]
    eixo_zoom.plot(
        tempos_sul_zoom,
        capacidade_sul_zoom,
        color=COR_POR_REGIAO["Sul"],
        linewidth=1.2,
        linestyle="--",
        alpha=0.7,
        label="capacidade disponível (Sul)",
    )

    eixo_zoom.axvspan(
        inicio_critico,
        fim_critico,
        color=COR_FAIXA_CRITICA,
        alpha=0.15,
        label="intervalo crítico encontrado",
    )

    eixo_zoom.set_title(
        "Consumo por região perto do evento crítico (com zoom)",
        color=COR_TINTA_PRIMARIA,
        fontsize=12,
        loc="left",
        pad=38,
    )
    eixo_zoom.set_xlabel("tempo", color=COR_TINTA_SECUNDARIA)
    eixo_zoom.set_ylabel("consumo", color=COR_TINTA_SECUNDARIA)
    eixo_zoom.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %Hh"))
    plt.setp(eixo_zoom.get_xticklabels(), rotation=30, ha="right")
    _estilizar_eixo(eixo_zoom)
    eixo_zoom.legend(
        loc="lower left",
        bbox_to_anchor=(0.0, 1.0),
        frameon=False,
        labelcolor=COR_TINTA_SECUNDARIA,
        fontsize=8,
        ncols=7,
        handlelength=1.5,
        columnspacing=1.2,
    )

    fig.tight_layout()

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    fig.savefig(caminho_saida, dpi=150)
    plt.close(fig)

    print(f"figura salva em {caminho_saida}")
    print(f"intervalo critico destacado: {inicio_critico} a {fim_critico} (criticidade {round(criticidade, 2)})")


if __name__ == "__main__":
    gerar_figura()

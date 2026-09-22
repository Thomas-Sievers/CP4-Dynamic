"""
Figura 2 da Questao 2: arvore de decomposicao do divide-and-conquer,
construida em cima do intervalo critico real da Figura 1. Salva em
figures/questao2/arvore_decomposicao.png.
"""

import os
from dataclasses import dataclass, field

import matplotlib.pyplot as plt

from src.divide_conquer import _melhor_intervalo_cruzando_o_meio
from src.criticidade import calcular_criticidade
from src.estruturas import carregar_leituras

INDICE_INICIO_REAL = 571  # onde comeca o intervalo critico real (Figura 1)
INDICE_FIM_REAL = 586  # onde termina

COR_NO = "#2a78d6"
COR_NO_VENCEDOR = "#d03b3b"
COR_TEXTO = "#0b0b0b"
COR_TEXTO_SECUNDARIO = "#52514e"
COR_LINHA = "#c3c2b7"
COR_SUPERFICIE = "#fcfcfb"


@dataclass
class No:
    esquerda: int  # indice local (0-based dentro do trecho usado)
    direita: int
    nivel: int
    criticidade: float
    inicio: int
    fim: int
    origem: str  # "base", "esquerda", "direita" ou "cruzando"
    filhos: list = field(default_factory=list)
    x: float = 0.0


def _construir_arvore(scores: list[float], esquerda: int, direita: int, nivel: int) -> No:
    """Mesma recursao de src/divide_conquer.py, so que guardando cada no."""
    if esquerda == direita:
        return No(esquerda, direita, nivel, scores[esquerda], esquerda, esquerda, "base")

    meio = (esquerda + direita) // 2
    no_esquerda = _construir_arvore(scores, esquerda, meio, nivel + 1)
    no_direita = _construir_arvore(scores, meio + 1, direita, nivel + 1)
    inicio_c, fim_c, criticidade_c = _melhor_intervalo_cruzando_o_meio(scores, esquerda, meio, direita)

    candidatos = [
        (no_esquerda.criticidade, no_esquerda.inicio, no_esquerda.fim, "esquerda"),
        (no_direita.criticidade, no_direita.inicio, no_direita.fim, "direita"),
        (criticidade_c, inicio_c, fim_c, "cruzando"),
    ]
    melhor_criticidade, melhor_inicio, melhor_fim, origem = max(candidatos, key=lambda c: c[0])

    no = No(esquerda, direita, nivel, melhor_criticidade, melhor_inicio, melhor_fim, origem)
    no.filhos = [no_esquerda, no_direita]
    return no


def _atribuir_posicoes_x(no: No, proximo_x: list[float]) -> None:
    """Folha ganha a proxima posicao livre; no interno fica no meio dos filhos."""
    if not no.filhos:
        no.x = proximo_x[0]
        proximo_x[0] += 1
        return
    for filho in no.filhos:
        _atribuir_posicoes_x(filho, proximo_x)
    no.x = sum(filho.x for filho in no.filhos) / len(no.filhos)


def _marcar_caminho_vencedor(no: No, caminho: set[int]) -> None:
    """
    Segue o caminho do no raiz ate onde a resposta final foi decidida.
    Se o vencedor foi uma das metades, continua descendo por ela. Se
    foi o caso cruzando o meio, o caminho para ali -- o intervalo
    vencedor nao e mais um unico filho a partir desse ponto.
    """
    caminho.add(id(no))
    if no.origem == "esquerda":
        _marcar_caminho_vencedor(no.filhos[0], caminho)
    elif no.origem == "direita":
        _marcar_caminho_vencedor(no.filhos[1], caminho)
    # se for "cruzando" ou "base", o caminho destacado termina aqui


def _rotulo(no: No, leituras: list[dict]) -> str:
    if not no.filhos:
        leitura = leituras[INDICE_INICIO_REAL + no.esquerda]
        hora = leitura["timestamp"][11:16]
        return f"{leitura['regiao']}\n{hora}\ncrit={no.criticidade:.0f}"
    return f"[{INDICE_INICIO_REAL + no.esquerda},{INDICE_INICIO_REAL + no.direita}]\ncrit={no.criticidade:.0f}\n({no.origem})"


def _desenhar_no(eixo, no: No, leituras: list[dict], caminho_vencedor: set[int]) -> None:
    y = -no.nivel
    cor_borda = COR_NO_VENCEDOR if id(no) in caminho_vencedor else COR_NO
    largura, altura = (0.9, 0.7) if no.filhos else (0.8, 0.65)

    caixa = plt.Rectangle(
        (no.x - largura / 2, y - altura / 2),
        largura,
        altura,
        facecolor=COR_SUPERFICIE,
        edgecolor=cor_borda,
        linewidth=1.8 if id(no) in caminho_vencedor else 1.1,
        zorder=3,
    )
    eixo.add_patch(caixa)
    eixo.text(
        no.x,
        y,
        _rotulo(no, leituras),
        ha="center",
        va="center",
        fontsize=6.5,
        color=COR_TEXTO,
        zorder=4,
    )

    for filho in no.filhos:
        eixo.plot([no.x, filho.x], [y - altura / 2, -filho.nivel + altura / 2], color=COR_LINHA, linewidth=1, zorder=1)
        _desenhar_no(eixo, filho, leituras, caminho_vencedor)


def gerar_figura(caminho_saida: str = "figures/questao2/arvore_decomposicao.png") -> None:
    """Monta a arvore em cima do intervalo critico real e salva a figura em caminho_saida."""
    leituras = carregar_leituras()
    trecho = leituras[INDICE_INICIO_REAL : INDICE_FIM_REAL + 1]
    scores = [calcular_criticidade(leitura) for leitura in trecho]

    raiz = _construir_arvore(scores, 0, len(scores) - 1, nivel=0)
    _atribuir_posicoes_x(raiz, [0.0])

    caminho_vencedor: set[int] = set()
    _marcar_caminho_vencedor(raiz, caminho_vencedor)

    profundidade_maxima = max(no.nivel for no in _todos_os_nos(raiz))

    fig, eixo = plt.subplots(figsize=(15, 2.2 * (profundidade_maxima + 1)), facecolor=COR_SUPERFICIE)
    eixo.set_facecolor(COR_SUPERFICIE)

    _desenhar_no(eixo, raiz, leituras, caminho_vencedor)

    eixo.set_xlim(-1, len(scores))
    eixo.set_ylim(-profundidade_maxima - 0.6, 0.6)
    eixo.axis("off")
    eixo.set_title(
        f"Árvore de decomposição do divide-and-conquer\nintervalo real [{INDICE_INICIO_REAL},{INDICE_FIM_REAL}] "
        f"(evento crítico, região Sul) -- contorno vermelho = caminho vencedor",
        color=COR_TEXTO,
        fontsize=11,
    )

    fig.tight_layout()
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    fig.savefig(caminho_saida, dpi=150)
    plt.close(fig)

    print(f"figura salva em {caminho_saida}")
    print(f"niveis da arvore: {profundidade_maxima + 1}")
    print(f"resultado no topo: [{INDICE_INICIO_REAL + raiz.inicio},{INDICE_INICIO_REAL + raiz.fim}] criticidade {round(raiz.criticidade, 2)}")


def _todos_os_nos(no: No) -> list[No]:
    nos = [no]
    for filho in no.filhos:
        nos.extend(_todos_os_nos(filho))
    return nos


if __name__ == "__main__":
    gerar_figura()

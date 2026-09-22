"""Shared data structures for Question 1 and Question 2.

Question 1 (emergency logistics) defines its types inside a delimited
``# ===== Question 1 =====`` block, added in Step 2: ``Depot``, ``Site``,
``Edge``, ``Instance``, the ``Graph`` type alias, and later ``Solution``.
Question 2 (energy consumption management) adds its own delimited block:
``carregar_leituras``, ``regioes_existentes``, ``agrupar_por_regiao``,
``agrupar_por_horario``, ``agrupar_por_regiao_e_hora`` and
``maiores_picos_de_consumo``.
"""

from __future__ import annotations

import csv
import heapq
from dataclasses import dataclass

# ===== Question 1 =====

# Adjacency list of available roads: node_id -> [(neighbor_id, distance), ...].
# A dict gives O(1) access from a node to its neighbors (Lesson 14 WeightedDAG style).
Graph = dict[int, list[tuple[int, int]]]


@dataclass(frozen=True, slots=True)
class Depot:
    """The single distribution center (node id 0)."""

    node_id: int
    name: str
    x: int
    y: int

    def __post_init__(self) -> None:
        # Base case of the whole model: there is exactly one depot, and it is node 0.
        if self.node_id != 0:
            raise ValueError(f"Depot node_id must be 0, got {self.node_id}.")


@dataclass(frozen=True, slots=True)
class Site:
    """A candidate service point, with its demands and expected benefit.

    ``load`` and ``effective_benefit`` (D10) are derived properties, not
    stored fields, so editing any single demand, the priority or the
    expected benefit automatically changes them -- needed for the live
    input changes during the defense.
    """

    node_id: int
    name: str
    x: int
    y: int
    people_affected: int
    priority: int
    water: int
    medicine: int
    food: int
    hygiene_kits: int
    blankets: int
    expected_benefit: int

    def __post_init__(self) -> None:
        if self.node_id <= 0:
            raise ValueError(f"Site node_id must be positive, got {self.node_id}.")
        if not (1 <= self.priority <= 5):
            raise ValueError(f"Site {self.node_id}: priority must be in 1..5, got {self.priority}.")
        for field_name, value in (
            ("people_affected", self.people_affected),
            ("water", self.water),
            ("medicine", self.medicine),
            ("food", self.food),
            ("hygiene_kits", self.hygiene_kits),
            ("blankets", self.blankets),
            ("expected_benefit", self.expected_benefit),
        ):
            if value < 0:
                raise ValueError(f"Site {self.node_id}: {field_name} must be non-negative, got {value}.")
        if self.load <= 0:
            raise ValueError(f"Site {self.node_id}: load (sum of demands) must be positive, got {self.load}.")

    @property
    def load(self) -> int:
        """Integer load in D1's single "load units": the sum of the five demands."""
        return self.water + self.medicine + self.food + self.hygiene_kits + self.blankets

    @property
    def effective_benefit(self) -> int:
        """D10: expected benefit scaled by priority, the value the algorithms optimize."""
        return self.expected_benefit * self.priority


@dataclass(frozen=True, slots=True)
class Edge:
    """An undirected road between two nodes, possibly blocked."""

    node_a: int
    node_b: int
    distance: int
    available: bool

    def __post_init__(self) -> None:
        if self.node_a >= self.node_b:
            raise ValueError(
                f"Edge node_a must be smaller than node_b, got ({self.node_a}, {self.node_b})."
            )
        if self.distance <= 0:
            raise ValueError(
                f"Edge ({self.node_a}, {self.node_b}): distance must be positive, got {self.distance}."
            )


@dataclass(frozen=True, slots=True)
class Instance:
    """The full Question 1 dataset: one depot, its candidate sites and the roads between them."""

    depot: Depot
    sites: tuple[Site, ...]
    edges: tuple[Edge, ...]

    def graph(self) -> Graph:
        """Build the adjacency list of the available edges only.

        Returns
        -------
        Graph
            node_id -> list of (neighbor_id, distance), available edges only.
        """
        adjacency: Graph = {self.depot.node_id: []}
        for site in self.sites:
            adjacency[site.node_id] = []
        for edge in self.edges:
            if not edge.available:
                continue
            adjacency[edge.node_a].append((edge.node_b, edge.distance))
            adjacency[edge.node_b].append((edge.node_a, edge.distance))
        return adjacency

    def site_by_id(self, node_id: int) -> Site:
        """Look up a site by its node_id.

        Parameters
        ----------
        node_id : int
            The id to search for.

        Returns
        -------
        Site
            The matching site.

        Raises
        ------
        ValueError
            If no site has this node_id.
        """
        for site in self.sites:
            if site.node_id == node_id:
                return site
        raise ValueError(f"Unknown site node_id: {node_id}")


@dataclass(frozen=True, slots=True)
class Solution:
    """A service plan: the shared return shape for Greedy (Step 3) and DP (Step 4).

    Storing ``selected_sites`` already in pi order lets Part E draw the
    service sequence directly, and lets Part D compare Greedy and DP by
    just diffing two ``Solution`` values under the same objective.
    """

    selected_sites: tuple[int, ...]  # site node ids, in pi (visiting) order
    total_benefit: int  # sum of effective_benefit over selected_sites
    total_load: int  # sum of load over selected_sites; must be <= capacity
    route_length: int  # L(S): depot -> selected_sites in pi order, no return
    objective_value: int  # J(S) = total_benefit - lambda_price * route_length

    def __post_init__(self) -> None:
        if self.total_load < 0:
            raise ValueError(f"Solution total_load must be non-negative, got {self.total_load}.")
        if self.route_length < 0:
            raise ValueError(f"Solution route_length must be non-negative, got {self.route_length}.")


# ===== end Question 1 =====

# ===== Question 2 =====


def carregar_leituras(caminho_csv: str = "data/problema2.csv") -> list[dict]:
    """
    LIST de dicts, uma leitura por linha do csv, na ordem do arquivo.
    Numa lista cada posicao tem um indice fixo, entao acessar
    leituras[5] ou pegar um pedaco leituras[inicio:fim+1] e so
    calcular o endereco daquela posicao -- nao precisa percorrer nada
    antes. E isso que a forca bruta e o divide and conquer usam pra
    selecionar qualquer intervalo continuo de tempo. Acesso O(1) por
    posicao, O(k) pra copiar um pedaco de tamanho k.
    """
    leituras = []
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            leituras.append(
                {
                    "timestamp": linha["timestamp"],
                    "regiao": linha["regiao"],
                    "consumo": float(linha["consumo"]),
                    "capacidade_disponivel": float(linha["capacidade_disponivel"]),
                    "prioridade": int(linha["prioridade"]),
                    "custo": float(linha["custo"]),
                }
            )

    if not leituras:
        raise ValueError(f"Leitura não encontrada {caminho_csv}")

    return leituras


def regioes_existentes(leituras: list[dict]) -> set[str]:
    """
    SET com os nomes de regiao sem repeticao. Um set guarda cada item
    numa posicao calculada a partir do hash do proprio valor -- pra
    testar se "Norte" esta no set, ele calcula o hash de "Norte" e
    olha direto naquela posicao, sem comparar com os outros itens.
    Numa lista, o Python teria que comparar item por item ate achar
    "Norte" ou chegar no fim. Por isso testar pertencimento e O(1) no
    set, contra O(n) na lista.
    """
    return {leitura["regiao"] for leitura in leituras}


def agrupar_por_regiao(leituras: list[dict]) -> dict[str, list[dict]]:
    """
    DICT regiao -> lista de leituras. Um dict funciona como o set: a
    chave vira um hash, e esse hash aponta direto pra posicao onde a
    lista daquela regiao esta guardada -- sem busca sequencial. Se as
    leituras estivessem so numa lista, achar "todas do Norte" exigiria
    percorrer tudo comparando a regiao de cada item; com o dict,
    agrupado["Norte"] vai direto no lugar certo. O(1) por consulta,
    contra O(n) na lista.
    """
    agrupado: dict[str, list[dict]] = {}
    for leitura in leituras:
        agrupado.setdefault(leitura["regiao"], []).append(leitura)
    return agrupado


def agrupar_por_horario(leituras: list[dict]) -> dict[int, list[dict]]:
    """
    DICT hora_do_dia -> lista de leituras naquela hora, juntando todas
    as regioes. Mesma vantagem de agrupar_por_regiao: consumo por
    horario vira uma busca por chave O(1) (ex.: agrupado[18] pra ver
    tudo que aconteceu as 18h em qualquer dia/regiao), em vez de
    percorrer as leituras inteiras toda consulta.
    """
    agrupado: dict[int, list[dict]] = {}
    for leitura in leituras:
        hora_do_dia = int(leitura["timestamp"][11:13])
        agrupado.setdefault(hora_do_dia, []).append(leitura)
    return agrupado


def agrupar_por_regiao_e_hora(leituras: list[dict]) -> dict[tuple[str, int], list[dict]]:
    """
    DICT com chave TUPLE (regiao, hora_do_dia). Pra virar chave de
    dict, o valor precisa ser hashavel, ou seja, o hash dele nao pode
    mudar depois de criado. Tupla e imutavel (nao da pra fazer
    append/remover item nela), entao o hash dela e fixo e ela serve
    como chave; lista e mutavel, entao o Python nem deixa usar lista
    como chave -- o hash poderia mudar e quebrar a busca interna do
    dict. Com (regiao, hora) como chave, "consumo do Norte as 18h" e
    uma busca direta O(1); sem a tupla, precisaria de um dict aninhado
    ou percorrer tudo comparando regiao e hora ao mesmo tempo.
    """
    agrupado: dict[tuple[str, int], list[dict]] = {}
    for leitura in leituras:
        hora_do_dia = int(leitura["timestamp"][11:13])
        chave = (leitura["regiao"], hora_do_dia)
        agrupado.setdefault(chave, []).append(leitura)
    return agrupado


def maiores_picos_de_consumo(leituras: list[dict], quantidade: int = 10) -> list[dict]:
    """
    HEAP (heapq.nlargest) pra achar os maiores consumos sem ordenar
    tudo. Ele percorre a lista mantendo so uma estrutura de
    tamanho "quantidade": a cada novo item, compara com o menor valor
    que ja esta guardado ali e so troca se o novo for maior, sem
    reorganizar tudo de novo. Ordenar o dataset inteiro pra depois
    pegar os primeiros custaria O(n log n); manter so os k maiores
    nessa estrutura custa O(n log k).
    """
    if quantidade <= 0:
        raise ValueError("quantidade precisa ser maior que zero")

    return heapq.nlargest(quantidade, leituras, key=lambda leitura: leitura["consumo"])


# ===== end Question 2 =====

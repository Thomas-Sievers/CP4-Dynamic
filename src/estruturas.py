"""
Estruturas de dados da Questao 2 (gestao de consumo de energia).
"""
import csv
import heapq


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

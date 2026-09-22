"""
Testes da Questao 2 (gestao de consumo de energia): criticidade,
estruturas de dados, forca bruta e divide-and-conquer.

Usa leituras pequenas e feitas a mao pra cada resultado esperado ser
facil de conferir na mao -- o dataset real (data/problema2.csv) so
entra no teste de integracao no final, pra garantir que os dois
algoritmos continuam concordando nele.
"""

import random

import pytest

from src.brute_force import buscar_intervalo_critico_forca_bruta
from src.criticidade import calcular_criticidade
from src.divide_conquer import buscar_intervalo_critico_divide_conquer
from src.estruturas import (
    agrupar_por_regiao,
    agrupar_por_regiao_e_hora,
    carregar_leituras,
    maiores_picos_de_consumo,
    regioes_existentes,
)


def leitura(consumo, capacidade=400.0, prioridade=1, regiao="Norte", timestamp="2025-01-01 00:00:00"):
    return {
        "timestamp": timestamp,
        "regiao": regiao,
        "consumo": consumo,
        "capacidade_disponivel": capacidade,
        "prioridade": prioridade,
        "custo": 0.0,
    }


def leitura_com_criticidade(score, timestamp="2025-01-01 00:00:00"):
    """
    Monta uma leitura cuja criticidade da exatamente 'score'. Usa uma
    capacidade bem alta (1000) pra nunca estourar -- assim
    consumo_relativo = consumo - 750 e a penalidade de excesso fica
    sempre zero, entao criticidade = consumo - 750. Basta escolher
    consumo = score + 750.
    """
    return leitura(consumo=score + 750.0, capacidade=1000.0, prioridade=1, timestamp=timestamp)


class TestCriticidade:
    def test_leitura_dentro_do_limiar_seguro_fica_negativa(self):
        # 200 de consumo numa capacidade de 400: bem abaixo dos 75% (300)
        l = leitura(consumo=200.0, capacidade=400.0)
        assert calcular_criticidade(l) < 0

    def test_leitura_passando_da_capacidade_fica_positiva(self):
        l = leitura(consumo=500.0, capacidade=400.0)
        assert calcular_criticidade(l) > 0

    def test_prioridade_maior_aumenta_a_penalidade_quando_ha_excesso(self):
        prioridade_baixa = leitura(consumo=500.0, capacidade=400.0, prioridade=1)
        prioridade_alta = leitura(consumo=500.0, capacidade=400.0, prioridade=3)
        assert calcular_criticidade(prioridade_alta) > calcular_criticidade(prioridade_baixa)

    def test_prioridade_nao_muda_nada_sem_excesso(self):
        # a prioridade so multiplica a penalidade de excesso; sem excesso, ela e zero dos dois jeitos
        prioridade_baixa = leitura(consumo=200.0, capacidade=400.0, prioridade=1)
        prioridade_alta = leitura(consumo=200.0, capacidade=400.0, prioridade=3)
        assert calcular_criticidade(prioridade_baixa) == calcular_criticidade(prioridade_alta)


class TestEstruturas:
    def _leituras_de_exemplo(self):
        return [
            leitura(300, 400, 1, "Norte", "2025-01-01 00:00:00"),
            leitura(200, 300, 2, "Sul", "2025-01-01 00:00:00"),
            leitura(500, 400, 1, "Norte", "2025-01-01 01:00:00"),
        ]

    def test_regioes_existentes_sem_repeticao(self):
        assert regioes_existentes(self._leituras_de_exemplo()) == {"Norte", "Sul"}

    def test_agrupar_por_regiao(self):
        agrupado = agrupar_por_regiao(self._leituras_de_exemplo())
        assert len(agrupado["Norte"]) == 2
        assert len(agrupado["Sul"]) == 1

    def test_agrupar_por_regiao_e_hora(self):
        agrupado = agrupar_por_regiao_e_hora(self._leituras_de_exemplo())
        assert agrupado[("Norte", 0)][0]["consumo"] == 300
        assert agrupado[("Norte", 1)][0]["consumo"] == 500

    def test_maiores_picos_de_consumo(self):
        picos = maiores_picos_de_consumo(self._leituras_de_exemplo(), 2)
        assert [p["consumo"] for p in picos] == [500, 300]

    def test_maiores_picos_de_consumo_quantidade_invalida(self):
        with pytest.raises(ValueError):
            maiores_picos_de_consumo(self._leituras_de_exemplo(), 0)

    def test_carregar_leituras_arquivo_inexistente(self):
        with pytest.raises(FileNotFoundError):
            carregar_leituras("data/isso_nao_existe.csv")


# scores classicos de exemplo (subarray de soma maxima): a resposta
# certa e o trecho [3,6] = 4-1+2+1 = 6
SCORES_DE_EXEMPLO = [-2, 1, -3, 4, -1, 2, 1, -5, 4]


class TestForcaBrutaEDivideConquer:
    def _leituras_de_exemplo(self):
        return [leitura_com_criticidade(score) for score in SCORES_DE_EXEMPLO]

    @pytest.mark.parametrize(
        "buscar_intervalo_critico",
        [buscar_intervalo_critico_forca_bruta, buscar_intervalo_critico_divide_conquer],
    )
    def test_acha_o_intervalo_critico_certo(self, buscar_intervalo_critico):
        inicio, fim, criticidade = buscar_intervalo_critico(self._leituras_de_exemplo())
        assert (inicio, fim) == (3, 6)
        assert criticidade == pytest.approx(6.0)

    @pytest.mark.parametrize(
        "buscar_intervalo_critico",
        [buscar_intervalo_critico_forca_bruta, buscar_intervalo_critico_divide_conquer],
    )
    def test_lista_de_um_elemento(self, buscar_intervalo_critico):
        inicio, fim, criticidade = buscar_intervalo_critico([leitura_com_criticidade(-5)])
        assert (inicio, fim) == (0, 0)
        assert criticidade == pytest.approx(-5.0)

    @pytest.mark.parametrize(
        "buscar_intervalo_critico",
        [buscar_intervalo_critico_forca_bruta, buscar_intervalo_critico_divide_conquer],
    )
    def test_lista_vazia_levanta_erro(self, buscar_intervalo_critico):
        with pytest.raises(ValueError):
            buscar_intervalo_critico([])

    def test_forca_bruta_e_divide_conquer_concordam_em_casos_aleatorios(self):
        random.seed(7)
        for _ in range(20):
            tamanho = random.randint(1, 40)
            scores = [random.uniform(-50, 50) for _ in range(tamanho)]
            leituras = [leitura_com_criticidade(score) for score in scores]

            resultado_fb = buscar_intervalo_critico_forca_bruta(leituras)
            resultado_dc = buscar_intervalo_critico_divide_conquer(leituras)

            assert resultado_fb[2] == pytest.approx(resultado_dc[2])


class TestIntegracaoComODatasetReal:
    def test_forca_bruta_e_divide_conquer_concordam_no_dataset_real(self):
        leituras = carregar_leituras()

        resultado_fb = buscar_intervalo_critico_forca_bruta(leituras)
        resultado_dc = buscar_intervalo_critico_divide_conquer(leituras)

        assert resultado_fb[2] == pytest.approx(resultado_dc[2])
        assert (resultado_fb[0], resultado_fb[1]) == (resultado_dc[0], resultado_dc[1])

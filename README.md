# CP4-Dynamic

Checkpoint 4 — Grafos, estratégias Greedy e Programação Dinâmica aplicadas a dois problemas
reais: logística emergencial após eventos climáticos (Questão 1) e gestão de consumo de energia
(Questão 2).

## Equipe

| Nome | RM |
|---|---|
| Thomas Sievers | 563566 |
| Marco Aurélio | 563827 |
| Áurea Sardinha | 563837 |
| Matheus Vasques | 563309 |
| Bernardo Hanashiro | 565266 |

## Reprodutibilidade

`SEED = 1` — identificador atribuído ao nosso grupo, usado como seed do gerador de números
aleatórios nos dois datasets (`SEED = numero_do_grupo`). Desenvolvido e testado com Python 3.12
(as sequências de números aleatórios só têm reprodutibilidade garantida na mesma versão do
Python).

# Questão 1 — Logística Emergencial

### 1 Problema

Uma equipe de defesa civil opera um único centro de distribuição com suprimentos limitados
(água, remédio, alimento, kits de higiene, cobertores) e um veículo para atender até 20 pontos
de atendimento afetados. Cada ponto tem uma população afetada, um nível de prioridade, uma
demanda mínima por recurso, um benefício esperado, e estradas até outros pontos que podem estar
indisponíveis (bloqueadas). O grafo não é totalmente conectado, e algumas estradas são declaradas
indisponíveis. Dada a capacidade de carga do veículo, o objetivo é escolher quais pontos atender
— e em que ordem — para maximizar o benefício total, usando duas estratégias diferentes (Greedy
e Programação Dinâmica) e comparando-as honestamente, incluindo um caso em que o Greedy *não* é
ótimo.

### 2 Modelo adotado

O modelo completo e cada trade-off estão registrados como um log de decisões em
`claude/SPEC.md` (Seção 3, decisões D1–D15); a versão resumida:

- **Grafo**: 1 depósito (nó 0) + 20 sites candidatos, estradas com distância inteira, algumas
  marcadas como indisponíveis. As distâncias entre dois nós quaisquer são distâncias de menor
  caminho apenas sobre estradas *disponíveis*, calculadas pelo nosso próprio Dijkstra (D6).
- **Capacidade**: uma capacidade `C` em "unidades de carga" inteiras por viagem do veículo; a
  carga de um site é a soma das suas cinco demandas (D1). O atendimento é tudo-ou-nada por site
  (0/1, D2) — sem entregas parciais.
- **Rota**: uma única viagem aberta, depósito → site → … → site, sem volta, sem múltiplas
  viagens (D3).
- **Objetivo**: `J(S) = soma(effective_benefit) - lambda * L(S)`, onde `effective_benefit =
  expected_benefit * priority` (D10) e `L(S)` é o comprimento da rota do conjunto `S` visitado
  em uma ordem canônica fixa `pi` (D5). `pi` é a busca em profundidade pré-ordem (pre-order DFS)
  da árvore de menor caminho a partir do depósito (D9) — sites do mesmo ramo ficam consecutivos,
  então um cluster compacto fica barato de visitar. `lambda` é um inteiro fixo, calibrado uma
  única vez a partir do dataset real (`mediana(effective_benefit) / mediana(distância até o
  depósito)`, D11): **21** para `SEED = 1`.
- Tanto o Greedy quanto o DP otimizam exatamente o mesmo `J(S)` (D4), então qualquer diferença
  entre os resultados vem apenas da estratégia, não de um objetivo diferente.

### 3 Estruturas de dados

Justificadas pela operação que cada uma torna barata (Seção 5.2 de `claude/SPEC.md`):

| Estrutura | Usada para | Por quê |
|---|---|---|
| `dict[int, list[tuple[int, int]]]` (`Graph`) | lista de adjacência | acesso O(1) de um nó aos seus vizinhos |
| `set` | posições ocupadas na grade, checagem de estrada bloqueada, candidatos visitados/elegíveis | teste de pertencimento O(1) |
| `heapq` (heap binária) | fronteira do Dijkstra | extract-min O(log n) |
| `collections.deque` | checagem de conectividade (BFS) ao bloquear estradas | `popleft` O(1) |
| `tuple` (dataclasses congeladas) | `Site`, `Edge`, `Depot`, `Instance`, `Solution` | objetos de valor imutáveis, seguros para reusar/comparar |
| `list[list[float]]` | a tabela do DP `dp[i][c]` | tabela densa: a maioria dos estados `(site, carga)` é preenchida |
| `dict[int, dict[int, float]]` | a matriz de distâncias entre todos os pares | acesso esparso por origem, um resultado de Dijkstra por chave |

### 4 Algoritmos

- **Greedy** (`src/greedy.py`, D12): atende repetidamente o site ainda não escolhido, que cabe
  na capacidade restante, com a maior densidade de benefício marginal `delta_J_i(S) / load_i`;
  para quando nenhum site tem ganho marginal positivo. É localmente ótimo para o relaxamento
  *fracionário* (um argumento de troca: trocar um item escolhido por outro de menor densidade
  não pode melhorar o resultado), mas a restrição 0/1 faz com que a capacidade que sobra após a
  melhor escolha por densidade possa ser desperdiçada — exatamente onde ele pode perder para o
  DP (Parte D).
- **Programação Dinâmica** (`src/dynamic_programming.py`, Seção 4): DP bottom-up sobre estados
  `dp[i][c]` = melhor `J` para uma rota que termina no i-ésimo site de `pi` com carga
  exatamente `c`. Caso base `dp[i][w_i] = b_i - lambda * d(depósito, site_i)`; a recorrência
  considera todo site anterior `j < i` como predecessor direto. A explicação completa de
  estado/decisão/caso base/recorrência/reconstrução está na docstring do módulo e em
  `docs/analise_complexidade.md`.
- Os dois retornam o mesmo formato `Solution` (D15: sem `Strategy`/`ABC` — funções simples), o
  que permite que a Parte D os compare diretamente.

### 5 Como executar

```bash
# 1. Crie um ambiente com Python >= 3.10 e instale as dependências
python3 -m venv .venv   # ou: uv venv --python 3.12 .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. (Re)gere o dataset a partir de SEED = 1 (data/problema1.csv, problema1_edges.csv)
python -m src.data_generator

# 3. Rode os testes
pytest -q

# 4. Regenere as figuras (figures/questao1/*.png)
python -m src.plots

# 5. Rode o notebook do início ao fim
jupyter nbconvert --to notebook --execute notebooks/questao1.ipynb --output questao1.ipynb
```

### 6 Resultados

No dataset seed-1, capacidade padrão `C = 581` (`floor(0.35 * 1662)`), `lambda = 21`:

| | Sites atendidos | Benefício total | Carga total | Comprimento da rota | J(S) |
|---|---:|---:|---:|---:|---:|
| Greedy | 8 | 15565 | 564 | 318 | **8887** |
| DP (ótimo) | 7 | 17439 | 580 | 274 | **11685** |

O DP supera estritamente o Greedy no dataset real (diferença = 2798): a escolha do Greedy por
densidade deixa capacidade sobrando que o DP preenche com uma combinação melhor. Um contraexemplo
pequeno, construído à mão (3 sites, capacidade 10, `lambda = 1`), torna a falha exata e
demonstrável no papel: o Greedy escolhe o único site de maior densidade (`J = 59`) e depois não
consegue encaixar mais nada, enquanto o DP escolhe os outros dois sites juntos (`J = 88`) — veja
`docs/analise_complexidade.md` e `tests/test_questao1.py` (`test_case_2_...`,
`test_case_3_...`) para o traço completo. As quatro figuras (rede de atendimento, plano de
solução do DP, tabela de evolução do DP, comparação de crescimento de tempo) estão em
`figures/questao1/` e são percorridas em `notebooks/questao1.ipynb`.

### 7 Complexidade

Derivação completa em `docs/analise_complexidade.md`. Resumo, nos próprios parâmetros do
problema (`V = 21`, `E = 38` para seed 1, `N` = sites candidatos, `C` = capacidade):

- **Greedy**: tempo `O(N^3)` (N rodadas x N candidatos x busca O(N) de ganho marginal),
  memória `O(N)`.
- **DP**: tempo `O(N^2 * C)` (`N * (C+1)` estados x até `N` predecessores cada), memória
  `O(N * C)` — pseudo-polinomial em `C`. Diferente de uma mochila 0/1 clássica, a recorrência
  deste DP permite que *qualquer* site anterior (não só o imediatamente anterior) seja
  predecessor direto, então não pode ser reduzida a um vetor rolante `O(C)` mesmo ignorando a
  reconstrução.
- O pré-processamento (Dijkstra + a matriz de distâncias completa + `pi`) é `O(N * (V+E) log
  V)`, desprezível perto do DP nessa escala (medido em menos de um milissegundo contra ~5 ms do
  próprio DP).

### 8 Limitações

- **Capacidade em um único recurso** (D1): as cinco demandas separadas de um site são
  colapsadas em um único número de carga, então o modelo não consegue expressar "água
  suficiente mas sem cobertores"; uma versão multi-recurso de verdade seria uma mochila
  multidimensional.
- **Atendimento 0/1** (D2): sem entregas parciais, embora seja exatamente isso que torna o DP
  bem definido e o modo de falha do Greedy possível.
- **Um veículo, uma viagem aberta, sem volta** (D3): uma simplificação de um roteamento real com
  múltiplas viagens (VRP), que é NP-difícil e está fora do escopo aqui.
- **Convenção de rota de um conjunto** (D5): `J(S)` é calculado com os sites visitados na ordem
  fixa `pi`; para um dado conjunto `S`, pode existir uma ordem de visita melhor. O DP é exato
  *para esse `J`*, não para a melhor rota irrestrita de cada `S` possível.
- **`lambda` é fixo**, não é recalibrado se o dataset mudar durante a execução (D11) — mudar
  pesos ao vivo durante a apresentação não o reajusta automaticamente.

# Questão 2 — Gestão de Consumo de Energia

Responsável: Marco Aurélio

### 1 Problema

A simplified power grid records hourly consumption readings from several regions
(`timestamp`, `regiao`, `consumo`, `capacidade_disponivel`, `prioridade`, `custo`). The goal is
to find the single **continuous** time interval with the highest accumulated **criticality** —
the worst stretch of time the grid went through — using two different strategies (brute force
and divide-and-conquer) and comparing them.

### 2 Modelo adotado

- **Dataset** (`src/gerar_dataset.py`): 1,200 synthetic hourly readings (10 days x 5 regions),
  documented and reproducible with `SEED = 1`.
- **Injected critical event**: region Sul has its available capacity cut in half for a
  continuous 30-hour window (simulating an outage/maintenance), while every region's capacity
  is otherwise sized at 2x its base consumption so ordinary daily peaks stay safely under it.
  Without a deliberate event like this, daily peaks repeat too evenly across all 10 days and the
  "most critical interval" degenerates to almost the entire dataset (see Limitations).
- **Criticality function** (`src/criticidade.py`):
  `criticidade = consumo_relativo + penalidade_por_excesso`, where
  `consumo_relativo = consumo - capacidade_disponivel * 0.75` (negative while a reading stays
  under 75% of *its own* capacity, which normalizes the score across regions of very different
  scale) and `penalidade_por_excesso = max(0, consumo - capacidade_disponivel) * 2.0 *
  prioridade` (only nonzero once capacity is actually exceeded; priority multiplies the excess
  instead of adding a flat bias, so a region only weighs more when it is genuinely overloaded).
  This departs from the assignment's literal example (`consumo + penalidade + prioridade`)
  because an always-nonnegative score makes the maximum-accumulated-interval search trivial.

### 3 Estruturas de dados

| Structure | Used for | Why |
|---|---|---|
| `list[dict]` (`carregar_leituras`) | ordered readings, indexable by position | O(1) access by index / O(k) slicing — what both search algorithms use to select a continuous interval |
| `set[str]` (`regioes_existentes`) | distinct region names | O(1) membership test vs. O(n) scan |
| `dict[str, list[dict]]` (`agrupar_por_regiao`) | consumption by region | O(1) lookup by key vs. O(n) scan |
| `dict[int, list[dict]]` (`agrupar_por_horario`) | consumption by hour of day | O(1) lookup by key, independent of region |
| `dict[tuple[str, int], list[dict]]` (`agrupar_por_regiao_e_hora`) | consumption by region + hour | `tuple` as a hashable composite key — a `list` could not be used as a dict key |
| `heapq.nlargest` (`maiores_picos_de_consumo`) | top-k consumption peaks | O(n log k) instead of sorting everything (O(n log n)) |

### 4 Algoritmos

- **Brute force** (`src/brute_force.py`): two nested loops explicitly test every `(start, end)`
  pair — no shortcut, no library max-subarray function.
- **Divide and conquer** (`src/divide_conquer.py`): the classic maximum-subarray recursion
  adapted to criticality — base case (single reading), split the range in half, solve the left
  half, solve the right half, solve the case that crosses the split
  (`_melhor_intervalo_cruzando_o_meio`: two linear scans outward from the midpoint), then combine
  (pick the best of the three candidates). `T(n) = 2T(n/2) + O(n) = O(n log n)` by the master
  theorem.
- Both call the same `calcular_criticidade` and always return the exact same interval (checked
  by `tests/test_questao2.py` and side by side in `notebooks/questao2.ipynb`).

### 5 Como executar

```bash
pip install -r requirements.txt

# regenerate the dataset (SEED = 1) -> data/problema2.csv
python src/gerar_dataset.py

# run either algorithm directly
python -m src.brute_force
python -m src.divide_conquer

# scalability experiment (n = 100..5000) -> data/escalabilidade.csv
python -m src.experimento_escalabilidade

# regenerate the three figures -> figures/questao2/*.png
python -m src.grafico_serie_temporal
python -m src.grafico_arvore_decomposicao
python -m src.grafico_escalabilidade

# tests
pytest tests/test_questao2.py -v

# full notebook, end to end
jupyter nbconvert --to notebook --execute notebooks/questao2.ipynb --output questao2.ipynb
```

### 6 Resultados

On the seed-1 dataset (1,200 readings), both algorithms find the exact same interval:

| | Interval (indices) | Period | Readings | Criticality |
|---|---:|---|---:|---:|
| Brute force | [571, 586] | 2025-06-05 18:00 to 21:00 | 16 | **1873.20** |
| Divide and conquer | [571, 586] | 2025-06-05 18:00 to 21:00 | 16 | **1873.20** |

This matches exactly the injected critical event (region Sul, capacity cut in half).
Scalability (`data/escalabilidade.csv`, each row one run at that `n`):

| n | Time — FB (s) | Time — DC (s) | Operations — FB | Operations — DC | Memory — FB (bytes) | Memory — DC (bytes) |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0.000246 | 0.000172 | 5,050 | 664 | 1,048 | 1,160 |
| 250 | 0.001352 | 0.000392 | 31,375 | 1,991 | 5,928 | 6,064 |
| 500 | 0.005839 | 0.000839 | 125,250 | 4,483 | 14,092 | 15,128 |
| 1,000 | 0.024137 | 0.001806 | 500,500 | 9,966 | 31,539 | 32,048 |
| 2,000 | 0.109495 | 0.003657 | 2,001,000 | 21,932 | 62,068 | 63,496 |
| 5,000 | 0.604972 | 0.009821 | 12,502,500 | 61,439 | 160,596 | 161,504 |

The most reliable comparison is `n = 1,000 -> 5,000` (5x): brute force gets **~25.1x** slower in
time and its operation count grows **~25.0x** (500,500 -> 12,502,500) — matching `5^2 = 25`,
i.e. `O(n^2)`. Divide-and-conquer gets only **~5.4x** slower in time and **~6.2x** in operation
count (9,966 -> 61,439) — close to the `O(n log n)` prediction of
`5 * log(5000)/log(1000) ~= 6.2x`, far below brute force's 25x. Memory grows **~5.0-5.1x** for
*both* algorithms (matching `n` growing 5x), confirming the `O(n)` `scores` array — not the
`O(log n)` recursion stack — dominates divide-and-conquer's memory too (Section 7). The wider
`n = 100 -> 5,000` span (50x) points the same direction (brute force ~2,459x slower, DC ~57x),
but with sub-millisecond timings at `n = 100` that ratio is noisier and is kept only as
supporting context, not as the number the `O(n^2)`/`O(n log n)` claim rests on. Figures and full
interpretation are in `figures/questao2/` and walked through in `notebooks/questao2.ipynb`.

### 7 Complexidade

Full derivation in `docs/analise_complexidade.md`. Summary:

- **Brute force**: `T(n) = O(n^2)` (two nested loops over every interval pair), `S(n) = O(n)`
  (the `scores` array).
- **Divide and conquer**: `T(n) = O(n log n)` (`T(n) = 2T(n/2) + O(n)`, master theorem),
  `S(n) = O(n)` (the `scores` array dominates the `O(log n)` recursion stack).
- Growing from 1,000 to 1,000,000 readings: brute force projects to **~24,000s** (~6.8h,
  infeasible); divide-and-conquer projects to **~3.4s** (still viable) — only divide-and-conquer
  scales.

### 8 Limitações

- **Synthetic dataset, single injected event**: real utility data would likely show several,
  possibly overlapping critical events across regions; this dataset injects only one, in one
  region, to keep the demonstration legible.
- **Criticality thresholds are our own choice, not regulatory**: `LIMIAR_SEGURO = 0.75` and
  `FATOR_PENALIDADE_EXCESSO = 2.0` (`src/criticidade.py`) were picked to make the search
  meaningful (avoid the degenerate "whole dataset" answer), not derived from a real grid
  operator's safety standard.
- **Region-interleaved sequence**: `carregar_leituras()` keeps the CSV's row order (five
  regions per hour, in timestamp order); a "continuous interval" is contiguous in that list, not
  on a single per-region time axis, so a found interval can span multiple regions within the
  same hour block rather than only consecutive hours of one region.
- **Memory measurement** (`tracemalloc`) only captures Python-level heap allocations, not
  C-level buffers.
- **Scalability experiment uses synthetic random readings**, not the real 1,200-row dataset,
  because `n` goes up to 5,000 (above the dataset's size); timing is representative, but the
  specific readings measured are not the real ones.

## Pergunta final (máximo 300 palavras)

_Qual foi a decisão algorítmica mais importante tomada pelo grupo? Apresente uma alternativa que
vocês descartaram e explique, considerando tempo, memória e qualidade da solução, por que a
abordagem escolhida foi considerada mais adequada._

A decisão mais importante foi a forma da recorrência da DP da Questão 1: em vez da mochila 0/1
clássica (`dp[i][c] = max(dp[i-1][c], dp[i-1][c-w_i] + b_i)`, onde o predecessor de cada item é
sempre a linha `i-1`), permitimos que **qualquer** site anterior `j < i` na ordem canônica `pi`
seja o predecessor direto de `i` (`src/dynamic_programming.py`, Seção 4 do README).

A alternativa descartada — a mochila clássica — seria mais barata: `O(N*C)` em tempo, contra o
`O(N^2*C)` da versão escolhida (Seção 7), e poderia até ser reduzida a um vetor rolante `O(C)`
de memória. Descartamos porque ela é **incorreta** para o nosso `J(S)`: como o benefício
depende do comprimento da rota `L(S)`, que soma distâncias entre sites *efetivamente visitados*
em sequência, a transição "pular o site `i-1`" da mochila clássica perde a informação de qual
foi o último site realmente visitado — e é exatamente isso que a distância do próximo trecho
precisa. Isso não é hipotético: a solução ótima real atende só 7 dos 20 sites candidatos
(Seção 6), ou seja, a maioria das transições da rota "pula" vários sites da ordem `pi`, e a
mochila clássica computaria uma `L(S)` errada nesses casos.

Em tempo, a diferença é irrelevante na prática (a DP inteira mede ~5ms para N=20, Seção 7); em
memória, ambas as versões precisam guardar a tabela completa para permitir a reconstrução
(Parte C), então não há perda real de memória ao escolher a recorrência mais cara. A única
dimensão em que a alternativa descartada realmente vencia — tempo assintótico — não compensava
o custo em qualidade da solução: preferimos uma resposta comprovadamente ótima a uma resposta
rápida e errada. É também essa recorrência mais expressiva que produz o contraexemplo real do
grupo (Seção 6): Greedy erra por 2.798 em `J(S)` justamente porque, ao contrário da DP, não
enxerga essa dependência entre sites não-adjacentes na rota.

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

`SEED = 1`. Desenvolvido e testado com Python 3.12 (as sequências de números aleatórios só têm
reprodutibilidade garantida na mesma versão do Python).

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

_TODO_

### 2 Modelo adotado

_TODO_

### 3 Estruturas de dados

_TODO_

### 4 Algoritmos

_TODO_

### 5 Como executar

_TODO_

### 6 Resultados

_TODO_

### 7 Complexidade

_TODO_

### 8 Limitações

_TODO_

## Pergunta final (máximo 300 palavras)

_TODO: cole aqui o enunciado exato da pergunta final do enunciado
(`Checkpoint_4_turma_W_21SET26`)._

_TODO_

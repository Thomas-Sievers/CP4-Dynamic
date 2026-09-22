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

Uma rede elétrica simplificada registra leituras horárias de consumo de várias regiões
(`timestamp`, `regiao`, `consumo`, `capacidade_disponivel`, `prioridade`, `custo`). O objetivo é
encontrar o único intervalo de tempo **contínuo** com a maior **criticidade** acumulada — o pior
trecho de tempo pelo qual a rede passou — usando duas estratégias diferentes (força bruta e
divisão e conquista) e comparando-as.

### 2 Modelo adotado

- **Dataset** (`src/gerar_dataset.py`): 1.200 leituras horárias sintéticas (10 dias x 5
  regiões), documentado e reprodutível com `SEED = 1`.
- **Evento crítico injetado**: a região Sul tem sua capacidade disponível reduzida pela metade
  durante uma janela contínua de 30 horas (simulando uma interrupção/manutenção), enquanto a
  capacidade de cada região é, do contrário, dimensionada em 2x seu consumo base, de modo que os
  picos diários comuns fiquem com folga segura abaixo dela. Sem um evento deliberado como esse,
  os picos diários se repetem de forma homogênea demais ao longo dos 10 dias e o "intervalo mais
  crítico" degenera para quase o dataset inteiro (ver Limitações).
- **Função de criticidade** (`src/criticidade.py`):
  `criticidade = consumo_relativo + penalidade_por_excesso`, onde
  `consumo_relativo = consumo - capacidade_disponivel * 0.75` (negativo enquanto uma leitura
  fica abaixo de 75% de *sua própria* capacidade, o que normaliza a pontuação entre regiões de
  escalas bem diferentes) e `penalidade_por_excesso = max(0, consumo - capacidade_disponivel) *
  2.0 * prioridade` (só diferente de zero quando a capacidade é de fato excedida; a prioridade
  multiplica o excesso em vez de somar um viés fixo, então uma região só pesa mais quando está
  genuinamente sobrecarregada). Isso se afasta do exemplo literal do enunciado
  (`consumo + penalidade + prioridade`) porque uma pontuação sempre não-negativa torna trivial a
  busca do intervalo de máxima criticidade acumulada.

### 3 Estruturas de dados

| Estrutura | Usada para | Por quê |
|---|---|---|
| `list[dict]` (`carregar_leituras`) | leituras ordenadas, indexáveis por posição | acesso O(1) por índice / fatiamento O(k) — o que os dois algoritmos de busca usam para selecionar um intervalo contínuo |
| `set[str]` (`regioes_existentes`) | nomes de regiões distintos | teste de pertencimento O(1) vs. varredura O(n) |
| `dict[str, list[dict]]` (`agrupar_por_regiao`) | consumo por região | busca por chave O(1) vs. varredura O(n) |
| `dict[int, list[dict]]` (`agrupar_por_horario`) | consumo por hora do dia | busca por chave O(1), independente da região |
| `dict[tuple[str, int], list[dict]]` (`agrupar_por_regiao_e_hora`) | consumo por região + hora | `tuple` como chave composta hasheável — uma `list` não poderia ser usada como chave de dict |
| `heapq.nlargest` (`maiores_picos_de_consumo`) | os k maiores picos de consumo | O(n log k) em vez de ordenar tudo (O(n log n)) |

### 4 Algoritmos

- **Força bruta** (`src/brute_force.py`): dois loops aninhados testam explicitamente todo par
  `(início, fim)` — sem atalho, sem função pronta de max-subarray.
- **Divisão e conquista** (`src/divide_conquer.py`): a recursão clássica de max-subarray
  adaptada para criticidade — caso base (uma única leitura), divide o intervalo ao meio, resolve
  a metade esquerda, resolve a metade direita, resolve o caso que cruza o meio
  (`_melhor_intervalo_cruzando_o_meio`: dois percursos lineares partindo do meio para fora),
  depois combina (escolhe o melhor entre os três candidatos). `T(n) = 2T(n/2) + O(n) = O(n log
  n)` pelo teorema mestre.
- Os dois chamam a mesma `calcular_criticidade` e sempre retornam exatamente o mesmo intervalo
  (verificado por `tests/test_questao2.py` e lado a lado em `notebooks/questao2.ipynb`).

### 5 Como executar

```bash
pip install -r requirements.txt

# regenera o dataset (SEED = 1) -> data/problema2.csv
python src/gerar_dataset.py

# roda qualquer um dos algoritmos diretamente
python -m src.brute_force
python -m src.divide_conquer

# experimento de escalabilidade (n = 100..5000) -> data/escalabilidade.csv
python -m src.experimento_escalabilidade

# regenera as três figuras -> figures/questao2/*.png
python -m src.grafico_serie_temporal
python -m src.grafico_arvore_decomposicao
python -m src.grafico_escalabilidade

# testes
pytest tests/test_questao2.py -v

# notebook completo, do início ao fim
jupyter nbconvert --to notebook --execute notebooks/questao2.ipynb --output questao2.ipynb
```

### 6 Resultados

No dataset seed-1 (1.200 leituras), os dois algoritmos encontram exatamente o mesmo intervalo:

| | Intervalo (índices) | Período | Leituras | Criticidade |
|---|---:|---|---:|---:|
| Força bruta | [571, 586] | 2025-06-05 18:00 às 21:00 | 16 | **1873,20** |
| Divisão e conquista | [571, 586] | 2025-06-05 18:00 às 21:00 | 16 | **1873,20** |

Isso corresponde exatamente ao evento crítico injetado (região Sul, capacidade reduzida pela
metade). Escalabilidade (`data/escalabilidade.csv`, cada linha uma execução naquele `n`):

| n | Tempo — FB (s) | Tempo — DC (s) | Operações — FB | Operações — DC | Memória — FB (bytes) | Memória — DC (bytes) |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0,000246 | 0,000172 | 5.050 | 664 | 1.048 | 1.160 |
| 250 | 0,001352 | 0,000392 | 31.375 | 1.991 | 5.928 | 6.064 |
| 500 | 0,005839 | 0,000839 | 125.250 | 4.483 | 14.092 | 15.128 |
| 1.000 | 0,024137 | 0,001806 | 500.500 | 9.966 | 31.539 | 32.048 |
| 2.000 | 0,109495 | 0,003657 | 2.001.000 | 21.932 | 62.068 | 63.496 |
| 5.000 | 0,604972 | 0,009821 | 12.502.500 | 61.439 | 160.596 | 161.504 |

A comparação mais confiável é `n = 1.000 -> 5.000` (5x): a força bruta fica **~25,1x** mais
lenta em tempo e sua contagem de operações cresce **~25,0x** (500.500 -> 12.502.500) — batendo
com `5^2 = 25`, ou seja, `O(n^2)`. A divisão e conquista fica apenas **~5,4x** mais lenta em
tempo e **~6,2x** em contagem de operações (9.966 -> 61.439) — perto da previsão `O(n log n)` de
`5 * log(5000)/log(1000) ~= 6,2x`, bem abaixo dos 25x da força bruta. A memória cresce
**~5,0-5,1x** para *ambos* os algoritmos (acompanhando o crescimento de 5x em `n`), confirmando
que o array `scores`, O(n) — e não a pilha de recursão O(log n) — também domina a memória da
divisão e conquista (Seção 7). O intervalo mais amplo `n = 100 -> 5.000` (50x) aponta na mesma
direção (força bruta ~2.459x mais lenta, DC ~57x), mas com tempos sub-milissegundo em `n = 100`
essa razão é mais ruidosa e é mantida só como contexto de apoio, não como o número em que a
afirmação `O(n^2)`/`O(n log n)` se baseia. Figuras e interpretação completa estão em
`figures/questao2/` e são percorridas em `notebooks/questao2.ipynb`.

### 7 Complexidade

Derivação completa em `docs/analise_complexidade.md`. Resumo:

- **Força bruta**: `T(n) = O(n^2)` (dois loops aninhados sobre todo par de intervalo),
  `S(n) = O(n)` (o array `scores`).
- **Divisão e conquista**: `T(n) = O(n log n)` (`T(n) = 2T(n/2) + O(n)`, teorema mestre),
  `S(n) = O(n)` (o array `scores` domina a pilha de recursão `O(log n)`).
- Crescendo de 1.000 para 1.000.000 de leituras: a força bruta projeta **~24.000s** (~6,8h,
  inviável); a divisão e conquista projeta **~3,4s** (ainda viável) — só a divisão e conquista
  escala.

### 8 Limitações

- **Dataset sintético, evento único injetado**: dados reais de uma concessionária provavelmente
  mostrariam vários eventos críticos, possivelmente sobrepostos entre regiões; este dataset
  injeta apenas um, em uma região, para manter a demonstração legível.
- **Limiares de criticidade são escolha nossa, não regulatória**: `LIMIAR_SEGURO = 0.75` e
  `FATOR_PENALIDADE_EXCESSO = 2.0` (`src/criticidade.py`) foram escolhidos para tornar a busca
  significativa (evitar a resposta degenerada de "o dataset inteiro"), não derivados do padrão
  de segurança real de uma operadora de rede.
- **Sequência intercalada por região**: `carregar_leituras()` mantém a ordem das linhas do CSV
  (cinco regiões por hora, em ordem de timestamp); um "intervalo contínuo" é contíguo nessa
  lista, não em um único eixo de tempo por região, então um intervalo encontrado pode abranger
  várias regiões dentro do mesmo bloco de hora, em vez de apenas horas consecutivas de uma única
  região.
- **Medição de memória** (`tracemalloc`) captura apenas alocações no heap em nível Python, não
  buffers em nível C.
- **O experimento de escalabilidade usa leituras aleatórias sintéticas**, não o dataset real de
  1.200 linhas, porque `n` chega a 5.000 (acima do tamanho do dataset); o tempo medido é
  representativo, mas as leituras específicas medidas não são as reais.

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

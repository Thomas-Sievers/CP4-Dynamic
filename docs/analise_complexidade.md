# Complexity Analysis

## Question 1

_TODO_

## Questão 2 — Gestão de consumo de energia

Os dois algoritmos (`src/brute_force.py` e `src/divide_conquer.py`) resolvem o
mesmo problema: achar o intervalo contínuo de leituras com maior criticidade
acumulada. `n` é o número de leituras (linhas do dataset).

### Força bruta (`src/brute_force.py`)

**T(n):**

- Antes dos loops, um `for` calcula a criticidade de cada leitura uma vez
  (`scores = [calcular_criticidade(l) for l in leituras]`) — O(n).
- Dois loops aninhados testam todo par `(inicio, fim)` possível: o de fora
  (`inicio`) roda n vezes, e pra cada `inicio` o de dentro (`fim`) roda de
  `inicio` até o fim da lista. O número total de pares é
  n + (n-1) + (n-2) + ... + 1 = n(n+1)/2.
- Dentro do loop de dentro, cada iteração só soma um valor e compara — custo
  constante por par.
- **T(n) = O(n) + O(n²) = O(n²)** — o termo quadrático domina.

**S(n):**

- `scores`: lista auxiliar de tamanho n — O(n).
- `melhor_inicio`, `melhor_fim`, `melhor_criticidade`, `soma_do_intervalo`:
  variáveis escalares, não crescem com n — O(1).
- **S(n) = O(n)**, só por causa da lista `scores`.

### Divide-and-conquer (`src/divide_conquer.py`)

**T(n):**

- Recorrência: **T(n) = 2·T(n/2) + O(n)**.
  - `2·T(n/2)`: a função `_buscar` chama a si mesma duas vezes, uma pra cada
    metade do intervalo (`esquerda..meio` e `meio+1..direita`).
  - `O(n)`: vem de `_melhor_intervalo_cruzando_o_meio`, que faz dois loops
    lineares — um andando do meio pra trás até `esquerda`, outro do
    `meio+1` pra frente até `direita`. Juntos, os dois loops nunca passam de
    n elementos no total nesse nível da recursão.
- Pelo teorema mestre (a=2, b=2, f(n)=O(n), log_b(a) = log_2(2) = 1, que é a
  mesma ordem de f(n) → caso 2): **T(n) = O(n log n)**.
- Profundidade da recursão: cada chamada divide o intervalo ao meio, então a
  árvore de chamadas tem profundidade log₂(n) — é quantas vezes dá pra
  dividir n por 2 até sobrar 1 elemento (o caso base). É por isso que a
  Figura 2 (árvore de decomposição, 16 leituras) tem 5 níveis: log₂(16) = 4
  divisões + o nível do caso base.

**S(n):**

- `scores`: calculado uma vez em `buscar_intervalo_critico_divide_conquer` —
  O(n).
- Pilha de recursão: cada chamada ativa de `_buscar` guarda só um punhado de
  variáveis locais (`esquerda`, `direita`, `meio`, os resultados dos dois
  filhos) — O(1) por chamada. Como a profundidade da recursão é O(log n), a
  pilha usa O(log n) no total.
- **S(n) = O(n) + O(log n) = O(n)**, dominado pelo array `scores` (o mesmo
  motivo do lado da força bruta).

### Força bruta vs divide-and-conquer: de 1.000 para 1.000.000 de registros

Os números abaixo vêm do experimento de escalabilidade
(`data/escalabilidade.csv` / `src/experimento_escalabilidade.py`), medido até
n = 5.000, e projetados pra n = 1.000.000 usando a ordem de crescimento de
cada algoritmo.

- **Força bruta é O(n²)**: multiplicar n por 1.000 (de 1.000 para 1.000.000)
  multiplica o tempo por 1.000² = 1.000.000. Com o tempo medido em n=1.000
  (≈0,024s), a projeção pra n=1.000.000 é ≈0,024 × 1.000.000 ≈ 24.000s (mais
  de 6 horas) — **inviável**.
- **Divide-and-conquer é O(n log n)**: multiplicar n por 1.000 multiplica o
  tempo por aproximadamente (1.000.000 × log₂(1.000.000)) / (1.000 ×
  log₂(1.000)) ≈ (1.000.000 × 19,9) / (1.000 × 10) ≈ 1.999. Com o tempo
  medido em n=1.000 (≈0,0017s), a projeção pra n=1.000.000 é ≈0,0017 × 1.999
  ≈ 3,4s — **continua viável**.

**Resposta:** o divide-and-conquer continua viável porque seu tempo cresce
proporcional a n log n, e log n cresce extremamente devagar — log₂ de um
milhão é só ≈20. Na prática, quem domina o crescimento é o próprio n, quase
como se fosse linear. Já a força bruta cresce com o quadrado de n: multiplicar
a entrada por 1.000 multiplica o tempo por um milhão, o que transforma um
algoritmo que roda em milissegundos com poucas leituras em um algoritmo que
levaria horas com um dataset grande. Pra um sistema real de gestão de energia,
que só tende a acumular mais leituras com o tempo, só o divide-and-conquer se
sustenta.

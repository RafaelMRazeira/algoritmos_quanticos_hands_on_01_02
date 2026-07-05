# Hands-on UA01/UA02 — Algoritmo de Grover em problemas computacionais

Reprodução completa dos experimentos do relatório técnico: implementação do
algoritmo de Grover (oráculo e operador de difusão construídos manualmente,
porta a porta) nos 4 cenários do roteiro, com análise de ruído, número de
*shots* e comparação com busca clássica.

## Estrutura

| Arquivo | Descrição |
|---|---|
| `grover_lab.py` | Módulo principal: oráculo, difusão, cálculo de r, circuito completo, execução e busca clássica linear |
| `noise_lab.py` | Modelo de ruído depolarizante e experimentos de *shots* |
| `run_experiments.py` | Orquestra os 4 cenários, gera histogramas/circuitos e consolida métricas em `artefatos/dados.json` |
| `requirements.txt` | Versões pinadas (Qiskit 2.5.0, Qiskit Aer 0.17.2, matplotlib 3.10.8) |
| `Dockerfile` | Imagem Python 3.12-slim com dependências instaladas via [uv](https://docs.astral.sh/uv/) |

## Pré-requisito

- Docker instalado (Docker Desktop ou Docker Engine).

## 1. Construir a imagem

```bash
docker build -t grover-handson .
```

## 2. Executar com os mesmos recursos do relatório (1 CPU, 4 GB de RAM)

Os resultados de tempo do relatório (Cenários 2 e 3, ponto de virada) foram
medidos em **1 vCPU e 4 GB de RAM**. Para forçar exatamente esses limites:

```bash
docker run --rm \
  --cpus="1.0" \
  --memory="4g" \
  --memory-swap="4g" \
  -v "$(pwd)/artefatos:/app/artefatos" \
  grover-handson
```

No Windows (PowerShell), troque `$(pwd)` por `${PWD}`:

```powershell
docker run --rm --cpus="1.0" --memory="4g" --memory-swap="4g" -v "${PWD}/artefatos:/app/artefatos" grover-handson
```

O que cada flag faz:

- `--cpus="1.0"` — limita o contêiner a **1 CPU** (via CFS quota do kernel);
- `--memory="4g"` — teto rígido de **4 GB de RAM**;
- `--memory-swap="4g"` — igual ao teto de RAM, ou seja, **swap desabilitado**
  (sem isso o contêiner poderia "escapar" do limite usando swap e os tempos
  medidos não seriam comparáveis);
- `-v .../artefatos:/app/artefatos` — monta a pasta local `artefatos/` para
  receber as saídas do experimento.

O `Dockerfile` também exporta `OMP_NUM_THREADS=1` (e equivalentes), de modo
que o Qiskit Aer não tente paralelizar internamente — coerente com 1 vCPU.

## 3. Saídas geradas (em `./artefatos`)

| Arquivo | Conteúdo |
|---|---|
| `dados.json` | Todas as métricas consolidadas (r, tempos, taxas de sucesso, contagens) |
| `c1_circ.png` / `c1_hist.png` | Cenário 1 — circuito completo e histograma (2 qubits) |
| `c2_circ.png` / `c2_hist.png` / `c2_hist_ruido.png` | Cenário 2 — 16 qubits, ideal e com ruído |
| `c3_escala.png` | Cenário 3 — tempo de simulação × número de qubits (escala log) |
| `c4_circ.png` / `c4_circ_detalhe.png` / `c4_hist.png` / `c4_hist_ruido.png` | Cenário 4 — múltiplos alvos |

## Tempo de execução esperado

Com os limites de 1 CPU / 4 GB, a execução completa leva **~10 a 15 minutos**.
As etapas mais longas são o Cenário 3 com 20 qubits (~110 s) e a simulação
com ruído do Cenário 2 com 100 *shots* (~270 s — cada *shot* exige uma
trajetória completa do circuito de 201 iterações).

> **Nota:** o Cenário 3 do roteiro pede o maior número de qubits viável no
> ambiente. Com 1 CPU/4 GB o limite prático é **20 qubits**; a tentativa com
> 22 qubits é registrada como abortada (tempo projetado de 15–20 min). Se
> quiser testar em uma máquina maior, basta aumentar `--cpus`/`--memory` e
> editar a lista de qubits em `run_experiments.py`.

## Reprodutibilidade

Todas as execuções usam semente fixa (`seed = 42`) no simulador; os
histogramas e as taxas de sucesso do relatório são reproduzidos exatamente.
Os tempos de parede variam com o hardware do host, mas a **ordem de
grandeza** e as conclusões (escala ~9× a cada 2 qubits, ruído destruindo a
amplificação, ausência de vantagem de tempo em simulação) se mantêm.

## Executar sem Docker (opcional, com uv)

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python run_experiments.py
```

Sem uv, o equivalente tradicional funciona igualmente:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_experiments.py
```

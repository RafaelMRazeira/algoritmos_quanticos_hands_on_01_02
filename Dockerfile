# ============================================================
# Hands-on UA01/UA02 — Algoritmo de Grover
# Imagem para reproduzir os experimentos do relatório (com uv)
# ============================================================
FROM python:3.12-slim

# uv: instalador/resolvedor de pacotes (https://docs.astral.sh/uv/)
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/

# Evita .pyc e garante logs sem buffer (progresso visível em tempo real)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Dependências pinadas nas mesmas versões usadas no relatório
# (--no-cache: imagem menor; camada separada para aproveitar o cache do build)
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt

# Códigos do experimento
COPY grover_lab.py noise_lab.py run_experiments.py ./

# Diretório de saída (histogramas, circuitos, dados.json)
RUN mkdir -p /app/artefatos

# Threads limitadas a 1 também no nível das bibliotecas numéricas,
# para casar com o cenário de 1 vCPU do relatório
ENV OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    QISKIT_NUM_PROCS=1

CMD ["python", "run_experiments.py"]

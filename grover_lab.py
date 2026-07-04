# -*- coding: utf-8 -*-
"""
Hands-on UA01/UA02 - Algoritmo de Grover em problemas computacionais
Implementacao do algoritmo de Grover com oraculo e operador de difusao
construidos manualmente a partir de portas elementares (sem funcoes prontas).

Bibliotecas: Qiskit 2.x + Qiskit Aer.
"""

import math
import time

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


# ----------------------------------------------------------------------
# 1. Oraculo (marcacao de fase dos estados-alvo)
# ----------------------------------------------------------------------
def build_oracle(n_qubits: int, targets: list[int]) -> QuantumCircuit:
    """Oraculo de fase: aplica |x> -> -|x> para cada x em `targets`.

    Construcao manual, porta a porta:
      - portas X levam o estado-alvo ao estado |11...1>;
      - um Z multicontrolado (H + MCX + H no ultimo qubit) inverte a fase;
      - as portas X sao desfeitas (reversibilidade da operacao unitaria).
    """
    oracle = QuantumCircuit(n_qubits, name="Oraculo")
    for target in targets:
        bits = format(target, f"0{n_qubits}b")[::-1]  # bit 0 = qubit 0
        zeros = [q for q in range(n_qubits) if bits[q] == "0"]
        # mapeia |alvo> -> |11...1>
        for q in zeros:
            oracle.x(q)
        # Z multicontrolado sobre |11...1> (inversao de fase)
        oracle.h(n_qubits - 1)
        oracle.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        oracle.h(n_qubits - 1)
        # desfaz o mapeamento (garante unitariedade/reversibilidade)
        for q in zeros:
            oracle.x(q)
    return oracle


# ----------------------------------------------------------------------
# 2. Operador de difusao (amplificacao de amplitude)
# ----------------------------------------------------------------------
def build_diffusion(n_qubits: int) -> QuantumCircuit:
    """Operador de difusao D = 2|s><s| - I, construido manualmente.

    Reflexao em torno da media das amplitudes:
    H^n . X^n . (Z multicontrolado) . X^n . H^n
    """
    diff = QuantumCircuit(n_qubits, name="Difusao")
    diff.h(range(n_qubits))
    diff.x(range(n_qubits))
    diff.h(n_qubits - 1)
    diff.mcx(list(range(n_qubits - 1)), n_qubits - 1)
    diff.h(n_qubits - 1)
    diff.x(range(n_qubits))
    diff.h(range(n_qubits))
    return diff


# ----------------------------------------------------------------------
# 3. Numero ideal de iteracoes:  r = floor( (pi/4) * sqrt(N/k) )
# ----------------------------------------------------------------------
def optimal_iterations(n_qubits: int, k_targets: int) -> int:
    N = 2 ** n_qubits
    return max(1, math.floor((math.pi / 4) * math.sqrt(N / k_targets)))


# ----------------------------------------------------------------------
# 4. Montagem do circuito completo de Grover
# ----------------------------------------------------------------------
def build_grover_circuit(n_qubits: int, targets: list[int],
                         iterations: int | None = None) -> tuple[QuantumCircuit, int]:
    if iterations is None:
        iterations = optimal_iterations(n_qubits, len(targets))
    oracle = build_oracle(n_qubits, targets)
    diffusion = build_diffusion(n_qubits)

    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(range(n_qubits))              # superposicao uniforme |s>
    for _ in range(iterations):        # r aplicacoes do operador de Grover
        qc.compose(oracle, inplace=True)
        qc.compose(diffusion, inplace=True)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc, iterations


# ----------------------------------------------------------------------
# 5. Execucao no simulador (com ou sem ruido)
# ----------------------------------------------------------------------
def run_grover(n_qubits: int, targets: list[int], shots: int = 1024,
               noise_model=None, seed: int = 42):
    """Executa Grover e retorna dicionario com contagens e metricas."""
    qc, r = build_grover_circuit(n_qubits, targets)
    backend = AerSimulator(noise_model=noise_model, seed_simulator=seed)
    tqc = transpile(qc, backend)       # mantem mcx nativo do Aer (ideal);
                                       # com ruido, decompoe nas portas basicas
    t0 = time.perf_counter()
    result = backend.run(tqc, shots=shots).result()
    elapsed = time.perf_counter() - t0

    counts = result.get_counts()
    target_strs = {format(t, f"0{n_qubits}b") for t in targets}
    hits = sum(v for k2, v in counts.items() if k2 in target_strs)
    return {
        "circuit": qc, "iterations": r, "counts": counts,
        "time_s": elapsed, "shots": shots,
        "success_rate": hits / shots,
        "n_qubits": n_qubits, "targets": targets,
    }


# ----------------------------------------------------------------------
# 6. Busca classica linear (baseline de comparacao)
# ----------------------------------------------------------------------
def classical_linear_search(n_qubits: int, target: int):
    """Percorre todos os estados de 0 ate 2^n - 1 ate encontrar o alvo."""
    N = 2 ** n_qubits
    t0 = time.perf_counter()
    found, queries = -1, 0
    for x in range(N):
        queries += 1
        if x == target:                # "consulta" ao oraculo classico
            found = x
            break
    elapsed = time.perf_counter() - t0
    return {"found": found, "queries": queries, "time_s": elapsed, "N": N}

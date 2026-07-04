# -*- coding: utf-8 -*-
"""
Experimentos de ruido e de numero de shots (Passo 3 do roteiro).
"""

import time

from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from grover_lab import build_grover_circuit


def make_noise_model(p1: float = 0.001, p2: float = 0.01) -> NoiseModel:
    """Modelo de ruido depolarizante simples:
       p1 -> erro em portas de 1 qubit; p2 -> erro em portas de 2 qubits (cx).
    """
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["h", "x", "u"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cx"])
    return nm


def run_with_noise(n_qubits, targets, shots, noise_model=None, seed=42,
                   keep_mcx=False):
    """Executa Grover com/sem ruido.

    keep_mcx=True mantem a porta mcx nativa do simulador (necessario para
    circuitos grandes, ja que decompor um MCX de 15 controles em portas
    basicas torna a simulacao com trajetorias de ruido inviavel).
    """
    qc, r = build_grover_circuit(n_qubits, targets)
    backend = AerSimulator(noise_model=noise_model, seed_simulator=seed)
    if keep_mcx:
        tqc = qc  # sem transpilacao: o Aer executa a mcx nativamente
    else:
        tqc = transpile(qc, backend)  # decompoe em portas basicas com ruido

    t0 = time.perf_counter()
    result = backend.run(
        tqc, shots=shots,
        shot_branching_enable=True,          # acelera trajetorias com ruido
        shot_branching_sampling_enable=True,
    ).result()
    elapsed = time.perf_counter() - t0

    counts = result.get_counts()
    target_strs = {format(t, f"0{n_qubits}b") for t in targets}
    hits = sum(v for k, v in counts.items() if k in target_strs)
    return {"counts": counts, "success_rate": hits / shots,
            "time_s": elapsed, "iterations": r, "shots": shots}

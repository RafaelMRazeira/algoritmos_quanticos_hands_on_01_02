# -*- coding: utf-8 -*-
"""Executa todos os experimentos do hands-on e salva artefatos."""
import json, math, time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qiskit import transpile
from qiskit_aer import AerSimulator
from grover_lab import (build_oracle, build_diffusion, build_grover_circuit,
                        optimal_iterations, run_grover, classical_linear_search)
from noise_lab import make_noise_model, run_with_noise

ART = "artefatos"
DATA = {}

def save_hist(counts, path, title, targets=None, n=None, max_bars=16):
    items = sorted(counts.items(), key=lambda x: -x[1])[:max_bars]
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    tstr = {format(t, f"0{n}b") for t in (targets or [])} if n else set()
    colors = ["#1a6feb" if l in tstr else "#9aa7b8" for l in labels]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.bar(range(len(vals)), vals, color=colors)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, rotation=60, fontsize=7, ha="right")
    ax.set_ylabel("contagens")
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)

# ---------------- Cenario 1: 2 qubits, 1 alvo ----------------
print("== Cenario 1 ==")
c1 = run_grover(2, [3], shots=1024)
save_hist(c1["counts"], f"{ART}/c1_hist.png",
          "Cenário 1 — 2 qubits, alvo |11⟩ (1024 shots, ideal)", [3], 2)
c1["circuit"].draw("mpl", style="clifford").savefig(f"{ART}/c1_circ.png", dpi=140, bbox_inches="tight")
DATA["c1"] = {"n": 2, "targets": [3], "r": c1["iterations"], "shots": 1024,
              "success": c1["success_rate"], "time_s": c1["time_s"],
              "counts": c1["counts"]}

# ---------------- Cenario 2: 16 qubits, 1 alvo + busca classica ----------------
print("== Cenario 2 ==")
c2 = run_grover(16, [2**16 - 1], shots=1024)
save_hist(c2["counts"], f"{ART}/c2_hist.png",
          "Cenário 2 — 16 qubits, alvo |111…1⟩ (1024 shots, ideal)", [2**16-1], 16, max_bars=10)
cl2 = classical_linear_search(16, 2**16 - 1)
DATA["c2"] = {"n": 16, "targets": [2**16-1], "r": c2["iterations"], "shots": 1024,
              "success": c2["success_rate"], "time_q_s": c2["time_s"],
              "classical": cl2}

# circuito esquematico do cenario 2 (oraculo/difusao como blocos)
from qiskit import QuantumCircuit
orc = build_oracle(16, [2**16-1]).to_gate(label="Oráculo")
dif = build_diffusion(16).to_gate(label="Difusão")
qs = QuantumCircuit(16, 16)
qs.h(range(16))
qs.append(orc, range(16)); qs.append(dif, range(16))
qs.barrier(label="× r = 201")
qs.measure(range(16), range(16))
qs.draw("mpl", fold=-1).savefig(f"{ART}/c2_circ.png", dpi=120, bbox_inches="tight")

# ---------------- Cenario 3: escala maxima ----------------
print("== Cenario 3 ==")
DATA["c3"] = {"runs": [
    {"n": 16, "r": 201, "time_s": round(c2["time_s"], 2), "success": c2["success_rate"], "status": "ok"},
]}
for n in [18, 20]:
    r3 = run_grover(n, [2**n - 1], shots=256)
    DATA["c3"]["runs"].append({"n": n, "r": r3["iterations"],
                               "time_s": round(r3["time_s"], 2),
                               "success": r3["success_rate"], "status": "ok"})
    print(f"n={n}: {r3['time_s']:.1f}s")
DATA["c3"]["runs"].append({"n": 22, "r": optimal_iterations(22, 1),
                           "time_s": None, "success": None,
                           "status": "abortado (>280 s sem concluir)"})

# grafico de escalabilidade
runs_ok = [r for r in DATA["c3"]["runs"] if r["status"] == "ok"]
fig, ax = plt.subplots(figsize=(6, 3.2))
ax.semilogy([r["n"] for r in runs_ok], [r["time_s"] for r in runs_ok], "o-", color="#1a6feb")
ax.set_xlabel("número de qubits (n)"); ax.set_ylabel("tempo de simulação (s, escala log)")
ax.set_title("Cenário 3 — crescimento do tempo de simulação", fontsize=10)
ax.grid(True, alpha=.3)
fig.tight_layout(); fig.savefig(f"{ART}/c3_escala.png", dpi=140); plt.close(fig)

# ---------------- Cenario 4: 5 qubits, alvos 3, 7 e 11 ----------------
print("== Cenario 4 ==")
c4 = run_grover(5, [3, 7, 11], shots=1024)
save_hist(c4["counts"], f"{ART}/c4_hist.png",
          "Cenário 4 — 5 qubits, alvos |00011⟩,|00111⟩,|01011⟩ (1024 shots, ideal)",
          [3, 7, 11], 5, max_bars=16)
DATA["c4"] = {"n": 5, "targets": [3, 7, 11], "r": c4["iterations"], "shots": 1024,
              "success": c4["success_rate"], "time_s": c4["time_s"],
              "counts": c4["counts"]}

orc4 = build_oracle(5, [3, 7, 11]).to_gate(label="Oráculo (3 alvos)")
dif4 = build_diffusion(5).to_gate(label="Difusão")
q4 = QuantumCircuit(5, 5)
q4.h(range(5))
for _ in range(2):
    q4.append(orc4, range(5)); q4.append(dif4, range(5))
q4.measure(range(5), range(5))
q4.draw("mpl").savefig(f"{ART}/c4_circ.png", dpi=140, bbox_inches="tight")
# circuito detalhado de 1 iteracao (portas elementares)
det = QuantumCircuit(5)
det.compose(build_oracle(5, [3, 7, 11]), inplace=True)
det.barrier()
det.compose(build_diffusion(5), inplace=True)
det.draw("mpl", fold=28).savefig(f"{ART}/c4_circ_detalhe.png", dpi=130, bbox_inches="tight")

# profundidade transpilada (portas basicas) — relevante para o ruido
backend_n = AerSimulator(noise_model=make_noise_model())
t4 = transpile(build_grover_circuit(5, [3, 7, 11])[0], backend_n)
DATA["c4"]["depth_basis"] = t4.depth()
DATA["c4"]["ops_basis"] = {k: int(v) for k, v in t4.count_ops().items()}

# ---------------- Passo 3: ruido e shots ----------------
print("== Ruido / shots ==")
nm = make_noise_model()
shots_grid = [1, 100, 1024]
exp = {"c4": {"ideal": {}, "ruido": {}}, "c2": {"ideal": {}, "ruido": {}}}
for s in shots_grid:
    r = run_with_noise(5, [3, 7, 11], s, noise_model=None)
    exp["c4"]["ideal"][s] = {"success": r["success_rate"], "time_s": round(r["time_s"], 3)}
    r = run_with_noise(5, [3, 7, 11], s, noise_model=nm)
    exp["c4"]["ruido"][s] = {"success": r["success_rate"], "time_s": round(r["time_s"], 3)}
    if s == 1024:
        save_hist(r["counts"], f"{ART}/c4_hist_ruido.png",
                  "Cenário 4 com ruído depolarizante (1024 shots)", [3, 7, 11], 5)
for s in shots_grid:
    r = run_with_noise(16, [2**16-1], s, noise_model=None, keep_mcx=True)
    exp["c2"]["ideal"][s] = {"success": r["success_rate"], "time_s": round(r["time_s"], 3)}
for s in [1, 100]:
    r = run_with_noise(16, [2**16-1], s, noise_model=nm, keep_mcx=True)
    exp["c2"]["ruido"][s] = {"success": r["success_rate"], "time_s": round(r["time_s"], 3)}
    if s == 100:
        save_hist(r["counts"], f"{ART}/c2_hist_ruido.png",
                  "Cenário 2 com ruído (100 shots) — alvo não amplificado", [2**16-1], 16, max_bars=12)
exp["c2"]["ruido"][1024] = {"success": None, "time_s": None,
                            "obs": "inviável (~45 min projetados no ambiente)"}
DATA["exp_shots"] = exp

# ---------------- Custo por consulta e ponto de virada ----------------
print("== Custos ==")
t_iter_sim = c2["time_s"] / c2["iterations"]              # tempo/iteração (n=16, simulação)
t_check = cl2["time_s"] / cl2["queries"]                   # tempo/consulta clássica
DATA["custos"] = {
    "t_iter_sim_n16_s": t_iter_sim,
    "t_check_classico_s": t_check,
    "razao": t_iter_sim / t_check,
}

with open(f"{ART}/dados.json", "w") as f:
    json.dump(DATA, f, indent=2, default=str)
print("OK — artefatos salvos")

"""
Простейший модуль ввода-вывода: чтение config.json, сохранение policy.csv и results.txt.
"""

import json
import csv
import os
from typing import Dict, List, Tuple
from dp_core import State

def load_config(path: str) -> Dict:
    """Читает и возвращает JSON-конфиг."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_policy(policy: Dict[Tuple[int,State], Tuple[float,float,float]], V: List[dict], outdir: str):
    """Сохраняет policy.csv и results.txt в outdir."""
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, "policy.csv")
    fieldnames = ["t","x1","x2","d","cash","dx1","dx2","dd","V"]
    rows = []
    for (t,s), a in policy.items():
        v = V[t].get(s, None)
        rows.append({
            "t": t, "x1": s.x1, "x2": s.x2, "d": s.d, "cash": s.cash,
            "dx1": a[0], "dx2": a[1], "dd": a[2], "V": v
        })
    # сортировка для удобства (по t, затем V убыв.)
    rows_sorted = sorted(rows, key=lambda r: (r['t'], - (r['V'] if r['V'] is not None else -1e18)))
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_sorted)
    # краткий summary — V0 и стартовое действие
    results_path = os.path.join(outdir, "results.txt")
    # найти нач. состояние (t==0), он должен быть единственным
    init_states = [s for (t,s) in policy.keys() if t==0]
    with open(results_path, 'w', encoding='utf-8') as f:
        if init_states:
            init_state = init_states[0]
            v0 = V[0].get(init_state, None)
            f.write(f"V0 = {v0}\n")
            f.write(f"Best initial action = {policy[(0,init_state)]}\n")
        else:
            f.write("No initial state in policy.\n")
    return csv_path, results_path

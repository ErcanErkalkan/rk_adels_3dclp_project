from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import time
import pandas as pd

from .instance import Instance
from .de import (
    run_decoder_only,
    run_rk_de,
    run_rk_ade,
    run_random_search,
    run_ga,
    run_sa,
    run_pso,
)

@dataclass
class RunConfig:
    seconds: float = 30.0
    NP: int = 50
    seed: int = 123
    trials: int = 10

def run_variant(inst: Instance, variant: str, seconds: float, NP: int, seed: int) -> Dict[str, Any]:
    t0 = time.time()
    if variant == "H0":
        res = run_decoder_only(inst, seconds=seconds, seed=seed)
    elif variant == "A1":
        res = run_rk_de(inst, seconds=seconds, seed=seed, NP=NP)
    elif variant == "A2":
        res = run_rk_ade(inst, seconds=seconds, seed=seed, NP=NP, use_local_search=False)
    elif variant == "A3":
        res = run_rk_ade(inst, seconds=seconds, seed=seed, NP=NP, use_local_search=True)
    elif variant == "RS":
        res = run_random_search(inst, seconds=seconds, seed=seed)
    elif variant == "GA":
        res = run_ga(inst, seconds=seconds, seed=seed, NP=NP)
    elif variant == "SA":
        res = run_sa(inst, seconds=seconds, seed=seed)
    elif variant == "PSO":
        res = run_pso(inst, seconds=seconds, seed=seed, NP=NP)
    else:
        raise ValueError(f"Unknown variant: {variant}")
    t1 = time.time()
    e = res.best_eval
    return {
        "instance": inst.name,
        "variant": variant,
        "seed": seed,
        "seconds_budget": seconds,
        "seconds_used": res.seconds,
        "wallclock": t1 - t0,
        "NP": NP,
        "V_best": e.V,
        "f_best": e.f,
        "placed_best": e.placed,
        "H_max": e.H_max,
        "D_max": e.D_max,
        "n_evals": res.n_evals,
        "evals_per_sec": res.n_evals / max(res.seconds, 1e-9),
    }

def summarize_runs(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["instance","variant"], as_index=False)
    out = g.agg(
        V_mean=("V_best","mean"),
        V_std=("V_best","std"),
        V_best=("V_best","max"),
        placed_mean=("placed_best","mean"),
        placed_std=("placed_best","std"),
        time_mean=("wallclock","mean"),
        time_std=("wallclock","std"),
        evalsps_mean=("evals_per_sec","mean"),
    )
    return out

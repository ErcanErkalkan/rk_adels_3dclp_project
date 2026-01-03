from __future__ import annotations
from dataclasses import dataclass
import time
import random
import math
import numpy as np

from .instance import Instance
from .decoder import decode_wall_heightmap
from .local_search import perm_from_keys, rplan_from_okeys, local_search_step, reencode_from_perm_and_r

@dataclass
class EvalInfo:
    V: float
    f: float
    placed: int
    H_max: float
    D_max: float
    eval_time: float

def reflect01(x: np.ndarray) -> np.ndarray:
    y = x.copy()
    for _ in range(3):
        y = np.where(y < 0.0, -y, y)
        y = np.where(y > 1.0, 2.0 - y, y)
    return np.clip(y, 0.0, 1.0)

def evaluate(inst: Instance, x: np.ndarray, eps_P=1e-4, eps_H=1e-6, eps_D=1e-6) -> EvalInfo:
    n = len(inst.items)
    k = x[:n]
    o = x[n:]
    perm = list(np.argsort(k, kind="mergesort"))
    r_plan = (np.floor(6.0 * np.clip(o, 0.0, 1.0 - 1e-12))).astype(int) + 1
    r_plan = np.clip(r_plan, 1, 6).tolist()

    t0 = time.time()
    res = decode_wall_heightmap(inst, perm, r_plan, eps_P=eps_P, eps_H=eps_H, eps_D=eps_D)
    t1 = time.time()
    return EvalInfo(V=res.V, f=res.f, placed=res.placed_count, H_max=res.H_max, D_max=res.D_max, eval_time=t1-t0)

@dataclass
class DEResult:
    best_x: np.ndarray
    best_eval: EvalInfo
    n_evals: int
    seconds: float

def run_decoder_only(inst: Instance, seconds: float, seed: int) -> DEResult:
    rng = random.Random(seed)
    n = len(inst.items)

    volumes = [(i, inst.items[i].w*inst.items[i].h*inst.items[i].d) for i in range(n)]
    perm_vol = [i for i,_ in sorted(volumes, key=lambda t: -t[1])]

    def rand_rplan():
        return [rng.randrange(1,7) for _ in range(n)]

    start = time.time()
    best_x = None
    best_eval = None
    n_evals = 0

    x0 = reencode_from_perm_and_r(n, perm_vol, rand_rplan())
    e0 = evaluate(inst, x0)
    best_x, best_eval = x0, e0
    n_evals += 1

    while time.time() - start < seconds:
        perm = list(range(n))
        rng.shuffle(perm)
        x = reencode_from_perm_and_r(n, perm, rand_rplan())
        ev = evaluate(inst, x)
        n_evals += 1
        if ev.f > best_eval.f:
            best_x, best_eval = x, ev

    return DEResult(best_x=best_x, best_eval=best_eval, n_evals=n_evals, seconds=time.time()-start)

def run_rk_de(
    inst: Instance,
    seconds: float,
    seed: int,
    NP: int = 50,
    F: float = 0.5,
    CR: float = 0.9,
    eps_P=1e-4, eps_H=1e-6, eps_D=1e-6,
) -> DEResult:
    rng = np.random.default_rng(seed)
    n = len(inst.items)
    dim = 2*n

    X = rng.random((NP, dim))
    E = [evaluate(inst, X[i], eps_P, eps_H, eps_D) for i in range(NP)]
    n_evals = NP

    best_idx = int(np.argmax([e.f for e in E]))
    best_x = X[best_idx].copy()
    best_eval = E[best_idx]

    start = time.time()

    while time.time() - start < seconds:
        for i in range(NP):
            if time.time() - start >= seconds:
                break
            idxs = list(range(NP))
            idxs.remove(i)
            r0, r1, r2 = rng.choice(idxs, size=3, replace=False)
            v = X[r0] + F*(X[r1] - X[r2])
            v = reflect01(v)

            j_rand = int(rng.integers(0, dim))
            cross_mask = rng.random(dim) < CR
            cross_mask[j_rand] = True
            u = np.where(cross_mask, v, X[i])
            u = reflect01(u)

            eu = evaluate(inst, u, eps_P, eps_H, eps_D)
            n_evals += 1
            if eu.f >= E[i].f:
                X[i] = u
                E[i] = eu
                if eu.f > best_eval.f:
                    best_eval = eu
                    best_x = u.copy()

    return DEResult(best_x=best_x, best_eval=best_eval, n_evals=n_evals, seconds=time.time()-start)

def run_rk_ade(
    inst: Instance,
    seconds: float,
    seed: int,
    NP: int = 50,
    p: float = 0.2,
    F_l: float = 0.1,
    F_u: float = 0.9,
    tau1: float = 0.1,
    tau2: float = 0.1,
    eps_P=1e-4, eps_H=1e-6, eps_D=1e-6,
    use_local_search: bool = False,
    ls_frac: float = 0.1,
    ls_moves: int = 30,
) -> DEResult:
    rng = np.random.default_rng(seed)
    py_rng = random.Random(seed + 99991)
    n = len(inst.items)
    dim = 2*n

    X = rng.random((NP, dim))
    F_i = rng.uniform(F_l, F_u, size=NP)
    CR_i = rng.random(NP)

    E = [evaluate(inst, X[i], eps_P, eps_H, eps_D) for i in range(NP)]
    n_evals = NP

    best_idx = int(np.argmax([e.f for e in E]))
    best_x = X[best_idx].copy()
    best_eval = E[best_idx]

    start = time.time()

    while time.time() - start < seconds:
        scores = np.array([e.f for e in E])
        elite_k = max(2, int(math.ceil(p * NP)))
        elite_idx = scores.argsort()[::-1][:elite_k]

        for i in range(NP):
            if time.time() - start >= seconds:
                break

            if rng.random() < tau1:
                F_i[i] = float(F_l + rng.random()*(F_u - F_l))
            if rng.random() < tau2:
                CR_i[i] = float(rng.random())

            pbest = int(rng.choice(elite_idx))
            idxs = list(range(NP))
            idxs.remove(i)
            r1, r2 = rng.choice(idxs, size=2, replace=False)

            Fi = float(F_i[i])
            v = X[i] + Fi*(X[pbest] - X[i]) + Fi*(X[r1] - X[r2])
            v = reflect01(v)

            j_rand = int(rng.integers(0, dim))
            cross_mask = rng.random(dim) < float(CR_i[i])
            cross_mask[j_rand] = True
            u = np.where(cross_mask, v, X[i])
            u = reflect01(u)

            eu = evaluate(inst, u, eps_P, eps_H, eps_D)
            n_evals += 1
            if eu.f >= E[i].f:
                X[i] = u
                E[i] = eu
                if eu.f > best_eval.f:
                    best_eval = eu
                    best_x = u.copy()

        if use_local_search:
            scores = np.array([e.f for e in E])
            K = max(1, int(math.ceil(ls_frac * NP)))
            top_idx = scores.argsort()[::-1][:K]
            for idx in top_idx:
                if time.time() - start >= seconds:
                    break
                x = X[idx]
                ev = E[idx]

                perm = perm_from_keys(x[:n])
                r_plan = rplan_from_okeys(x[n:])

                for _ in range(ls_moves):
                    perm2, r2 = local_search_step(perm, r_plan, py_rng)
                    x2 = reencode_from_perm_and_r(n, perm2, r2)
                    ev2 = evaluate(inst, x2, eps_P, eps_H, eps_D)
                    n_evals += 1
                    if ev2.f > ev.f:
                        perm, r_plan = perm2, r2
                        x, ev = x2, ev2
                        if ev.f > best_eval.f:
                            best_eval = ev
                            best_x = x.copy()

                X[idx] = x
                E[idx] = ev

    return DEResult(best_x=best_x, best_eval=best_eval, n_evals=n_evals, seconds=time.time()-start)

# =========================================================
# Additional baselines for comparison (matched-budget)
# =========================================================

def _decode_perm_rplan(x: np.ndarray, n: int):
    """Decode random-key vector x -> (perm, r_plan)"""
    k = x[:n]
    o = x[n:]
    perm = list(np.argsort(k))
    r_plan = list(1 + np.minimum(5, np.floor(6 * o)).astype(int))
    return perm, r_plan

def run_random_search(inst: Instance, *, seconds: float, seed: int, batch: int = 32) -> DEResult:
    """Pure random search in the same random-key space (anytime)."""
    rng = np.random.default_rng(seed)
    dim = 2 * inst.n
    start = time.time()
    best_x = None
    best_eval = None
    n_evals = 0

    while time.time() - start < seconds:
        X = rng.random((batch, dim))
        for i in range(batch):
            ev = evaluate(inst, X[i])
            n_evals += 1
            if (best_eval is None) or (ev.f > best_eval.f):
                best_eval = ev
                best_x = X[i].copy()

    if best_eval is None:
        # fall back to a single evaluation (should not happen)
        best_x = rng.random(dim)
        best_eval = evaluate(inst, best_x)
        n_evals += 1

    return DEResult(best_x=best_x, best_eval=best_eval, n_evals=n_evals, seconds=time.time() - start)

def _reflect01(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = np.where(x < 0.0, -x, x)
    x = np.where(x > 1.0, 2.0 - x, x)
    return np.clip(x, 0.0, 1.0)

def run_ga(inst: Instance, *, seconds: float, seed: int, NP: int = 50,
           cx_rate: float = 0.9, mut_rate: float = 0.05, sigma: float = 0.1,
           tourn_k: int = 3) -> DEResult:
    """Simple GA baseline operating directly on random keys."""
    rng = np.random.default_rng(seed)
    dim = 2 * inst.n
    start = time.time()

    pop = rng.random((NP, dim))
    E = [evaluate(inst, pop[i]) for i in range(NP)]
    n_evals = NP

    best_idx = int(np.argmax([e.f for e in E]))
    best_x = pop[best_idx].copy()
    best_eval = E[best_idx]

    def tournament() -> int:
        idx = rng.integers(0, NP, size=tourn_k)
        best = idx[0]
        bf = E[best].f
        for j in idx[1:]:
            if E[j].f > bf:
                best = int(j)
                bf = E[j].f
        return best

    while time.time() - start < seconds:
        # elitism
        elite = best_x.copy()
        new_pop = [elite]

        while len(new_pop) < NP:
            p1 = pop[tournament()]
            p2 = pop[tournament()]

            if rng.random() < cx_rate:
                alpha = rng.random(dim)
                child = alpha * p1 + (1.0 - alpha) * p2
            else:
                child = p1.copy()

            mask = rng.random(dim) < mut_rate
            if np.any(mask):
                child = child.copy()
                child[mask] += rng.normal(0.0, sigma, size=mask.sum())

            child = _reflect01(child)
            new_pop.append(child)

        pop = np.array(new_pop)
        E = [evaluate(inst, pop[i]) for i in range(NP)]
        n_evals += NP

        idx = int(np.argmax([e.f for e in E]))
        if E[idx].f > best_eval.f:
            best_eval = E[idx]
            best_x = pop[idx].copy()

    return DEResult(best_x=best_x, best_eval=best_eval, n_evals=n_evals, seconds=time.time() - start)

def run_sa(inst: Instance, *, seconds: float, seed: int,
           T0: float = 1e-2, Tend: float = 1e-4) -> DEResult:
    """Simulated annealing baseline in (perm, orientation) space with re-encoding."""
    np_rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)
    dim = 2 * inst.n
    start = time.time()

    x = np_rng.random(dim)
    ev = evaluate(inst, x)
    n_evals = 1

    best_x = x.copy()
    best_eval = ev

    while True:
        t = time.time() - start
        if t >= seconds:
            break

        frac = min(1.0, t / max(seconds, 1e-9))
        T = T0 * ((Tend / T0) ** frac)

        perm, rplan = _decode_perm_rplan(x, inst.n)
        perm2, rplan2 = local_search_step(perm, rplan, py_rng)
        x2 = reencode_from_perm_and_r(inst.n, perm2, rplan2)

        ev2 = evaluate(inst, x2)
        n_evals += 1

        d = ev2.f - ev.f
        if d >= 0.0 or (T > 0 and py_rng.random() < float(np.exp(d / T))):
            x, ev = x2, ev2
            if ev.f > best_eval.f:
                best_eval = ev
                best_x = x.copy()

    return DEResult(best_x=best_x, best_eval=best_eval, n_evals=n_evals, seconds=time.time() - start)


def run_pso(
    inst: Instance,
    *,
    seconds: float,
    seed: int,
    NP: int = 60,
    w: float = 0.72,
    c1: float = 1.49,
    c2: float = 1.49,
    vmax: float = 0.2,
) -> DEResult:
    """Particle Swarm Optimization baseline in random-key space.

    Notes
    -----
    - Operates directly on the same [0,1]^{2n} encoding used by RK-ADELS.
    - Bound handling uses reflection (same helper as DE).
    - Fitness is the utilization-dominant score f (Eq. 5 / Algorithm 1).
    """
    rng = np.random.default_rng(seed)
    dim = 2 * inst.n
    start = time.time()

    # Initialize swarm
    X = rng.random((NP, dim), dtype=np.float64)
    V = rng.uniform(-vmax, vmax, size=(NP, dim)).astype(np.float64)

    pbest = X.copy()
    pbest_eval = np.full(NP, -1e18, dtype=np.float64)
    gbest = None
    gbest_eval = -1e18

    n_evals = 0

    # Initial evaluation
    for i in range(NP):
        ev = evaluate(inst, X[i])
        n_evals += 1
        pbest_eval[i] = ev.f
        if ev.f > gbest_eval:
            gbest_eval = ev.f
            gbest = X[i].copy()

    assert gbest is not None

    # Main loop (time-budgeted)
    while (time.time() - start) < seconds:
        r1 = rng.random((NP, dim))
        r2 = rng.random((NP, dim))

        # Velocity + position update
        V = w * V + c1 * r1 * (pbest - X) + c2 * r2 * (gbest[None, :] - X)
        V = np.clip(V, -vmax, vmax)
        X = X + V
        X = _reflect01(X)

        # Evaluate and update bests
        for i in range(NP):
            ev = evaluate(inst, X[i])
            n_evals += 1
            if ev.f > pbest_eval[i]:
                pbest_eval[i] = ev.f
                pbest[i] = X[i].copy()
                if ev.f > gbest_eval:
                    gbest_eval = ev.f
                    gbest = X[i].copy()

        # Safety: if time is exceeded during the inner loop, stop early
        if (time.time() - start) >= seconds:
            break

    best_x = gbest
    best_eval = evaluate(inst, best_x)
    n_evals += 1
    return DEResult(best_x=best_x, best_eval=best_eval, n_evals=n_evals, seconds=time.time() - start)


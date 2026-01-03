from __future__ import annotations
from typing import List, Tuple
import random
import numpy as np

def reencode_from_perm_and_r(n: int, perm: List[int], r_plan: List[int]) -> np.ndarray:
    k = np.zeros(n, dtype=float)
    for pos, idx in enumerate(perm):
        k[idx] = (pos + 0.5) / n
    o = np.zeros(n, dtype=float)
    for i in range(n):
        r = int(r_plan[i])
        o[i] = (r - 1 + 0.5) / 6.0
    return np.concatenate([k, o])

def perm_from_keys(k: np.ndarray) -> List[int]:
    return list(np.argsort(k, kind="mergesort"))

def rplan_from_okeys(o: np.ndarray) -> List[int]:
    r = (np.floor(6.0 * np.clip(o, 0.0, 1.0 - 1e-12))).astype(int) + 1
    r = np.clip(r, 1, 6)
    return list(map(int, r.tolist()))

def local_search_step(perm: List[int], r_plan: List[int], rng: random.Random) -> Tuple[List[int], List[int]]:
    n = len(perm)
    move = rng.choice(["swap","insert","reverse","rot"])
    perm2 = perm[:]
    r2 = r_plan[:]

    if move == "swap" and n >= 2:
        i, j = rng.randrange(n), rng.randrange(n)
        perm2[i], perm2[j] = perm2[j], perm2[i]

    elif move == "insert" and n >= 2:
        i, j = rng.randrange(n), rng.randrange(n)
        if i != j:
            v = perm2.pop(i)
            perm2.insert(j, v)

    elif move == "reverse" and n >= 4:
        i = rng.randrange(0, n-2)
        j = rng.randrange(i+1, min(n, i+1+rng.randint(2, 6)))
        perm2[i:j] = list(reversed(perm2[i:j]))

    elif move == "rot":
        item = rng.randrange(n)
        cur = r2[item]
        cand = rng.randrange(1, 7)
        if cand == cur:
            cand = (cand % 6) + 1
        r2[item] = cand

    return perm2, r2

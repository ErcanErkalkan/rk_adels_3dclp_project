from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import bisect
import numpy as np

from .instance import Instance, orientations

@dataclass
class Placement:
    x: float
    y: float
    z: float
    w: float
    h: float
    d: float
    r: int  # 1..6

@dataclass
class DecodeResult:
    V: float
    placed_count: int
    H_max: float
    D_max: float
    f: float
    placements: List[Placement]

class HeightMap2D:
    def __init__(self, W: float, D: float):
        self.W = float(W)
        self.D = float(D)
        self.X = [0.0, self.W]
        self.Z = [0.0, self.D]
        self.S = np.zeros((1,1), dtype=float)

    def _insert_breakpoint_axis(self, axis: str, value: float):
        value = float(value)
        if axis == "x":
            arr = self.X
            if value <= 0.0 or value >= self.W:
                return
            idx = bisect.bisect_left(arr, value)
            if idx < len(arr) and abs(arr[idx] - value) < 1e-12:
                return
            arr.insert(idx, value)
            old_row = idx - 1
            self.S = np.insert(self.S, idx, self.S[old_row, :], axis=0)
        elif axis == "z":
            arr = self.Z
            if value <= 0.0 or value >= self.D:
                return
            idx = bisect.bisect_left(arr, value)
            if idx < len(arr) and abs(arr[idx] - value) < 1e-12:
                return
            arr.insert(idx, value)
            old_col = idx - 1
            self.S = np.insert(self.S, idx, self.S[:, old_col], axis=1)
        else:
            raise ValueError("axis must be 'x' or 'z'")

    def insert_breakpoints(self, xs: List[float], zs: List[float]):
        for v in xs:
            self._insert_breakpoint_axis("x", v)
        for v in zs:
            self._insert_breakpoint_axis("z", v)

    def _interval_range(self, arr: List[float], a: float, b: float) -> Tuple[int,int]:
        i0 = max(0, bisect.bisect_right(arr, a) - 1)
        i1 = max(0, bisect.bisect_left(arr, b))
        i0 = min(i0, len(arr)-2)
        i1 = min(max(i1, i0+1), len(arr)-1)
        return i0, i1

    def max_over(self, x0: float, x1: float, z0: float, z1: float) -> float:
        ix0, ix1 = self._interval_range(self.X, x0, x1)
        iz0, iz1 = self._interval_range(self.Z, z0, z1)
        return float(np.max(self.S[ix0:ix1, iz0:iz1]))

    def set_over(self, x0: float, x1: float, z0: float, z1: float, value: float):
        ix0, ix1 = self._interval_range(self.X, x0, x1)
        iz0, iz1 = self._interval_range(self.Z, z0, z1)
        self.S[ix0:ix1, iz0:iz1] = float(value)

    def H_max(self) -> float:
        return float(np.max(self.S))

def decode_wall_heightmap(
    inst: Instance,
    order: List[int],
    r_plan: List[int],
    eps_P: float = 1e-4,
    eps_H: float = 1e-6,
    eps_D: float = 1e-6,
) -> DecodeResult:
    W,H,D = inst.container.W, inst.container.H, inst.container.D
    n = len(inst.items)

    hm = HeightMap2D(W, D)
    placements: List[Placement] = []
    V_placed = 0.0
    D_max = 0.0

    for idx in order:
        it = inst.items[idx]
        r = int(r_plan[idx])
        orients = orientations(it.w, it.h, it.d, getattr(it, 'vert_ok', (1,1,1)))
        w,h,d = orients[(r-1) % len(orients)]

        Xc = [0.0]
        Zc = [0.0]
        for pl in placements:
            Xc.append(pl.x + pl.w)
            Zc.append(pl.z + pl.d)

        Xc = sorted(set([x for x in Xc if x <= W]))
        Zc = sorted(set([z for z in Zc if z <= D]))

        best_key = None
        best_xyz = None

        for x in Xc:
            if x + w > W + 1e-12:
                continue
            for z in Zc:
                if z + d > D + 1e-12:
                    continue

                y = hm.max_over(x, x+w, z, z+d)
                if y + h > H + 1e-12:
                    continue

                Hprime = max(hm.H_max(), y + h)
                key = (y, z, x, Hprime)  # bottom-left-front + peak tie-break

                if best_key is None or key < best_key:
                    best_key = key
                    best_xyz = (x,y,z)

        if best_xyz is None:
            continue

        x,y,z = best_xyz
        hm.insert_breakpoints([x, x+w], [z, z+d])
        hm.set_over(x, x+w, z, z+d, y + h)

        placements.append(Placement(x=x,y=y,z=z,w=w,h=h,d=d,r=r))
        V_placed += w*h*d
        D_max = max(D_max, z + d)

    V = V_placed/(W*H*D) if W*H*D > 0 else 0.0
    placed_count = len(placements)
    H_max = hm.H_max()
    f = V + eps_P*(placed_count/n) - eps_H*(H_max/H) - eps_D*(D_max/D)

    return DecodeResult(V=V, placed_count=placed_count, H_max=H_max, D_max=D_max, f=f, placements=placements)

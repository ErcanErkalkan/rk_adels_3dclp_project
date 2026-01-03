from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np

from rk_adels.instance import Instance, Container, Item

def generate_instance(name: str, W: float, H: float, D: float, n_items: int, fill_ratio: float, seed: int) -> Instance:
    rng = np.random.default_rng(seed)
    container_vol = W*H*D
    target_vol = fill_ratio * container_vol

    items = []
    vol = 0.0

    for _ in range(n_items):
        a = float(np.clip(rng.lognormal(mean=-0.7, sigma=0.7), 0.05, 0.9))
        b = float(np.clip(rng.lognormal(mean=-0.8, sigma=0.8), 0.05, 0.9))
        c = float(np.clip(rng.lognormal(mean=-0.9, sigma=0.9), 0.05, 0.9))

        w = min(W, max(1.0, a * W))
        h = min(H, max(1.0, b * H))
        d = min(D, max(1.0, c * D))

        items.append(Item(w=w, h=h, d=d))
        vol += w*h*d

    if vol > 1e-9:
        s = (target_vol / vol) ** (1.0/3.0)
        s = float(np.clip(s, 0.6, 1.4))
        new_items = []
        for it in items:
            w = min(W, max(1.0, it.w * s))
            h = min(H, max(1.0, it.h * s))
            d = min(D, max(1.0, it.d * s))
            new_items.append(Item(w=w,h=h,d=d))
        items = new_items

    return Instance(name=name, container=Container(W=W,H=H,D=D), items=items)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--n_instances", type=int, default=10)
    ap.add_argument("--n_items", type=int, default=100)
    ap.add_argument("--fill_ratio", type=float, default=1.2)
    ap.add_argument("--W", type=float, default=100)
    ap.add_argument("--H", type=float, default=100)
    ap.add_argument("--D", type=float, default=100)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for k in range(args.n_instances):
        name = f"syn_{k:03d}"
        inst = generate_instance(
            name=name,
            W=args.W, H=args.H, D=args.D,
            n_items=args.n_items,
            fill_ratio=args.fill_ratio,
            seed=args.seed + 1000*k
        )
        inst.save_json(str(out / f"{name}.json"))

    print(f"OK: wrote {args.n_instances} instances to {out}")

if __name__ == "__main__":
    main()

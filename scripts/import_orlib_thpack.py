from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterator, Optional, List, Dict, Any

import pandas as pd

from rk_adels.instance import Instance, Container, Item

def _nonempty_lines(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s:
                yield s

def parse_thpack_file(path: Path, limit_problems: Optional[int] = None) -> List[Instance]:
    """Parse OR-Library thpack{1..9} style files.

    Format (see OR-Library thpackinfo):
      P
      [for each problem]
        p [seed]
        L W H  (container length, width, height)
        n      (number of box types)
        i li ri wi ri hi ri qi  (8 ints per type)
    After each box dimension, the 0/1 indicates whether placement in the vertical orientation is permissible.
    """
    it = _nonempty_lines(path)
    try:
        P = int(next(it).split()[0])
    except StopIteration:
        raise ValueError(f"Empty file: {path}")
    instances: List[Instance] = []
    for _ in range(P):
        header = next(it).split()
        if len(header) >= 2:
            p = int(header[0])
            seed: Optional[int] = int(header[1])
        else:
            p = int(header[0])
            seed = None

        LWH = [int(x) for x in next(it).split()]
        if len(LWH) != 3:
            raise ValueError(f"Bad container dims line in {path} for problem {p}: {LWH}")
        Lc, Wc, Hc = LWH  # length, width, height
        n_types = int(next(it).split()[0])

        items: List[Item] = []
        for _k in range(n_types):
            parts = [int(x) for x in next(it).split()]
            if len(parts) != 8:
                raise ValueError(f"Expected 8 ints per box-type line in {path} for problem {p}, got {len(parts)}: {parts}")
            _type_id, l, vl, w, vw, h, vh, q = parts

            # Map OR-Library (length,width,height) to our (w,d,h) with base plane (W,D) and vertical H:
            # item.w <- length, item.d <- width, item.h <- height
            # Vertical-permission flags must align with (w,h,d) = (length,height,width)
            vert_ok = (vl, vh, vw)

            for _ in range(q):
                items.append(Item(w=float(l), h=float(h), d=float(w), vert_ok=vert_ok))

        name = f"{path.stem}_p{p:03d}" + (f"_seed{seed}" if seed is not None else "")
        inst = Instance(name=name, container=Container(W=float(Lc), H=float(Hc), D=float(Wc)), items=items)
        instances.append(inst)

        if limit_problems is not None and len(instances) >= limit_problems:
            break

    return instances

def main() -> None:
    ap = argparse.ArgumentParser(description="Convert OR-Library thpack datasets (Bischoff–Ratcliff, etc.) into this project's JSON instance format.")
    ap.add_argument("--thpack", nargs="+", required=True, help="Path(s) to thpack*.txt file(s) (download from OR-Library)")
    ap.add_argument("--out_dir", required=True, help="Output directory for .json instances")
    ap.add_argument("--limit_problems", type=int, default=None, help="Optional: only convert first N problems per file")
    ap.add_argument("--manifest", action="store_true", help="Write a manifest CSV into out_dir")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []

    for th in args.thpack:
        p = Path(th)
        if not p.exists():
            raise FileNotFoundError(p)
        insts = parse_thpack_file(p, limit_problems=args.limit_problems)
        for inst in insts:
            out_path = out_dir / f"{inst.name}.json"
            inst.save_json(str(out_path))
            rows.append({
                "name": inst.name,
                "file": str(out_path),
                "W": inst.container.W,
                "H": inst.container.H,
                "D": inst.container.D,
                "n_items": inst.n,
            })

        print(f"OK: {p.name} -> {len(insts)} instances")

    if args.manifest:
        df = pd.DataFrame(rows).sort_values(["name"])
        mf = out_dir / "manifest.csv"
        df.to_csv(mf, index=False)
        print(f"OK: wrote {mf}")

if __name__ == "__main__":
    main()

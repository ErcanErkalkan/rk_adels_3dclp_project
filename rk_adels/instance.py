from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import json

@dataclass
class Container:
    # W: x-axis length (base)
    # H: vertical height
    # D: z-axis width/depth (base)
    W: float
    H: float
    D: float

@dataclass
class Item:
    # w: x-axis size, h: vertical size, d: z-axis size
    w: float
    h: float
    d: float
    # For OR-Library thpack-style datasets: per-dimension flag indicating
    # whether that dimension is allowed to be placed vertically (as height).
    # Order follows (w, h, d). Defaults to unrestricted rotations.
    vert_ok: Tuple[int, int, int] = (1, 1, 1)

@dataclass
class Instance:
    name: str
    container: Container
    items: List[Item]

    @property
    def n(self) -> int:
        """Number of items."""
        return len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        items_out: List[Dict[str, Any]] = []
        for it in self.items:
            d = {"w": it.w, "h": it.h, "d": it.d}
            if tuple(it.vert_ok) != (1, 1, 1):
                d["vert_ok"] = list(it.vert_ok)
            items_out.append(d)
        return {
            "name": self.name,
            "container": {"W": self.container.W, "H": self.container.H, "D": self.container.D},
            "items": items_out,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Instance":
        c = d["container"]
        items: List[Item] = []
        for it in d["items"]:
            if "vert_ok" in it and it["vert_ok"] is not None:
                vo = tuple(int(x) for x in it["vert_ok"])
                items.append(Item(w=float(it["w"]), h=float(it["h"]), d=float(it["d"]), vert_ok=vo))  # type: ignore[arg-type]
            else:
                items.append(Item(w=float(it["w"]), h=float(it["h"]), d=float(it["d"])))
        return Instance(name=d.get("name", "instance"), container=Container(**c), items=items)

    def save_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load_json(path: str) -> "Instance":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return Instance.from_dict(d)

def orientations(w: float, h: float, d: float, vert_ok: Tuple[int, int, int] = (1, 1, 1)) -> List[Tuple[float, float, float]]:
    """All axis-aligned orientations, optionally restricted by vertical permission.

    The returned tuples are (w,h,d) where the middle component is vertical (y axis).
    If vert_ok[j] == 0, then the corresponding original dimension is not allowed to be vertical.
    """
    dims = (w, h, d)
    flags = tuple(int(x) for x in vert_ok)
    perms = [
        (0, 1, 2),
        (0, 2, 1),
        (1, 0, 2),
        (1, 2, 0),
        (2, 0, 1),
        (2, 1, 0),
    ]
    out: List[Tuple[float, float, float]] = []
    seen = set()
    for a, b, c in perms:
        if flags[b] != 1:
            continue
        tup = (dims[a], dims[b], dims[c])
        if tup not in seen:
            out.append(tup)
            seen.add(tup)
    return out

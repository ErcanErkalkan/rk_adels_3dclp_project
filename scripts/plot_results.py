from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

VARIANT_LABEL = {
    "H0": "H0 (Decoder-only)",
    "A1": "A1 (RK-DE)",
    "A2": "A2 (RK-ADE)",
    "A3": "A3 (RK-ADELS)",
    "RS": "Random Search (RK)",
    "GA": "GA (RK)",
    "SA": "SA (Perm+Orient)",
}

def make_plots(runs_csv: str, summary_csv: str, out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    runs = pd.read_csv(runs_csv)
    summ = pd.read_csv(summary_csv)

    # Bar plot: mean utilization per variant (averaged over instances)
    agg = summ.groupby("variant", as_index=False).agg(V_mean=("V_mean","mean"), V_std=("V_mean","std"))
    agg["label"] = agg["variant"].map(lambda v: VARIANT_LABEL.get(v, v))

    plt.figure()
    plt.bar(agg["label"], agg["V_mean"], yerr=agg["V_std"])
    plt.ylabel("Mean utilization V")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(out / "fig_utilization_bars.png", dpi=200)
    plt.close()

    # Scatter: wallclock vs utilization
    plt.figure()
    for v, g in runs.groupby("variant"):
        plt.scatter(g["wallclock"], g["V_best"], label=VARIANT_LABEL.get(v, v), alpha=0.6)
    plt.xlabel("Wall-clock time (s)")
    plt.ylabel("Utilization V (best)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "fig_runtime_scatter.png", dpi=200)
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_csv", required=True)
    ap.add_argument("--summary_csv", required=True)
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()
    make_plots(args.runs_csv, args.summary_csv, args.out_dir)
    print(f"OK: plots saved to {args.out_dir}")

if __name__ == "__main__":
    main()

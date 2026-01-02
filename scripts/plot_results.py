import argparse
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def bar_utilization(df, outdir):
    for inst in df["instance"].unique():
        d = df[df["instance"] == inst].sort_values("variant")
        plt.figure()
        plt.bar(d["variant"], d["meanV"])
        plt.ylabel("Mean utilization V")
        plt.title(f"Utilization (mean) — {inst}")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, f"util_bar_{inst}.png"), dpi=200)
        plt.close()

def scatter_runtime(df, outdir):
    plt.figure()
    for var in df["variant"].unique():
        d = df[df["variant"] == var]
        plt.scatter(d["meanTimeSec"], d["meanV"], label=var)
    plt.xlabel("Mean time (s)")
    plt.ylabel("Mean utilization V")
    plt.title("Utilization vs runtime (summary)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "util_vs_time_scatter.png"), dpi=200)
    plt.close()

def attribution_deltas(df, outdir):
    needed = {"H0","A1","A2","A3"}
    if not needed.issubset(set(df["variant"].unique())):
        return
    rows = []
    for inst in df["instance"].unique():
        di = df[df["instance"] == inst].set_index("variant")
        dv1 = di.loc["A1","meanV"] - di.loc["H0","meanV"]
        dv2 = di.loc["A2","meanV"] - di.loc["A1","meanV"]
        dv3 = di.loc["A3","meanV"] - di.loc["A2","meanV"]
        rows.append((inst, dv1, dv2, dv3))
    D = pd.DataFrame(rows, columns=["instance","H0_to_A1","A1_to_A2","A2_to_A3"])
    D.to_csv(os.path.join(outdir, "attribution_deltas.csv"), index=False)

    plt.figure()
    x = np.arange(len(D))
    w = 0.25
    plt.bar(x - w, D["H0_to_A1"], width=w, label="H0→A1")
    plt.bar(x,     D["A1_to_A2"], width=w, label="A1→A2")
    plt.bar(x + w, D["A2_to_A3"], width=w, label="A2→A3")
    plt.xticks(x, D["instance"], rotation=45, ha="right")
    plt.ylabel("Δ utilization (mean)")
    plt.title("Attribution deltas (mean V)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "attribution_deltas.png"), dpi=200)
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.summary)
    ensure_dir(args.out)

    bar_utilization(df, args.out)
    scatter_runtime(df, args.out)
    attribution_deltas(df, args.out)
    print("Figures written to:", os.path.abspath(args.out))

if __name__ == "__main__":
    main()

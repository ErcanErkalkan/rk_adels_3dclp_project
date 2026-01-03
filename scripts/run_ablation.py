from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from rk_adels.instance import Instance
from rk_adels.runner import run_variant, summarize_runs
from scripts.plot_results import make_plots

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances_dir", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--NP", type=int, default=50)
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--variants", type=str, default="H0,A1,A2,A3",
                    help="Comma-separated list of variants to run (e.g., H0,A1,A2,A3,RS,GA,SA)")
    args = ap.parse_args()

    inst_dir = Path(args.instances_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    inst_paths = sorted(inst_dir.glob("*.json"))
    if not inst_paths:
        raise SystemExit(f"No instances found in {inst_dir}. Run generate_instances first.")

    rows = []
    variants = [v.strip() for v in args.variants.split(",") if v.strip()]
    seed_off = {"H0":0,"A1":17,"A2":31,"A3":47,"RS":61,"GA":79,"SA":97}

    for ip in inst_paths:
        inst = Instance.load_json(str(ip))
        inst.name = inst.name or ip.stem

        for t in range(args.trials):
            trial_seed_base = args.seed + 100000*t + (abs(hash(inst.name)) % 10000)
            for v in variants:
                row = run_variant(inst, variant=v, seconds=args.seconds, NP=args.NP, seed=trial_seed_base + seed_off.get(v, 0))
                row["trial"] = t
                rows.append(row)
                print(f"{inst.name} trial={t} {v} V={row['V_best']:.4f} placed={row['placed_best']} evals/s={row['evals_per_sec']:.1f}")

    df = pd.DataFrame(rows)
    runs_csv = out_dir / "runs.csv"
    df.to_csv(runs_csv, index=False)

    summary = summarize_runs(df)
    summary_csv = out_dir / "summary.csv"
    summary.to_csv(summary_csv, index=False)

    print(f"OK: wrote {runs_csv}")
    print(f"OK: wrote {summary_csv}")

    make_plots(str(runs_csv), str(summary_csv), str(out_dir))
    print(f"OK: plots saved to {out_dir}")

if __name__ == "__main__":
    main()

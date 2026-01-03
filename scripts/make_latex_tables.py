#!/usr/bin/env python
"""Render LaTeX tables from summary CSV files produced by scripts/plot_results.py.

Outputs:
  - results_table.tex   (benchmarks vs baselines)
  - ablation_table.tex  (H0/A1/A2/A3)

This is intentionally simple: you can paste the tables into the EAAI LaTeX template
and tweak formatting (column widths, rounding, multirow) as needed.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


def _fmt_float(x, nd=4):
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


def _latex_escape(s: str) -> str:
    # Minimal escaping for underscores etc.
    return (
        str(s)
        .replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
    )


def results_table(df: pd.DataFrame) -> str:
    # Expect columns: instance, method, V_mean, V_std, V_best, placed_mean, time_s
    cols = ["instance", "method", "V_mean", "V_std", "V_best", "placed_mean", "time_s"]
    df = df.copy()
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"Missing column '{c}' in results_summary.csv")

    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Volume utilization and runtime on benchmarks.}")
    lines.append("\\label{tab:results}")
    lines.append("\\begin{tabular}{l l c c c c c}")
    lines.append("\\toprule")
    lines.append("Instance & Method & $\\mu(V)$ & $\\sigma(V)$ & Best $V$ & Placed & Time (s) \\\\")
    lines.append("\\midrule")

    # Group by instance
    for inst, g in df.groupby("instance", sort=True):
        g = g.sort_values(["method"])
        first = True
        for _, r in g.iterrows():
            inst_cell = _latex_escape(inst) if first else ""
            first = False
            lines.append(
                f"{inst_cell} & {_latex_escape(r['method'])} & {_fmt_float(r['V_mean'])} & {_fmt_float(r['V_std'])} & {_fmt_float(r['V_best'])} & {int(round(float(r['placed_mean'])))} & {_fmt_float(r['time_s'], nd=1)} \\\\"  # noqa: E501
            )
        lines.append("\\midrule")

    if lines[-1] == "\\midrule":
        lines.pop()

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    return "\n".join(lines)


def ablation_table(df: pd.DataFrame) -> str:
    # Expect columns: instance, variant, V_mean, V_std, V_best, placed_mean, time_s, decodes_per_s
    cols = ["instance", "variant", "V_mean", "V_std", "V_best", "placed_mean", "time_s", "decodes_per_s"]
    df = df.copy()
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"Missing column '{c}' in ablation_summary.csv")

    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Matched-budget ablation and component attribution.}")
    lines.append("\\label{tab:ablation}")
    lines.append("\\begin{tabular}{l l c c c c c c}")
    lines.append("\\toprule")
    lines.append("Instance & Variant & $\\mu(V)$ & $\\sigma(V)$ & Best $V$ & Placed & Time (s) & Decodes/s \\\\")
    lines.append("\\midrule")

    order = {"H0": 0, "A1": 1, "A2": 2, "A3": 3}

    for inst, g in df.groupby("instance", sort=True):
        g = g.sort_values(by="variant", key=lambda s: s.map(lambda x: order.get(str(x), 99)))
        first = True
        for _, r in g.iterrows():
            inst_cell = _latex_escape(inst) if first else ""
            first = False
            lines.append(
                f"{inst_cell} & {_latex_escape(r['variant'])} & {_fmt_float(r['V_mean'])} & {_fmt_float(r['V_std'])} & {_fmt_float(r['V_best'])} & {int(round(float(r['placed_mean'])))} & {_fmt_float(r['time_s'], nd=1)} & {_fmt_float(r['decodes_per_s'], nd=1)} \\\\"  # noqa: E501
            )
        lines.append("\\midrule")

    if lines[-1] == "\\midrule":
        lines.pop()

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", required=True, help="Directory containing results_summary.csv and ablation_summary.csv")
    ap.add_argument("--out_dir", required=True, help="Output directory for .tex files")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rs_path = in_dir / "results_summary.csv"
    ab_path = in_dir / "ablation_summary.csv"

    if not rs_path.exists():
        raise FileNotFoundError(f"Missing {rs_path}. Run scripts/plot_results.py first.")
    if not ab_path.exists():
        raise FileNotFoundError(f"Missing {ab_path}. Run scripts/plot_results.py first.")

    rs = pd.read_csv(rs_path)
    ab = pd.read_csv(ab_path)

    (out_dir / "results_table.tex").write_text(results_table(rs) + "\n", encoding="utf-8")
    (out_dir / "ablation_table.tex").write_text(ablation_table(ab) + "\n", encoding="utf-8")

    print(f"Wrote: {out_dir / 'results_table.tex'}")
    print(f"Wrote: {out_dir / 'ablation_table.tex'}")


if __name__ == "__main__":
    main()

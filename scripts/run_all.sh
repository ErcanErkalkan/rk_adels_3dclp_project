#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------
# Full pipeline (Linux/macOS): generate instances -> run experiments -> plots
# ---------------------------------------------------------
# Usage:
#   bash scripts/run_all.sh [OUT_DIR]
#
# You can customize the knobs below.

OUT_DIR=${1:-runs/run_$(date +%Y%m%d_%H%M%S)}
INST_DIR="$OUT_DIR/instances"

# ---- instance generation knobs ----
N_INSTANCES=10
N_ITEMS=200
FILL_RATIO=1.15
W=100
H=100
D=100
SEED=1

# ---- experiment knobs ----
TRIALS=5
SECONDS=30
NP=60

mkdir -p "$OUT_DIR"

echo "[1/3] Generating instances -> $INST_DIR"
PYTHONPATH=. python scripts/generate_instances.py \
  --out_dir "$INST_DIR" \
  --n_instances $N_INSTANCES \
  --n_items $N_ITEMS \
  --fill_ratio $FILL_RATIO \
  --W $W --H $H --D $D \
  --seed $SEED

echo "[2/3] Running ablation + baselines -> $OUT_DIR"
PYTHONPATH=. python scripts/run_ablation.py \
  --instances_dir "$INST_DIR" \
  --out_dir "$OUT_DIR" \
  --trials $TRIALS \
  --seconds $SECONDS \
  --NP $NP \
  --seed $SEED \
  --variants H0,A1,A2,A3,RS,PSO,GA,SA

echo "[3/3] Plotting summaries"
PYTHONPATH=. python scripts/plot_results.py --in_dir "$OUT_DIR" --out_dir "$OUT_DIR"

PYTHONPATH=. python scripts/make_latex_tables.py --in_dir "$OUT_DIR" --out_dir "$OUT_DIR"

echo "Done. Outputs in: $OUT_DIR"

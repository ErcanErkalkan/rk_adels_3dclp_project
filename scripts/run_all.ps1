# ---------------------------------------------------------
# Full pipeline (Windows PowerShell): generate -> run -> plot
# ---------------------------------------------------------
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1 -OutDir runs\run_001
#
# You can customize the knobs below.

param(
  [string]$OutDir = (Join-Path "runs" ("run_{0}" -f (Get-Date -Format "yyyyMMdd_HHmmss")))
)

$InstDir = Join-Path $OutDir "instances"

# ---- instance generation knobs ----
$N_INSTANCES = 10
$N_ITEMS = 200
$FILL_RATIO = 1.15
$W = 100
$H = 100
$D = 100
$SEED = 1

# ---- experiment knobs ----
$TRIALS = 5
$SECONDS = 30
$NP = 60

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "[1/3] Generating instances -> $InstDir"
$env:PYTHONPATH = "."
python scripts\generate_instances.py `
  --out_dir $InstDir `
  --n_instances $N_INSTANCES `
  --n_items $N_ITEMS `
  --fill_ratio $FILL_RATIO `
  --W $W --H $H --D $D `
  --seed $SEED

Write-Host "[2/3] Running ablation + baselines -> $OutDir"
python scripts\run_ablation.py `
  --instances_dir $InstDir `
  --out_dir $OutDir `
  --trials $TRIALS `
  --seconds $SECONDS `
  --NP $NP `
  --seed $SEED `
  --variants H0,A1,A2,A3,RS,PSO,GA,SA

Write-Host "[3/3] Plotting summaries"
python scripts\plot_results.py --in_dir $OutDir --out_dir $OutDir
python scripts\make_latex_tables.py --in_dir $OutDir --out_dir $OutDir

Write-Host "Done. Outputs in: $OutDir"

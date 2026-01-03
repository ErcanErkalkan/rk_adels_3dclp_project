# RK-ADELS (3D-CLP) — Full runnable project (Python)

This package is a benchmark-oriented prototype for the **3D Container Loading Problem (3D-CLP)**, including:
- **Automatic instance generation**
- **3D wall–heightmap decoder**
- **Ablation study**: H0 (decoder-only), A1 (RK-DE), A2 (RK-ADE), A3 (RK-ADELS + Local Search)
- **Result CSVs + plot generation**

> Note: This is an academic/benchmark prototype. The decoder is **budget-oriented** and designed for **fast evaluation**.

---

## 1) Setup

### Windows
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2) Generate instances (automatic)

```bash
PYTHONPATH=. python -m scripts.generate_instances   --out_dir data/instances   --n_instances 10   --n_items 100   --fill_ratio 1.20   --W 100 --H 100 --D 100   --seed 42
```

Outputs: `data/instances/syn_000.json`, `syn_001.json`, ...

---

## 3) Ablation + results + plots (single command)

```bash
PYTHONPATH=. python -m scripts.run_ablation   --instances_dir data/instances   --out_dir outputs/run1   --trials 10   --seconds 30   --NP 50   --seed 123
```

Outputs:
- `outputs/run1/runs.csv` (all runs, per seed)
- `outputs/run1/summary.csv` (instance × variant summary)
- `outputs/run1/fig_utilization_bars.png`
- `outputs/run1/fig_runtime_scatter.png`

---

## 4) If you only want to generate plots

```bash
PYTHONPATH=. python -m scripts.plot_results   --runs_csv outputs/run1/runs.csv   --summary_csv outputs/run1/summary.csv   --out_dir outputs/run1
```

---

## 4.5) One-command end-to-end (synthetic instances + runs + plots)

### Linux/macOS
```bash
bash scripts/run_all.sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

This script performs: (1) **synthetic instance generation**, (2) runs **H0/A1/A2/A3 + RS/PSO/GA/SA**, (3) produces **CSVs + plots**.

If you also want **LaTeX outputs** for paper tables:

```bash
PYTHONPATH=. python -m scripts.make_latex_tables --in_dir outputs/run1 --out_dir outputs/run1
```

---

## Recommended parameters (aligned with paper template)
- `seconds`: 30 / 60 / 120 (**matched-budget**)
- `trials`: 10 or 20
- `NP`: 50 or 100

---

## Folder structure
- `rk_adels/` : core algorithms
- `scripts/`  : CLI commands
- `data/instances/` : JSON instance files
- `outputs/` : CSVs + plots

Good luck!

---

## 5) Comparison with other algorithms (RS / GA / SA)

In this project, “external” algorithm comparisons can be done in two ways:

1) **Matched-budget comparison using the same decoder (recommended):**  
   All methods share the same wall–heightmap decoder. This ensures differences come only from the **outer search** (DE/GA/SA/RS), making the comparison fair.

2) **Comparison against full methods from the literature (hard):**  
   Each paper typically uses its own decoder and constraints. A truly fair comparison requires re-implementing those methods or using official code.

This package includes baselines for approach (1):
- `RS` : Random Search (in the same random-key space)
- `PSO`: Random-Key Particle Swarm Optimization
- `GA` : Random-Key Genetic Algorithm
- `SA` : Simulated Annealing on permutation + orientations

### Command
You can extend ablation by using `--variants`:

```bash
PYTHONPATH=. python -m scripts.run_ablation \
  --instances_dir data/instances \
  --out_dir outputs/compare1 \
  --trials 10 \
  --seconds 30 \
  --NP 50 \
  --seed 123 \
  --variants H0,A1,A2,A3,RS,PSO,GA,SA
```

> Note: `GA` is population-based, so it uses `--NP`. For `RS` and `SA`, `--NP` is ignored.

---

## 5) Importing OR-Library datasets (Bischoff–Ratcliff / thpack)

1) Download `thpack1` ... `thpack7` from OR-Library (Bischoff–Ratcliff 1995 test sets).
2) Place them under `data/orlib/` (for example).
3) Convert them into the project’s JSON instance format:

### Windows (PowerShell)
```powershell
PYTHONPATH=. python -m scripts.import_orlib_thpack `
  --thpack data/orlib/thpack1.txt data/orlib/thpack2.txt `
  --out_dir data/instances_orlib `
  --manifest
```

### Linux / macOS
```bash
PYTHONPATH=. python -m scripts.import_orlib_thpack \
  --thpack data/orlib/thpack1.txt data/orlib/thpack2.txt \
  --out_dir data/instances_orlib \
  --manifest
```

Then run the ablation/benchmark directly:
```bash
PYTHONPATH=. python -m scripts.run_ablation \
  --instances_dir data/instances_orlib \
  --out_dir outputs/orlib_run1 \
  --trials 10 --seconds 30 --NP 50 --seed 123
```

> Note: The OR-Library “0/1” flags (whether a dimension allows vertical placement) are supported.

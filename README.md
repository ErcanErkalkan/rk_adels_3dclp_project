# RK-ADELS for 3D Container Loading (3D-CLP) — Full Reproducible Project

This repository contains a **complete, runnable** implementation of the manuscript draft:
**“Solving the Three-Dimensional Container Loading Problem with Random-Key Adaptive Differential Evolution and Local Search”**
(double-anonymized).

It includes:
- A 3D **wall–heightmap** decoder with **dynamic breakpoints** (coordinate-compressed envelope grid)
- Random-key encoding (order + orientation keys), faithful DE operators
- Matched-budget variants: **H0**, **A1**, **A2**, **A3 (= RK-ADELS)**
- Batch experiment runner that writes **CSV summaries**
- Python scripts to generate **tables and plots** (PNG) from results

> Public benchmark instance files are not bundled. Drop your instance JSON files into `data/instances/`
> using the provided schema (see `data/examples/inst_example.json`).

---

## 1) Build
Requires **.NET 8 SDK**.

```bash
cd src/RKAdels3D
dotnet build -c Release
```

## 2) Run a single instance
```bash
dotnet run -c Release -- \
  --instance ../../data/examples/inst_example.json \
  --variant A3 \
  --seed 42 \
  --timeLimitSec 5 \
  --np 60
```

Variants:
- `H0`: decoder-only (random sampling + volume-descending)
- `A1`: RK-DE (DE/rand/1 fixed F/CR, no adaptation, no local search)
- `A2`: RK-ADE (current-to-pbest + self-adaptive F/CR, no local search)
- `A3`: RK-ADELS (A2 + local search)

## 3) Batch experiments
Put instance files in `data/instances/` (each `*.json`), then run:

```bash
dotnet run -c Release -- \
  --batch ../../data/instances \
  --out ../../results \
  --variant A3 \
  --trials 10 \
  --timeLimitSec 30 \
  --np 80 \
  --seed 1337
```

Outputs:
- `results/per_run.csv` (one row per trial)
- `results/summary.csv` (mean±std, best, etc.)

## 4) Plots and tables (Python)
Requires Python 3.10+.

```bash
cd scripts
pip install -r requirements.txt
python plot_results.py --summary ../results/summary.csv --out ../results/figures
```

---

## Instance JSON schema
See `data/examples/inst_example.json`:
- container: W,H,D
- items: list of {id, w,h,d, qty(optional)}

If `qty` is provided, the loader expands items.

---

## Reproducibility
- All trials use explicit seeds (base seed + trial index)
- CSV outputs include machine/time parameters you provide
- The solver is time-budgeted using `Stopwatch`

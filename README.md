# RK-ADELS (3D-CLP) — Full runnable project (Python)

Bu paket, 3D Container Loading Problem (3D-CLP) için:
- Instance üretimi (otomatik)
- 3D wall–heightmap decoder
- Ablation: H0 (decoder-only), A1 (RK-DE), A2 (RK-ADE), A3 (RK-ADELS + Local Search)
- Sonuç CSV’leri + grafik üretimi

> Not: Bu akademik/benchmark amaçlı bir prototiptir. Decoder “budget-oriented” ve hızlı değerlendirme hedeflidir.

---

## 1) Kurulum

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

## 2) Instance üret (otomatik)

```bash
PYTHONPATH=. python -m scripts.generate_instances   --out_dir data/instances   --n_instances 10   --n_items 100   --fill_ratio 1.20   --W 100 --H 100 --D 100   --seed 42
```

Çıktı: `data/instances/syn_000.json`, `syn_001.json`, ...

---

## 3) Ablation + sonuç + grafik (tek komut)

```bash
PYTHONPATH=. python -m scripts.run_ablation   --instances_dir data/instances   --out_dir outputs/run1   --trials 10   --seconds 30   --NP 50   --seed 123
```

Çıktılar:
- `outputs/run1/runs.csv` (tüm koşular, seed bazında)
- `outputs/run1/summary.csv` (instance × variant özet)
- `outputs/run1/fig_utilization_bars.png`
- `outputs/run1/fig_runtime_scatter.png`

---

## 4) Sadece grafik üretmek istersen

```bash
PYTHONPATH=. python -m scripts.plot_results   --runs_csv outputs/run1/runs.csv   --summary_csv outputs/run1/summary.csv   --out_dir outputs/run1
```

---

## 4.5) Tek komutla her şey (sentetik instance + koşu + grafik)

### Linux/macOS

```bash
bash scripts/run_all.sh
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

Bu script şunları yapar: (1) **sentetik instance üretir**, (2) **H0/A1/A2/A3 + RS/PSO/GA/SA** çalıştırır, (3) **CSV + grafik** üretir.

İsterseniz makale tablosu için LaTeX çıktısı:

```bash
PYTHONPATH=. python -m scripts.make_latex_tables --in_dir outputs/run1 --out_dir outputs/run1
```

---

## Parametre önerisi (makale şablonuna uygun)
- `seconds`: 30 / 60 / 120 (matched-budget)
- `trials`: 10 veya 20
- `NP`: 50 veya 100

---

## Klasör yapısı
- `rk_adels/` : çekirdek algoritmalar
- `scripts/`  : CLI komutları
- `data/instances/` : JSON instance dosyaları
- `outputs/` : CSV + grafikler

İyi çalışmalar!

---

## 5) Diğer algoritmalarla karşılaştırma (RS / GA / SA)

Bu projede “dış” algoritma karşılaştırmasını iki şekilde yapabilirsiniz:

1) **Aynı decoder ile matched-budget karşılaştırma (önerilen):**
   Tüm yöntemler aynı wall–heightmap decoder’ı kullanır. Böylece fark, sadece “dış arama” (DE/GA/SA/RS) kaynaklı olur.

2) **Literatürdeki tam yöntemlerle karşılaştırma (zor):**
   Her makalenin kendi decoder/yan kısıtları vardır. Birebir adil karşılaştırma için o kodların yeniden uygulanması veya resmi kodların kullanılması gerekir.

Bu pakette 1) için ek baselines hazır:
- `RS` : Random Search (aynı random-key uzayında)
- `PSO`: Random-Key Particle Swarm Optimization (PSO)
- `GA` : Random-Key Genetic Algorithm
- `SA` : Permütasyon+oryantasyon üzerinde Simulated Annealing

### Komut
Ablation komutunu `--variants` ile genişletebilirsiniz:

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

> Not: `GA` popülasyon tabanlı olduğu için `--NP` kullanır. `RS` ve `SA` için `--NP` yok sayılır.



---

## 5) OR-Library (Bischoff–Ratcliff / thpack) veri setlerini içe aktarma

1) OR-Library’den `thpack1` ... `thpack7` dosyalarını indir (Bischoff–Ratcliff 1995 test setleri).
2) Dosyaları örn. `data/orlib/` altına koy.
3) JSON instance formatına çevir:

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

Sonra direkt ablation/benchmark:
```bash
PYTHONPATH=. python -m scripts.run_ablation \
  --instances_dir data/instances_orlib \
  --out_dir outputs/orlib_run1 \
  --trials 10 --seconds 30 --NP 50 --seed 123
```

> Not: OR-Library formatındaki “0/1” işaretleri (bir boyutun dikey yerleşime izin verip vermediği) desteklenir.

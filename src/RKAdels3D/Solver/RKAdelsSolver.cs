using System.Diagnostics;
using RKAdels3D.Decoder;

namespace RKAdels3D.Core;

public sealed class RKAdelsSolver
{
    private readonly SolverOptions opt;
    private readonly WallHeightmapDecoder decoder = new();

    public RKAdelsSolver(SolverOptions opt) => this.opt = opt;

    public SolveResult Solve(Instance inst)
    {
        var sw = Stopwatch.StartNew();
        var rng = new Rng(opt.Seed);

        return opt.Variant.ToUpperInvariant() switch
        {
            "H0" => SolveH0(inst, rng, sw),
            "A1" => SolveA1(inst, rng, sw),
            "A2" => SolveA2A3(inst, rng, sw, useLocalSearch: false),
            _ => SolveA2A3(inst, rng, sw, useLocalSearch: true),
        };
    }

    // H0: decoder-only (volume-desc + random sampling)
    private SolveResult SolveH0(Instance inst, Rng rng, Stopwatch sw)
    {
        int n = inst.Items.Count;
        int evals = 0;

        var permVD = Enumerable.Range(0, n).OrderByDescending(i => inst.Items[i].W * inst.Items[i].H * inst.Items[i].D).ToArray();
        var rPlan0 = Enumerable.Repeat(1, n).ToArray();
        var best = decoder.Evaluate(inst, permVD, rPlan0);
        evals++;

        while (sw.Elapsed.TotalSeconds < opt.TimeLimitSec)
        {
            var perm = Enumerable.Range(0, n).ToArray();
            for (int i=n-1;i>0;i--)
            {
                int j = rng.NextInt(0, i+1);
                (perm[i], perm[j]) = (perm[j], perm[i]);
            }
            var rPlan = new int[n];
            for (int i=0;i<n;i++) rPlan[i] = 1 + rng.NextInt(0, 6);

            var res = decoder.Evaluate(inst, perm, rPlan);
            evals++;
            if (res.FitnessF > best.FitnessF) best = res;
        }

        sw.Stop();
        return new SolveResult
        {
            Variant = "H0",
            Seed = opt.Seed,
            TimeSec = sw.Elapsed.TotalSeconds,
            BestV = best.UtilizationV,
            BestF = best.FitnessF,
            BestPlaced = best.PlacedCount,
            Generations = 0,
            Evaluations = evals
        };
    }

    // A1: RK-DE (DE/rand/1)
    private SolveResult SolveA1(Instance inst, Rng rng, Stopwatch sw)
    {
        int n = inst.Items.Count;
        int dim = 2 * n;
        int NP = Math.Max(10, opt.NP);

        var X = new double[NP][];
        var fit = new double[NP];
        var bestV = new double[NP];
        var bestPlaced = new int[NP];

        int evals = 0, gen = 0;

        for (int i=0;i<NP;i++)
        {
            X[i] = new double[dim];
            for (int j=0;j<dim;j++) X[i][j] = rng.NextDouble();

            var dec = DecodeAndEval(inst, X[i]);
            fit[i] = dec.FitnessF;
            bestV[i] = dec.UtilizationV;
            bestPlaced[i] = dec.PlacedCount;
            evals++;
        }

        int bIdx = ArgMax(fit);
        double bestF = fit[bIdx];
        double bestVglob = bestV[bIdx];
        int bestPlacedGlob = bestPlaced[bIdx];

        while (sw.Elapsed.TotalSeconds < opt.TimeLimitSec && gen < opt.MaxGenerations)
        {
            gen++;

            for (int i=0;i<NP;i++)
            {
                int r0, r1, r2;
                do { r0 = rng.NextInt(0, NP); } while (r0 == i);
                do { r1 = rng.NextInt(0, NP); } while (r1 == i || r1 == r0);
                do { r2 = rng.NextInt(0, NP); } while (r2 == i || r2 == r0 || r2 == r1);

                var v = new double[dim];
                for (int j=0;j<dim;j++)
                    v[j] = X[r0][j] + opt.FixedF * (X[r1][j] - X[r2][j]);

                var u = BinCrossover(rng, X[i], v, opt.FixedCR);
                Clamp01(u);

                var decU = DecodeAndEval(inst, u);
                evals++;

                if (decU.FitnessF >= fit[i])
                {
                    X[i] = u;
                    fit[i] = decU.FitnessF;
                    bestV[i] = decU.UtilizationV;
                    bestPlaced[i] = decU.PlacedCount;

                    if (fit[i] > bestF)
                    {
                        bestF = fit[i];
                        bestVglob = bestV[i];
                        bestPlacedGlob = bestPlaced[i];
                    }
                }
            }
        }

        sw.Stop();
        return new SolveResult
        {
            Variant = "A1",
            Seed = opt.Seed,
            TimeSec = sw.Elapsed.TotalSeconds,
            BestV = bestVglob,
            BestF = bestF,
            BestPlaced = bestPlacedGlob,
            Generations = gen,
            Evaluations = evals
        };
    }

    // A2/A3: current-to-pbest + self-adaptive F/CR (+ optional LS)
    private SolveResult SolveA2A3(Instance inst, Rng rng, Stopwatch sw, bool useLocalSearch)
    {
        int n = inst.Items.Count;
        int dim = 2 * n;
        int NP = Math.Max(10, opt.NP);

        var X = new double[NP][];
        var fit = new double[NP];
        var V = new double[NP];
        var placed = new int[NP];
        var Fi = new double[NP];
        var CRi = new double[NP];

        int evals = 0, gen = 0;
        int stagnant = 0;

        for (int i=0;i<NP;i++)
        {
            X[i] = new double[dim];
            for (int j=0;j<dim;j++) X[i][j] = rng.NextDouble();
            Fi[i] = opt.Fl + rng.NextDouble() * (opt.Fu - opt.Fl);
            CRi[i] = rng.NextDouble();

            var dec = DecodeAndEval(inst, X[i]);
            fit[i] = dec.FitnessF; V[i] = dec.UtilizationV; placed[i] = dec.PlacedCount;
            evals++;
        }

        int bIdx = ArgMax(fit);
        double bestF = fit[bIdx];
        double bestV = V[bIdx];
        int bestPlaced = placed[bIdx];

        while (sw.Elapsed.TotalSeconds < opt.TimeLimitSec && gen < opt.MaxGenerations)
        {
            gen++;

            var elite = ElitePool(fit, opt.PbestFrac);

            for (int i=0;i<NP;i++)
            {
                if (rng.NextDouble() < opt.Tau1) Fi[i] = opt.Fl + rng.NextDouble() * (opt.Fu - opt.Fl);
                if (rng.NextDouble() < opt.Tau2) CRi[i] = rng.NextDouble();

                int pbest = elite[rng.NextInt(0, elite.Length)];
                int r1, r2;
                do { r1 = rng.NextInt(0, NP); } while (r1 == i || r1 == pbest);
                do { r2 = rng.NextInt(0, NP); } while (r2 == i || r2 == pbest || r2 == r1);

                var v = new double[dim];
                for (int j=0;j<dim;j++)
                    v[j] = X[i][j] + Fi[i] * (X[pbest][j] - X[i][j]) + Fi[i] * (X[r1][j] - X[r2][j]);

                var u = BinCrossover(rng, X[i], v, CRi[i]);
                Clamp01(u);

                var decU = DecodeAndEval(inst, u);
                evals++;

                if (decU.FitnessF >= fit[i])
                {
                    X[i] = u;
                    fit[i] = decU.FitnessF;
                    V[i] = decU.UtilizationV;
                    placed[i] = decU.PlacedCount;
                }
            }

            if (useLocalSearch && sw.Elapsed.TotalSeconds < opt.TimeLimitSec)
            {
                int K = Math.Max(1, (int)Math.Ceiling(opt.LocalSearchTopFrac * NP));
                var top = TopKIndices(fit, K);

                foreach (var idx in top)
                {
                    if (sw.Elapsed.TotalSeconds >= opt.TimeLimitSec) break;

                    var improved = LocalSearchOne(inst, rng, X[idx], fit[idx], opt.LocalSearchMoves, out var newX, out var newFit, out var newV, out var newPlaced, ref evals);
                    if (improved)
                    {
                        X[idx] = newX;
                        fit[idx] = newFit;
                        V[idx] = newV;
                        placed[idx] = newPlaced;
                    }
                }
            }

            int curBest = ArgMax(fit);
            if (fit[curBest] > bestF + 1e-15)
            {
                bestF = fit[curBest];
                bestV = V[curBest];
                bestPlaced = placed[curBest];
                stagnant = 0;
            }
            else stagnant++;

            if (stagnant >= opt.StagnationGens && opt.RestartWorstFrac > 0)
            {
                int m = Math.Max(1, (int)Math.Floor(opt.RestartWorstFrac * NP));
                var worst = BottomKIndices(fit, m);
                foreach (var wi in worst)
                {
                    for (int j=0;j<dim;j++) X[wi][j] = rng.NextDouble();
                    Fi[wi] = opt.Fl + rng.NextDouble() * (opt.Fu - opt.Fl);
                    CRi[wi] = rng.NextDouble();
                    var dec = DecodeAndEval(inst, X[wi]);
                    fit[wi] = dec.FitnessF; V[wi] = dec.UtilizationV; placed[wi] = dec.PlacedCount;
                    evals++;
                }
                stagnant = 0;
            }
        }

        sw.Stop();
        return new SolveResult
        {
            Variant = useLocalSearch ? "A3" : "A2",
            Seed = opt.Seed,
            TimeSec = sw.Elapsed.TotalSeconds,
            BestV = bestV,
            BestF = bestF,
            BestPlaced = bestPlaced,
            Generations = gen,
            Evaluations = evals
        };
    }

    // ---------- Local search ----------
    private bool LocalSearchOne(Instance inst, Rng rng, double[] x, double curFit, int moves,
                               out double[] bestX, out double bestFit, out double bestV, out int bestPlaced,
                               ref int evals)
    {
        int n = inst.Items.Count;

        bestX = (double[])x.Clone();
        bestFit = curFit;

        DecodeKeys(bestX, n, out var perm, out var rPlan);
        var dec0 = decoder.Evaluate(inst, perm, rPlan);
        bestV = dec0.UtilizationV;
        bestPlaced = dec0.PlacedCount;

        bool improved = false;

        for (int t=0;t<moves;t++)
        {
            var perm2 = (int[])perm.Clone();
            var r2 = (int[])rPlan.Clone();

            int op = rng.NextInt(0, 4);

            if (op == 0) // swap
            {
                int i = rng.NextInt(0, n);
                int j = rng.NextInt(0, n);
                (perm2[i], perm2[j]) = (perm2[j], perm2[i]);
            }
            else if (op == 1) // insert
            {
                int from = rng.NextInt(0, n);
                int to = rng.NextInt(0, n);
                if (from != to)
                {
                    var list = perm2.ToList();
                    int val = list[from];
                    list.RemoveAt(from);
                    list.Insert(to, val);
                    perm2 = list.ToArray();
                }
            }
            else if (op == 2) // short reversal
            {
                int a = rng.NextInt(0, n);
                int b = rng.NextInt(0, n);
                if (a > b) (a, b) = (b, a);
                int len = b - a + 1;
                if (len >= 2 && len <= Math.Min(12, n))
                    Array.Reverse(perm2, a, len);
            }
            else // orientation change
            {
                int k = rng.NextInt(0, n);
                int newR;
                do { newR = 1 + rng.NextInt(0, 6); } while (newR == r2[k]);
                r2[k] = newR;
            }

            var cand = (double[])bestX.Clone();
            Reencode(cand, perm2, r2);

            var dec = DecodeAndEval(inst, cand);
            evals++;

            if (dec.FitnessF > bestFit + 1e-15)
            {
                bestX = cand;
                bestFit = dec.FitnessF;
                bestV = dec.UtilizationV;
                bestPlaced = dec.PlacedCount;

                perm = perm2;
                rPlan = r2;
                improved = true;
            }
        }

        return improved;
    }

    // ---------- Decode / Re-encode ----------
    private DecoderResult DecodeAndEval(Instance inst, double[] x)
    {
        int n = inst.Items.Count;
        DecodeKeys(x, n, out var perm, out var rPlan);
        return decoder.Evaluate(inst, perm, rPlan);
    }

    private static void DecodeKeys(double[] x, int n, out int[] perm, out int[] rPlan)
    {
        var keys = new (double key, int idx)[n];
        rPlan = new int[n];

        for (int i=0;i<n;i++)
        {
            keys[i] = (x[i], i);
            rPlan[i] = Orientation.KeyToR(x[n + i]);
        }

        Array.Sort(keys, (a,b) => a.key.CompareTo(b.key));
        perm = new int[n];
        for (int p=0;p<n;p++) perm[p] = keys[p].idx;
    }

    private static void Reencode(double[] x, int[] perm, int[] rPlan)
    {
        int n = perm.Length;

        var pos = new int[n];
        for (int p=0;p<n;p++) pos[perm[p]] = p;

        for (int i=0;i<n;i++)
            x[i] = (pos[i] + 1.0) / (n + 1.0);

        for (int i=0;i<n;i++)
            x[n + i] = Orientation.RToKey(rPlan[i]);
    }

    // ---------- DE utils ----------
    private static double[] BinCrossover(Rng rng, double[] x, double[] v, double cr)
    {
        int dim = x.Length;
        var u = new double[dim];
        int jrand = rng.NextInt(0, dim);

        for (int j=0;j<dim;j++)
            u[j] = (rng.NextDouble() < cr || j == jrand) ? v[j] : x[j];

        return u;
    }

    private static void Clamp01(double[] u)
    {
        for (int j=0;j<u.Length;j++)
            u[j] = Math.Clamp(u[j], 0.0, 1.0);
    }

    // ---------- Ranking helpers ----------
    private static int ArgMax(double[] a)
    {
        int best = 0;
        for (int i=1;i<a.Length;i++) if (a[i] > a[best]) best = i;
        return best;
    }

    private static int[] ElitePool(double[] fit, double pfrac)
    {
        int n = fit.Length;
        int k = Math.Max(2, (int)Math.Ceiling(pfrac * n));
        var idx = Enumerable.Range(0, n).ToArray();
        Array.Sort(idx, (i,j) => fit[j].CompareTo(fit[i]));
        return idx.Take(k).ToArray();
    }

    private static int[] TopKIndices(double[] fit, int k)
    {
        var idx = Enumerable.Range(0, fit.Length).ToArray();
        Array.Sort(idx, (i,j) => fit[j].CompareTo(fit[i]));
        return idx.Take(k).ToArray();
    }

    private static int[] BottomKIndices(double[] fit, int k)
    {
        var idx = Enumerable.Range(0, fit.Length).ToArray();
        Array.Sort(idx, (i,j) => fit[i].CompareTo(fit[j]));
        return idx.Take(k).ToArray();
    }
}

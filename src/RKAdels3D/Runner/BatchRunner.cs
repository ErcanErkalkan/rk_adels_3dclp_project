using System.Globalization;
using RKAdels3D.Core;
using RKAdels3D.IO;

namespace RKAdels3D.Runner;

public sealed class BatchRunner
{
    public void Run(string folder, string outDir, int baseSeed, string variant, int trials, double timeLimitSec, int np)
    {
        if (!Directory.Exists(folder)) throw new DirectoryNotFoundException(folder);

        var files = Directory.GetFiles(folder, "*.json", SearchOption.TopDirectoryOnly)
            .OrderBy(x => x, StringComparer.OrdinalIgnoreCase)
            .ToArray();

        if (files.Length == 0)
        {
            Console.WriteLine($"No *.json instances found in {folder}");
            return;
        }

        var perRunPath = Path.Combine(outDir, "per_run.csv");
        var summaryPath = Path.Combine(outDir, "summary.csv");

        var perRun = new List<string>
        {
            "instance,variant,trial,seed,np,timeLimitSec,bestV,bestF,bestPlaced,timeSec,gens,evals"
        };

        foreach (var f in files)
        {
            var inst = InstanceLoader.Load(f);
            Console.WriteLine($"Running: {inst.Name} (n={inst.Items.Count})");

            for (int t=0;t<trials;t++)
            {
                int seed = baseSeed + t;
                var opts = SolverOptions.Default(seed, timeLimitSec, np, variant);
                var solver = new RKAdelsSolver(opts);

                var res = solver.Solve(inst);

                perRun.Add(string.Join(",",
                    Esc(inst.Name), variant, t, seed, np,
                    timeLimitSec.ToString(CultureInfo.InvariantCulture),
                    res.BestV.ToString(CultureInfo.InvariantCulture),
                    res.BestF.ToString(CultureInfo.InvariantCulture),
                    res.BestPlaced,
                    res.TimeSec.ToString(CultureInfo.InvariantCulture),
                    res.Generations,
                    res.Evaluations
                ));

                Console.WriteLine($"  trial {t}: V={res.BestV:F6}, placed={res.BestPlaced}, time={res.TimeSec:F2}s");
            }
        }

        File.WriteAllLines(perRunPath, perRun);

        // Summarize
        var rows = perRun.Skip(1).Select(ParseRow).ToList();
        var groups = rows.GroupBy(r => (r.instance, r.variant));

        var summary = new List<string>
        {
            "instance,variant,trials,np,timeLimitSec,meanV,stdV,bestV,meanTimeSec,meanPlaced"
        };

        foreach (var g in groups.OrderBy(g => g.Key.instance).ThenBy(g => g.Key.variant))
        {
            var arrV = g.Select(x => x.bestV).ToArray();
            var arrT = g.Select(x => x.timeSec).ToArray();
            var arrP = g.Select(x => x.bestPlaced).ToArray();

            double meanV = arrV.Average();
            double stdV = Std(arrV);
            double bestV = arrV.Max();
            double meanT = arrT.Average();
            double meanP = arrP.Average();

            summary.Add(string.Join(",",
                Esc(g.Key.instance), g.Key.variant, g.Count(), g.First().np,
                g.First().timeLimitSec.ToString(CultureInfo.InvariantCulture),
                meanV.ToString(CultureInfo.InvariantCulture),
                stdV.ToString(CultureInfo.InvariantCulture),
                bestV.ToString(CultureInfo.InvariantCulture),
                meanT.ToString(CultureInfo.InvariantCulture),
                meanP.ToString(CultureInfo.InvariantCulture)
            ));
        }

        File.WriteAllLines(summaryPath, summary);
    }

    private sealed record Row(string instance, string variant, int np, double timeLimitSec, double bestV, double timeSec, int bestPlaced);

    private static Row ParseRow(string line)
    {
        var parts = SplitCsv(line);
        return new Row(
            instance: parts[0],
            variant: parts[1],
            np: int.Parse(parts[4]),
            timeLimitSec: double.Parse(parts[5], CultureInfo.InvariantCulture),
            bestV: double.Parse(parts[6], CultureInfo.InvariantCulture),
            timeSec: double.Parse(parts[9], CultureInfo.InvariantCulture),
            bestPlaced: int.Parse(parts[8])
        );
    }

    private static double Std(double[] x)
    {
        if (x.Length <= 1) return 0.0;
        double m = x.Average();
        double s = 0.0;
        foreach (var v in x) s += (v - m) * (v - m);
        return Math.Sqrt(s / (x.Length - 1));
    }

    private static string Esc(string s)
    {
        if (s.Contains(',') || s.Contains('"'))
            return """ + s.Replace(""", """") + """;
        return s;
    }

    private static List<string> SplitCsv(string line)
    {
        var res = new List<string>();
        bool inQ = false;
        var cur = new System.Text.StringBuilder();

        for (int i=0;i<line.Length;i++)
        {
            char c = line[i];
            if (c == '"')
            {
                if (inQ && i+1 < line.Length && line[i+1] == '"')
                {
                    cur.Append('"');
                    i++;
                }
                else inQ = !inQ;
            }
            else if (c == ',' && !inQ)
            {
                res.Add(cur.ToString());
                cur.Clear();
            }
            else cur.Append(c);
        }
        res.Add(cur.ToString());
        return res;
    }
}

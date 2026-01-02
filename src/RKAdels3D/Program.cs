using RKAdels3D.Core;
using RKAdels3D.IO;
using RKAdels3D.Runner;

static int GetIntArg(Dictionary<string,string> args, string key, int def)
    => args.TryGetValue(key, out var v) && int.TryParse(v, out var x) ? x : def;
static double GetDoubleArg(Dictionary<string,string> args, string key, double def)
    => args.TryGetValue(key, out var v) && double.TryParse(v, out var x) ? x : def;
static string GetStrArg(Dictionary<string,string> args, string key, string def)
    => args.TryGetValue(key, out var v) ? v : def;
static bool HasArg(Dictionary<string,string> args, string key) => args.ContainsKey(key);

var parsed = Cli.Parse(args);

if (HasArg(parsed, "--instance"))
{
    var path = GetStrArg(parsed, "--instance", "");
    var inst = InstanceLoader.Load(path);

    var seed = GetIntArg(parsed, "--seed", 42);
    var variant = GetStrArg(parsed, "--variant", "A3");
    var timeLimitSec = GetDoubleArg(parsed, "--timeLimitSec", 30);
    var np = GetIntArg(parsed, "--np", 80);

    var opts = SolverOptions.Default(seed, timeLimitSec, np, variant);

    var solver = new RKAdelsSolver(opts);
    var res = solver.Solve(inst);

    Console.WriteLine(res.ToPrettyString(inst.Name));
    return 0;
}

if (HasArg(parsed, "--batch"))
{
    var folder = GetStrArg(parsed, "--batch", "");
    var outDir = GetStrArg(parsed, "--out", "results");
    var seed = GetIntArg(parsed, "--seed", 1337);
    var variant = GetStrArg(parsed, "--variant", "A3");
    var trials = GetIntArg(parsed, "--trials", 10);
    var timeLimitSec = GetDoubleArg(parsed, "--timeLimitSec", 30);
    var np = GetIntArg(parsed, "--np", 80);

    Directory.CreateDirectory(outDir);

    var batch = new BatchRunner();
    batch.Run(folder, outDir, seed, variant, trials, timeLimitSec, np);

    Console.WriteLine($"Batch complete. Results written to: {Path.GetFullPath(outDir)}");
    return 0;
}

Console.WriteLine("Usage:\n" +
"  --instance <path.json> [--variant H0|A1|A2|A3] [--seed N] [--timeLimitSec S] [--np NP]\n" +
"  --batch <folder> --out <outdir> [--variant ...] [--trials R] [--seed N] [--timeLimitSec S] [--np NP]\n");
return 0;

namespace RKAdels3D.Core;

public sealed class SolverOptions
{
    public int Seed { get; init; } = 42;
    public double TimeLimitSec { get; init; } = 30;
    public int NP { get; init; } = 80;
    public int MaxGenerations { get; init; } = int.MaxValue;

    public string Variant { get; init; } = "A3"; // H0, A1, A2, A3
    public double PbestFrac { get; init; } = 0.2;

    // A1 fixed DE params
    public double FixedF { get; init; } = 0.6;
    public double FixedCR { get; init; } = 0.9;

    // A2/A3 self-adaptive params
    public double Fl { get; init; } = 0.1;
    public double Fu { get; init; } = 0.9;
    public double Tau1 { get; init; } = 0.1;
    public double Tau2 { get; init; } = 0.1;

    // A3 local search
    public int LocalSearchMoves { get; init; } = 30;
    public double LocalSearchTopFrac { get; init; } = 0.1;

    // optional restart
    public int StagnationGens { get; init; } = 50;
    public double RestartWorstFrac { get; init; } = 0.2;

    public static SolverOptions Default(int seed, double timeLimitSec, int np, string variant)
        => new() { Seed = seed, TimeLimitSec = timeLimitSec, NP = np, Variant = variant };
}

public sealed class SolveResult
{
    public string Variant { get; init; } = "A3";
    public int Seed { get; init; }
    public double TimeSec { get; init; }
    public double BestV { get; init; }
    public double BestF { get; init; }
    public int BestPlaced { get; init; }
    public int Generations { get; init; }
    public int Evaluations { get; init; }

    public string ToPrettyString(string name) =>
        $"Instance: {name}\nVariant: {Variant}\nSeed: {Seed}\nTime(s): {TimeSec:F3}\nBest V: {BestV:F6}\nBest placed: {BestPlaced}\nEvals: {Evaluations}\nGens: {Generations}";
}

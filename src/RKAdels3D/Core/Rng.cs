namespace RKAdels3D.Core;

public sealed class Rng
{
    private readonly Random r;
    public Rng(int seed) { r = new Random(seed); }
    public double NextDouble() => r.NextDouble();
    public int NextInt(int loInclusive, int hiExclusive) => r.Next(loInclusive, hiExclusive);
}

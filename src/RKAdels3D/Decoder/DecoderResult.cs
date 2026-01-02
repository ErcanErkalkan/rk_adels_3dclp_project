namespace RKAdels3D.Decoder;

using RKAdels3D.Core;

public sealed class DecoderResult
{
    public double UtilizationV { get; init; }
    public int PlacedCount { get; init; }
    public double Hmax { get; init; }
    public double Dmax { get; init; }
    public double FitnessF { get; init; }
    public List<Placement> Placements { get; init; } = new();
}

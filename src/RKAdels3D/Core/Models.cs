namespace RKAdels3D.Core;

public sealed record Container(double W, double H, double D);

public sealed record Item(int Id, double W, double H, double D);

public sealed record OrientedDims(double W, double H, double D);

public sealed record Placement(int ItemId, int R, double X, double Y, double Z, double W, double H, double D);

public sealed class Instance
{
    public string Name { get; init; } = "instance";
    public Container Container { get; init; } = new Container(1,1,1);
    public List<Item> Items { get; init; } = new();
}

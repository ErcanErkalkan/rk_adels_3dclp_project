using System.Text.Json;
using RKAdels3D.Core;

namespace RKAdels3D.IO;

public static class InstanceLoader
{
    private sealed class InstanceJson
    {
        public string? name { get; set; }
        public ContainerJson? container { get; set; }
        public List<ItemJson>? items { get; set; }
    }

    private sealed class ContainerJson { public double W { get; set; } public double H { get; set; } public double D { get; set; } }

    private sealed class ItemJson { public int id { get; set; } public double w { get; set; } public double h { get; set; } public double d { get; set; } public int? qty { get; set; } }

    public static Instance Load(string path)
    {
        if (!File.Exists(path)) throw new FileNotFoundException(path);
        var json = File.ReadAllText(path);
        var obj = JsonSerializer.Deserialize<InstanceJson>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
                  ?? throw new Exception("Invalid JSON instance.");

        if (obj.container is null) throw new Exception("Missing container.");
        if (obj.items is null || obj.items.Count == 0) throw new Exception("Missing items.");

        var inst = new Instance
        {
            Name = obj.name ?? Path.GetFileNameWithoutExtension(path),
            Container = new Container(obj.container.W, obj.container.H, obj.container.D),
        };

        int nextId = 1;
        foreach (var it in obj.items)
        {
            int id = it.id != 0 ? it.id : nextId++;
            int q = Math.Max(1, it.qty ?? 1);
            for (int k=0;k<q;k++)
                inst.Items.Add(new Item(id*1000 + k, it.w, it.h, it.d));
        }

        // Re-index sequentially for internal use
        for (int i=0;i<inst.Items.Count;i++)
            inst.Items[i] = inst.Items[i] with { Id = i };

        return inst;
    }
}

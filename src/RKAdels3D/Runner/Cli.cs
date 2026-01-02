namespace RKAdels3D.Runner;

public static class Cli
{
    public static Dictionary<string,string> Parse(string[] args)
    {
        var d = new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
        for (int i=0;i<args.Length;i++)
        {
            var a = args[i];
            if (!a.StartsWith("--")) continue;
            if (i==args.Length-1 || args[i+1].StartsWith("--"))
            {
                d[a] = "true";
            }
            else
            {
                d[a] = args[i+1];
                i++;
            }
        }
        return d;
    }
}

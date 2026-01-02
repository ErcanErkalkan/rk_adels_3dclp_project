using RKAdels3D.Core;

namespace RKAdels3D.Decoder;

public sealed class WallHeightmapDecoder
{
    private readonly double epsP;
    private readonly double epsH;
    private readonly double epsD;

    public WallHeightmapDecoder(double epsP = 1e-4, double epsH = 1e-6, double epsD = 1e-6)
    {
        this.epsP = epsP;
        this.epsH = epsH;
        this.epsD = epsD;
    }

    public DecoderResult Evaluate(Instance inst, int[] perm, int[] rPlan)
    {
        var W = inst.Container.W;
        var H = inst.Container.H;
        var D = inst.Container.D;
        var items = inst.Items;
        int n = items.Count;

        var placements = new List<Placement>(n);

        // breakpoints and envelope grid
        var X = new List<double>() { 0.0, W };
        var Z = new List<double>() { 0.0, D };
        double[,] S = new double[1, 1]; // one cell with height 0

        double volPlaced = 0.0;
        double dMax = 0.0;
        double hMax = 0.0;

        int FindInterval(List<double> brk, double coord, double upper)
        {
            coord = Math.Clamp(coord, brk[0], upper - 1e-12);
            int lo = 0, hi = brk.Count - 2;
            while (lo <= hi)
            {
                int mid = (lo + hi) >> 1;
                if (coord < brk[mid]) hi = mid - 1;
                else if (coord >= brk[mid + 1]) lo = mid + 1;
                else return mid;
            }
            return Math.Clamp(lo, 0, brk.Count - 2);
        }

        double GetMaxHeight(double x0, double x1, double z0, double z1)
        {
            if (x1 <= x0 || z1 <= z0) return 0.0;
            int xi0 = FindInterval(X, x0 + 1e-12, W);
            int xi1 = FindInterval(X, x1 - 1e-12, W);
            int zi0 = FindInterval(Z, z0 + 1e-12, D);
            int zi1 = FindInterval(Z, z1 - 1e-12, D);

            double m = 0.0;
            for (int a = xi0; a <= xi1; a++)
                for (int b = zi0; b <= zi1; b++)
                    if (S[a, b] > m) m = S[a, b];
            return m;
        }

        void RebuildGrid(List<double> newX, List<double> newZ, List<double> oldX, List<double> oldZ, double[,] oldS)
        {
            int nx = newX.Count - 1;
            int nz = newZ.Count - 1;
            var newS = new double[nx, nz];

            for (int a = 0; a < nx; a++)
            {
                double xmid = 0.5 * (newX[a] + newX[a + 1]);
                int ao = FindInterval(oldX, xmid, W);
                for (int b = 0; b < nz; b++)
                {
                    double zmid = 0.5 * (newZ[b] + newZ[b + 1]);
                    int bo = FindInterval(oldZ, zmid, D);
                    newS[a, b] = oldS[ao, bo];
                }
            }

            X = newX;
            Z = newZ;
            S = newS;
        }

        void InsertBreakpoints(double x0, double x1, double z0, double z1)
        {
            bool changed = false;

            if (!X.Contains(x0)) { X.Add(x0); changed = true; }
            if (!X.Contains(x1)) { X.Add(x1); changed = true; }
            if (!Z.Contains(z0)) { Z.Add(z0); changed = true; }
            if (!Z.Contains(z1)) { Z.Add(z1); changed = true; }

            if (!changed) return;

            var oldX = new List<double>(X);
            var oldZ = new List<double>(Z);
            var oldS = (double[,])S.Clone();

            X.Sort();
            Z.Sort();
            if (X[0] != 0.0) X.Insert(0, 0.0);
            if (X[^1] != W) X.Add(W);
            if (Z[0] != 0.0) Z.Insert(0, 0.0);
            if (Z[^1] != D) Z.Add(D);

            RebuildGrid(X, Z, oldX, oldZ, oldS);
        }

        void SetFootprint(double x0, double x1, double z0, double z1, double newHeight)
        {
            int xi0 = FindInterval(X, x0 + 1e-12, W);
            int xi1 = FindInterval(X, x1 - 1e-12, W);
            int zi0 = FindInterval(Z, z0 + 1e-12, D);
            int zi1 = FindInterval(Z, z1 - 1e-12, D);

            for (int a = xi0; a <= xi1; a++)
                for (int b = zi0; b <= zi1; b++)
                    S[a, b] = newHeight;
        }

        // evaluate items
        foreach (var idx in perm)
        {
            var it = items[idx];
            int r = rPlan[idx];
            var od = Orientation.Apply(it, r);

            // candidate coordinates
            var Xc = new HashSet<double>() { 0.0 };
            var Zc = new HashSet<double>() { 0.0 };
            foreach (var pl in placements)
            {
                Xc.Add(pl.X + pl.W);
                Zc.Add(pl.Z + pl.D);
            }

            (double x, double y, double z, double hmaxPrime, double dmaxPrime)? best = null;

            foreach (var x in Xc)
            {
                if (x + od.W > W + 1e-12) continue;
                foreach (var z in Zc)
                {
                    if (z + od.D > D + 1e-12) continue;

                    double y = GetMaxHeight(x, x + od.W, z, z + od.D);
                    if (y + od.H > H + 1e-12) continue;

                    double hmaxPrime = Math.Max(hMax, y + od.H);
                    double dmaxPrime = Math.Max(dMax, z + od.D);

                    if (best is null)
                    {
                        best = (x, y, z, hmaxPrime, dmaxPrime);
                    }
                    else
                    {
                        var cur = best.Value;
                        bool better =
                            (y < cur.y - 1e-12) ||
                            (Math.Abs(y - cur.y) <= 1e-12 && z < cur.z - 1e-12) ||
                            (Math.Abs(y - cur.y) <= 1e-12 && Math.Abs(z - cur.z) <= 1e-12 && x < cur.x - 1e-12) ||
                            (Math.Abs(y - cur.y) <= 1e-12 && Math.Abs(z - cur.z) <= 1e-12 && Math.Abs(x - cur.x) <= 1e-12 && hmaxPrime < cur.hmaxPrime - 1e-12);

                        if (better) best = (x, y, z, hmaxPrime, dmaxPrime);
                    }
                }
            }

            if (best is not null)
            {
                var b = best.Value;

                InsertBreakpoints(b.x, b.x + od.W, b.z, b.z + od.D);
                SetFootprint(b.x, b.x + od.W, b.z, b.z + od.D, b.y + od.H);

                placements.Add(new Placement(it.Id, r, b.x, b.y, b.z, od.W, od.H, od.D));
                volPlaced += od.W * od.H * od.D;

                hMax = Math.Max(hMax, b.y + od.H);
                dMax = Math.Max(dMax, b.z + od.D);
            }
        }

        // compute Hmax from grid
        double HmaxGrid = 0.0;
        for (int a=0;a<S.GetLength(0);a++)
            for (int b=0;b<S.GetLength(1);b++)
                if (S[a,b] > HmaxGrid) HmaxGrid = S[a,b];
        hMax = Math.Max(hMax, HmaxGrid);

        double V = volPlaced / (W * H * D);
        int placedCount = placements.Count;

        double f = V + epsP * (placedCount / (double)n) - epsH * (hMax / H) - epsD * (dMax / D);

        return new DecoderResult
        {
            UtilizationV = V,
            PlacedCount = placedCount,
            Hmax = hMax,
            Dmax = dMax,
            FitnessF = f,
            Placements = placements
        };
    }
}

namespace RKAdels3D.Core;

public static class Orientation
{
    public static OrientedDims Apply(Item it, int r)
    {
        var w = it.W; var h = it.H; var d = it.D;
        return r switch
        {
            1 => new OrientedDims(w,h,d),
            2 => new OrientedDims(w,d,h),
            3 => new OrientedDims(h,w,d),
            4 => new OrientedDims(h,d,w),
            5 => new OrientedDims(d,w,h),
            6 => new OrientedDims(d,h,w),
            _ => new OrientedDims(w,h,d),
        };
    }

    public static int KeyToR(double o)
    {
        var idx = (int)Math.Floor(6.0 * Math.Clamp(o, 0.0, 0.999999999));
        idx = Math.Clamp(idx, 0, 5);
        return 1 + idx;
    }

    public static double RToKey(int r)
    {
        r = Math.Clamp(r, 1, 6);
        return (r - 0.5) / 6.0; // center of the bin
    }
}

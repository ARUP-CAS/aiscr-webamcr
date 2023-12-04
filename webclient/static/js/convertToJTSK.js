function convertToJTSK(long,lat) {
    function sqr(x) {
        return x * x;
    }
    var d2r = Math.PI / 180;
    var a = 6378137.0;
    var f1 = 298.257223563;
    var dx = -570.69;
    var dy = -85.69;
    var dz = -462.84;
    var wx = 4.99821 / 3600 * Math.PI / 180;
    var wy = 1.58676 / 3600 * Math.PI / 180;
    var wz = 5.2611 / 3600 * Math.PI / 180;
    var m = -3.543e-6;

    var B = lat * d2r;
    var L = long * d2r;
    var H = 400;

    var e2 = 1 - sqr(1 - 1 / f1);
    var rho = a / Math.sqrt(1 - e2 * sqr(Math.sin(B)));
    var x1 = (rho + H) * Math.cos(B) * Math.cos(L);
    var y1 = (rho + H) * Math.cos(B) * Math.sin(L);
    var z1 = ((1 - e2) * rho + H) * Math.sin(B);

    var x2 = dx + (1 + m) * (x1 + wz * y1 - wy * z1);
    var y2 = dy + (1 + m) * (-wz * x1 + y1 + wx * z1);
    var z2 = dz + (1 + m) * (wy * x1 - wx * y1 + z1);

    a = 6377397.15508;
    f1 = 299.152812853;
    var ab = f1 / (f1 - 1);
    var p = Math.sqrt(sqr(x2) + sqr(y2));
    e2 = 1 - sqr(1 - 1 / f1);
    var th = Math.atan(z2 * ab / p);
    var st = Math.sin(th);
    var ct = Math.cos(th);
    var t = (z2 + e2 * ab * a * (st * st * st)) / (p - e2 * a * (ct * ct * ct));

    B = Math.atan(t);
    H = Math.sqrt(1 + t * t) * (p - a / Math.sqrt(1 + (1 - e2) * t * t));
    L = 2 * Math.atan(y2 / (p + x2));

    a = 6377397.15508;
    var e = 0.081696831215303;
    var n = 0.97992470462083;
    var rho0 = 12310230.12797036;
    var sinUQ = 0.863499969506341;
    var cosUQ = 0.504348889819882;
    var sinVQ = 0.420215144586493;
    var cosVQ = 0.907424504992097;
    var alpha = 1.000597498371542;
    var k2 = 1.00685001861538;

    var sinB = Math.sin(B);
    t = (1 - e * sinB) / (1 + e * sinB);
    t = sqr(1 + sinB) / (1 - sqr(sinB)) * Math.exp(e * Math.log(t));
    t = k2 * Math.exp(alpha * Math.log(t));

    var sinU = (t - 1) / (t + 1);
    var cosU = Math.sqrt(1 - sinU * sinU);
    var V = alpha * L;
    var sinV = Math.sin(V);
    var cosV = Math.cos(V);
    var cosDV = cosVQ * cosV + sinVQ * sinV;
    var sinDV = sinVQ * cosV - cosVQ * sinV;
    var sinS = sinUQ * sinU + cosUQ * cosU * cosDV;
    var cosS = Math.sqrt(1 - sinS * sinS);
    var sinD = sinDV * cosU / cosS;
    var cosD = Math.sqrt(1 - sinD * sinD);

    var eps = n * Math.atan(sinD / cosD);
    rho = rho0 * Math.exp(-n * Math.log((1 + sinS) / cosS));

    return [-1*rho * Math.sin(eps), -1*rho * Math.cos(eps)]
}

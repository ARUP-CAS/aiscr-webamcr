import math


def square(x):
    return math.pow(x, 2)


def convertToJTSK(lat, long):
    d2r = math.pi / 180
    a = 6378137.0
    f1 = 298.257223563
    dx = -570.69
    dy = -85.69
    dz = -462.84
    wx = 4.99821 / 3600 * math.pi / 180
    wy = 1.58676 / 3600 * math.pi / 180
    wz = 5.2611 / 3600 * math.pi / 180
    m = -3.543e-6

    B = lat * d2r
    L = long * d2r
    H = 400

    e2 = 1 - square(1 - 1 / f1)
    rho = a / math.sqrt(1 - e2 * square(math.sin(B)))
    x1 = (rho + H) * math.cos(B) * math.cos(L)
    y1 = (rho + H) * math.cos(B) * math.sin(L)
    z1 = ((1 - e2) * rho + H) * math.sin(B)

    x2 = dx + (1 + m) * (x1 + wz * y1 - wy * z1)
    y2 = dy + (1 + m) * (-wz * x1 + y1 + wx * z1)
    z2 = dz + (1 + m) * (wy * x1 - wx * y1 + z1)

    a = 6377397.15508
    f1 = 299.152812853
    ab = f1 / (f1 - 1)
    p = math.sqrt(square(x2) + square(y2))
    e2 = 1 - square(1 - 1 / f1)
    th = math.atan(z2 * ab / p)
    st = math.sin(th)
    ct = math.cos(th)
    t = (z2 + e2 * ab * a * (st * st * st)) / (p - e2 * a * (ct * ct * ct))

    B = math.atan(t)
    H = math.sqrt(1 + t * t) * (p - a / math.sqrt(1 + (1 - e2) * t * t))
    L = 2 * math.atan(y2 / (p + x2))

    a = 6377397.15508
    e = 0.081696831215303
    n = 0.97992470462083
    rho0 = 12310230.12797036
    sinUQ = 0.863499969506341
    cosUQ = 0.504348889819882
    sinVQ = 0.420215144586493
    cosVQ = 0.907424504992097
    alpha = 1.000597498371542
    k2 = 1.00685001861538

    sinB = math.sin(B)
    t = (1 - e * sinB) / (1 + e * sinB)
    t = square(1 + sinB) / (1 - square(sinB)) * math.exp(e * math.log(t))
    t = k2 * math.exp(alpha * math.log(t))

    sinU = (t - 1) / (t + 1)
    cosU = math.sqrt(1 - sinU * sinU)
    V = alpha * L
    sinV = math.sin(V)
    cosV = math.cos(V)
    cosDV = cosVQ * cosV + sinVQ * sinV
    sinDV = sinVQ * cosV - cosVQ * sinV
    sinS = sinUQ * sinU + cosUQ * cosU * cosDV
    cosS = math.sqrt(1 - sinS * sinS)
    sinD = sinDV * cosU / cosS
    cosD = math.sqrt(1 - sinD * sinD)

    eps = n * math.atan(sinD / cosD)
    rho = rho0 * math.exp(-n * math.log((1 + sinS) / cosS))

    return [rho * math.sin(eps), rho * math.cos(eps)]


def get_multi_transform_to_sjtsk(wgs_points):
    my = []
    for i in wgs_points:
        [x, y] = convertToJTSK(float(i[1]), float(i[0]))
        my.append([str(round(x, 2)), str(round(y, 2))])
    return my

import math
from datetime import date
import os

#načtení tabulky s opravamy  
def readCoef(table):
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    f = open(os.path.join(__location__, 'table_yx_3_v1710.dat') , 'r')
    for line in f: 
        row = line.split()
        table[int(row[0]),int(row[1])]=(float(row[2]),float(row[3]))  
    f.close()          
      
CORRTABLE={}
readCoef(CORRTABLE)          

     
# Conversion from WGS-84 to JTSK
def convertToJTSK(longitude, latitude, height=0):
    if latitude < 40 or latitude > 60 or longitude < 5 or longitude > 25:
        #return x,y
        return  [0, 0]
    else:
        [latitude, longitude] = wgs84_to_bessel(latitude, longitude)
        [X05,Y05]= bessel_to_jtsk(latitude, longitude)
        [X,Y] = jtsk05_to_jtsk(X05,Y05)
        return [-Y,-X]
    


# Conversion from ellipsoid WGS-84 to Bessel's ellipsoid
def wgs84_to_bessel(latitude, longitude, altitude=0.0):
    b = math.radians(latitude)
    l = math.radians(longitude)
    h = altitude

    [x1, y1, z1] = blht_to_geo_coords(b, l, h)
    [x2, y2, z2] = WGS2ETRFtransform_coords(x1, y1, z1)
    [x3, y3, z3] = ETRF2JTSK05transform_coords(x2, y2, z2)
    [b, l, h] = geo_coords_to_blh(x3, y3, z3)

    latitude = math.degrees(b)
    longitude = math.degrees(l)
    # Altitude = h

    return [latitude, longitude]


# Conversion from Bessel's lat/lon to jtsk05
def bessel_to_jtsk(B, L):
    
    B=math.radians(B)
    L=math.radians(L)
    fi0=math.radians(49.5)
    a=6_377_397.155
    e2=0.00667437223062
    e=e2**0.5
    alfa=(1+(e2*math.cos(fi0)**4)/(1-e2))**0.5
    Uq=math.radians(59+42/60+42.69689/3600)
    U0=math.asin(math.sin(fi0)/alfa)
    gfi0=((1+e*math.sin(fi0))/(1-e*math.sin(fi0)))**(alfa*e/2)
    k=math.tan(U0/2+math.radians(45))*(math.tan(fi0/2+math.radians(45))**-alfa)*gfi0
    k1=0.9999
    N0=(a*(1-e2)**0.5)/(1-e2*math.sin(fi0)**2)
    S0=math.radians(78.5)
    n=math.sin(S0)
    rho_0=k1*N0*(1/math.tan(S0))
    
    gB=((1+e*math.sin(B))/(1-e*math.sin(B)))**(alfa*e/2)
    U=2*(math.atan(k*math.tan(B/2+math.radians(45))**alfa*gB**-1)-math.radians(45))
    lam=L+math.radians(17+40/60)
    
    dV=alfa*(math.radians(42.5)-lam)
    a_c=math.radians(90)-Uq
    
    S=math.asin(math.cos(a_c)*math.sin(U)+math.sin(a_c)*math.cos(U)*math.cos(dV))
    #eps = n * math.atan(sin_d / cos_d)
    D=math.asin(math.cos(U)*math.sin(dV)/math.cos(S))
    eps=n*D
    #rho = rho_0 * math.exp(-n * math.log((1 + sin_s) / cos_s))
    
    rho = rho_0 * (math.tan(S0/2+ math.radians(45))**n)*(math.tan(S/2+math.radians(45))**-n)
    Xc = rho * math.cos(eps)
    Yc= rho * math.sin(eps)
    A1 = 0.2946529277e-01
    A2 = 0.2515965696e-01
    A3 = 0.1193845912e-06
    A4 = -0.4668270147e-06
    A5 = 0.9233980362e-11
    A6 = 0.1523735715e-11
    A7 = 0.1696780024e-17
    A8 = 0.4408314235e-17
    A9 = -0.8331083518e-23
    A10 = -0.3689471323e-23
    
    Yred=Yc-654000.0
    Xred=Xc-1089000.0
    dY=A2+A3*Yred+A4*Xred+2*A5*Yred*Xred+A6*(Xred**2-Yred**2)+A8*Xred*(Xred**2-3*Yred**2)+\
        A7*Yred*(3*Xred**2-Yred**2)-4*A10*Yred*Xred*(Xred**2-Yred**2)+A9*(Xred**4+Yred**4-6*Xred**2*Yred**2)
    dX=A1+A3*Xred-A4*Yred-2*A6*Yred*Xred+A5*(Xred**2-Yred**2)+A7*Xred*(Xred**2-3*Yred**2)-\
        A8*Yred*(3*Xred**2-Yred**2)+4*A9*Yred*Xred*(Xred**2-Yred**2)+A10*(Xred**4+Yred**4-6*Xred**2*Yred**2)
        
    Y05=(Yc-dY)+5000000.0    
    X05=(Xc-dX)+5000000.0
    
    # 785478.581 1032422.386 0
    #5785478.64 6032422.452 0
    return [X05,Y05]


# Conversion from geodetic coordinates to Cartesian coordinates
def blht_to_geo_coords(b, l, h):
    # WGS-84 ellipsoid parameters
    a = 6378137.0
    e2 = 0.006694380022901
    N = a / math.sqrt(1 - e2 * math.pow(math.sin(b), 2))
    x = (N + h) * math.cos(b) * math.cos(l)
    y = (N + h) * math.cos(b) * math.sin(l)
    z = (N * (1 - e2) + h) * math.sin(b)

    return [x, y, z]


# Conversion from Cartesian coordinates to geodetic coordinates
def geo_coords_to_blh(X, Y, Z):
    # Bessel's ellipsoid parameters
    a = 6377397.155
    e2 = 0.00667437223062
    L = math.atan(Y/X)
    B0= math.atan(Z/((X**2+Y**2)**0.5)*(1+e2/(1-e2)))
    i=0
    while(True):
        N1=a/((1-e2*(math.sin(B0)**2))**0.5)
        Hel=((X**2+Y**2)**0.5)/math.cos(B0)-N1
        B=math.atan(Z/((X**2+Y**2)**0.5)*(1-(N1*e2)/(N1+Hel))**-1)
        if(abs( B0-B)<0.00001 or i>50): 
            break
        B0=B
        i+=1
        
    return [B,L,Hel]


# Coordinates transformation
def ETRF2JTSK05transform_coords(xs, ys, zs):
    # coeficients of transformation from WGS-84 to JTSK
    p1 = -572.203
    p2 = -85.328
    p3 = -461.934  
    ro=206264.806
    p5 = 5.24832714/ro
    p6 = 1.52900087/ro
    p7 = 4.97311727/ro
    p4 = -3.5393e-6  

    xn = p1 + (1 + p4) * (+xs + p5 * ys - p6* zs)
    yn = p2 + (1 + p4) * (-p5 * xs + ys + p7 * zs)
    zn = p3 + (1 + p4) * (+p6 * xs - p7 * ys + zs)

    return [xn, yn, zn]

def WGS2ETRFtransform_coords(xs, ys, zs):
    today=date.today()
    epoch=today.year-2000+(today.month-1)/12+(today.day-1)/365.25
    ro=1/3600/180*math.pi/1000
    p1=5.21E-02+1E-04*epoch
    p2=4.93E-02+1E-04*epoch
    p3=-5.85E-02-1.8E-03*epoch
    p4=1.34E-09+8E-11*epoch
    p5=(0.891+0.081*epoch)*ro
    p6=(5.390+0.490*epoch)*ro
    p7=(-8.712-0.792*epoch)*ro

    xn = xs+p1+p4*xs-p7*ys+p6*zs
    yn = ys+p2+p4*ys+p7*xs-p5*zs
    zn = zs+p3+p4*zs-p6*xs+p5*ys
    return [xn, yn, zn]


def jtsk05_to_jtsk(x05,y05):
    x05-=5000000
    y05-=5000000   
    hy=int(y05/2000)*2000
    hx=int(x05/2000)*2000
    try:
        redyx0=CORRTABLE[hy,hx]
        redyx1=CORRTABLE[hy+2000,hx]
        redyx2=CORRTABLE[hy,hx+2000]
        redyx3=CORRTABLE[hy+2000,hx+2000]
    except:
        redyx0=0;
        redyx1=0;
        redyx2=0;
        redyx3=0;
    coefY=(y05-hy)/2000
    coefX=(x05-hx)/2000
    redX1=redyx1[1]*coefY+redyx0[1]*(1-coefY)
    redX2=redyx3[1]*coefY+redyx2[1]*(1-coefY)
    redX=redX1*(1-coefX)+redX2*coefX
    
    redY1=redyx1[0]*coefY+redyx0[0]*(1-coefY)
    redY2=redyx3[0]*coefY+redyx2[0]*(1-coefY)
    redY=redY1*(1-coefX)+redY2*coefX
    
    return[x05-redX,y05-redY]

def get_multi_transform_to_sjtsk(wgs_points):
    my = []
    for i in wgs_points:
        [x1, x2] = convertToJTSK(float(i[0]), float(i[1]))
        my.append([str(round(x1, 2)), str(round(x2, 2))])
    return my

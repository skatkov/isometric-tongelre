"""RD New <-> WGS84 (the usual polynomial approximation, about a meter off) and map projections."""

import math

from config import CX, CY, XMAX, XMIN, YMAX, YMIN

HX, HZ = (XMAX - XMIN) / 2, (YMAX - YMIN) / 2


def wgs_to_rd(lat, lon):
    dp, dl = 0.36 * (lat - 52.15517440), 0.36 * (lon - 5.38720621)
    x = (155000 + 190094.945 * dl - 11832.228 * dp * dl - 114.221 * dp**2 * dl - 32.391 * dl**3 - 0.705 * dp
         - 2.340 * dp**3 * dl - 0.608 * dp * dl**3 - 0.008 * dl**2 + 0.148 * dp**2 * dl**3)
    y = (463000 + 309056.544 * dp + 3638.893 * dl**2 + 73.077 * dp**2 - 157.984 * dp * dl**2 + 59.788 * dp**3
         + 0.433 * dl - 6.439 * dp**2 * dl**2 - 0.032 * dp * dl + 0.092 * dl**4 - 0.054 * dp * dl**4)
    return x, y


def rd_to_wgs(x, y):
    dx, dy = (x - 155000) * 1e-5, (y - 463000) * 1e-5
    n = (3235.65389 * dy - 32.58297 * dx**2 - 0.2475 * dy**2 - 0.84978 * dx**2 * dy - 0.0655 * dy**3 - 0.01709 * dx**2 * dy**2
         - 0.00738 * dx + 0.0053 * dx**4 - 0.00039 * dx**2 * dy**3 + 0.00033 * dx**4 * dy - 0.00012 * dx * dy)
    e = (5260.52916 * dx + 105.94684 * dx * dy + 2.45656 * dx * dy**2 - 0.81885 * dx**3 + 0.05594 * dx * dy**3 - 0.05607 * dx**3 * dy
         + 0.01199 * dy - 0.00256 * dx**3 * dy**2 + 0.00128 * dx * dy**4 + 0.00022 * dy**2 - 0.00022 * dx**2 + 0.00026 * dx**5)
    return 52.15517440 + n / 3600, 5.38720621 + e / 3600


def screen(x, z, h=0.0, look=45):
    """Local meters (x east, z south, h up) to the render's screen meters (u right, v up) for a camera looking `look`
    degrees from north, 30 degrees down (render/scene.js). Works on numbers and numpy arrays alike."""
    a = math.radians(look)
    return x * math.cos(a) + z * math.sin(a), (x * math.sin(a) - z * math.cos(a)) * 0.5 + h * math.cos(math.radians(30))


def rd_to_image(x, y, scale=4, height_m=0.0):
    """Pixel position in the full isometric render of an RD point at a height above ground (see render/scene.js)."""
    width = round(2 * (HX + HZ) / math.sqrt(2) * scale)
    lx, lz = x - CX, CY - y
    u = (lx + lz) / math.sqrt(2)
    v = (lx - lz) / (2 * math.sqrt(2)) + height_m * math.cos(math.radians(30))
    top = (HX + HZ) / math.sqrt(2) * 0.5 + 32
    return u * scale + width / 2, (top - v) * scale

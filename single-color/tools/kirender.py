"""kirender.py : crops of kicad-cli SVG exports (true widths, KiCad colours). render(svg, x0, y0, x1, y1, ppmm) -> PIL image; mm -> pixel: ((x - x0) * ppmm, (y - y0) * ppmm)"""
import pymupdf
from PIL import Image
K = 72 / 25.4
def render(svg, x0, y0, x1, y1, ppmm=300):
    d = pymupdf.open(svg); p = d[0]
    clip = pymupdf.Rect((x0 - 79.0) * K, (y0 - 74.41) * K, (x1 - 79.0) * K, (y1 - 74.41) * K)
    z = ppmm / K
    pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=clip, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

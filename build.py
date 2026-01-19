from pathlib import Path
import tempfile

from PIL import Image

import fontforge
import psMat

CX = 50
CY = CX * 1.2

ASCENT = CX * 2 * 7
BASELINE = 2
DESCENT = CX * 2 * BASELINE
SIDE = CX

NO_LEFT = set(' .,;:-!|ijst')
NO_RIGHT = set('rf')

SUBST = {'\\': '/', '.': '.', ';': ':'}

OUT = 'Cosm.ttf'

KAPPA = 0.5522847498307936

def main():
    font = fontforge.font()

    font.encoding = 'UnicodeFull'
    font.ascent = ASCENT
    font.descent = DESCENT
    font.familyname = 'Cosm'
    font.fontname = 'Cosm'
    font.fullname = 'Cosm Regular'

    for path in sorted(Path('./glyphs').glob('*.png')):
        create_char(font, path)

    font.generate(OUT)
    print(f'wrote {OUT}')

def create_char(font, path):
    ch = get_char(path.stem)
    f, vb_w, vb_h = create_svg(path)

    g = font.createChar(ord(ch), ch)
    g.importOutlines(f.name, scale=False, correctdir=True)

    f.close()

    s = ASCENT / vb_h
    baseline = BASELINE * 2 * CY * s

    lsb = 0 if ch in NO_LEFT else SIDE
    rsb = 0 if ch in NO_RIGHT else SIDE

    g.transform(psMat.scale(s))
    g.transform(psMat.translate(lsb, -baseline))

    g.removeOverlap()

    g.simplify()
    g.round()
    g.correctDirection()

    g.width = int(vb_w * s + lsb + rsb)

def get_char(stem):
    if stem.startswith('_') and len(stem) > 1:
        return SUBST[stem[1]] if stem[1] in SUBST else stem[1].upper()

    return stem

def create_svg(path):
    img = Image.open(path).convert('LA')
    paths = get_paths(img)

    w, h = img.size
    vb_w = w * CX
    vb_h = h * CX * 0.95

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {vb_w} {vb_h}">'
        + ''.join(f'<path d="{d}" fill="black"/>' for d in paths)
        + '</svg>'
    )

    f = tempfile.NamedTemporaryFile(suffix='.svg')
    f.write(svg.encode('utf-8'))
    f.flush()

    return f, vb_w, vb_h

def get_paths(img):
    w, h = img.size
    px = img.load()

    paths = []

    for y in range(h):
        x = 0

        while x < w:
            if not is_black(px[x, y]):
                x += 1
                continue

            start = x
            while x < w and is_black(px[x, y]):
                x += 1
            run_length = x - start

            cx = start * CX
            cy = y * CY

            if run_length == 1:
                paths.append(circle(cx, cy))
            else:
                paths.append(pill(cx, cy, run_length * CX, CX))

    return paths

def is_black(la):
    return la[0] == 0 and la[1] == 255

def circle(cx, cy):
    r = CX / 2

    cx += r
    cy += r

    k = r * KAPPA

    return (
        f'M {cx+r} {cy} '
        f'C {cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r} '
        f'C {cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy} '
        f'C {cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r} '
        f'C {cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy} Z'
    )

def pill(x, y, w, h):
    r = min(CX / 2, w / 2, h / 2)
    k = r * KAPPA

    return (
        f'M {x+r} {y} '
        f'H {x+w-r} '
        f'C {x+w-r+k} {y} {x+w} {y+r-k} {x+w} {y+r} '
        f'V {y+h-r} '
        f'C {x+w} {y+h-r+k} {x+w-r+k} {y+h} {x+w-r} {y+h} '
        f'H {x+r} '
        f'C {x+r-k} {y+h} {x} {y+h-r+k} {x} {y+h-r} '
        f'V {y+r} '
        f'C {x} {y+r-k} {x+r-k} {y} {x+r} {y} Z'
    )

if __name__ == '__main__':
    main()

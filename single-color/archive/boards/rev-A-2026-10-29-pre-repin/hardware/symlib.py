"""Tiny KiCad symbol-library reader: extract a symbol block + its pins."""
import re, os
SYM_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
_cache = {}

def _lib_text(lib):
    if lib not in _cache:
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)), lib + ".kicad_sym")
        path = local if os.path.exists(local) else os.path.join(SYM_DIR, lib + ".kicad_sym")
        _cache[lib] = open(path, encoding="utf8").read()
    return _cache[lib]

def _block(text, start):
    """balanced-paren block beginning at text[start] == '('"""
    depth = 0
    i = start
    in_str = False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\": i += 1
            elif c == '"': in_str = False
        else:
            if c == '"': in_str = True
            elif c == "(": depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    raise ValueError("unbalanced")

def get_symbol(lib, name):
    t = _lib_text(lib)
    m = re.search(r'\n\t\(symbol "' + re.escape(name) + r'"\n', t)
    if not m:
        m = re.search(r'\n\t\(symbol "' + re.escape(name) + r'"', t)
    if not m:
        raise KeyError(f"{lib}:{name}")
    blk = _block(t, m.start() + 2)
    ext = re.search(r'\(extends "([^"]+)"\)', blk)
    return blk, (ext.group(1) if ext else None)

def pins(lib, name):
    """list of dicts: number,name,x,y,angle,length,type  (symbol coords, y up)"""
    blk, ext = get_symbol(lib, name)
    if ext:
        blk, _ = get_symbol(lib, ext)
    out = []
    for m in re.finditer(r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s*\(length ([-\d.]+)\)(.*?)\(number "([^"]*)"', blk, re.S):
        nm = re.search(r'\(name "([^"]*)"', m.group(7))
        out.append(dict(type=m.group(1), x=float(m.group(3)), y=float(m.group(4)), angle=float(m.group(5)),
                        length=float(m.group(6)), name=nm.group(1) if nm else "", number=m.group(8)))
    return out

def flat_symbol_text(lib, name):
    """full text of the symbol with 'extends' resolved by copying the parent and renaming."""
    blk, ext = get_symbol(lib, name)
    if not ext:
        return blk
    parent, _ = get_symbol(lib, ext)
    # child overrides properties; simplest: use parent geometry with the child's name and properties
    child_props = re.findall(r'\n\t\t\(property "([^"]+)" "([^"]*)"', blk)
    out = parent.replace(f'(symbol "{ext}"', f'(symbol "{name}"', 1)
    out = re.sub(rf'\(symbol "{re.escape(ext)}_(\d+_\d+)"', rf'(symbol "{name}_\1"', out)
    for k, v in child_props:
        out = re.sub(rf'(\(property "{re.escape(k)}" )"[^"]*"', rf'\1"{v}"', out, count=1)
    return out

"""Join the city schedule (docs/data.json) with OSM street geometry (data/osm.json) -> docs/geo.json."""
import json, re, math
W = "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth fifteenth sixteenth".split()
def norm(s):
    s = s.lower().replace(".", "").strip()
    for i, w in enumerate(W, 1):
        s = re.sub(r"\b%s\b" % w, {1: "1st", 2: "2nd", 3: "3rd"}.get(i, "%dth" % i), s)
    for a, b in [("st", "street"), ("ave", "avenue"), ("hwy", "highway"), ("pl", "place"), ("ter", "terrace")]:
        s = re.sub(r"\b%s$" % a, b, s)
    return s
els = json.load(open("data/osm.json"))["elements"]
def inside(e): return all(40.73 < p["lat"] < 40.76 and -74.05 < p["lon"] < -74.02 for p in e["geometry"])
streets = {}
for e in els:
    if not inside(e): continue
    streets.setdefault(norm(e["tags"]["name"]), []).append([(p["lat"], p["lon"]) for p in e["geometry"]])
for k in list(streets):  # fold "sinatra drive north" etc. into the base street
    base = re.sub(r" (north|south)$", "", k)
    if base != k and base in streets: streets[base] += streets.pop(k)
rows = json.load(open("docs/data.json"))
def pts(name): return [p for l in streets[name] for p in l]
def axis(name):
    P = pts(name); la = [p[0] for p in P]; lo = [p[1] for p in P]
    return "ns" if (max(la) - min(la)) > (max(lo) - min(lo)) * 0.9 else "ew"
def t(p, ax): return p[0] if ax == "ns" else p[1]
def m(a, b): return math.hypot((a[0]-b[0])*110540, (a[1]-b[1])*84500)
def cross_t(sname, xname, ax):
    best = None
    for p in pts(sname):
        for q in pts(xname):
            d = m(p, q)
            if best is None or d < best[0]: best = (d, t(p, ax))
    return best[1]
def split_loc(loc):
    parts = re.split(r"\s+(?:to|and)\s+", loc.strip(), maxsplit=1)
    return parts if len(parts) == 2 else (None, None)
out, bad = [], []
for r in rows:
    s = norm(r["street"]); res = {"axis": None, "pts": []}
    if s not in streets: bad.append((r["street"], "no geometry")); out.append(res); continue
    ax = axis(s); P = sorted(set(pts(s)), key=lambda p: t(p, ax)); lo, hi = t(P[0], ax), t(P[-1], ax)
    a, b = split_loc(r["location"]); rng = []
    for end in (a, b):
        if end is None: rng.append(None); continue
        e = end.lower()
        if "boundary" in e or "limit" in e:
            if "north" in e or "east" in e: rng.append(hi)
            elif "south" in e or "west" in e: rng.append(lo)
            else: rng.append(None)
        elif norm(end) in streets: rng.append(cross_t(s, norm(end), ax))
        else: rng.append(None); bad.append((r["street"], "unresolved end: " + end))
    if rng[0] is None and rng[1] is None: lo2, hi2 = lo, hi
    else:
        v = [x for x in rng if x is not None]
        lo2, hi2 = (min(v), max(v)) if len(v) == 2 else ((min(v[0], hi), max(v[0], hi)) if False else (lo, hi))
    sl = [p for p in P if lo2 - 1e-5 <= t(p, ax) <= hi2 + 1e-5]
    if len(sl) < 2: sl = P
    out.append({"axis": ax, "pts": [[round(p[0], 6), round(p[1], 6)] for p in sl]})
sj = {k: {"lines": [[[round(a, 6), round(b, 6)] for a, b in l] for l in v]} for k, v in streets.items() if k in {norm(r["street"]) for r in rows}}
json.dump({"rows": out, "streets": sj}, open("docs/geo.json", "w"), separators=(",", ":"))
print("rows with geometry:", sum(1 for o in out if o["pts"]), "/", len(out)); print(*bad, sep="\n")

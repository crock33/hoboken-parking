"""Parse the city's street-cleaning page (page.html) into docs/data.json."""
import re, html, json, sys
DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
def hour(h, ap):
    h = int(h)
    if ap == "noon": return 12
    if ap == "pm" and h != 12: h += 12
    if ap == "am" and h == 12: h = 0
    return h
def parse_time(s):
    s = s.lower()
    m = re.search(r"(\d+)\s*(am|pm)?\s*(?:to|-|–)\s*(\d+)\s*(am|pm|noon)", s)
    if not m: raise SystemExit("cannot parse: " + repr(s))
    a, ap1, b, ap2 = m.groups()
    ap1 = ap1 or ("pm" if ap2 == "noon" else ap2)
    return hour(a, ap1), hour(b, ap2)
t = open("data/page.html", errors="ignore").read()
rows = []
for it in re.split(r'<div role="listitem" class="w-dyn-item">', t)[1:]:
    hs = [html.unescape(h).strip() for h in re.findall(r"<h4>(.*?)</h4>", it)][:4]
    if len(hs) == 4 and hs[1] != "Side": rows.append(hs)
out = []
for street, side, dh, loc in rows:
    m = re.search(r"\d", dh); day_part, time_part = dh[:m.start()], dh[m.start():]
    if re.search(r"Monday\s*(through|-)\s*Friday", day_part): days = DAYS
    else:
        d = [x for x in DAYS if x in day_part]
        days = d or [x for x in DAYS if x in dh][:1]
    s, e = parse_time(time_part)
    out.append(dict(street=street.rstrip("."), side=side, days=days, start=s, end=e, location=loc, raw=dh))
json.dump(out, open("docs/data.json", "w"), indent=1)
print(len(out), "rows"); bad = [r for r in out if not r["days"]]; print("unparsed:", bad)

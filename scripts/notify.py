"""Send an ntfy push for every block whose street-cleaning window just ended.
Run every ~10 min by GitHub Actions. Usage: notify.py [--dry] [--now 2026-10-05T09:05]"""
import json, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
PREFIX = "hoboken-clean-7f3a9c"          # keep in sync with TOPIC_PREFIX in docs/index.html
SITE = "https://crock33.github.io/hoboken-parking/"
WINDOW = timedelta(minutes=20)           # look back this far; ntfy history de-dupes repeats
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def nth(y, m, wd, n):
    d = date(y, m, 1); d += timedelta((wd - d.weekday()) % 7 + 7 * (n - 1)); return d
def last(y, m, wd):
    d = date(y + (m == 12), m % 12 + 1, 1) - timedelta(1); return d - timedelta((d.weekday() - wd) % 7)
def holidays(y):  # keep in sync with holidays() in docs/index.html
    return {date(y,1,1), nth(y,1,0,3), nth(y,2,0,3), last(y,5,0), date(y,6,19), date(y,7,4), nth(y,9,0,1),
            nth(y,10,0,2), date(y,11,11), nth(y,11,3,4), date(y,12,25)}

args = sys.argv[1:]
dry = "--dry" in args
now = datetime.fromisoformat(args[args.index("--now") + 1]).replace(tzinfo=TZ) if "--now" in args else datetime.now(TZ)
rows = json.load(open("docs/data.json"))
side = lambda s: "both sides" if s == "Both" else s.lower() + " side"
sent = 0
for day in sorted({now.date(), (now - WINDOW).date()}):
    if day in holidays(day.year): continue
    for r in rows:
        if DAYS[day.weekday()] not in r["days"]: continue
        end = datetime(day.year, day.month, day.day, r["end"], tzinfo=TZ)
        if not (now - WINDOW < end <= now): continue
        topic = f'{PREFIX}-{r["id"]}'
        seen = ""
        if not dry:
            try: seen = urllib.request.urlopen(f"https://ntfy.sh/{topic}/json?poll=1&since=1h", timeout=15).read().decode()
            except Exception as e: print("poll failed", e)
        tag = f'{r["id"]}-{day}'
        if tag in seen: print("already sent", tag); continue
        title = f'🅿️ {r["street"]} {side(r["side"])} is clear'
        body = f'Street cleaning just ended ({r["location"]}). Good time to grab a spot.'
        print(("DRY " if dry else "SEND ") + topic, "|", title)
        if dry: continue
        payload = json.dumps({"topic": topic, "title": title, "message": body, "tags": [tag], "click": SITE}).encode()
        urllib.request.urlopen(urllib.request.Request("https://ntfy.sh/", data=payload, method="POST"), timeout=15)
        sent += 1
print("sent", sent)

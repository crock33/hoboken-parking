# Hoboken Street Cleaning

Phone-friendly web app: which Hoboken blocks were cleaned most recently, and when your parked car gets swept next.

- `docs/` – the app (static; served by GitHub Pages)
- `scripts/build_data.py` – parses the city's schedule page (`data/page.html`) into `docs/data.json`
- `scripts/build_geo.py` – joins it with OpenStreetMap street geometry (`data/osm.json`) into `docs/geo.json`

Schedule source: https://hobokennj.gov/resources/street-cleaning-schedule. Always obey posted signs.

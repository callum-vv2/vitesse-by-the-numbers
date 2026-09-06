# Vitesse by the numbers

A single-page, data-led profile of Vitesse Arnhem prepared by ClubOS: the 2025/26 season at team and
player level, the start of 2026/27, the summer signings, and three scouting reports.

Served by GitHub Pages from `index.html` on `main`.

## Build

`index.html` is generated. Do not edit it by hand.

```
python3 src/build.py      # writes index.html from src/
```

- `src/body.html` — page structure and copy
- `src/styles.css` — ClubOS brand tokens (Sora, DM Sans, ink on paper, one blue)
- `src/app.js` — the charts (inline SVG) and interactions
- `src/build.py` — assembles the data block from `src/data/` and inlines everything into one file
- `src/data/analysis/` — derived CSVs from the independent xG model (season tables, players 900+ min, set pieces)
- `src/data/refresh/` — 2026/27 squad and minutes as at 3 September 2026 (Transfermarkt + the independent model).
  The fixture list also carries match 5 (TOP Oss, 4 September) with the result only: the independent model has not
  been re-run and the Twelve figures for that match are a different model, so those columns are left blank
- `src/data/earpiece/` — the three Twelve Earpiece scouting reports, page text captured 3 September 2026
- `src/brand/` — logomark and crest
- `reports/` — the three scouting reports written up in full, with radar charts

Fonts load from Google Fonts; everything else is inline. No other dependencies.

## Sources and limits

Every vendor number on the page is attributed and quoted with its pool size. Transfermarkt values are
never quoted as fact. The independent xG model is labelled as such and is not vendor xG. Vendor
narrative text is not quoted anywhere; only the tables are.

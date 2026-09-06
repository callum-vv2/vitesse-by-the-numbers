#!/usr/bin/env python3
"""Assemble the Vitesse site: data from the dossier CSVs + hand-carried figures
from the briefs and the two vendor reports, inlined into one HTML file."""
import base64, csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(HERE)
LOCAL = os.path.isdir(os.path.join(HERE, "data"))          # repo layout: src/data/*, src/brand/*
AN = os.path.join(HERE, "data/analysis") if LOCAL else os.path.join(SCRATCH, "dossier/vitesse-analysis/data/analysis")
BRAND = os.path.join(HERE, "brand") if LOCAL else os.path.join(SCRATCH, "brand")

def rows(name):
    with open(os.path.join(AN, name), newline="") as f:
        return list(csv.DictReader(f))

RESERVE = {"AZ II", "Ajax II", "PSV II", "FC Utrecht II"}
SHORT = {"ADO Den Haag": "ADO Den Haag", "AZ II": "Jong AZ", "Ajax II": "Jong Ajax", "PSV II": "Jong PSV",
         "FC Utrecht II": "Jong Utrecht", "Almere City FC": "Almere City", "Cambuur Leeuwarden": "Cambuur",
         "VVV Venlo": "VVV-Venlo", "RKC Waalwijk": "RKC Waalwijk"}

# ---- 1. the 20-club season table (Koetsier model) ----------------------------
clubs = []
for r in rows("q6_2025-26.csv"):
    pts = int(r["Pts"])
    clubs.append({
        "name": SHORT.get(r["HomeName"], r["HomeName"]),
        "pts": pts,
        "published": 44 if r["HomeName"] == "Vitesse" else pts,   # only Vitesse were deducted in 2025-26
        "xpts": round(float(r["xPts"]), 1),
        "xgd": round(float(r["xGD"]), 1),
        "reserve": r["HomeName"] in RESERVE,
        "vit": r["HomeName"] == "Vitesse",
    })

# Twelve / Wyscout-level xG per match ×38 (read off the report; crest-paired)
TWELVE_XGD = {"ADO Den Haag": 1.23, "De Graafschap": 0.48, "RKC Waalwijk": 0.47, "Roda JC": 0.30, "Cambuur": 0.30,
              "Almere City": 0.29, "Jong Utrecht": 0.28, "Willem II": 0.23, "FC Dordrecht": 0.17, "Vitesse": -0.02,
              "VVV-Venlo": -0.05, "FC Den Bosch": -0.14, "FC Emmen": -0.16, "Jong PSV": -0.26, "Helmond Sport": -0.32,
              "Jong AZ": -0.36, "FC Eindhoven": -0.37, "TOP Oss": -0.54, "Jong Ajax": -0.63, "MVV": -0.92}
for c in clubs:
    c["xgd_w"] = round(TWELVE_XGD[c["name"]] * 38, 1)

# ---- 2. players (900+ minutes) for the scatter -------------------------------
players = []
for r in rows("players_2025-26_kkd_900.csv"):
    players.append({
        "n": r["player"], "t": SHORT.get(r["team"], r["team"]),
        "x": round(float(r["NPxG90"]), 3), "y": round(float(r["xA90"]), 3),
        "gi": round(float(r["xGI90"]), 3), "m": int(r["mins"]),
        "rk": int(float(r["rank_xGI90"])), "rxt": int(float(r["rank_xT90"])),
        "g": int(r["NP_Goals"]), "npxg": round(float(r["NPxG"]), 2),
        "v": r["team"] == "Vitesse",
    })
players.sort(key=lambda p: (not p["v"], -p["gi"]))
npxg_median = sorted(p["x"] for p in players)[len(players) // 2]

# ---- 3. set pieces: 2025-26 KKD, 20 clubs, and Vitesse's six seasons -----------
sp_all = rows("setpiece_team_seasons.csv")
sp2526 = [r for r in sp_all if r["season"] == "2025-26" and r["div"] == "KKD"]
setpieces = [{
    "name": SHORT.get(r["team"], r["team"]), "sp": round(float(r["setpiece_xgd"]), 2),
    "corner": round(float(r["corner_xgd"]), 2), "ifk": round(float(r["indirectfk_for"]), 2),
    "vit": r["team"] == "Vitesse", "reserve": r["team"] in RESERVE,
} for r in sp2526]

sp_seasons = []
for s in ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]:
    for div in ["ERE", "KKD"]:
        rs = [r for r in sp_all if r["season"] == s and r["div"] == div]
        v = next((r for r in rs if r["team"] == "Vitesse"), None)
        if not v:
            continue
        def rank(key, desc=True):
            order = sorted(rs, key=lambda r: -float(r[key]) if desc else float(r[key]))
            return [r["team"] for r in order].index("Vitesse") + 1
        sp_seasons.append({"season": s, "div": div, "n": len(rs),
                           "sp": round(float(v["setpiece_xgd"]), 2), "sp_rank": rank("setpiece_xgd"),
                           "corner": round(float(v["corner_xgd"]), 2), "corner_rank": rank("corner_xgd"),
                           "ifk": round(float(v["indirectfk_for"]), 2), "ifk_rank": rank("indirectfk_for")})

# ---- 4. squad: Transfermarkt fields + the three opening line-ups ---------------
REFRESH = os.path.join(HERE, "data/refresh") if LOCAL else os.path.join(SCRATCH, "refresh")   # 3 Sep 2026 refresh: Transfermarkt squad + Koetsier minutes to match 4
with open(os.path.join(REFRESH, "vitesse_squad_2026-09-03.json")) as f:
    squad_raw = json.load(f)
with open(os.path.join(REFRESH, "vitesse_players_2026-27.csv"), newline="") as f:
    PLAY = {r["name"]: r for r in csv.DictReader(f)}
STARTS_OLD = {  # 24 Aug state, kept for the 2025-26 minutes column only
    "Connor van den Berg": ([1], 84, 2208), "Maximilian Brüll": ([2, 3], 195, 1427), "Tyrick Bodak": ([], 0, 0),
    "Jayden Siecker": ([], 0, 123), "Omar Achouitar": ([1, 2, 3], 266, 2203), "Valon Zumberi": ([1, 2, 3], 281, 3178),
    "Marcus Steffen": ([], 20, 1573), "Chiel Olde Keizer": ([1, 2, 3], 267, 164), "Alexander Büttner": ([], 34, 2614),
    "Xiamaro Thenu": ([], 15, 1022), "Nathan Markelo": ([2, 3], 184, 2189), "Solomon Bonnah": ([1], 190, 1696),
    "Marco Schikora": ([1, 2, 3], 281, 3144), "Mathijs Marschalk": ([1, 3], 143, 2506), "Teun Bosch": ([], 0, 0),
    "Koen te Veluwe": ([], 0, 76), "Youssef Ouallil": ([], 0, 145), "Ricardo-Felipe Schwarz": ([1, 2, 3], 263, 1933),
    "Pontus Dahbo": ([], 59, 0), "Yuval Ranon": ([], 0, 603), "Ayman Sellouf": ([1, 2, 3], 249, 0),
    "Filipe de Carvalho": ([2, 3], 146, 0), "Nino Zonneveld": ([], 59, 1479), "Naoufal Bannis": ([1, 2, 3], 257, 1536),
    "Eduard Probst": ([2], 110, 0), "João Pinto": ([1], 83, 1744),
}
POS = {"Goalkeeper": "GK", "Centre-Back": "CB", "Left-Back": "LB", "Right-Back": "RB", "Defensive Midfield": "DM",
       "Central Midfield": "CM", "Attacking Midfield": "AM", "Left Winger": "LW", "Right Winger": "RW", "Centre-Forward": "CF"}
squad = []
for p in squad_raw:
    name = re.sub(r"<[^>]+>", "", p["name"]).strip()
    pl = PLAY.get(name, {})
    starts = [int(x) for x in pl.get("started_matches", "").split(",") if x.strip()]
    m26 = STARTS_OLD.get(name, ([], 0, 0))[2]
    squad.append({"name": name, "pos": POS[p["pos"]], "age": int(p["age"]), "contract": p["contract"] or None,
                  "value": p["val"] if p["val"] not in ("-", "", None) else None, "joined": p["joined"], "prev": p["prev"],
                  "starts": starts, "m27": int(pl.get("min_2627", 0) or 0), "m26": m26})

# ---- 4b. the three Twelve Earpiece scouting reports (captured 3 Sep 2026, page text) ------
EARP = os.path.join(HERE, "data/earpiece") if LOCAL else os.path.join(SCRATCH, "earpiece")
def parse_earpiece(fname):
    txt = open(os.path.join(EARP, fname)).read()
    facets = []
    for m in re.finditer(r"^--- ([^\n]+?) — Quality rank (\d+) of (\d+) ---\n(.*?)(?=^--- |\Z)", txt, re.M | re.S):
        name, rank, pool, body = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        metrics = [[a.strip(), b.strip(), int(c)] for a, b, c in re.findall(r"^([^:\n]+): (.+?) \| (\d+) of \d+$", body, re.M)]
        zone = re.search(r"Zone map(?: prose)?: (.+)", body)
        facets.append({"name": name, "rank": rank, "metrics": metrics, "zone": zone.group(1).strip().strip('"') if zone else None})
    pool = facets[0]["rank"] and int(re.search(r"Quality rank \d+ of (\d+)", txt).group(1))
    return facets, pool
SC_NOTES = {  # from the scouting reports written 3 Sep (vitesse-analysis/scouting/*.md)
 "wouters": {
   "period": "before", "periodLabel": "Before Vitesse · RKC Waalwijk · Eerste Divisie 2025/26",
   "file": "wouters-776769c6.txt", "name": "Luuk Wouters", "role": "Centre-back · signed 31 Aug 2026 from RKC Waalwijk",
   "sample": "Eerste Divisie 2025/26 · 2,929 minutes · 33 matches · 32 starts", "poolLabel": "90 Eerste Divisie centre-backs",
   "intro": "Luuk Wouters is the shape the three findings describe: 27, left-footed, a full season at RKC Waalwijk (2,924 minutes on the independent model’s count, the seventh-heaviest workload of any centre-back in the league, at the side that conceded the second-lowest expected goals in it), one of six left-footed centre-backs in the 25-to-29 band among the 67 with 900+ minutes, signed on a free, on a deal to June 2028. One season of data cannot pass a persistence test, and no page can settle how he plays in this block. What the data does settle is that the profile the analysis points to is the one the club bought, at the cost of contract length and nothing else.",
   "shows": "The rates are the robust numbers, produced on roughly a hundred duels rather than counts: 69% of aerial duels won (2nd of 90), 70% of defensive aerials (6th), 75% of tackles (5th), 78% of one-against-ones (7th), and the tenth-best defensive-heading profile in the pool. Those are what a deep, direct block asks of its centre-backs, and they were produced inside the division’s second-tightest defence. On the ball the sample puts every progression measure at the median and pressure resistance below it, in a side that averaged 3.5 passes per possession and so tested both less than most.",
   "cannot": "One season, one club, so no persistence test is possible. Pressure resistance (70%, 79th of 90) rests on roughly 55 pressured actions all season; the aerial win rate on nearly twice that. Every zone read makes him a left-of-the-pair specialist with gaps on the right, and his weakest aerial zone is his own penalty area, so he does not fix the corner record by himself.",
   "prose": "The vendor’s prose fails its own table four times: “falls short in aerial duels” describes a duel count (63rd of 90) while the win rate is 2nd; “inconsistent” intelligent defence is three metrics at the median; “excels in crucial moments” has no metric behind it; and the progression headline says “strong creative impact” over three ranks between 40th and 53rd.",
   "fit": "His numbers were produced at RKC, a build-up side: 62 on the vendor’s long-ball-to-build-up spectrum against Vitesse’s 37 last season. Over the first three matches of 2026/27 Vitesse have moved toward that model, keeping 57% of the ball against 48% last season and cutting the long-pass share from 14% to 10%, so the on-ball context he comes from now resembles the one he joins. That is the case for the fit: xGBuildup 12th of 90 and touches 32nd say he is used to being involved in a side that plays out. It also raises the stakes on his weakest axes, because a possession side tests pressure resistance (79th) and composure (67th) more often than a long-ball side does; the zone read says the risk sits in his own penalty area. What the current model asks of him is therefore narrower than what RKC did: keep winning the header where corners land, and play early and simple when pressed near his own goal. The aerial side transfers cleanly either way: Vitesse are winning 57% of aerial duels this season against 42% last, and his 69% win rate reinforces that. The left-of-the-pair slot the zone reads point to is the one beside Zumberi that Achouitar, also left-footed, has held in every match this season, so which side he plays decides how much of this transfers."},
 "dahbo": {
   "period": "before", "periodLabel": "Before Vitesse · BK Häcken · Allsvenskan 2026",
   "file": "dahbo-93c8e9cb.txt", "name": "Pontus Dahbo", "role": "Winger by the vendor’s frame · on loan from BK Häcken per Transfermarkt · used centrally by Vitesse",
   "sample": "Allsvenskan 2026 · 220 minutes · 9 matches · 1 start; a few games, read that way", "poolLabel": "72 Allsvenskan wingers",
   "shows": "220 minutes is 2.4 matches, so only the frequent events carry information: roughly 27 defensive actions and 26 intensity events put him 1st of 72 on both, and 87% of his actions under pressure succeeded (3rd). That agrees with the larger 2025 sample at Häcken from a different vendor (1,308 minutes; top three among Allsvenskan attacking midfielders on possession gains, MyGamePlan), and it is the profile that maps onto Vitesse’s worst phase of 2025/26, retention after a recovery.",
   "cannot": "Everything attacking is a count of zero or one: no key passes, no xA, 0.15 npxG, five shots. The 72nd of 72 on providing is a description of substitute minutes on the right wing, not of ability. Across both Swedish seasons he has two assists in 1,528 minutes; nothing in hand says he closes the creativity gap, and nothing says he cannot. Ten Eerste Divisie matches is the earliest a key-pass rate becomes a number.",
   "prose": "Two zone-map headlines contradict the rows beneath them: “excels in providing assists” over zero chance-creating passes, and “skilled chance creator” over zero key passes. The finishing headline (“misses chances regularly”) sits over a median finishing residual; the low rank is shot volume, not conversion. And the pressing prose omits that counter-pressing is 40th of 72, the median.",
   "fit": "Vitesse have used him where the vendor does not rate him, as one of a midfield three in a 4-3-3 at Den Bosch, in a side now averaging more passes per possession and keeping 57% of the ball. A possession side needs players who keep it under pressure, and that is his strongest row: 87% pressure resistance (3rd of 72) and first of 72 on low turnovers per reception. It also needs ball-winning when the ball is lost, which last season was Vitesse’s worst phase (retention after a recovery 19th of 20) and is his other strength (1st on defensive actions won). What the current shape asks for that he has not shown is creation from the centre: Tahaui’s 10 assists left with him, and Dahbo has two in 1,528 Allsvenskan minutes. His 123 minutes are too few to have moved the results either way."},
 "decarvalho": {
   "period": "at", "periodLabel": "At Vitesse · Eerste Divisie 2026/27 · the first four matches",
   "file": "decarvalho-1972fc49.txt", "name": "Filipe de Carvalho", "role": "Wide forward · three consecutive starts on Hoogewerf’s flank",
   "sample": "Eerste Divisie 2026/27 · 215 minutes · 4 matches · 3 starts · 1 goal, 2 assists", "poolLabel": "21 Eerste Divisie wingers — one place is 4.8 percentile points",
   "shows": "Reconstructed from the per-90s: about 63 touches, 8 receptions in the box, 4 shots, 3 key passes of which two became goals. The shape is consistent: he arrives in the box (box receptions 2nd of 21) and presses the instant the ball is lost (counter-pressing 1st), while the build-up numbers are at the bottom (touches 19th, passes into the final third 18th). Arriving in the box and pressing on the loss are the two things last season’s numbers said the side most needed. He finishes moves rather than building them, and the club decided that before any of these numbers existed by starting him three times.",
   "cannot": "Every headline number is four shots or three passes. Two assists from 0.65 xA and a first place on a zero-numerator ratio will not persist. The vendor itself declined to zone-map five of the nine facets for lack of data. The measure at 600–800 minutes, mid-October to November, is np xG, xA and box receptions per 90.",
   "prose": "The vendor calls him “well-rounded” with facets spanning 1st to 16th, “average” in box threat while listing it 7th as a strength, and says his finishing is “hindered by low-quality chance creation” when his xG per shot is 4th of 21: the low number is shots on target.",
   "fit": "He fits the side Vitesse are playing as this season. Over the first three matches the crosses went up from 16.7 to 26 a match and box entries from 23 to 39, and a winger whose best row is receptions inside the penalty area (2nd of 21) is the player that pattern feeds; his goal at Den Bosch and both assists came in those four matches. The side is pressing slightly less than last season (PPDA 12.1 to 13.1), which makes his counter-pressing (1st of 21) a resource the team is not yet built around rather than a requirement. The one line to watch as the ball is kept more (57% possession) is his involvement in the build-up, where he is 19th of 21 on touches and 18th on passes into the final third, so he does not replace Tahaui’s creation from deep; Vitesse have played him on the right for 60% of his minutes and the left for 30%, and the vendor’s zone reads are consistent that he produces from the right."},
}
scouting = []
# HIDDEN 6 Sep 2026: "dahbo" and "decarvalho" removed from this list on request.
# Their SC_NOTES entries and earpiece source files are retained; restoring is adding
# the two keys back here. app.js only draws a "Scouting report" link on a signing card
# when that player is in D["scouting"], so their cards lose the link automatically.
for key in ["wouters"]:
    n = SC_NOTES[key]; facets, pool = parse_earpiece(n["file"])
    scouting.append({"key": key, "name": n["name"], "role": n["role"], "sample": n["sample"], "pool": pool, "poolLabel": n["poolLabel"],
                     "facets": facets, "intro": n.get("intro"), "shows": n["shows"], "cannot": n["cannot"], "prose": n["prose"], "fit": n["fit"], "period": n["period"], "periodLabel": n["periodLabel"]})

# ---- 5. hand-carried figures (source noted per block) --------------------------
D = {
    "clubs": clubs, "players": players, "npxgMedian": round(npxg_median, 3),
    "setpieces": setpieces, "spSeasons": sp_seasons, "squad": squad, "scouting": scouting,
    # VITESSE-ON-PITCH §1 / TALK-TRACK claim 1 / Twelve cross-reference
    "methods": [
        {"name": "Independent xG model", "note": "XGBoost on Opta event data · 38 matches", "xgd": "+2.8", "xgdRank": "10th", "xpts": "53.7", "resid": "+2.3", "residRank": "9th"},
        {"name": "Licensed xG (Twelve · Wyscout)", "note": "Twelve season report on Vitesse · 38 matches", "xgd": "−0.8", "xgdRank": "10th", "xpts": "52.1", "resid": "+3.8", "residRank": "6th"},
    ],
    # Twelve season report p2 + per-metric pages
    "phases": [
        {"name": "Defence", "rank": 7, "why": "Opponents reach the final third slightly more often than average (14th) but get into the box less than against anyone: final-third-to-box 1st, box touches 3rd, shots faced 2nd."},
        {"name": "Defensive transition", "rank": 3, "why": "Lose the ball rarely (2nd fewest turnovers) and high (4th), so opponents start their transitions more than 60 m from Vitesse’s goal. Counter-pressing itself is 14th."},
        {"name": "Opposition chance creation", "rank": 8, "why": "Low volume conceded; the shots that do arrive are above-average quality (xG per shot 14th)."},
        {"name": "Attacking transition", "rank": 17, "why": "Possession retained after a recovery 19th of 20. Transition xG is exactly median — the ball goes straight back."},
        {"name": "Attack", "rank": 15, "why": "Possession 17th, possessions reaching the final third 19th, box touches 17th. Long-ball share 5th highest."},
        {"name": "Chance creation", "rank": 14, "why": "Box-to-shot 1st of 20 (they shoot at the first sight), so np xG per shot is 19th. Volume 6th, quality 19th."},
        {"name": "Outcome", "rank": 7, "why": "56 points from ≈52 expected. Non-penalty goals 6th from np xG 15th: finishing carried the table position."},
    ],
    # Wyscout export, all 38 league matches (licensed) — WYSCOUT-FULL-MINE / the board
    "styleA": [
        ["Match tempo", "actions per minute", "14.70", "16.06", "0.00003"],
        ["Average pass length", "metres", "20.93", "19.82", "0.00002"],
        ["Long-pass share", "", "14.2%", "10.2%", "0.0001"],
        ["Lateral passes", "season", "4,649", "6,221", "0.0018"],
        ["Passes per possession", "", "3.51", "4.15", "0.0041"],
        ["Accurate passes into the final third", "season", "1,056", "1,409", "0.0100"],
        ["Accurate smart passes", "Wyscout’s term · season", "9", "21", "0.0165"],
        ["PPDA", "lower = presses harder", "12.14", "9.78", "0.038"],
    ],
    "styleB": [
        ["Crosses", "season", "633", "545", ""],
        ["Cross accuracy", "", "38.5%", "33.9%", ""],
        ["Deep completed crosses", "season", "237", "173", ""],
        ["Box entries", "season", "889", "838", ""],
        ["…arriving by cross", "", "422 (47.5%)", "324 (38.7%)", ""],
        ["…arriving by run", "", "131 (14.7%)", "141 (16.8%)", ""],
        ["Touches in the penalty area", "season", "662", "663", ""],
        ["Shots", "season", "520", "450", ""],
        ["Shots on target", "season", "184", "187", ""],
        ["xG per shot", "", "0.109", "0.128", ""],
    ],
    # VITESSE-ON-PITCH §4
    "persistence": [
        ["Set-piece xG difference", "+0.741", "+0.729", "+0.740"],
        ["Corner xG difference", "+0.735", "+0.720", "+0.732"],
        ["Open-play xG difference", "+0.549", "+0.841", "+0.788"],
        ["A club's finishing residual", "—", "—", "+0.290"],
        ["A player's finishing residual", "—", "—", "+0.045"],
    ],
    # VITESSE-ON-PITCH §8
    "bands": [
        {"band": "below −10", "n": 37, "top8": 2}, {"band": "−10 to 0", "n": 24, "top8": 2},
        {"band": "0 to +5", "n": 11, "top8": 2, "here": True}, {"band": "+5 to +10", "n": 9, "top8": 7, "target": True},
        {"band": "+10 to +15", "n": 13, "top8": 11}, {"band": "above +15", "n": 26, "top8": 24},
    ],
    # refresh/vitesse_fixtures_2026-27.csv — five matches. xG on matches 1–4 is the independent model
    # (Koetsier). There is no independent figure for match 5 yet, so the pair carried there is Twelve
    # Football's, summed off their own shot map, and is labelled on the card. The two are never added
    # together and match 5 is not in the cumulative xG difference, which is a Koetsier running total.
    "fixtures": [
        {"date": "7 Aug", "opp": "RKC Waalwijk", "ha": "H", "gf": 1, "ga": 1, "shape": "back three", "xg": 1.76, "xga": 2.23, "note": "Led through Bannis; goalkeeper sent off late on and finished with ten men."},
        {"date": "17 Aug", "opp": "Jong Utrecht", "ha": "A", "gf": 3, "ga": 1, "shape": "back four", "xg": 3.42, "xga": 0.65, "note": "Won on merit: 19 shots to 11."},
        {"date": "21 Aug", "opp": "Almere City", "ha": "H", "gf": 0, "ga": 3, "shape": "back four", "xg": 2.01, "xga": 1.55, "note": "Lost while winning the expected goals and the box entries, 36 to 17."},
        {"date": "28 Aug", "opp": "FC Den Bosch", "ha": "A", "gf": 4, "ga": 1, "shape": "back four", "xg": 2.29, "xga": 2.98, "note": "Won while losing the expected goals: out-shot 25 to 12, a penalty saved in the fifth minute, two counter-attack goals. Twelve’s shot map, summed, reaches the same verdict on its own numbers: 1.91 to Vitesse, 2.70 to Den Bosch."},
        {"date": "4 Sep", "opp": "TOP Oss", "ha": "H", "gf": 2, "ga": 1, "shape": "back four", "xg": 2.21, "xga": 0.36, "xgsrc": "Twelve, summed from the shot map",
         "note": "Nineteen shots to five on Twelve’s count, and the ball won back far higher up the pitch than at Den Bosch a week earlier. The independent model has not been run on this match."},
    ],
    "shift": [
        ["Aerial duels won", "42.0%", "56.8%", 1], ["Box entries", "23.4", "39.0", 1], ["Possession", "48.1%", "57.2%", 1],
        ["Long-pass share", "14.2%", "9.8%", 1], ["xG", "1.49", "2.31", 1],
        ["Crosses", "16.7", "26.0", -1], ["PPDA", "12.14", "13.12", -1],
    ],
    # Twelve Football single-match opposition reports, both generated 6 Sep 2026: match 4 away at Den Bosch,
    # match 5 at home to TOP Oss. Each figure is that one match. Neither report prints a season baseline.
    "posture": {
        "cols": ["Away · Den Bosch – Vitesse 1–4", "Home · Vitesse – TOP Oss 2–1"],
        "rows": [
            ["Defensive action height", "mean height of defensive actions, metres from own goal", "33.45", "42.95"],
            ["Final-third recoveries", "share of all recoveries", "0% (0 of 34)", "28% (11 of 39)"],
            ["Fouls in the attacking half", "share of the side’s fouls", "35%", "73%"],
            ["PPDA", "opponent passes per defensive action; lower = presses harder", "7.57", "5.71"],
            ["Defensive intensity", "defensive actions per minute out of possession", "5.73", "5.92"],
        ],
    },
    "xi4": ["van den Berg", "Bonnah", "Achouitar", "Zumberi", "Olde Keizer", "Schikora", "Schwarz", "Dahbo", "de Carvalho", "Sellouf", "Bannis"],
    # CURRENT-SQUAD.md + the MyGamePlan report pp21–24 (third-party rating, labelled)
    "signings": [
        {"name": "Pontus Dahbo", "age": 20, "pos": "Attacking midfield", "from": "BK Häcken, on loan per Transfermarkt", "when": "13 Aug 2026", "value": "€2.00m", "contract": "June 2027 · the question is the option",
         "sample": "BK Häcken, Allsvenskan · 2025: 1,308 min, 23 apps, 1G 2A · 2026: 220 min, 9 apps, 1 start, 0G 0A", "league": "Two seasons before the move, both from vendor reports", "sofar": "123 min; two substitute appearances, then a first start at Den Bosch, used centrally",
         "read": "", "report": True,
         "verdict": "The one durable signal is that he wins the ball. The rest is judged at 800 minutes."},
        {"name": "Ayman Sellouf", "age": 25, "pos": "Left wing", "from": "Free agent", "when": "20 Jul 2026", "value": "€125k", "contract": "June 2027",
         "sample": "146 min · 5 apps · 0G 0A", "league": "Bulgaria First League 2024-25, at his previous club", "sofar": "Started all four, one goal",
         "read": "Before Vitesse, the thinnest record of the attackers: five appearances totalling 146 minutes in Bulgaria, no goal involvement. At Vitesse he has started every match and scored. A free 25-year-old walking straight into the team is the recruitment thesis working; the prior data says nothing either way.",
         "verdict": "Unproven on paper; starting every match."},
        {"name": "Filipe de Carvalho", "age": 22, "pos": "Wide forward", "from": "FC Rapperswil-Jona", "when": "21 Jul 2026", "value": "€250k", "contract": "June 2028",
         "sample": "213 min · 7 apps · 0G 0A", "league": "Swiss Super League 2024-25, at FC Rapperswil-Jona", "sofar": "Three starts, 1 goal and 2 assists in 215 minutes",
         "read": "", "report": True,
         "verdict": "The club has already picked him. The measure at 800 minutes is np xG, xA and box receptions."},
        {"name": "Eduard Probst", "age": 25, "pos": "Centre-forward", "from": "SV Rödinghausen", "when": "7 Jul 2026", "value": "€200k", "contract": "June 2028",
         "sample": "366 min · 12 apps · 3G 0A", "league": "3. Bundesliga 2024-25, at SV Rödinghausen", "sofar": "129 min, one start, three appearances off the bench",
         "read": "Before Vitesse: three goals in 366 bench minutes in the 3. Bundesliga, a rate rather than a record. Brought in against Huth's departure. A season of Eerste Divisie minutes will settle it and nothing before that will.",
         "verdict": "Unproven. Bannis remains the only proven KKD centre-forward."},
        {"name": "Luuk Wouters", "age": 27, "pos": "Centre-back", "from": "RKC Waalwijk, free", "when": "31 Aug 2026", "value": "€300k", "contract": "June 2028",
         "sample": "2,929 min · 33 matches · 32 starts · 0G 0A", "league": "Eerste Divisie 2025-26, at RKC Waalwijk", "sofar": "Signed after match 4; no minutes yet",
         "read": "", "report": True,
         "verdict": "The right shape, on real samples: a left-footed centre-back, 27, in the age band this division under-prices, on a deal to 2028."},
    ],
    "departures": [
        {"name": "Adam Tahaui", "pos": "AM", "lost": "5 non-penalty goals · 10 assists · 2,943 min", "note": "The chief creator: 50th of 355 on expected goal involvement, on the largest attacking sample at the club."},
        {"name": "Dillon Hoogewerf", "pos": "LW", "lost": "8 non-penalty goals · 2,834 min", "note": "Wide output the two wide arrivals have 359 combined minutes of prior data to replace."},
        {"name": "Elias Huth", "pos": "CF", "lost": "6.08 NPxG · 2,214 min", "note": "The target man: top-four among KKD strikers for aerial and offensive duels (MyGamePlan)."},
    ],
    # Twelve Football "Team Fit" page for Luuk Wouters, 3 Sep 2026 (radar read from the chart,
    # percentile-type vs Eerste Divisie centre-backs, ±2); cohort facts from players_2025-26_enriched.csv;
    # RKC context from q5_all_stand.csv / q3_gamestate.csv; recruitment findings from VITESSE-ON-PITCH §3, §7
    "profile": {
        "name": "Luuk Wouters", "club": "RKC Waalwijk", "age": 27, "foot": "left",
        "mins": 2924, "minsRank": "7th of 67", "cohort": 67,
        "radar": [["Involvement", 77], ["Active defence", 76], ["Intelligent defence", 48], ["Territorial dominance", 33],
                  ["Chance prevention", 74], ["Defensive heading", 89, True], ["Aerial threat", 88, True],
                  ["Composure", 26], ["Progression", 39]],
        "style": [["Defence", "Low block", "High press", 45, 41], ["Attack", "Long ball", "Build-up", 37, 62],
                  ["Chance creation", "Sustained", "Direct", 70, 39]],
    },
    # TALK-TRACK / VITESSE-ON-PITCH §6
    "killed": [
        {"claim": "“He underperformed his xG — he’s due.”", "why": "A player’s finishing residual persists at r = +0.045 across 676 player-pairs: 96% of it evaporates by the next season. A nine-player buy list built on it was cut."},
        {"claim": "“The defence was fixed in the run-in.”", "why": "A ten-match run that good occurs in 5.5% of all windows, and two matches supply 96% of it. Variance, not a mechanism."},
        {"claim": "“The leak is at 0–0.”", "why": "Half of the level-state deficit is four penalty kicks. In settled open play at 0–0, Vitesse are level with the division average."},
    ],
}

with open(os.path.join(BRAND, "nw-vitesse.webp"), "rb") as f:
    crest = "data:image/webp;base64," + base64.b64encode(f.read()).decode()
with open(os.path.join(BRAND, "logomark-blue.svg")) as f:
    logomark = f.read()
logomark = re.sub(r'width="\d+" height="\d+" ', "", logomark).replace("<svg ", '<svg class="logomark" aria-hidden="true" ')
logomark = re.sub(r'fill="#[0-9A-Fa-f]{6}"', 'fill="currentColor"', logomark)

def read(name):
    with open(os.path.join(HERE, name)) as f:
        return f.read()

html = read("body.html")
html = html.replace("/*STYLES*/", read("styles.css")).replace("/*APP*/", read("app.js"))
html = html.replace("/*DATA*/", json.dumps(D, ensure_ascii=False, separators=(",", ":")))
html = html.replace("{{CREST}}", crest).replace("{{LOGOMARK}}", logomark)

out = os.path.join(os.path.dirname(HERE), "index.html") if LOCAL else os.path.join(HERE, "vitesse-by-the-numbers.html")
with open(out, "w") as f:
    f.write(html)
print(out, f"{os.path.getsize(out)/1024:.0f} KB", f"{len(players)} players", f"{len(clubs)} clubs")

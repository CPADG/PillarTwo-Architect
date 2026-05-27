#!/usr/bin/env python3
"""
Generate a complex ~400-entity P2A demo file for testing scalability and
correctness of Pillar Two analysis. Designed to exercise:
  - UPE (최종모기업), IPE (중간), POPE (부분소유) all bearing IIR
  - IIR / UTPR / QDMTT / SH all triggered in various sub-trees
  - JV/JV_sub groups
  - MOPE (소수지분 모기업) sub-groups
  - Investment entity, excluded entity
  - Treasury stock (자기주식)
  - 100% ownership constraint compliance
  - Realistic multi-tier consolidated structure across 25 countries
"""
import json
import random

random.seed(42)  # reproducible

# ── Country/city pool — 잘 알려진 도시 위주 (마이너 도시 정리) ──
# 큰 국가는 ~20-25개 메이저 도시, 작은 국가는 풀이 한정되니 핵심만.
CITIES = {
    "KR": ["Seoul","Busan","Incheon","Daegu","Daejeon","Gwangju","Suwon","Ulsan","Sejong","Jeju","Pohang","Changwon","Jeonju","Cheongju","Anyang","Ansan","Goyang","Yongin","Bucheon","Mokpo","Yeosu","Gimhae","Gangneung","Sokcho","Hwaseong","Pyeongtaek","Wonju","Chuncheon","Andong","Paju","Gimpo","Asan","Gyeongju","Tongyeong","Hanam","Iksan"],
    "US": ["New York","Chicago","Houston","Los Angeles","San Francisco","Boston","Seattle","Miami","Atlanta","Denver","Phoenix","Philadelphia","Portland","Dallas","Detroit","Minneapolis","Pittsburgh","Charlotte","Nashville","Austin","San Diego","Salt Lake City","Indianapolis","Columbus","Cleveland","Orlando","Sacramento"],
    "JP": ["Tokyo","Osaka","Kyoto","Nagoya","Sapporo","Yokohama","Kobe","Hiroshima","Fukuoka","Sendai","Nara","Chiba","Niigata","Okayama","Saitama","Kanazawa","Kumamoto","Naha","Shizuoka","Kagoshima"],
    "CN": ["Beijing","Shanghai","Guangzhou","Shenzhen","Tianjin","Hangzhou","Wuhan","Chengdu","Xi'an","Suzhou","Nanjing","Qingdao","Dalian","Harbin","Chongqing","Ningbo","Xiamen","Kunming","Changsha","Lhasa"],
    "DE": ["Berlin","Munich","Hamburg","Frankfurt","Cologne","Stuttgart","Düsseldorf","Leipzig","Dortmund","Essen","Bremen","Hanover","Nuremberg","Dresden","Bonn","Mannheim","Karlsruhe","Wiesbaden","Freiburg","Aachen"],
    "GB": ["London","Manchester","Birmingham","Glasgow","Liverpool","Edinburgh","Leeds","Bristol","Sheffield","Newcastle","Cardiff","Belfast","Nottingham","Oxford","Cambridge","Aberdeen","Brighton","Southampton","York","Bath"],
    "FR": ["Paris","Marseille","Lyon","Toulouse","Nice","Nantes","Strasbourg","Bordeaux","Lille","Rennes","Reims","Le Havre","Toulon","Grenoble","Saint-Étienne","Dijon","Tours","Orléans","Rouen","Caen","Avignon","Versailles","Cannes","Aix-en-Provence","Montpellier","Brest","Limoges","Amiens","Metz","Nancy","Mulhouse"],
    "IT": ["Rome","Milan","Naples","Turin","Palermo","Genoa","Bologna","Florence","Bari","Catania","Venice","Verona","Padua","Trieste","Brescia","Modena","Parma","Bergamo","Perugia","Vicenza","Ravenna","Pisa","Siena","Lecce","Como","Lucca","Rimini","Salerno"],
    "ES": ["Madrid","Barcelona","Valencia","Seville","Zaragoza","Málaga","Murcia","Palma","Bilbao","Alicante","Córdoba","Valladolid","Vigo","Granada","Pamplona","Salamanca","Marbella","Oviedo","Cartagena","Tarragona","Toledo","Cádiz","Santander","Burgos","Ibiza","Tenerife"],
    "IN": ["Mumbai","Delhi","Bangalore","Hyderabad","Chennai","Kolkata","Pune","Ahmedabad","Jaipur","Lucknow","Kanpur","Nagpur","Indore","Bhopal","Coimbatore","Agra","Varanasi","Kochi","Amritsar","Chandigarh","Goa","Surat","Mysore","Trivandrum","Jodhpur","Patna"],
    "BR": ["São Paulo","Rio de Janeiro","Brasília","Salvador","Fortaleza","Belo Horizonte","Manaus","Curitiba","Recife","Porto Alegre","Belém","Goiânia","Campinas","Natal","Florianópolis","Santos","Niterói","Joinville","Vitória","Maceió","Sorocaba","Londrina","Petrópolis","Búzios","Olinda"],
    "CA": ["Toronto","Montreal","Vancouver","Calgary","Edmonton","Ottawa","Winnipeg","Quebec City","Hamilton","Mississauga","Halifax","Saskatoon","Burnaby","Richmond","Oakville","Regina","Sherbrooke","Markham"],
    "AU": ["Sydney","Melbourne","Brisbane","Perth","Adelaide","Canberra","Hobart","Darwin","Gold Coast","Geelong","Cairns","Newcastle","Wollongong"],
    "MX": ["Mexico City","Guadalajara","Monterrey","Puebla","Tijuana","León","Juárez","Mérida","Querétaro","Acapulco","Cancún","Veracruz","Cuernavaca","Chihuahua","Hermosillo"],
    "NL": ["Amsterdam","Rotterdam","The Hague","Utrecht","Eindhoven","Tilburg","Groningen","Breda","Nijmegen","Haarlem","Maastricht","Almere","Leiden","Arnhem","Dordrecht"],
    "CH": ["Zurich","Geneva","Basel","Bern","Lausanne","Lugano","Winterthur","St. Gallen","Lucerne","Fribourg","Neuchâtel"],
    "SE": ["Stockholm","Gothenburg","Malmö","Uppsala","Linköping","Örebro","Helsingborg","Umeå","Lund","Norrköping"],
    "NO": ["Oslo","Bergen","Trondheim","Stavanger","Drammen","Kristiansand","Tromsø","Ålesund"],
    "IE": ["Dublin","Cork","Limerick","Galway","Waterford","Drogheda","Dundalk","Kilkenny","Sligo"],
    "ID": ["Jakarta","Surabaya","Bandung","Medan","Semarang","Palembang","Tangerang","Depok","Bekasi","Bogor","Makassar","Batam","Malang","Padang","Yogyakarta","Bali","Pekanbaru","Solo","Balikpapan","Manado"],
    # 도시국가/소영토 — 행정구·교외도시·자치구 (더 알려진 이름 중심)
    "SG": ["Singapore","Marina Bay","Jurong","Tampines","Woodlands","Changi","Orchard","Bedok","Bukit Timah","Clementi","Sentosa","Punggol","Bishan","Toa Payoh","Hougang","Yishun","Ang Mo Kio","Holland Village","Raffles Place","Boat Quay"],
    "HK": ["Hong Kong","Kowloon","Wan Chai","Central","Causeway Bay","Tsim Sha Tsui","Mong Kok","Sha Tin","Tai Po","Yuen Long","Lantau"],
    "BM": ["Hamilton","St. George","Somerset","Paget","Pembroke"],
    "KY": ["George Town","West Bay","Bodden Town","Cayman Brac"],
    "LU": ["Luxembourg City","Esch-sur-Alzette","Differdange","Dudelange","Bettembourg","Sanem","Ettelbruck"],
}

# Pre-shuffle each country's cities so picks feel arbitrary but stable
for cc in CITIES:
    random.shuffle(CITIES[cc])

# Used set per country — explicit names + take_city both register here to prevent dups
_idx = {cc: 0 for cc in CITIES}
_used = {cc: set() for cc in CITIES}

# 사전 예약 — 명시적 이름들은 시작 시점에 등록해서 take_city가 절대 못 뽑게 함
# (스크립트 후반의 JV/MOPE/Investment 명시 이름이 앞 take_city에 의해 소비되는 것 방지)
RESERVED_NAMES = [
    ("KR","Seoul"),("KR","Busan"),("KR","Incheon"),("KR","Daegu"),
    ("JP","Tokyo"),("US","New York"),("DE","Frankfurt"),("GB","London"),
    ("BR","São Paulo"),("BR","Rio de Janeiro"),("BR","Brasília"),
    ("CH","Zurich"),("IE","Dublin"),("AU","Sydney"),
    ("BM","Hamilton"),("KY","George Town"),("KY","Cayman Brac"),
    ("LU","Luxembourg City"),("SG","Marina Bay"),
    ("HK","Lantau"),("CH","Chur"),("CH","Neuchâtel"),
    ("NL","Eindhoven"),("JP","Naha"),
]
for cc, nm in RESERVED_NAMES:
    _used[cc].add(nm)
def take_city(cc):
    """Reserve next unused city. Returns None if pool exhausted (caller should skip)."""
    lst = CITIES[cc]
    while _idx[cc] < len(lst) and lst[_idx[cc]] in _used[cc]:
        _idx[cc] += 1
    if _idx[cc] >= len(lst):
        return None  # 풀 소진 — 폴백 이름 만들지 말고 None 반환
    name = lst[_idx[cc]]
    _used[cc].add(name)
    _idx[cc] += 1
    return name

# ── Node/edge accumulators ─────────────────────────────────────────
nodes = []
edges = []
next_node_id = 1
next_edge_id = 1

def add_node(country, x, y, entity_type="general", name=None):
    """Add a node. Returns None if no name available (pool exhausted) — caller skips."""
    global next_node_id
    if name:
        _used[country].add(name)
        nm = name
    else:
        nm = take_city(country)
        if nm is None:
            return None  # 풀 소진 — 노드 생성 안 함
    n = {"id": next_node_id, "name": nm, "country": country,
         "entityType": entity_type, "globe": {}, "x": x, "y": y}
    nodes.append(n)
    next_node_id += 1
    return n

def add_edge(src, dst, pct, etype="consolidated"):
    global next_edge_id
    e = {"id": next_edge_id, "from": src["id"], "to": dst["id"],
         "pct": pct, "type": etype}
    edges.append(e)
    next_edge_id += 1
    return e

# ── Layout helpers ─────────────────────────────────────────────────
# Tier-based vertical layout: each tier at a Y level, horizontal spread.
TIER_Y = [80, 280, 480, 680, 880, 1080, 1280, 1480, 1680]
COL_W = 180  # horizontal spacing per node within a tier

def spread_x(idx, total, center_x=6000):
    """Spread idx-of-total nodes horizontally around center_x."""
    if total == 1:
        return center_x
    span = (total - 1) * COL_W
    return int(center_x - span / 2 + idx * COL_W)

# ════════════════════════════════════════════════════════════════════
# STRUCTURE
# ════════════════════════════════════════════════════════════════════

# ── Tier 0: UPE (Seoul, KR) ────────────────────────────────────────
upe = add_node("KR", 6000, TIER_Y[0], name="Seoul")  # UPE = Seoul
# (자기주식 없음 — 사용자 요청으로 제거)

# ── Tier 1: 5 Regional HQs (consolidated 100% with UPE) ────────────
# These will be IPE candidates (intermediate parent entities in IIR countries)
regional_specs = [
    ("JP", "Tokyo"),         # Asia-Pacific
    ("US", "New York"),      # North America
    ("DE", "Frankfurt"),     # Europe
    ("GB", "London"),        # UK/Ireland
    ("BR", "São Paulo"),     # Latin America
]
regional = []
for i, (cc, nm) in enumerate(regional_specs):
    n = add_node(cc, spread_x(i, 5), TIER_Y[1], name=nm)
    regional.append(n)
    add_edge(upe, n, 100, "consolidated")

# ── POPE setup: HQ owned <80% by UPE (creates POPE candidate) ──────
# We need POPE = entity in IIR country, ownership ≤ 80% by UPE indirect.
# Plan: a "EU Holding" entity (CH, Zurich) — UPE owns 70% directly,
# remaining 30% owned by an external "investor" entity (no-globe).
# Then EU Holding owns several CEs in DE/FR/IT/ES.
# Wait — POPE Test 2: UPE direct/indirect ownership ≤ 80%. But for the entity
# to be a CE itself, it needs to be consolidated with UPE somehow. Hmm.
#
# Actually re-reading: POPE = CE in IIR country that owns other CEs AND
# UPE owns ≤80% of it. So we need:
#   - UPE → POPE_candidate via consolidated edge at <80%? Engine's calcOwnership
#     uses consolidated edge ratios for ownership.
#   - POPE_candidate → its CE subs via consolidated 100% (sub-tree)
#
# So POPE_candidate is consolidated with UPE but at <80% (e.g., UPE 75%).
# The remaining 25% can be ignored (external minority).
pope_eu = add_node("CH", spread_x(2, 5) + 1100, TIER_Y[1] + 100, name="Zurich")
add_edge(upe, pope_eu, 75, "consolidated")  # POPE: UPE owns 75% (≤80%)

# Another POPE in Asia: UPE owns 70% of "AsiaPac Hold" in IE
pope_asia = add_node("IE", spread_x(0, 5) - 800, TIER_Y[1] + 100, name="Dublin")
add_edge(upe, pope_asia, 70, "consolidated")

# ── Tier 2: Country HQs under Regional HQs ─────────────────────────
# Each Regional HQ owns 100% of country-HQ entities in its region.
asia_countries = ["JP", "CN", "IN", "ID", "SG", "HK"]
na_countries   = ["US", "CA", "MX"]
eu_countries   = ["DE", "FR", "IT", "ES", "NL", "SE", "NO", "LU"]
uk_countries   = ["GB", "IE"]
latam_countries = ["BR"]

# Plus POPE-managed sub-regions
pope_eu_countries = ["CH", "FR", "IT", "ES"]  # POPE owns these in EU (overlap with EU regional OK — we'll use separate HQ entities)
pope_asia_countries = ["IN", "ID", "SG"]      # POPE owns these in Asia

country_hqs = {}  # country_code → list of HQ entity dicts

# Helper to create country-HQ
def create_country_hq(parent, cc, x_offset_idx, total_in_parent, tier_y_idx, parent_x_anchor):
    n = add_node(cc, spread_x(x_offset_idx, total_in_parent, parent_x_anchor), TIER_Y[tier_y_idx])
    if n is None:
        return None
    add_edge(parent, n, 100, "consolidated")
    country_hqs.setdefault(cc, []).append(n)
    return n

# KR domestic sub-HQs — UPE directly owns several KR HQs (Korean home market)
for i, nm in enumerate(["Busan", "Incheon", "Daegu"]):
    n = add_node("KR", spread_x(i, 3, 6000) + 0, TIER_Y[1] + 200, name=nm)
    add_edge(upe, n, 100, "consolidated")
    country_hqs.setdefault("KR", []).append(n)

# Regional HQ Asia (JP) → country HQs in asia_countries
for i, cc in enumerate(asia_countries):
    create_country_hq(regional[0], cc, i, len(asia_countries), 2, spread_x(0, 5))

# Regional HQ NA (US) → country HQs
for i, cc in enumerate(na_countries):
    create_country_hq(regional[1], cc, i, len(na_countries), 2, spread_x(1, 5))

# Regional HQ EU (DE) → country HQs
for i, cc in enumerate(eu_countries):
    create_country_hq(regional[2], cc, i, len(eu_countries), 2, spread_x(2, 5))

# Regional HQ UK (GB) → country HQs
for i, cc in enumerate(uk_countries):
    create_country_hq(regional[3], cc, i, len(uk_countries), 2, spread_x(3, 5))

# Regional HQ LATAM (BR) → BR itself is already the HQ, add a couple more BR sub-HQs
country_hqs.setdefault("BR", []).append(regional[4])
for i, nm in enumerate(["Rio de Janeiro", "Brasília"]):
    n = add_node("BR", regional[4]["x"] + (i-0.5)*200, TIER_Y[2], name=nm)
    add_edge(regional[4], n, 100, "consolidated")
    country_hqs["BR"].append(n)

# POPE EU → its sub HQs
pope_eu_subs = []
for i, cc in enumerate(pope_eu_countries):
    n = add_node(cc, spread_x(i, len(pope_eu_countries), 4500), TIER_Y[2] + 100)
    if n is None: continue
    add_edge(pope_eu, n, 100, "consolidated")
    pope_eu_subs.append(n)
    country_hqs.setdefault(cc, []).append(n)

# POPE Asia → its sub HQs
pope_asia_subs = []
for i, cc in enumerate(pope_asia_countries):
    n = add_node(cc, spread_x(i, len(pope_asia_countries), 1800), TIER_Y[2] + 100)
    if n is None: continue
    add_edge(pope_asia, n, 100, "consolidated")
    pope_asia_subs.append(n)
    country_hqs.setdefault(cc, []).append(n)

# ── Tier 3-5: Operational subsidiaries under each country HQ ───────
# Each country HQ gets several operating subs (consolidated 100%).
# Some sub-trees go deeper (2-3 levels of consolidation).
def add_subtree(root, cc, depth, max_children, total_target, current_count):
    """Recursively add a consolidated sub-tree under root. 일부는 cross-country (multinational 특성).
    Stops at depth 5 or pool exhaustion."""
    if current_count[0] >= total_target or depth >= 5:
        return
    n_children = random.randint(2, max_children)
    children = []
    for _ in range(n_children):
        if current_count[0] >= total_target:
            break
        # 20% 확률로 child의 국가 변경 — 다국적그룹 cross-country 특성
        child_cc = cc
        if random.random() < 0.20 and depth >= 1:
            # 풀 여유 있는 다른 국가 후보 중 무작위
            other_pool = [c for c in CITIES if c != cc and _idx[c] < len(CITIES[c]) - 2]
            if other_pool:
                child_cc = random.choice(other_pool)
        x = root["x"] + random.randint(-400, 400)
        y = TIER_Y[depth + 2] if depth + 2 < len(TIER_Y) else TIER_Y[-1]
        c = add_node(child_cc, x, y)
        if c is None:
            continue  # 풀 소진 — 다음 시도
        add_edge(root, c, 100, "consolidated")
        children.append(c)
        current_count[0] += 1
    for c in children:
        add_subtree(c, c["country"], depth + 1, max(2, max_children - 1), total_target, current_count)

# Target ~400 nodes total. Allocate subs proportional to country city pool size
# (countries with more cities get more subs).
all_country_hqs = []
for cc, hqs in country_hqs.items():
    for hq in hqs:
        all_country_hqs.append((cc, hq))

# Aim for ~400 total (subs + ~30 baseline + ~25 JV/MOPE/inv).
TARGET_SUBS = 360
total_pool = sum(max(1, len(CITIES[cc]) - _idx[cc]) for cc, _ in all_country_hqs)
for cc, hq in all_country_hqs:
    if len(nodes) >= 395:
        break
    remaining_in_country = len(CITIES[cc]) - _idx[cc]
    # Allocate proportionally; min 6, max 22 — fallback names handle exhausted city pools
    quota = max(6, min(22, int(TARGET_SUBS * max(1,remaining_in_country) / total_pool) + 4))
    counter = [0]
    add_subtree(hq, cc, 1, 5, quota, counter)

# ── JV setup ────────────────────────────────────────────────────────
# Create 2-3 JV groups. JV = equity edge (50%) from a consolidated parent.
# JV_sub = consolidated 100% under JV.
# JV groups exercise the JV/JV_sub MNE-within-MNE logic.
jv_parent_1 = country_hqs["DE"][0]  # German HQ
jv_root_1 = add_node("BM", jv_parent_1["x"] + 400, jv_parent_1["y"] + 200, name="Hamilton")
add_edge(jv_parent_1, jv_root_1, 50, "equity")  # 50/50 JV
# JV subs (BM 도시풀 소진 가능 → None 가드)
for i in range(3):
    sub = add_node("BM", jv_root_1["x"] + (i-1)*200, jv_root_1["y"] + 200)
    if sub is None: continue
    add_edge(jv_root_1, sub, 100, "consolidated")
# Add a JV sub in another country
jv_sub_de = add_node("DE", jv_root_1["x"] - 400, jv_root_1["y"] + 200)
if jv_sub_de: add_edge(jv_root_1, jv_sub_de, 100, "consolidated")

jv_parent_2 = country_hqs["US"][0]
jv_root_2 = add_node("KY", jv_parent_2["x"] + 400, jv_parent_2["y"] + 200, name="George Town")
add_edge(jv_parent_2, jv_root_2, 50, "equity")
for i in range(2):
    sub = add_node("KY", jv_root_2["x"] + (i-0.5)*200, jv_root_2["y"] + 200)
    if sub is None: continue
    add_edge(jv_root_2, sub, 100, "consolidated")
jv_sub_us = add_node("US", jv_root_2["x"] - 300, jv_root_2["y"] + 200)
if jv_sub_us: add_edge(jv_root_2, jv_sub_us, 100, "consolidated")

# ── MOPE sub-group setup ───────────────────────────────────────────
# MOPE: minority-owned parent entity. UPE direct/indirect ownership ≤ 30%
# of the MOPE root, MOPE root must control other CEs.
# Easiest: UPE owns 25% of a HoldCo directly, HoldCo consolidates subs.
# But for HoldCo to be in MNE group, it needs to be controlled (consolidated).
# Actually MOPE rules: it's a non-UPE constituent that owns other CEs but where
# UPE has ≤ 30% indirect ownership (minority-owned). So we need a consolidated
# (not equity!) edge with low percentage. Hmm but consolidated implies control.
#
# In Korean tax law context, MOPE is part of the MNE Group through control
# (consolidated) but UPE's economic ownership is minor.
# Set up: UPE → MOPE_root via consolidated 30% (consolidated edge from UPE to
# show inclusion in MNE Group, but at <30% ownership ratio).
mope_root = add_node("AU", 3200, TIER_Y[1] + 100, name="Sydney")
add_edge(upe, mope_root, 25, "consolidated")  # MOPE: UPE owns 25%
for i in range(4):
    sub = add_node("AU", 3200 + (i-1.5)*200, TIER_Y[2] + 100)
    if sub is None: continue
    add_edge(mope_root, sub, 100, "consolidated")

# MOPE #2 — 캐나다 소수지분 모기업 (UPE 28% 보유). 영국 regional이 컨트롤하지 않고 직접 UPE에서.
mope_root_2 = add_node("CA", 2400, TIER_Y[1] + 100)
add_edge(upe, mope_root_2, 28, "consolidated")
for i in range(3):
    sub = add_node("CA", 2400 + (i-1)*200, TIER_Y[2] + 100)
    if sub is None: continue
    add_edge(mope_root_2, sub, 100, "consolidated")

# MOPE #3 — 멕시코 소수지분 (Regional NA가 25% 컨트롤)
mope_root_3 = add_node("MX", regional[1]["x"]+1100, TIER_Y[2])
add_edge(regional[1], mope_root_3, 25, "consolidated")
for i in range(3):
    sub = add_node("MX", mope_root_3["x"] + (i-1)*200, TIER_Y[3])
    if sub is None: continue
    add_edge(mope_root_3, sub, 100, "consolidated")

# MOPE #4 — 인도네시아 소수지분 (Regional Asia가 22% 컨트롤)
mope_root_4 = add_node("ID", regional[0]["x"]-1100, TIER_Y[2])
add_edge(regional[0], mope_root_4, 22, "consolidated")
for i in range(3):
    sub = add_node("ID", mope_root_4["x"] + (i-1)*200, TIER_Y[3])
    if sub is None: continue
    add_edge(mope_root_4, sub, 100, "consolidated")

# ── Investment entities — 금융센터 곳곳에 배치(특수 판정 시나리오 확보) ─────────
# Investment fund (LU) — 룩셈부르크 펀드 비히클
inv1 = add_node("LU", 9500, TIER_Y[2], entity_type="investment", name="Luxembourg City")
add_edge(regional[2], inv1, 100, "consolidated")

# Investment fund (SG) — 싱가포르 패밀리오피스
inv2 = add_node("SG", 1200, TIER_Y[2], entity_type="investment", name="Marina Bay")
add_edge(regional[0], inv2, 100, "consolidated")

# Investment fund (KY) — 케이만 헤지펀드
inv3 = add_node("KY", 9700, TIER_Y[3], entity_type="investment", name="Cayman Brac")
add_edge(regional[2], inv3, 100, "consolidated")

# Investment fund (HK) — 홍콩 자산운용. 명시 이름으로 풀 소진 영향 없음.
inv4 = add_node("HK", 800, TIER_Y[3], entity_type="investment", name="Lantau")
add_edge(regional[0], inv4, 100, "consolidated")

# Investment fund (CH) — 스위스 PE
inv5 = add_node("CH", pope_eu["x"] + 600, TIER_Y[2] + 200, entity_type="investment", name="Chur")
add_edge(pope_eu, inv5, 100, "consolidated")

# ── Excluded entities — 비영리/연기금/정부기관 등 GloBE 제외기업 ──────────────
# Non-profit foundation (NL)
exc1 = add_node("NL", 8500, TIER_Y[2] + 100, entity_type="excluded", name="Eindhoven")
add_edge(regional[2], exc1, 100, "consolidated")

# Pension fund (CH) — 스위스 연기금
exc2 = add_node("CH", pope_eu["x"] - 300, TIER_Y[2] + 200, entity_type="excluded", name="Neuchâtel")
add_edge(pope_eu, exc2, 100, "consolidated")

# Charity (JP) — 일본 공익재단
exc3 = add_node("JP", regional[0]["x"] + 600, TIER_Y[2] + 200, entity_type="excluded", name="Naha")
add_edge(regional[0], exc3, 100, "consolidated")

# ════════════════════════════════════════════════════════════════════
# 후처리 — 지분관계 다양성 주입
#   1) Joint subsidiary: 한 기업이 두 모기업에 의해 공동 연결 (60%+40% 연결)
#   2) 전략적 지분: 1차 연결 70~80% + 다른 sub-tree 기업의 지분법 20~30%
#   3) Cross-sub-group equity: 다른 sub-tree 기업이 추가 지분법 보유
# UPE 직접 자회사·Regional HQ·POPE·MOPE·JV root 같은 핵심 노드는 건드리지 않음.
# ════════════════════════════════════════════════════════════════════
rng2 = random.Random(99)

# 보호 ID 목록 — 구조적으로 중요한 핵심 노드
protected_ids = {upe["id"]}
protected_ids.update(r["id"] for r in regional)
protected_ids.update([pope_eu["id"], pope_asia["id"], mope_root["id"]])
protected_ids.update([jv_root_1["id"], jv_root_2["id"]])
# Country HQs도 보호 (multi-parent 만들면 트리 구조 깨짐)
for hqs in country_hqs.values():
    for hq in hqs:
        protected_ids.add(hq["id"])
# Investment/excluded entity는 보호
for n in nodes:
    if n["entityType"] != "general":
        protected_ids.add(n["id"])

# 노드 ID → 노드 매핑
nodes_by_id = {n["id"]: n for n in nodes}

# 노드의 primary parent edge 찾기 (consolidated 100%, in==1 케이스만)
def primary_edge_of(node_id):
    incoming = [e for e in edges if e["to"] == node_id and e["from"] != node_id]
    if len(incoming) != 1: return None
    e = incoming[0]
    if e["type"] != "consolidated" or e["pct"] != 100: return None
    return e

# UPE에서 도달 가능한 조상 집합 (cycle 방지용)
def ancestors_of(node_id, max_depth=20):
    visited = set()
    stack = [(node_id, 0)]
    while stack:
        nid, d = stack.pop()
        if d > max_depth or nid in visited: continue
        visited.add(nid)
        for e in edges:
            if e["to"] == nid and e["from"] != nid:
                stack.append((e["from"], d+1))
    return visited

# 노드의 자손 집합 (cycle 방지용 — 자손을 새 부모로 고르면 cycle 발생)
def descendants_of(node_id, max_depth=20):
    visited = set()
    stack = [(node_id, 0)]
    while stack:
        nid, d = stack.pop()
        if d > max_depth or nid in visited: continue
        visited.add(nid)
        for e in edges:
            if e["from"] == nid and e["to"] != nid:
                stack.append((e["to"], d+1))
    return visited

# cycle 방지를 위해 후보에서 제외할 노드 집합 (자기 자신 + 조상 + 자손)
def cycle_exclusion_set(node_id):
    s = ancestors_of(node_id) | descendants_of(node_id)
    s.add(node_id)
    return s

# (A) Joint subsidiary 패턴 — 12개 정도 주입
joint_target = 14
joint_added = 0
candidates = [n for n in nodes if n["id"] not in protected_ids and primary_edge_of(n["id"])]
rng2.shuffle(candidates)
for cand in candidates:
    if joint_added >= joint_target: break
    pe = primary_edge_of(cand["id"])
    if not pe: continue
    cand_country = cand["country"]
    # 새 부모 찾기 — cross-country 다국적 패턴 강화 (절반 정도는 다른 국가)
    # 조상+자손+자기 모두 제외해야 cycle 안 생김
    excl = cycle_exclusion_set(cand["id"])
    prefer_cross = (rng2.random() < 0.5)
    if prefer_cross:
        pool = [n for n in nodes if n["id"] not in excl
                and n["entityType"] == "general"
                and n["country"] != cand_country]
        if not pool:
            pool = [n for n in nodes if n["id"] not in excl
                    and n["entityType"] == "general"]
    else:
        pool = [n for n in nodes if n["id"] not in excl
                and n["entityType"] == "general"
                and n["country"] == cand_country]
        if not pool:
            pool = [n for n in nodes if n["id"] not in excl
                    and n["entityType"] == "general"]
    if not pool: continue
    new_parent = rng2.choice(pool)
    # primary 100% → 60% 로 축소, 새 부모가 40% 연결
    pe["pct"] = 60
    add_edge(new_parent, cand, 40, "consolidated")
    joint_added += 1

# (B) 전략적 지분 — 8개 정도 (연결 75% + 다른 sub-tree 지분법 25%)
strategic_target = 8
strategic_added = 0
candidates = [n for n in nodes if n["id"] not in protected_ids and primary_edge_of(n["id"])]
rng2.shuffle(candidates)
for cand in candidates:
    if strategic_added >= strategic_target: break
    pe = primary_edge_of(cand["id"])
    if not pe: continue
    excl = cycle_exclusion_set(cand["id"])
    # 지분법 보유 측 — 다른 국가의 다른 sub-tree에서 (cross-regional)
    pool = [n for n in nodes if n["id"] not in excl
            and n["entityType"] == "general"
            and n["country"] != cand["country"]]
    if not pool: continue
    equity_holder = rng2.choice(pool)
    pe["pct"] = 75
    add_edge(equity_holder, cand, 25, "equity")
    strategic_added += 1

# (C) Cross sub-group equity — 6개 (primary를 80%로 줄이고 다른 sub-tree에서 20% 지분법)
# 아직 안 건드린 100% consolidated 노드 대상.
cross_target = 6
cross_added = 0
shuffled = list(nodes)
rng2.shuffle(shuffled)
for cand in shuffled:
    if cross_added >= cross_target: break
    if cand["id"] in protected_ids: continue
    pe = primary_edge_of(cand["id"])
    if not pe: continue  # 이미 변형된 노드 제외 (primary_edge_of은 100% 단일 부모만 반환)
    excl = cycle_exclusion_set(cand["id"])
    parent_country = nodes_by_id[pe["from"]]["country"]
    # 지분법 보유 측 — primary 부모와 다른 sub-tree, 다른 국가에서
    pool = [n for n in nodes if n["id"] not in excl
            and n["entityType"] == "general"
            and n["country"] != cand["country"]
            and n["country"] != parent_country]
    if not pool: continue
    holder = rng2.choice(pool)
    pe["pct"] = 80
    add_edge(holder, cand, 20, "equity")
    cross_added += 1

print(f"\n지분관계 다양성 패턴 주입:")
print(f"  Joint subsidiary (공동연결): {joint_added}개")
print(f"  전략적 지분 (연결+지분법): {strategic_added}개")
print(f"  Cross sub-group equity: {cross_added}개")

# Print summary
print(f"\nTotal nodes: {len(nodes)}")
print(f"Total edges: {len(edges)}")
country_counts = {}
for n in nodes:
    country_counts[n["country"]] = country_counts.get(n["country"], 0) + 1
print("Countries:", sorted(country_counts.items(), key=lambda x: -x[1]))

# ── Country GloBE settings — balanced IIR/UTPR/QDMTT mix ───────────
# countryGlobeSettings: [["CC", {hasIIR:bool, hasUTPR:bool, hasQDMTT:bool, qdmttSafeHarbor:bool}], ...]
country_settings = [
    ["KR", {"hasIIR": True,  "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": True}],   # Full coverage
    ["US", {"hasIIR": True,  "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["JP", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],   # IIR + UTPR + QDMTT
    ["DE", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": False}],  # No SH — residual to UTPR/IIR
    ["GB", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["FR", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["IT", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["ES", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["NL", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["IE", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["CA", {"hasIIR": True,  "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["AU", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["CH", {"hasIIR": True,  "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["SE", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["NO", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["LU", {"hasIIR": True,  "hasUTPR": True,  "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["CN", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": False}],  # QDMTT only, non-SH
    ["BR", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["MX", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": False, "qdmttSafeHarbor": False}],  # Nothing
    ["IN", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": False, "qdmttSafeHarbor": False}],
    ["ID", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": False, "qdmttSafeHarbor": False}],
    ["SG", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["HK", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": True,  "qdmttSafeHarbor": True}],
    ["BM", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": False, "qdmttSafeHarbor": False}],  # Low-tax (UTPR target)
    ["KY", {"hasIIR": False, "hasUTPR": False, "hasQDMTT": False, "qdmttSafeHarbor": False}],
]

# ── Output P2A ──────────────────────────────────────────────────────
out = {
    "version": 1,
    "savedAt": "2026-05-27T00:00:00.000Z",
    "referenceDate": "2024-12-31",
    "canvas": {"panX": -120, "panY": 30, "zoom": 0.15},
    "nodeSeq": next_node_id,
    "edgeSeq": next_edge_id,
    "nodes": nodes,
    "edges": edges,
    "countryGlobeSettings": country_settings,
}

with open("/workspaces/codespaces-blank/P2A_MNE_400_demo.p2a", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"Wrote /workspaces/codespaces-blank/P2A_MNE_400_demo.p2a")

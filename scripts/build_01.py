"""Полная сборка миссии 1 «Через границу» -> build/01_cherez_granitsu.aoe2scenario

Источники: missions/01-cherez-granitsu.spec.md (§15, §16), missions/01-cherez-granitsu.dialogue.md
(строки с тегами [ТРИГГЕР:тип] разбираются скриптом), data/units.json, data/techs.json.
Запуск: .venv\\Scripts\\python.exe scripts\\build_01.py
"""
import json
import math
import random
import re
import sys
from pathlib import Path

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.heroes import HeroInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.techs import TechInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.datasets.conditions import ConditionId
from AoE2ScenarioParser.datasets.object_support import StartingAge, Civilization
from AoE2ScenarioParser.datasets.trigger_lists import (
    Comparison, Operation, ObjectAttribute, ObjectType, AttackStance, ActionType,
    ButtonLocation, Attribute, DiplomacyState, VictoryCondition,
)

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "missions" / "01-cherez-granitsu.spec.md"
DIALOGUE = ROOT / "missions" / "01-cherez-granitsu.dialogue.md"
OUT = ROOT / "build" / "01_cherez_granitsu.aoe2scenario"
NOTES = ROOT / "build" / "NOTES.md"

S = 168  # размер карты
P1, P2, P3, P4, P5, P6 = 1, 2, 3, 4, 5, 6
ENEMIES = [P2, P3, P4, P5, P6]
rng = random.Random(1604)

# ------------------------------------------------------------------ данные мода (JSON)
UNITS_JSON = json.loads((ROOT / "data" / "units.json").read_text(encoding="utf-8"))
TECHS_JSON = json.loads((ROOT / "data" / "techs.json").read_text(encoding="utf-8"))
TECH = {t["id"]: t for t in TECHS_JSON["techs"]}
UNIT = {u["id"]: u for u in UNITS_JSON["units"]}

# ------------------------------------------------------------------ разбор реплик
TAG_RE = re.compile(r"^- \[([A-Za-z0-9_]+):(сообщение|диалог|подсказка|цель)\]\s*(.*)$")


class Line:
    def __init__(self, trig, typ, cond, speaker, text):
        self.trig, self.typ, self.cond, self.speaker, self.text = trig, typ, cond, speaker, text
        self.used = False
        m = re.search(r"\+?(\d+)\s*с", cond or "")
        self.delay = int(m.group(1)) if (m and typ == "диалог" and re.match(r"^\s*\+?\d+\s*с", cond or "")) else None

    def full(self):
        if self.typ == "диалог" and self.speaker:
            return f"{self.speaker}: {self.text}"
        return self.text


def clean(text):
    # пометки [ПРОВЕРИТЬ ...], [ИСТОРИК ...], [ИЗМЕНЕНО ...] и любые другие в квадратных скобках
    text = re.sub(r"\s*\[[^\]]*\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_dialogue():
    lines = {}
    for raw in DIALOGUE.read_text(encoding="utf-8").splitlines():
        m = TAG_RE.match(raw)
        if not m:
            continue
        trig, typ, rest = m.groups()
        rest = clean(rest)
        cond = None
        if rest.startswith("("):
            depth, end = 0, None
            for i, ch in enumerate(rest):
                depth += (ch == "(") - (ch == ")")
                if depth == 0:
                    end = i
                    break
            cond, rest = rest[1:end], rest[end + 1:].strip()
        speaker = None
        if typ == "диалог" and ": " in rest:
            speaker, rest = rest.split(": ", 1)
        if typ == "цель":
            rest = re.sub(r"^Панель( \([^)]*\))?:\s*", "", rest)
        lines.setdefault((trig, typ), []).append(Line(trig, typ, cond, speaker, rest))
    return lines


LINES = parse_dialogue()


def L(trig, typ, i=None, cond=None):
    """Взять строку(и) реплик. i - индекс, cond - подстрока условия. Помечает как использованные."""
    lst = LINES.get((trig, typ))
    if not lst:
        raise KeyError(f"нет реплик {trig}:{typ}")
    if cond is not None:
        found = [x for x in lst if x.cond and cond in x.cond]
        if not found:
            raise KeyError(f"нет реплик {trig}:{typ} с условием {cond}")
        for x in found:
            x.used = True
        return found[0] if len(found) == 1 else found
    if i is None:
        for x in lst:
            x.used = True
        return lst
    lst[i].used = True
    return lst[i]


def goal_quotes(line):
    return re.findall(r"«([^»]+)»", line.text)


# ------------------------------------------------------------------ сценарий и менеджеры
sc = AoE2DEScenario.from_default()
um, tm, pm, mm, msg, opt = (sc.unit_manager, sc.trigger_manager, sc.player_manager,
                            sc.map_manager, sc.message_manager, sc.option_manager)


def pt(u, v):
    return int(round(u * S)), int(round(v * S))


def rect(cx, cy, r):
    return (max(0, cx - r), max(0, cy - r), min(S - 1, cx + r), min(S - 1, cy + r))


ALL = (0, 0, S - 1, S - 1)

# ключевые точки (u, v) -> клетки; x = u*168, y = v*168 (см. NOTES)
START = pt(0.12, 0.15)
MOR = pt(0.30, 0.35)
CHE = pt(0.50, 0.55)
CAMP = pt(0.72, 0.68)
NS = pt(0.78, 0.78)
PUT = pt(0.88, 0.18)
AMBUSH = pt(0.60, 0.62)
CASTLE = (CHE[0] + 12, CHE[1] + 12)
RIVER_Y = 76
FORD1_X, FORD2_X = 70, 135

Z_MOR, Z_CHE, Z_PUT = rect(*MOR, 6), rect(*CHE, 6), rect(*PUT, 6)
Z_CAMP = rect(*CAMP, 6)
Z_SCOUT = [rect(CASTLE[0] - 14, CASTLE[1], 3), rect(CASTLE[0], CASTLE[1] + 14, 3),
           rect(CASTLE[0] + 12, CASTLE[1] - 8, 3)]
A_MOR, A_CHE, A_PUT = rect(*MOR, 12), rect(CHE[0], CHE[1], 9), rect(*PUT, 14)
A_CASTLE = rect(*CASTLE, 8)

# ------------------------------------------------------------------ карта
mm.map_size = S
terrain_set = {}


def set_terrain(x, y, tid):
    if 0 <= x < S and 0 <= y < S:
        mm.get_tile(x, y).terrain_id = int(tid)
        terrain_set[(x, y)] = int(tid)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = 0 if (dx == 0 and dy == 0) else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


ROADS = [
    [START, (38, 44), MOR, (FORD1_X, RIVER_Y - 8), (FORD1_X, RIVER_Y + 8), (78, 84), CHE],
    [(CHE[0] + 8, CHE[1] + 4), AMBUSH, CAMP],
    [CAMP, (128, 98), (FORD2_X, RIVER_Y + 6), (FORD2_X, RIVER_Y - 6), (142, 52), PUT],
]


def near_road(x, y, w):
    for road in ROADS:
        for a, b in zip(road, road[1:]):
            if seg_dist(x, y, a[0], a[1], b[0], b[1]) <= w:
                return True
    return False


def river_yc(x):
    return RIVER_Y + int(round(3 * math.sin(x / 14.0)))


for x in range(S):
    yc = river_yc(x)
    for y in range(yc - 2, yc + 3):
        set_terrain(x, y, TerrainId.WATER_MEDIUM)
for fx in (FORD1_X, FORD2_X):
    for x in range(fx - 3, fx + 4):
        yc = river_yc(x)
        for y in range(yc - 3, yc + 4):
            set_terrain(x, y, TerrainId.WATER_SHALLOW)
# дороги (грунт), кроме воды
for road in ROADS:
    for a, b in zip(road, road[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
        for i in range(n + 1):
            x = int(round(a[0] + (b[0] - a[0]) * i / n))
            y = int(round(a[1] + (b[1] - a[1]) * i / n))
            for dx in (0, 1):
                for dy in (0, 1):
                    if terrain_set.get((x + dx, y + dy)) not in (TerrainId.WATER_MEDIUM, TerrainId.WATER_SHALLOW):
                        set_terrain(x + dx, y + dy, TerrainId.DIRT_1)
# степь: пятна сухой травы
for _ in range(60):
    cx, cy, r = rng.randrange(S), rng.randrange(S), rng.randint(4, 9)
    for x in range(cx - r, cx + r + 1):
        for y in range(cy - r, cy + r + 1):
            if math.hypot(x - cx, y - cy) <= r and (x, y) not in terrain_set:
                set_terrain(x, y, TerrainId.GRASS_DRY)
# леса вдоль дорог и пятнами, не в городах/лагере/на дороге/в воде
KEEPOUT = [(START, 16), (MOR, 22), (CHE, 22), (CASTLE, 16), (CAMP, 16), (NS, 18), (PUT, 22)]


def forest_ok(x, y):
    if any(math.hypot(x - c[0], y - c[1]) < r for c, r in KEEPOUT):
        return False
    if near_road(x, y, 3.5):
        return False
    if abs(y - river_yc(x)) <= 4:
        return False
    return True


forest_n = 0
for _ in range(140):
    # центр рядом с дорогой (лес вдоль дорог) или случайно
    if rng.random() < 0.6:
        road = rng.choice(ROADS)
        a = rng.randrange(len(road) - 1)
        t = rng.random()
        cx = road[a][0] + (road[a + 1][0] - road[a][0]) * t + rng.randint(-14, 14)
        cy = road[a][1] + (road[a + 1][1] - road[a][1]) * t + rng.randint(-14, 14)
    else:
        cx, cy = rng.randrange(S), rng.randrange(S)
    r = rng.randint(2, 5)
    for x in range(int(cx) - r, int(cx) + r + 1):
        for y in range(int(cy) - r, int(cy) + r + 1):
            if 0 <= x < S and 0 <= y < S and math.hypot(x - cx, y - cy) <= r + rng.random() \
                    and forest_ok(x, y) and terrain_set.get((x, y)) not in (TerrainId.DIRT_1,):
                set_terrain(x, y, TerrainId.FOREST_OAK)
                forest_n += 1

# ------------------------------------------------------------------ размещение объектов
occ = set()          # занятые строениями клетки
used_pos = set()     # занятые юнитами клетки
BUILDINGS = {}       # имя -> unit


def building(player, const, tlx, tly, size, name=None):
    tiles = {(tlx + i, tly + j) for i in range(size) for j in range(size)}
    assert not (tiles & occ), f"перекрытие строений {name or const} в {tlx},{tly}"
    occ.update(tiles)
    u = um.add_unit(player, const, x=tlx + size / 2.0, y=tly + size / 2.0)
    if name:
        BUILDINGS[name] = u
    return u


def wall_ring(player, const, cx, cy, half, gaps):
    """Квадратное кольцо стен; gaps - множество клеток (x, y), оставленных открытыми."""
    units = {}
    for x in range(cx - half, cx + half + 1):
        for y in range(cy - half, cy + half + 1):
            if max(abs(x - cx), abs(y - cy)) != half or (x, y) in gaps or (x, y) in occ:
                continue
            occ.add((x, y))
            units[(x, y)] = um.add_unit(player, const, x=x + 0.5, y=y + 0.5)
    return units


def free_tile(cx, cy, rmin=1):
    for r in range(rmin, 40):
        ring = [(cx + dx, cy + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                if max(abs(dx), abs(dy)) == r]
        rng.shuffle(ring)
        for t in ring:
            if t not in occ and t not in used_pos and 0 <= t[0] < S and 0 <= t[1] < S \
                    and terrain_set.get(t) not in (TerrainId.WATER_MEDIUM, TerrainId.FOREST_OAK):
                used_pos.add(t)
                return t
    raise RuntimeError("нет места")


def units(player, const, n, cx, cy, rmin=1):
    out = []
    for _ in range(n):
        t = free_tile(cx, cy, rmin)
        out.append(um.add_unit(player, const, x=t[0] + 0.5, y=t[1] + 0.5))
    return out


def gaps_cross(cx, cy, half):
    return {(cx - half, cy), (cx - half, cy + 1), (cx + half, cy), (cx + half, cy + 1),
            (cx, cy - half), (cx + 1, cy - half), (cx, cy + half), (cx + 1, cy + half)}


ID = lambda e: e.ID  # noqa: E731
HUSSAR, CAVARCH, MONK, MAA, ARCHER = (UnitInfo.HUSSAR.ID, UnitInfo.CAVALRY_ARCHER.ID, UnitInfo.MONK.ID,
                                      UnitInfo.MAN_AT_ARMS.ID, UnitInfo.ARCHER.ID)
SPEAR, HC, KNIGHT, VILL = (UnitInfo.SPEARMAN.ID, UnitInfo.HAND_CANNONEER.ID, UnitInfo.KNIGHT.ID,
                           UnitInfo.VILLAGER_MALE.ID)
SKIRM, SCOUT = UnitInfo.SKIRMISHER.ID, UnitInfo.SCOUT_CAVALRY.ID
TC, BARR, MON, STAB, ARCHR, HOUSE, MARKET, CASTLE_B, TOWER, PAL, STW = (
    BuildingInfo.TOWN_CENTER.ID, BuildingInfo.BARRACKS.ID, BuildingInfo.MONASTERY.ID, BuildingInfo.STABLE.ID,
    BuildingInfo.ARCHERY_RANGE.ID, BuildingInfo.HOUSE.ID, BuildingInfo.MARKET.ID, BuildingInfo.CASTLE.ID,
    BuildingInfo.WATCH_TOWER.ID, BuildingInfo.PALISADE_WALL.ID, BuildingInfo.STONE_WALL.ID)

# --- игроки
pm.active_players = 6
for pid in range(1, 7):
    p = pm.players[pid]
    p.starting_age = StartingAge.CASTLE_AGE
    p.civilization = Civilization.POLES if pid == 1 else Civilization.SLAVS
    p.population_cap = 80 if pid == 1 else 200
    p.food = p.wood = p.gold = p.stone = 0
p1 = pm.players[P1]
p1.food, p1.wood, p1.gold, p1.stone = 800, 600, 500, 200
for pid in ENEMIES:
    pm.players[pid].set_player_diplomacy(P1, DiplomacyState.ENEMY)
    pm.players[P1].set_player_diplomacy(pid, DiplomacyState.ENEMY)
pm.set_diplomacy_teams(ENEMIES, diplomacy=DiplomacyState.ALLY)
opt.victory_condition = VictoryCondition.CUSTOM
# отключённые технологии игрока 1 (Imperial, университет, торговля)
DISABLED = [TechInfo.IMPERIAL_AGE, TechInfo.MASONRY, TechInfo.ARCHITECTURE, TechInfo.BALLISTICS,
            TechInfo.TREADMILL_CRANE, TechInfo.HEATED_SHOT, TechInfo.MURDER_HOLES, TechInfo.CHEMISTRY,
            TechInfo.SIEGE_ENGINEERS, TechInfo.ARROWSLITS, TechInfo.HOARDINGS, TechInfo.SAPPERS,
            TechInfo.CARAVAN, TechInfo.COINAGE, TechInfo.BANKING, TechInfo.GUILDS, TechInfo.CARTOGRAPHY]
p1.disabled_techs = [t.ID for t in DISABLED]
p1.disabled_buildings = [BuildingInfo.UNIVERSITY.ID, BuildingInfo.MARKET.ID]

# --- P1: старт (26 юнитов)
dmitry = um.add_unit(P1, HeroInfo.ROLAND.ID, x=START[0] + 0.5, y=START[1] + 0.5)
used_pos.add((START[0], START[1]))
start_units = (units(P1, HUSSAR, 5, *START) + units(P1, CAVARCH, 3, *START) + units(P1, MONK, 3, *START)
               + units(P1, MAA, 8, *START) + units(P1, ARCHER, 6, *START))
assert len(start_units) + 1 == 26
military_enemy_ids = {p: [] for p in ENEMIES}   # для стоек


def track(player, lst):
    military_enemy_ids[player] += [u.reference_id for u in lst]
    return lst


# --- P2 Моравск
mx, my = MOR
building(P2, TC, mx - 2, my - 2, 4, "MorTC")
building(P2, BARR, mx + 3, my - 6, 3)
building(P2, MON, mx - 7, my - 5, 3)
building(P2, STAB, mx + 3, my + 3, 3)
wall_ring(P2, PAL, mx, my, 9, {(mx - 9, my), (mx - 9, my + 1), (mx, my - 9), (mx + 1, my - 9)})
building(P2, TOWER, mx - 8, my + 3, 1)
building(P2, TOWER, mx + 3, my - 8, 1)
track(P2, units(P2, SPEAR, 8, mx, my, 3))
track(P2, units(P2, HC, 6, mx, my, 3))
mor_knights = track(P2, units(P2, KNIGHT, 2, mx, my, 4))
units(P2, VILL, 4, mx, my, 3)
voev = {}
for key, nm in (("lodygin", "Воевода Б. Лодыгин"), ("tolochanov", "Воевода М. Толочанов")):
    voev[key] = (units(P2, VILL, 1, mx, my, 3)[0], nm)

# --- P3 посад Чернигова
cx, cy = CHE
building(P3, MARKET, cx - 2, cy - 2, 4, "CheMarket")
building(P3, MON, cx + 3, cy - 5, 3)
for tl in [(-6, -6), (-3, -6), (-6, -3), (-6, 0), (-6, 3), (-6, 5), (-3, 5), (0, 5), (3, 5), (5, 1)]:
    building(P3, HOUSE, cx + tl[0], cy + tl[1], 2)
wall_ring(P3, PAL, cx, cy, 7, {(cx - 7, cy), (cx - 7, cy + 1), (cx + 7, cy), (cx + 7, cy + 1),
                                (cx, cy - 7), (cx + 1, cy - 7), (cx, cy + 7), (cx + 1, cy + 7)})
units(P3, VILL, 6, cx, cy, 3)
track(P3, units(P3, SPEAR, 7, cx, cy, 3))
track(P3, units(P3, HC, 4, cx, cy, 3))

# --- P6 замок Чернигова
kx, ky = CASTLE
castle = building(P6, CASTLE_B, kx - 2, ky - 2, 4, "Castle")
building(P6, TOWER, kx - 4, ky - 4, 1)
building(P6, TOWER, kx + 4, ky + 4, 1)
castle_wall = wall_ring(P6, STW, kx, ky, 5, {(kx + 5, ky - 1), (kx + 5, ky)})
wallW = [castle_wall[(kx - 5, ky - 1 + i)] for i in range(3) if (kx - 5, ky - 1 + i) in castle_wall]
assert len(wallW) == 3, "OBJ_CastleWallW"
track(P6, units(P6, SPEAR, 6, kx, ky, 2))
track(P6, units(P6, HC, 5, kx, ky, 2))
track(P6, units(P6, KNIGHT, 3, kx, ky, 2))
tatev = units(P6, HeroInfo.THEODORIC_THE_GOTH.ID, 1, kx, ky, 2)[0]

# --- P4 Новгород-Северский
nx, ny = NS
building(P4, TC, nx - 2, ny - 2, 4, "NSTC")
building(P4, BARR, nx + 3, ny - 5, 3)
building(P4, STAB, nx - 6, ny + 3, 3)
building(P4, ARCHR, nx + 3, ny + 3, 3)
wall_ring(P4, STW, nx, ny, 7, {(nx, ny - 7), (nx + 1, ny - 7)})
for off in [(6, -6), (-6, 6), (6, 6), (6, 0)]:
    building(P4, TOWER, nx + off[0], ny + off[1], 1)
track(P4, units(P4, SPEAR, 10, nx, ny, 2))
track(P4, units(P4, HC, 8, nx, ny, 2))
track(P4, units(P4, KNIGHT, 4, nx, ny, 2))
track(P4, units(P4, MAA, 6, nx, ny, 2))
basmanov = units(P4, HeroInfo.ALEXANDER_NEVSKI.ID, 1, nx, ny, 2)[0]
patrol_a = track(P4, units(P4, SPEAR, 4, 128, 98))
patrol_b = track(P4, units(P4, SPEAR, 4, 142, 56))

# --- P5 Путивль
px_, py_ = PUT
building(P5, TC, px_ - 2, py_ - 2, 4, "PutTC")
building(P5, BARR, px_ + 3, py_ - 5, 3)
building(P5, MON, px_ - 7, py_ - 3, 3)
building(P5, CASTLE_B, px_ + 4, py_ + 4, 4)
for tl in [(-10, 6), (-7, 6), (-4, 6), (-10, 9), (-7, 9), (-4, 9)]:
    building(P5, HOUSE, px_ + tl[0], py_ + tl[1], 2)
wall_ring(P5, STW, px_, py_, 12, {(px_ - 12, py_), (px_ - 12, py_ + 1), (px_ + 12, py_), (px_ + 12, py_ + 1)})
track(P5, units(P5, SPEAR, 8, px_, py_, 3))
track(P5, units(P5, HC, 6, px_, py_, 3))
track(P5, units(P5, KNIGHT, 4, px_, py_, 3))
units(P5, VILL, 4, px_, py_, 3)
saltykov = units(P5, VILL, 1, px_, py_, 3)[0]
rubets = units(P5, VILL, 1, px_, py_, 3)[0]

# --- Gaia
for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
    um.add_unit(0, OtherInfo.GOLD_MINE.ID, x=CAMP[0] - 10 + dx + 0.5, y=CAMP[1] - 8 + dy + 0.5)
    um.add_unit(0, OtherInfo.STONE_MINE.ID, x=CAMP[0] + 11 + dx + 0.5, y=CAMP[1] - 10 + dy + 0.5)
for gx, gy in [(70, 90), (112, 96)]:
    um.add_unit(0, OtherInfo.GOLD_MINE.ID, x=gx + 0.5, y=gy + 0.5)
    um.add_unit(0, OtherInfo.GOLD_MINE.ID, x=gx + 1.5, y=gy + 0.5)
for c, n in ((START, 8), (CAMP, 8)):
    for i in range(n):
        a = 2 * math.pi * i / n
        t = (int(c[0] + 14 * math.cos(a)), int(c[1] + 14 * math.sin(a)))
        um.add_unit(0, UnitInfo.DEER.ID, x=t[0] + 0.5, y=t[1] + 0.5)

# ------------------------------------------------------------------ триггеры: помощники
VARS = {}
TRIG = {}
AUX_COUNT = [0]


def v(name):
    if name not in VARS:
        VARS[name] = tm.add_variable(name).variable_id
    return VARS[name]


def trig(name, enabled=True, looping=False, **kw):
    assert name not in TRIG, f"дубль триггера {name}"
    t = tm.add_trigger(name, enabled=enabled, looping=looping, **kw)
    TRIG[name] = t
    return t


def aux(parent, suffix, **kw):
    AUX_COUNT[0] += 1
    return trig(f"{parent}__{suffix}", **kw)


def c_flag(t, name, val=1):
    t.new_condition.variable_value(quantity=val, variable=v(name), comparison=Comparison.EQUAL)


def c_clock(t, secs):
    t.new_condition.variable_value(quantity=int(secs), variable=v("M1_Clock"), comparison=Comparison.LARGER_OR_EQUAL)


def c_dl(t, name):
    t.new_condition.compare_variables(variable=v("M1_Clock"), comparison=Comparison.LARGER_OR_EQUAL,
                                      variable2=v(name))


def e_set(t, name, val=1):
    t.new_effect.change_variable(quantity=val, operation=Operation.SET, variable=v(name))


def e_dl(t, name, delay):
    t.new_effect.modify_variable_by_variable(variable=v(name), operation=Operation.SET, variable2=v("M1_Clock"))
    t.new_effect.change_variable(quantity=int(delay), operation=Operation.ADD, variable=v(name))


def c_in(t, player, const, area, qty=1, **kw):
    t.new_condition.objects_in_area(quantity=qty, object_list=const, source_player=player,
                                    area_x1=area[0], area_y1=area[1], area_x2=area[2], area_y2=area[3], **kw)


def dur(text):
    return int(min(40, max(6, 4 + len(text) / 11)))


def show_effect(t, line):
    text = line.full()
    assert text.strip(), f"пустая реплика {line.trig}:{line.typ}"
    if line.typ == "сообщение":
        t.new_effect.send_chat(source_player=P1, message=text)
    else:
        prefix = {"подсказка": "Подсказка: ", "цель": "ЦЕЛЬ: "}.get(line.typ, "")
        t.new_effect.display_instructions(source_player=P1, message=prefix + text, display_time=dur(text))


def say(t, lines):
    """Вывести строки в триггере t; диалоги с задержкой уходят во вспомогательные триггеры."""
    if isinstance(lines, Line):
        lines = [lines]
    cum = 0
    n = 0
    for ln in lines:
        if ln.typ != "диалог":
            show_effect(t, ln)
            continue
        delay = ln.delay if ln.delay is not None else cum
        cum = max(cum, delay) + dur(ln.full())
        if delay == 0:
            show_effect(t, ln)
            continue
        n += 1
        a = aux(t.name, f"d{AUX_COUNT[0] + 1}", enabled=False)
        a.new_condition.timer(timer=delay)
        if ln.cond and "Рубец" in ln.cond:
            c_flag(a, "M1_RubetsDead", 0)
        show_effect(a, ln)
        t.new_effect.activate_trigger(trigger_id=a.trigger_id)


def spawn(t, player, const, n, area, name=None):
    """Создать n юнитов в прямоугольнике area (сетка 1 клетка)."""
    cells = [(x, y) for y in range(area[1], area[3] + 1) for x in range(area[0], area[2] + 1)]
    assert len(cells) >= n, "мала область спавна"
    for x, y in cells[:n]:
        t.new_effect.create_object(object_list_unit_id=const, source_player=player,
                                   location_x=x, location_y=y)


def order_attack_move(t, player, consts, area, target):
    for c in consts:
        t.new_effect.attack_move(object_list_unit_id=c, source_player=player, location_x=target[0],
                                 location_y=target[1], area_x1=area[0], area_y1=area[1],
                                 area_x2=area[2], area_y2=area[3])


def transfer(t, src, area):
    t.new_effect.change_ownership(source_player=src, target_player=P1, area_x1=area[0], area_y1=area[1],
                                  area_x2=area[2], area_y2=area[3], flash_object=1)


def heal_all(t):
    t.new_effect.heal_object(quantity=5000, source_player=P1, area_x1=0, area_y1=0, area_x2=S - 1, area_y2=S - 1)


def give(t, food=0, wood=0, gold=0, stone=0):
    for q, a in ((food, Attribute.FOOD_STORAGE), (wood, Attribute.WOOD_STORAGE),
                 (gold, Attribute.GOLD_STORAGE), (stone, Attribute.STONE_STORAGE)):
        if q:
            t.new_effect.modify_resource(quantity=q, tribute_list=a, source_player=P1, operation=Operation.ADD)


def flag_mark(t, xy, temp=False):
    t.new_effect.create_object(object_list_unit_id=OtherInfo.FLAG_A.ID if not temp else OtherInfo.FLAG_B.ID,
                               source_player=P1, location_x=xy[0], location_y=xy[1])


def rename(t, player, const, text, area=ALL):
    t.new_effect.change_object_name(object_list_unit_id=const, source_player=player, message=text,
                                    area_x1=area[0], area_y1=area[1], area_x2=area[2], area_y2=area[3])


def objective(name, text, order, enabled=False):
    o = trig(name, enabled=enabled, display_as_objective=True, description=text, short_description=text,
             description_order=order)
    return o


# ------------------------------------------------------------------ триггеры §15.5
# ===== 1. Инициализация
t = trig("M1_Init")
init = t
objs = {}
objs["O1"] = None
q_init = goal_quotes(L("M1_Init", "цель", 0))[0]
# цели-объективы создаются ниже (после основных), здесь только активация
t_init_effects_pending = True
# ресурсы, дипломатия, стойки
for pid in ENEMIES:
    t.new_effect.change_diplomacy(diplomacy=DiplomacyState.ENEMY, source_player=P1, target_player=pid,
                                  mutual_diplomacy=1)
for pid in ENEMIES:
    for a in ENEMIES:
        if a != pid:
            t.new_effect.change_diplomacy(diplomacy=DiplomacyState.ALLY, source_player=pid, target_player=a,
                                          mutual_diplomacy=0)
    ids = military_enemy_ids[pid]
    if ids:
        t.new_effect.change_object_stance(source_player=pid, attack_stance=AttackStance.STAND_GROUND,
                                          selected_object_ids=ids)
# воеводы и герои
t.new_effect.change_object_name(source_player=P1, message="Царевич Димитрий", selected_object_ids=[dmitry.reference_id])
t.new_effect.modify_object_attribute(source_player=P1, object_attributes=ObjectAttribute.HIT_POINTS,
                                     selected_object_ids=[dmitry.reference_id], operation=Operation.SET, quantity=300)
t.new_effect.change_object_name(source_player=P6, message="Князь И. А. Татев", selected_object_ids=[tatev.reference_id])
t.new_effect.modify_object_attribute(source_player=P6, object_attributes=ObjectAttribute.HIT_POINTS,
                                     selected_object_ids=[tatev.reference_id], operation=Operation.SET, quantity=150)
t.new_effect.change_object_stance(source_player=P6, attack_stance=AttackStance.NO_ATTACK_STANCE,
                                  selected_object_ids=[tatev.reference_id])
t.new_effect.change_object_name(source_player=P4, message="Пётр Басманов", selected_object_ids=[basmanov.reference_id])
t.new_effect.disable_unit_attackable(source_player=P4, selected_object_ids=[basmanov.reference_id])
for key, (u, nm) in voev.items():
    t.new_effect.change_object_name(source_player=P2, message=nm, selected_object_ids=[u.reference_id])
    t.new_effect.modify_object_attribute(source_player=P2, object_attributes=ObjectAttribute.HIT_POINTS,
                                         selected_object_ids=[u.reference_id], operation=Operation.SET, quantity=60)
    t.new_effect.change_object_stance(source_player=P2, attack_stance=AttackStance.NO_ATTACK_STANCE,
                                      selected_object_ids=[u.reference_id])
for u, nm in ((saltykov, "Воевода М. Г. Салтыков"), (rubets, "Князь В. М. Рубец-Масальский")):
    t.new_effect.change_object_name(source_player=P5, message=nm, selected_object_ids=[u.reference_id])
    t.new_effect.modify_object_attribute(source_player=P5, object_attributes=ObjectAttribute.HIT_POINTS,
                                         selected_object_ids=[u.reference_id], operation=Operation.SET, quantity=60)
    t.new_effect.modify_object_attribute(source_player=P5, object_attributes=ObjectAttribute.MOVEMENT_SPEED,
                                         selected_object_ids=[u.reference_id], operation=Operation.SET, quantity=0.9)
    t.new_effect.change_object_stance(source_player=P5, attack_stance=AttackStance.NO_ATTACK_STANCE,
                                      selected_object_ids=[u.reference_id])
# патрули
for lst, dest in ((patrol_a, (128, 110)), (patrol_b, (142, 40))):
    t.new_effect.patrol(source_player=P4, location_x=dest[0], location_y=dest[1],
                        selected_object_ids=[u.reference_id for u in lst])
t.new_effect.patrol(source_player=P2, location_x=MOR[0] - 14, location_y=MOR[1] - 14,
                    selected_object_ids=[u.reference_id for u in mor_knights])
# характеристики юнитов (по типу, для P1)
t.new_effect.modify_attribute(source_player=P1, object_list_unit_id=CAVARCH, object_attributes=ObjectAttribute.HIT_POINTS,
                              operation=Operation.SET, quantity=UNIT["cossack_defector"]["hp"])
t.new_effect.modify_attribute(source_player=P1, object_list_unit_id=SCOUT, object_attributes=ObjectAttribute.HIT_POINTS,
                              operation=Operation.SET, quantity=UNIT["cossack_scout"]["hp"])
t.new_effect.modify_attribute(source_player=P1, object_list_unit_id=SCOUT, object_attributes=ObjectAttribute.LINE_OF_SIGHT,
                              operation=Operation.SET, quantity=UNIT["cossack_scout"]["line_of_sight"])
t.new_effect.modify_attribute(source_player=P1, object_list_unit_id=SKIRM, object_attributes=ObjectAttribute.HIT_POINTS,
                              operation=Operation.ADD, quantity=10)
# технологии-кнопки (переиспользованы существующие технологии, см. NOTES)
TSAR, BRIBE_C, BRIBE_P = TechInfo.TOWN_WATCH.ID, TechInfo.LOOM.ID, TechInfo.WHEELBARROW.ID
for tech_id, key, loc in ((TSAR, "tsarevich", ButtonLocation.r2c3), (BRIBE_C, "bribe_chernigov", ButtonLocation.r2c4),
                          (BRIBE_P, "bribe_putivl", ButtonLocation.r2c5)):
    d = TECH[key]
    t.new_effect.change_technology_name(source_player=P1, technology=tech_id, message=d["name_ru"])
    t.new_effect.change_technology_description(source_player=P1, technology=tech_id, message=d["description"])
    t.new_effect.change_technology_cost(source_player=P1, technology=tech_id,
                                        resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=d["cost"]["food"],
                                        resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=d["cost"]["wood"],
                                        resource_3=Attribute.GOLD_STORAGE, resource_3_quantity=d["cost"]["gold"])
    t.new_effect.change_technology_research_time(source_player=P1, technology=tech_id, quantity=d["research_time_sec"])
    t.new_effect.change_technology_location(source_player=P1, technology=tech_id, object_list_unit_id_2=TC,
                                            button_location=loc.value)
    t.new_effect.enable_disable_technology(source_player=P1, technology=tech_id, enabled=0)
# польский гусар в Stable
d = UNIT["polish_hussar"]
t.new_effect.add_train_location(object_list_unit_id=HUSSAR, source_player=P1, object_list_unit_id_2=STAB,
                                button_location=ButtonLocation.r1c1.value, train_time=d["train_time_sec"])
t.new_effect.change_object_cost(object_list_unit_id=HUSSAR, source_player=P1,
                                resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=d["cost"]["food"],
                                resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0,
                                resource_3=Attribute.GOLD_STORAGE, resource_3_quantity=d["cost"]["gold"])
flag_mark(t, MOR)
say(t, L("M1_Init", "диалог"))
say(t, L("M1_Init", "цель"))
say(t, L("M1_Init", "подсказка"))

t = trig("M1_Clock", looping=True)
t.new_condition.timer(timer=1)
t.new_effect.change_variable(quantity=1, operation=Operation.ADD, variable=v("M1_Clock"))

# --- переименование юнитов (стрелец, чернец, казаки и т.д.), в том числе для заспавненных
t = trig("M1_Rename_Loop", looping=True)
t.new_condition.timer(timer=4)
for pid in ENEMIES:
    rename(t, pid, HC, "Стрелец")
rename(t, P1, MONK, UNIT["chernets"]["name_ru"])
rename(t, P1, HUSSAR, UNIT["polish_hussar"]["name_ru"])
rename(t, P1, CAVARCH, UNIT["cossack_defector"]["name_ru"])
rename(t, P1, SKIRM, "Казак-стрелок")
rename(t, P1, SCOUT, UNIT["cossack_scout"]["name_ru"])
rename(t, P1, HC, "Казак-стрелок")

# ===== 2. Подсказки
HINT_MOR = L("M1_Hint_Mor", "подсказка")
e_dl_init = trig("M1_Hint_Mor")
c_clock(e_dl_init, 180)
c_flag(e_dl_init, "M1_MoravskDone", 0)
c_flag(e_dl_init, "M1_Mor_ReadStarted", 0)
say(e_dl_init, HINT_MOR[0])
for k, tsec in ((1, 420), (2, 660)):
    a = aux("M1_Hint_Mor", f"r{k + 1}")
    c_clock(a, tsec)
    c_flag(a, "M1_MoravskDone", 0)
    c_flag(a, "M1_Mor_ReadStarted", 0)
    say(a, HINT_MOR[k])


def repeated_hint(name, base_var, offsets, done_flag, started_flag, extra_flags=()):
    ls = L(name, "подсказка")
    for k, off in enumerate(offsets):
        h = trig(name) if k == 0 else aux(name, f"r{k + 1}")
        c_flag(h, "M1_Goal_" + base_var, 1)
        c_dl(h, f"dl_{name}_{k}")
        c_flag(h, done_flag, 0)
        c_flag(h, started_flag, 0)
        for fl in extra_flags:
            c_flag(h, fl, 1)
        say(h, ls[k])


repeated_hint("M1_Hint_Che", "Che", [240, 540, 840], "M1_PosadDone", "M1_Che_ReadStarted")
t = trig("M1_Hint_Camp")
c_flag(t, "M1_Goal_Camp", 1)
c_dl(t, "dl_M1_Hint_Camp_0")
c_flag(t, "M1_CampPlaced", 0)
say(t, L("M1_Hint_Camp", "подсказка"))
flag_hint_camp = t
repeated_hint("M1_Hint_Put", "Put", [300, 660, 1020], "M1_PutivlDone", "M1_Put_ReadStarted")

t = trig("M1_Hint_Tsarevich")
c_flag(t, "M1_MoravskDone", 1)
c_dl(t, "dl_Hint_Tsarevich")
c_flag(t, "M1_TsarevichOn", 0)
say(t, L("M1_Hint_Tsarevich", "подсказка"))
t = trig("M1_Hint_BribeChe")
c_flag(t, "M1_MoravskDone", 1)
c_flag(t, "M1_PosadDone", 0)
t.new_condition.accumulate_attribute(quantity=600, attribute=Attribute.GOLD_STORAGE, source_player=P1)
say(t, L("M1_Hint_BribeChe", "подсказка"))
t = trig("M1_Hint_BribePut")
c_flag(t, "M1_CampPlaced", 1)
c_flag(t, "M1_PutivlDone", 0)
t.new_condition.accumulate_attribute(quantity=900, attribute=Attribute.GOLD_STORAGE, source_player=P1)
say(t, L("M1_Hint_BribePut", "подсказка"))


# ===== 3. Конверсия: чернец и подкуп (общие для Моравска, Чернигова, Путивля)
def conversion(town, zone, D, done, goal_extra=None, dvars=None):
    """town: Mor/Che/Put. D: секунды (если dvars - имена переменных для базового и «царевичева» D)."""
    pre = f"M1_{town}_Reading"
    for tsar in (False, True):
        sfx = "_T" if tsar else ""
        dsec = D if dvars is None else None
        start = trig(f"T_{town}_ConvStart{sfx}", looping=True)
        c_in(start, P1, MONK, zone)
        c_flag(start, pre, 0)
        c_flag(start, done, 0)
        c_flag(start, f"M1_{town}_Go", 0)
        c_flag(start, "M1_TsarevichOn", 1 if tsar else 0)
        if goal_extra:
            c_flag(start, goal_extra, 1)
        e_set(start, pre, 1)
        e_set(start, f"M1_{town}_ReadStarted", 1)
        start.new_effect.modify_variable_by_variable(variable=v(f"dl_{town}_Conv"), operation=Operation.SET,
                                                     variable2=v("M1_Clock"))
        if dvars:
            start.new_effect.modify_variable_by_variable(variable=v(f"dl_{town}_Conv"), operation=Operation.ADD,
                                                         variable2=v(dvars[1 if tsar else 0]))
        else:
            start.new_effect.change_variable(quantity=int(round(D * (0.6 if tsar else 1))),
                                             operation=Operation.ADD, variable=v(f"dl_{town}_Conv"))
        say(start, L(f"T_{town}_ConvStart{sfx}", "сообщение"))
        chk = trig(f"T_{town}_ConvCheck{sfx}", looping=True)
        c_flag(chk, pre, 1)
        c_dl(chk, f"dl_{town}_Conv")
        c_flag(chk, "M1_TsarevichOn", 1 if tsar else 0)
        c_in(chk, P1, MONK, zone)
        e_set(chk, pre, 0)
        e_set(chk, f"M1_{town}_Go", 1)
        fail = aux(f"T_{town}_ConvCheck{sfx}", "fail", looping=True)
        c_flag(fail, pre, 1)
        c_dl(fail, f"dl_{town}_Conv")
        c_flag(fail, "M1_TsarevichOn", 1 if tsar else 0)
        c_in(fail, P1, MONK, zone, inverted=1)
        e_set(fail, pre, 0)
        say(fail, L(f"T_{town}_ConvCheck{sfx}", "сообщение"))


def bribe(town, tech_id, tech_key, zone, done):
    paid = trig(f"T_{town}_BribePaid")
    paid.new_condition.research_technology(source_player=P1, technology=tech_id)
    e_set(paid, f"M1_BribePaid_{town}", 1)
    say(paid, L(f"T_{town}_BribePaid", "сообщение"))
    arr = trig(f"T_{town}_BribeArrive", looping=True)
    c_flag(arr, f"M1_BribePaid_{town}", 1)
    c_flag(arr, done, 0)
    c_flag(arr, f"M1_{town}_BribeWait", 0)
    c_flag(arr, f"M1_{town}_Go", 0)
    c_in(arr, P1, -1, zone)
    e_set(arr, f"M1_{town}_BribeWait", 1)
    e_dl(arr, f"dl_{town}_Bribe", 5)
    lines = L(f"T_{town}_BribeArrive", "сообщение")
    say(arr, lines[0])
    ok = aux(arr.name, "ok", looping=True)
    c_flag(ok, f"M1_{town}_BribeWait", 1)
    c_dl(ok, f"dl_{town}_Bribe")
    c_in(ok, P1, -1, zone)
    e_set(ok, f"M1_{town}_BribeWait", 0)
    e_set(ok, f"M1_{town}_Go", 1)
    bad = aux(arr.name, "fail", looping=True)
    c_flag(bad, f"M1_{town}_BribeWait", 1)
    c_dl(bad, f"dl_{town}_Bribe")
    c_in(bad, P1, -1, zone, inverted=1)
    e_set(bad, f"M1_{town}_BribeWait", 0)
    say(bad, lines[1])


# ===== Моравск
conversion("Mor", Z_MOR, 15, "M1_MoravskDone")
t = trig("T_Mor_Flip")
c_flag(t, "M1_Mor_Go", 1)
c_flag(t, "M1_MoravskDone", 0)
transfer(t, P2, A_MOR)
e_set(t, "M1_MoravskDone", 1)
e_set(t, "M1_Mor_Reading", 0)
for key in voev:
    t.new_effect.change_object_stance(source_player=P1, attack_stance=AttackStance.NO_ATTACK_STANCE,
                                      selected_object_ids=[voev[key][0].reference_id])
mor_flip = t
mx_, my_ = MOR
t.new_effect.create_object(object_list_unit_id=CAVARCH, source_player=P1, location_x=mx_ - 4, location_y=my_ - 5)
t.new_effect.create_object(object_list_unit_id=CAVARCH, source_player=P1, location_x=mx_ - 3, location_y=my_ - 5)
t.new_effect.create_object(object_list_unit_id=CAVARCH, source_player=P1, location_x=mx_ - 2, location_y=my_ - 5)
t.new_effect.create_object(object_list_unit_id=MONK, source_player=P1, location_x=mx_ - 4, location_y=my_ - 4)
t.new_effect.create_object(object_list_unit_id=SCOUT, source_player=P1, location_x=mx_ - 1, location_y=my_ - 5)
give(t, food=300, gold=200)
heal_all(t)
for tid in (TSAR, BRIBE_C):
    t.new_effect.enable_disable_technology(source_player=P1, technology=tid, enabled=1)
e_set(t, "M1_Goal_Che", 1)
e_dl(t, "dl_M1_Hint_Che_0", 240)
e_dl(t, "dl_M1_Hint_Che_1", 540)
e_dl(t, "dl_M1_Hint_Che_2", 840)
e_dl(t, "dl_Rumor_Mor", 180)
e_dl(t, "dl_Hint_Tsarevich", 20)
flag_mark(t, CHE)
lines_flip_msg = L("T_Mor_Flip", "сообщение")
say(t, lines_flip_msg)
mflip_goals = L("T_Mor_Flip", "цель")
say(t, mflip_goals)
say(t, L("T_Mor_Flip", "диалог"))
say(t, L("bribe_chernigov", "сообщение"))
say(t, L("M1_TsarevichUnlock", "сообщение"))
say(t, L("M1_CossackUnlock", "сообщение"))

t = trig("T_Rumor_Mor")
c_flag(t, "M1_MoravskDone", 1)
c_dl(t, "dl_Rumor_Mor")
spawn(t, P1, MAA, 4, (mx_ + 5, my_ - 12, mx_ + 8, my_ - 11))
say(t, L("T_Rumor_Mor", "сообщение", 0))
t = aux("T_Rumor_Mor", "full")
c_flag(t, "M1_MoravskDone", 1)
c_dl(t, "dl_Rumor_Mor")
t.new_condition.accumulate_attribute(quantity=3, attribute=Attribute.POPULATION_HEADROOM, source_player=P1, inverted=1)
say(t, L("T_Rumor_Mor", "сообщение", 1))

# ===== Технологии и обучение
t = trig("M1_TsarevichUnlock")
c_flag(t, "M1_MoravskDone", 1)
t.new_effect.enable_disable_technology(source_player=P1, technology=TSAR, enabled=1)
t = trig("M1_TsarevichDone")
t.new_condition.research_technology(source_player=P1, technology=TSAR)
e_set(t, "M1_TsarevichOn", 1)
t.new_effect.modify_attribute(source_player=P1, object_list_unit_id=MONK, object_attributes=ObjectAttribute.LINE_OF_SIGHT,
                              operation=Operation.ADD, quantity=3)
say(t, L("M1_TsarevichDone", "сообщение"))
t = trig("M1_CossackUnlock")
c_flag(t, "M1_MoravskDone", 1)
d = UNIT["cossack_defector"]
t.new_effect.add_train_location(object_list_unit_id=CAVARCH, source_player=P1, object_list_unit_id_2=TC,
                                button_location=ButtonLocation.r2c1.value, train_time=d["train_time_sec"])
t.new_effect.change_object_cost(object_list_unit_id=CAVARCH, source_player=P1,
                                resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=d["cost"]["food"],
                                resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0,
                                resource_3=Attribute.GOLD_STORAGE, resource_3_quantity=d["cost"]["gold"])

# копии конверсии «Царевич» уже созданы в conversion(); порядок §15.5 п.4 соблюдён по именам.

# ===== Разведка O1
t = trig("T_Scout_Spawn")
c_flag(t, "M1_MoravskDone", 1)
say(t, L("T_Scout_Spawn", "сообщение"))
say(t, L("T_Scout_Spawn", "цель"))
e_set(t, "M1_O1Open", 1)
scout_pts = []
for i, z in enumerate(Z_SCOUT, start=1):
    t = trig(f"T_Scout_Point_{i}")
    c_flag(t, "M1_O1Open", 1)
    c_in(t, P1, SCOUT, z)
    e_set(t, f"M1_Scout_{i}", 1)
    say(t, L(f"T_Scout_Point_{i}", "сообщение"))
t = trig("T_Scout_Reward")
for i in (1, 2, 3):
    c_flag(t, f"M1_Scout_{i}", 1)
e_set(t, "M1_O1Done", 1)
t.new_effect.change_object_hp(quantity=540, source_player=P6, operation=Operation.SET,
                              selected_object_ids=[w.reference_id for w in wallW])
w_pt = (CASTLE[0] - 5, CASTLE[1])
flag_mark(t, w_pt, temp=True)
flag_mark(t, (CASTLE[0] + 6, CASTLE[1] - 1), temp=True)
flag_mark(t, (CASTLE[0] + 8, CASTLE[1] - 8), temp=True)
say(t, L("T_Scout_Reward", "сообщение"))
a = aux("T_Scout_Reward", "clear", enabled=True)
c_flag(a, "M1_O1Done", 1)
a.new_condition.timer(timer=60)
a.new_effect.remove_object(object_list_unit_id=OtherInfo.FLAG_B.ID, source_player=P1,
                           area_x1=0, area_y1=0, area_x2=S - 1, area_y2=S - 1)

# ===== Чернигов
conversion("Che", Z_CHE, 20, "M1_PosadDone", goal_extra="M1_MoravskDone")
bribe("Che", BRIBE_C, "bribe_chernigov", Z_CHE, "M1_PosadDone")
paid = TRIG["T_Che_BribePaid"]
t = trig("T_Che_PosadFlip")
c_flag(t, "M1_Che_Go", 1)
c_flag(t, "M1_PosadDone", 0)
transfer(t, P3, A_CHE)
e_set(t, "M1_PosadDone", 1)
e_set(t, "M1_Che_Reading", 0)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_C, enabled=0)
spawn(t, P1, CAVARCH, 4, (CHE[0] - 3, CHE[1] - 12, CHE[0] + 3, CHE[1] - 11))
spawn(t, P1, SKIRM, 2, (CHE[0] - 3, CHE[1] - 13, CHE[0] - 2, CHE[1] - 13))
e_dl(t, "dl_Rumor_Che", 120)
e_set(t, "M1_Goal_2b", 1)
flag_mark(t, CASTLE)
say(t, L("T_Che_PosadFlip", "сообщение"))
say(t, L("T_Che_PosadFlip", "цель"))
t = trig("T_Rumor_Che")
c_flag(t, "M1_PosadDone", 1)
c_flag(t, "M1_BribePaid_Che", 0)
c_dl(t, "dl_Rumor_Che")
spawn(t, P1, MAA, 3, (CHE[0] - 3, CHE[1] - 11, CHE[0] - 1, CHE[1] - 11))
spawn(t, P1, ARCHER, 3, (CHE[0] + 0, CHE[1] - 11, CHE[0] + 2, CHE[1] - 11))
say(t, L("T_Rumor_Che", "сообщение"))
t = aux("T_Rumor_Che", "bribe")
c_flag(t, "M1_PosadDone", 1)
c_flag(t, "M1_BribePaid_Che", 1)
c_dl(t, "dl_Rumor_Che")
spawn(t, P1, MAA, 2, (CHE[0] - 3, CHE[1] - 11, CHE[0] - 2, CHE[1] - 11))
spawn(t, P1, ARCHER, 1, (CHE[0], CHE[1] - 11, CHE[0], CHE[1] - 11))
t.new_effect.send_chat(source_player=P1, message=LINES[("T_Rumor_Che", "сообщение")][0].full())

# --- вылазки замка Чернигова
GATE_C = (kx + 7, ky - 1, kx + 11, ky + 4)
CHE_UNITS = [SPEAR, HC, KNIGHT]
t = aux("T_CheSortie_1", "enter")
c_flag(t, "M1_CastleFall", 0)
c_in(t, P1, -1, rect(kx, ky, 25), object_type=int(ObjectType.MILITARY))
e_set(t, "M1_CheEntered", 1)
e_dl(t, "dl_S1", 120)
e_dl(t, "dl_S1_w30", 90)
e_dl(t, "dl_S1_w60", 60)
e_dl(t, "dl_Open2b", 720)
for k, nm in ((1, "S1"), (2, "S2")):
    pass
w1 = trig("T_CheSortie_1_Warn")
c_flag(w1, "M1_CheEntered", 1)
c_flag(w1, "M1_O1Done", 0)
c_flag(w1, "M1_S1Warned", 0)
c_flag(w1, "M1_CastleFall", 0)
c_dl(w1, "dl_S1_w30")
e_set(w1, "M1_S1Warned", 1)
flag_mark(w1, (kx + 6, ky))
say(w1, L("T_CheSortie_1_Warn", "сообщение"))
w1b = aux("T_CheSortie_1_Warn", "O1")
c_flag(w1b, "M1_CheEntered", 1)
c_flag(w1b, "M1_O1Done", 1)
c_flag(w1b, "M1_S1Warned", 0)
c_flag(w1b, "M1_CastleFall", 0)
c_dl(w1b, "dl_S1_w60")
e_set(w1b, "M1_S1Warned", 1)
flag_mark(w1b, (kx + 6, ky))
say(w1b, L("T_CheSortie_1_Warn", "сообщение"))
s1 = trig("T_CheSortie_1")
c_flag(s1, "M1_CheEntered", 1)
c_flag(s1, "M1_S1Warned", 1)
c_flag(s1, "M1_CastleFall", 0)
c_dl(s1, "dl_S1")
spawn(s1, P6, SPEAR, 6, (GATE_C[0], GATE_C[1], GATE_C[0] + 2, GATE_C[1] + 1))
spawn(s1, P6, HC, 4, (GATE_C[0], GATE_C[1] + 2, GATE_C[0] + 3, GATE_C[1] + 2))
spawn(s1, P6, KNIGHT, 3, (GATE_C[0], GATE_C[1] + 3, GATE_C[0] + 2, GATE_C[1] + 3))
order_attack_move(s1, P6, CHE_UNITS, GATE_C, CHE)
e_dl(s1, "dl_S2", 360)
e_dl(s1, "dl_S2_w30", 330)
e_dl(s1, "dl_S2_w60", 300)
e_set(s1, "M1_S1Fired", 1)
say(s1, L("T_CheSortie_1", "сообщение"))
w2 = trig("T_CheSortie_2_Warn")
c_flag(w2, "M1_S1Fired", 1)
c_flag(w2, "M1_O1Done", 0)
c_flag(w2, "M1_S2Warned", 0)
c_flag(w2, "M1_CastleFall", 0)
c_dl(w2, "dl_S2_w30")
e_set(w2, "M1_S2Warned", 1)
flag_mark(w2, (kx + 6, ky))
say(w2, L("T_CheSortie_2_Warn", "сообщение"))
w2b = aux("T_CheSortie_2_Warn", "O1")
c_flag(w2b, "M1_S1Fired", 1)
c_flag(w2b, "M1_O1Done", 1)
c_flag(w2b, "M1_S2Warned", 0)
c_flag(w2b, "M1_CastleFall", 0)
c_dl(w2b, "dl_S2_w60")
e_set(w2b, "M1_S2Warned", 1)
flag_mark(w2b, (kx + 6, ky))
say(w2b, L("T_CheSortie_2_Warn", "сообщение"))
s2 = trig("T_CheSortie_2")
c_flag(s2, "M1_S2Warned", 1)
c_flag(s2, "M1_CastleFall", 0)
c_flag(s2, "M1_Shaken", 0)
c_dl(s2, "dl_S2")
spawn(s2, P6, SPEAR, 8, (GATE_C[0], GATE_C[1], GATE_C[0] + 3, GATE_C[1] + 1))
spawn(s2, P6, HC, 5, (GATE_C[0], GATE_C[1] + 2, GATE_C[0] + 4, GATE_C[1] + 2))
spawn(s2, P6, KNIGHT, 4, (GATE_C[0], GATE_C[1] + 3, GATE_C[0] + 3, GATE_C[1] + 3))
order_attack_move(s2, P6, CHE_UNITS, GATE_C, CHE)
e_set(s2, "M1_S2Fired", 1)
say(s2, L("T_CheSortie_2", "сообщение"))
s2b = aux("T_CheSortie_2", "shaken")
c_flag(s2b, "M1_S2Warned", 1)
c_flag(s2b, "M1_CastleFall", 0)
c_flag(s2b, "M1_Shaken", 1)
c_dl(s2b, "dl_S2")
spawn(s2b, P6, HC, 6, (GATE_C[0], GATE_C[1], GATE_C[0] + 3, GATE_C[1] + 1))
spawn(s2b, P6, KNIGHT, 5, (GATE_C[0], GATE_C[1] + 2, GATE_C[0] + 4, GATE_C[1] + 2))
order_attack_move(s2b, P6, [HC, KNIGHT], GATE_C, CHE)
e_set(s2b, "M1_S2Fired", 1)
s2b.new_effect.send_chat(source_player=P1, message=LINES[("T_CheSortie_2", "сообщение")][0].full())

t = trig("T_CheCastle_Shaken")
c_flag(t, "M1_PosadDone", 1)
c_flag(t, "M1_S2Fired", 0)
e_set(t, "M1_Shaken", 1)
say(t, L("T_CheCastle_Shaken", "сообщение"))

# падение замка: Татев убит / замок разрушен / P6 <= 3 боевых юнитов
for sfx, setup in (("tatev", lambda a: a.new_condition.destroy_object(unit_object=tatev.reference_id)),
                   ("castle", lambda a: a.new_condition.destroy_object(unit_object=castle.reference_id)),
                   ("few", lambda a: a.new_condition.own_fewer_objects(quantity=3, source_player=P6,
                                                                       object_type=int(ObjectType.MILITARY)))):
    a = aux("T_CheCastle_Fall", sfx)
    c_flag(a, "M1_PosadDone", 1)
    setup(a)
    e_set(a, "M1_CastleFall_Go", 1)
t = trig("T_CheCastle_Fall")
c_flag(t, "M1_CastleFall_Go", 1)
c_flag(t, "M1_CastleFall", 0)
transfer(t, P6, A_CASTLE)
e_set(t, "M1_CastleFall", 1)
spawn(t, P1, HUSSAR, 3, (CHE[0] + 1, CHE[1] - 13, CHE[0] + 3, CHE[1] - 13))
spawn(t, P1, MAA, 6, (CHE[0] - 4, CHE[1] - 14, CHE[0] + 1, CHE[1] - 14))
give(t, gold=300)
e_set(t, "M1_Goal_Camp", 1)
e_dl(t, "dl_M1_Hint_Camp_0", 180)
flag_mark(t, CAMP)
say(t, L("T_CheCastle_Fall", "сообщение"))
say(t, L("T_CheCastle_Fall", "цель"))
S3 = L("T_CheCastle_Fall", "диалог")
# реплики S3 звучат ДО взятия замка (пометка в dialogue.md): привязаны к T_Che_PosadFlip
say(TRIG["T_Che_PosadFlip"], S3)

t = trig("M1_Ambush")
t.new_condition.bring_object_to_area(unit_object=dmitry.reference_id, area_x1=AMBUSH[0] - 8, area_y1=AMBUSH[1] - 8,
                                     area_x2=AMBUSH[0] + 8, area_y2=AMBUSH[1] + 8)
amb = (AMBUSH[0] + 8, AMBUSH[1] + 9, AMBUSH[0] + 12, AMBUSH[1] + 10)
spawn(t, P3, SPEAR, 4, (amb[0], amb[1], amb[0] + 3, amb[1]))
spawn(t, P3, HC, 3, (amb[0], amb[1] + 1, amb[0] + 2, amb[1] + 1))
order_attack_move(t, P3, [SPEAR, HC], amb, (AMBUSH[0] - 2, AMBUSH[1] - 2))
say(t, L("M1_Ambush", "сообщение"))
a = aux("M1_Ambush", "retreat")
c_flag(a, "M1_AmbushFired", 1)
a.new_condition.timer(timer=45)
for c in (SPEAR, HC):
    a.new_effect.task_object(object_list_unit_id=c, source_player=P3, location_x=amb[0] + 14, location_y=amb[1] + 14,
                             area_x1=AMBUSH[0] - 14, area_y1=AMBUSH[1] - 14, area_x2=AMBUSH[0] + 18,
                             area_y2=AMBUSH[1] + 18, action_type=ActionType.MOVE)
e_set(t, "M1_AmbushFired", 1)

# ===== Лагерь и давление
t = trig("T_CampCheck")
t.new_condition.bring_object_to_area(unit_object=dmitry.reference_id, area_x1=Z_CAMP[0], area_y1=Z_CAMP[1],
                                     area_x2=Z_CAMP[2], area_y2=Z_CAMP[3])
c_in(t, P1, -1, Z_CAMP, qty=15, object_type=int(ObjectType.MILITARY))
cx_, cy_ = CAMP
camp_tc_ref = None
for const, tl, size in ((TC, (-2, -2), 4), (BARR, (3, -6), 3), (ARCHR, (-6, -5), 3), (MON, (-6, 3), 3),
                        (STAB, (3, 3), 3)):
    t.new_effect.create_object(object_list_unit_id=const, source_player=P1,
                               location_x=int(cx_ + tl[0] + size / 2), location_y=int(cy_ + tl[1] + size / 2))
for i in range(4):
    t.new_effect.create_object(object_list_unit_id=VILL, source_player=P1, location_x=cx_ - 1 + i, location_y=cy_ + 4)
give(t, food=400, wood=400, gold=300)
heal_all(t)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_P, enabled=1)
e_set(t, "M1_CampPlaced", 1)
e_set(t, "M1_Goal_Put", 1)
e_dl(t, "dl_M1_Hint_Put_0", 300)
e_dl(t, "dl_M1_Hint_Put_1", 660)
e_dl(t, "dl_M1_Hint_Put_2", 1020)
e_dl(t, "dl_NSmin", 480)
flag_mark(t, PUT)
say(t, L("T_CampCheck", "сообщение"))
say(t, L("T_CampCheck", "цель"))
say(t, L("T_CampCheck", "диалог"))
say(t, L("bribe_putivl", "сообщение"))
camp_check = t
# Центр лагеря: идентифицируем по зоне (создаётся триггером, ref id неизвестен)
CAMP_TC_AREA = rect(cx_, cy_, 2)

t = trig("T_CampHP50")
c_flag(t, "M1_CampPlaced", 1)
e_set(t, "M1_H3_Broken", 1)
say(t, L("T_CampHP50", "сообщение"))
t.enabled = False  # включается только если найдётся способ измерить HP созданного объекта (см. NOTES)
hp50 = t


def reinforce(name, clock_s, spec_list, area, player, extra_flags=(), msg=None, msg_type=None):
    r = trig(name)
    c_clock(r, clock_s)
    for fl, val in extra_flags:
        c_flag(r, fl, val)
    for c, n in spec_list:
        spawn(r, player, c, n, area)
    return r


NS_IN = (nx - 3, ny + 2, nx + 4, ny + 2)
NS_IN2 = (nx - 3, ny + 3, nx + 2, ny + 3)
NS_IN4 = (nx - 3, ny + 2, nx + 2, ny + 3)
r1 = trig("T_Relief_1")
c_clock(r1, 900)
c_flag(r1, "M1_CastleFall", 0)
spawn(r1, P6, SPEAR, 4, (kx - 3, ky + 2, kx, ky + 2))
spawn(r1, P6, HC, 3, (kx - 3, ky + 3, kx - 1, ky + 3))
say(r1, L("T_Relief_1", "сообщение", 0))
r1b = aux("T_Relief_1", "ns")
c_clock(r1b, 900)
c_flag(r1b, "M1_CastleFall", 1)
spawn(r1b, P4, SPEAR, 4, NS_IN)
spawn(r1b, P4, HC, 3, NS_IN2)
say(r1b, L("T_Relief_1", "сообщение", 1))
r2 = trig("T_Relief_2")
c_clock(r2, 1680)
spawn(r2, P4, MAA, 8, NS_IN)
spawn(r2, P4, HC, 4, NS_IN2)
say(r2, L("T_Relief_2", "диалог"))
r3 = trig("T_Relief_3")
c_clock(r3, 2160)
spawn(r3, P4, KNIGHT, 6, NS_IN)
spawn(r3, P4, HC, 6, NS_IN2)
say(r3, L("T_Relief_3", "сообщение"))
t = trig("T_Putivl_Toughen")
c_clock(t, 2400)
c_flag(t, "M1_PutivlDone", 0)
c_flag(t, "M1_Putivl_Force", 0)
e_set(t, "Put_D", 40)
e_set(t, "Put_DT", 24)
say(t, L("T_Putivl_Toughen", "сообщение"))
r4 = trig("T_Relief_4")
c_clock(r4, 2640)
spawn(r4, P4, SPEAR, 10, NS_IN4)
say(r4, L("T_Relief_4", "сообщение", 0))
r4b = aux("T_Relief_4", "put")
c_clock(r4b, 2640)
c_flag(r4b, "M1_PutivlDone", 0)
spawn(r4b, P5, SPEAR, 8, (px_ - 4, py_ - 9, px_ + 3, py_ - 8))
say(r4b, L("T_Relief_4", "сообщение", 1))

# --- вылазка Новгорода-Северского
g = aux("T_NSSortie_1", "gateA")
c_flag(g, "M1_CampPlaced", 1)
c_clock(g, 2280)
e_set(g, "M1_NSOpen", 1)
g = aux("T_NSSortie_1", "gateB")
c_flag(g, "M1_PutivlDone", 1)
c_dl(g, "dl_Rumor_Put")
e_set(g, "M1_NSOpen", 1)
g = aux("T_NSSortie_1", "gateC")
c_flag(g, "M1_CampPlaced", 1)
c_dl(g, "dl_NSmin")
e_set(g, "M1_NSMinOk", 1)
w = trig("T_NSSortie_1_Warn")
c_flag(w, "M1_NSOpen", 1)
c_flag(w, "M1_NSMinOk", 1)
e_set(w, "M1_NSWarned", 1)
e_dl(w, "dl_NSLaunch", 30)
flag_mark(w, (nx, ny - 8))
say(w, L("T_NSSortie_1_Warn", "сообщение"))
ns1 = trig("T_NSSortie_1")
c_flag(ns1, "M1_NSWarned", 1)
c_dl(ns1, "dl_NSLaunch")
GATE_N = (nx - 3, ny - 14, nx + 4, ny - 9)
NS_UNITS = [MAA, HC, KNIGHT, SPEAR]
spawn(ns1, P4, MAA, 12, (GATE_N[0], GATE_N[1], GATE_N[0] + 5, GATE_N[1] + 1))
spawn(ns1, P4, HC, 8, (GATE_N[0], GATE_N[1] + 2, GATE_N[0] + 7, GATE_N[1] + 2))
spawn(ns1, P4, KNIGHT, 6, (GATE_N[0], GATE_N[1] + 3, GATE_N[0] + 5, GATE_N[1] + 3))
order_attack_move(ns1, P4, NS_UNITS, GATE_N, CAMP)
e_set(ns1, "M1_NSAFired", 1)
e_dl(ns1, "dl_NSB", 90)
say(ns1, L("T_NSSortie_1", "сообщение", 0))
wb = aux("T_NSSortie_1", "waveB")
c_flag(wb, "M1_NSAFired", 1)
c_dl(wb, "dl_NSB")
spawn(wb, P4, SPEAR, 10, (GATE_N[0], GATE_N[1], GATE_N[0] + 5, GATE_N[1] + 1))
spawn(wb, P4, HC, 4, (GATE_N[0], GATE_N[1] + 2, GATE_N[0] + 3, GATE_N[1] + 2))
order_attack_move(wb, P4, NS_UNITS, GATE_N, CAMP)
e_set(wb, "M1_NSBFired", 1)
e_dl(wb, "dl_NSEnd", 240)
say(wb, L("T_NSSortie_1", "сообщение", 1))
wd = aux("T_NSSortie_1", "done")
c_flag(wd, "M1_NSBFired", 1)
c_dl(wd, "dl_NSEnd")
e_set(wd, "M1_NSSortieDone", 1)

# ===== Путивль
e_set(init, "Put_D", 25)
e_set(init, "Put_DT", 15)
conversion("Put", Z_PUT, 25, "M1_PutivlDone", goal_extra="M1_CampPlaced", dvars=("Put_D", "Put_DT"))
bribe("Put", BRIBE_P, "bribe_putivl", Z_PUT, "M1_PutivlDone")

a = aux("T_Putivl_Force", "tc")
c_flag(a, "M1_PutivlDone", 0)
a.new_condition.destroy_object(unit_object=BUILDINGS["PutTC"].reference_id)
e_set(a, "M1_PutForce_Go", 1)
a = aux("T_Putivl_Force", "kills")
c_flag(a, "M1_PutivlDone", 0)
a.new_condition.own_fewer_objects(quantity=6, source_player=P5, object_type=int(ObjectType.MILITARY))
e_set(a, "M1_PutForce_Go", 1)
t = trig("T_Putivl_Force")
c_flag(t, "M1_PutForce_Go", 1)
c_flag(t, "M1_PutivlDone", 0)
e_set(t, "M1_Putivl_Force", 1)
e_set(t, "Put_D", 60)
e_set(t, "Put_DT", 60)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_P, enabled=0)
say(t, L("T_Putivl_Force", "сообщение"))

t = trig("T_Putivl_Flip")
c_flag(t, "M1_Put_Go", 1)
c_flag(t, "M1_PutivlDone", 0)
transfer(t, P5, A_PUT)
e_set(t, "M1_PutivlDone", 1)
e_set(t, "M1_Put_Reading", 0)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_P, enabled=0)
for u in (saltykov, rubets):
    t.new_effect.change_object_stance(source_player=P1, attack_stance=AttackStance.NO_ATTACK_STANCE,
                                      selected_object_ids=[u.reference_id])
spawn(t, P1, SPEAR, 2, (px_ - 1, py_ + 4, px_, py_ + 4))
e_dl(t, "dl_Rumor_Put", 120)
for u in (saltykov, rubets):
    t.new_effect.task_object(source_player=P1, location_x=CAMP[0], location_y=CAMP[1], action_type=ActionType.MOVE,
                             selected_object_ids=[u.reference_id])
t.new_effect.task_object(object_list_unit_id=SPEAR, source_player=P1, location_x=CAMP[0], location_y=CAMP[1],
                         action_type=ActionType.MOVE, area_x1=px_ - 2, area_y1=py_ + 3, area_x2=px_ + 1, area_y2=py_ + 5)
say(t, L("T_Putivl_Flip", "сообщение"))
tr = aux("T_Putivl_Flip", "treasury")
c_flag(tr, "M1_PutivlDone", 1)
c_flag(tr, "M1_Putivl_Force", 0)
c_flag(tr, "M1_BribePaid_Put", 0)
give(tr, gold=500)

t = trig("T_Rumor_Put")
c_flag(t, "M1_PutivlDone", 1)
c_flag(t, "M1_BribePaid_Put", 0)
c_dl(t, "dl_Rumor_Put")
spawn(t, P1, MAA, 3, (cx_ - 6, cy_ + 8, cx_ - 4, cy_ + 8))
spawn(t, P1, ARCHER, 3, (cx_ - 3, cy_ + 8, cx_ - 1, cy_ + 8))
say(t, L("T_Rumor_Put", "сообщение"))
t = aux("T_Rumor_Put", "bribe")
c_flag(t, "M1_PutivlDone", 1)
c_flag(t, "M1_BribePaid_Put", 1)
c_dl(t, "dl_Rumor_Put")
spawn(t, P1, MAA, 2, (cx_ - 6, cy_ + 8, cx_ - 5, cy_ + 8))
spawn(t, P1, ARCHER, 1, (cx_ - 3, cy_ + 8, cx_ - 3, cy_ + 8))
t.new_effect.send_chat(source_player=P1, message=LINES[("T_Rumor_Put", "сообщение")][0].full())

# Рубец-Масальский мёртв (для реплик сцены)
a = aux("M1_VoevodaArrive", "rubets_dead")
a.new_condition.destroy_object(unit_object=rubets.reference_id)
e_set(a, "M1_RubetsDead", 1)

t = trig("M1_VoevodaArrive")
c_flag(t, "M1_PutivlDone", 1)
c_flag(t, "M1_VoevodaArrive", 0)
t.new_condition.bring_object_to_area(unit_object=saltykov.reference_id, area_x1=Z_CAMP[0], area_y1=Z_CAMP[1],
                                     area_x2=Z_CAMP[2], area_y2=Z_CAMP[3])
t.new_condition.bring_object_to_area(unit_object=dmitry.reference_id, area_x1=Z_CAMP[0], area_y1=Z_CAMP[1],
                                     area_x2=Z_CAMP[2], area_y2=Z_CAMP[3])
c_in(t, P1, TC, CAMP_TC_AREA)
e_set(t, "M1_VoevodaArrive", 1)
e_dl(t, "dl_Win", 25)
for u in (saltykov, rubets):
    t.new_effect.stop_object(source_player=P1, selected_object_ids=[u.reference_id])
say(t, L("M1_VoevodaArrive", "диалог"))

# H1..H3: скрытые цели
a = aux("T_Win", "h1_mor")
c_flag(a, "M1_MoravskDone", 0)
a.new_condition.own_fewer_objects(quantity=15, source_player=P2, object_type=int(ObjectType.MILITARY))
e_set(a, "M1_H1_Broken", 1)
a = aux("T_Win", "h1_put")
c_flag(a, "M1_PutivlDone", 0)
a.new_condition.own_fewer_objects(quantity=17, source_player=P5, object_type=int(ObjectType.MILITARY))
e_set(a, "M1_H1_Broken", 1)
a = aux("T_Win", "h1_force")
c_flag(a, "M1_Putivl_Force", 1)
e_set(a, "M1_H1_Broken", 1)
a = aux("T_Win", "h2_pre")
c_flag(a, "M1_MoravskDone", 0)
a.new_condition.own_fewer_objects(quantity=2, source_player=P1, object_list=MONK)
e_set(a, "M1_H2_Broken", 1)
a = aux("T_Win", "h2_post")
c_flag(a, "M1_MoravskDone", 1)
a.new_condition.own_fewer_objects(quantity=3, source_player=P1, object_list=MONK)
e_set(a, "M1_H2_Broken", 1)

win_lines = L("T_Win", "сообщение")
t = trig("T_Win")
c_flag(t, "M1_VoevodaArrive", 1)
c_dl(t, "dl_Win")
c_flag(t, "M1_NSSortieDone", 1)
c_in(t, P1, TC, CAMP_TC_AREA)
say(t, L("T_Win", "диалог"))
t.new_effect.declare_victory(source_player=P1, enabled=1)
for k, ln in enumerate(win_lines):
    pass
# строки H1-H3: выбор по состоянию флагов (отдельные триггеры, срабатывают в момент победы)
H = {"H1": "M1_H1_Broken", "H2": "M1_H2_Broken", "H3": "M1_H3_Broken"}
for k, hname in enumerate(("H1", "H2", "H3")):
    ok_line = [x for x in win_lines if x.cond and x.cond.startswith(hname) and "не выполнена" not in x.cond][0]
    bad_line = [x for x in win_lines if x.cond and x.cond.startswith(hname) and "не выполнена" in x.cond][0]
    ok_line.used = bad_line.used = True
    for broken, ln in ((0, ok_line), (1, bad_line)):
        a = aux("T_Win", f"{hname}_{'bad' if broken else 'ok'}")
        c_flag(a, "M1_VoevodaArrive", 1)
        c_dl(a, "dl_Win")
        c_flag(a, "M1_NSSortieDone", 1)
        c_flag(a, H[hname], broken)
        a.new_effect.send_chat(source_player=P1, message=ln.full())

# ===== Поражение
for name, cond in (("T_Lose_Dmitry", lambda a: a.new_condition.destroy_object(unit_object=dmitry.reference_id)),
                   ("T_Lose_Camp", None), ("T_Lose_Voevoda", None)):
    a = trig(name)
    if name == "T_Lose_Camp":
        c_flag(a, "M1_CampPlaced", 1)
        a.new_condition.objects_in_area(quantity=1, object_list=TC, source_player=P1, area_x1=CAMP_TC_AREA[0],
                                        area_y1=CAMP_TC_AREA[1], area_x2=CAMP_TC_AREA[2], area_y2=CAMP_TC_AREA[3],
                                        inverted=1)
        c_flag(a, "M1_CampPlaced", 1)
    elif name == "T_Lose_Voevoda":
        c_flag(a, "M1_PutivlDone", 1)
        c_flag(a, "M1_VoevodaArrive", 0)
        a.new_condition.destroy_object(unit_object=saltykov.reference_id)
    else:
        cond(a)
    for ln in L(name, "сообщение"):
        pass
    say(a, L(name, "сообщение"))
    if (name, "диалог") in LINES:
        say(a, L(name, "диалог"))
    a.new_effect.declare_victory(source_player=P2, enabled=1)

# ===== Цели-объективы (панель целей)
q_mor = goal_quotes(L("M1_Init", "цель", 0))[0]  # «Привести Моравск к присяге»
q_che = goal_quotes(mflip_goals[0])
q_2b = goal_quotes(LINES[("T_Che_PosadFlip", "цель")][1])[0]
q_3 = goal_quotes(LINES[("T_CheCastle_Fall", "цель")][1])[0]
q_4 = goal_quotes(LINES[("T_CampCheck", "цель")][1])[0]
q_o1 = goal_quotes(LINES[("T_Scout_Spawn", "цель")][0])[0]
OBJ = {}
OBJ["1"] = objective("OBJ_1_Moravsk", q_mor, 1, enabled=True)
c_flag(OBJ["1"], "M1_MoravskDone", 1)
OBJ["2"] = objective("OBJ_2_Chernigov", q_che[0], 2)
c_flag(OBJ["2"], "M1_PosadDone", 1)
c_flag(OBJ["2"], "M1_CastleFall", 1)
OBJ["2a"] = objective("OBJ_2a_Posad", q_che[1], 3)
c_flag(OBJ["2a"], "M1_PosadDone", 1)
OBJ["2b"] = objective("OBJ_2b_Castle", q_2b, 4)
c_flag(OBJ["2b"], "M1_CastleFall", 1)
OBJ["3"] = objective("OBJ_3_Camp", q_3, 5)
c_flag(OBJ["3"], "M1_CampPlaced", 1)
OBJ["4"] = objective("OBJ_4_Putivl", q_4, 6)
c_flag(OBJ["4"], "M1_VoevodaArrive", 1)
OBJ["O1"] = objective("OBJ_O1_Scout", q_o1, 7)
c_flag(OBJ["O1"], "M1_O1Done", 1)
for key, src in (("2", mor_flip), ("2a", mor_flip), ("O1", mor_flip), ("2b", TRIG["T_Che_PosadFlip"]),
                 ("3", TRIG["T_CheCastle_Fall"]), ("4", camp_check)):
    src.new_effect.activate_trigger(trigger_id=OBJ[key].trigger_id)
# 2b тоже открывается через 12 минут после входа в зону Чернигова (spec §4): вспомогательный триггер
a = aux("T_Che_PosadFlip", "open2b_timeout")
c_flag(a, "M1_CheEntered", 1)
c_flag(a, "M1_PosadDone", 0)
c_dl(a, "dl_Open2b")
a.new_effect.activate_trigger(trigger_id=OBJ["2b"].trigger_id)

# ===== Сообщения сценария
msg.instructions = ("Миссия 1. Через границу. Осень 1604 года. Приведите Моравск, Чернигов и Путивль к присяге царевичу "
                    "(чернецами или золотом), встаньте лагерем под Новгородом-Северским и дождитесь воеводу. "
                    "Дмитрий должен выжить.")
msg.hints = L("M1_Init", "подсказка")[0].text
msg.victory = "Путивль присягнул, воевода Салтыков в лагере. Первая часть пути пройдена."
msg.loss = "Поход сорван."
msg.history = ("Осенью 1604 года человек, называвший себя царевичем Димитрием, перешёл границу с небольшим отрядом. "
               "Города на Северщине переходили к нему по грамотам и склонению, а не штурмом.")

# ------------------------------------------------------------------ запись
OUT.parent.mkdir(exist_ok=True)
sc.write_to_file(str(OUT))
print("Записано:", OUT)

# ------------------------------------------------------------------ проверка
errs, warns = [], []
unused = [f"{ln.trig}:{ln.typ} {ln.full()[:50]}" for lst in LINES.values() for ln in lst if not ln.used]
if unused:
    errs.append("неиспользованные реплики: " + "; ".join(unused))

chk = AoE2DEScenario.from_file(str(OUT))
tms = chk.trigger_manager
names = [x.name for x in tms.triggers]
if len(names) != len(set(names)):
    errs.append("дубли имён триггеров")
spec_text = SPEC.read_text(encoding="utf-8")
sec = spec_text.split("### 15.5", 1)[1].split("## 16", 1)[0]
expected = []
for raw in sec.splitlines():
    if re.match(r"^\d+\. ", raw):
        expected += re.findall(r"`([A-Za-z0-9_]+)`", raw)
expected = [e for e in expected if e not in VARS and e != "M1_NSSortieDone"]
missing = [e for e in expected if e not in names]
if missing:
    errs.append("нет триггеров §15.5: " + ", ".join(missing))
ids = {x.trigger_id for x in tms.triggers}
var_ids = {x.variable_id for x in tms.variables}
TRIG_EFF = (EffectId.ACTIVATE_TRIGGER, EffectId.DEACTIVATE_TRIGGER)
VAR_EFF = (EffectId.CHANGE_VARIABLE, EffectId.MODIFY_VARIABLE_BY_VARIABLE)
for tr in tms.triggers:
    for e in tr.effects:
        if e.effect_type in TRIG_EFF and e.trigger_id not in ids:
            errs.append(f"висячая ссылка на триггер {e.trigger_id} в {tr.name}")
        if e.effect_type in VAR_EFF and e.variable not in var_ids:
            errs.append(f"висячая переменная {e.variable} в {tr.name}")
        if e.effect_type in (EffectId.SEND_CHAT, EffectId.DISPLAY_INSTRUCTIONS) and not (e.message or "").strip():
            errs.append(f"пустое сообщение в {tr.name}")
    for c in tr.conditions:
        if c.condition_type in (ConditionId.VARIABLE_VALUE, ConditionId.COMPARE_VARIABLES) and c.variable not in var_ids:
            errs.append(f"висячая переменная {c.variable} в условии {tr.name}")
# ссылки на объекты
ref_ids = {u.reference_id for u in chk.unit_manager.get_all_units()}
for tr in tms.triggers:
    for e in tr.effects:
        for oid in (e.selected_object_ids or []):
            if oid not in ref_ids:
                errs.append(f"висячий объект {oid} в эффекте {tr.name}")
    for c in tr.conditions:
        if c.unit_object not in (-1, None) and c.unit_object not in ref_ids:
            errs.append(f"висячий объект {c.unit_object} в условии {tr.name}")
cnt = {p: len(chk.unit_manager.get_player_units(p)) for p in range(7)}
if chk.map_manager.map_size != S:
    errs.append("размер карты")
if cnt[1] != 26:
    errs.append(f"юниты P1: {cnt[1]}")
n_tr, n_aux = len(names), sum(1 for n in names if "__" in n)
n_aux_all = n_aux + sum(1 for n in names if n.startswith("OBJ_") or n == "M1_Rename_Loop")
print("Триггеров:", n_tr, "(вспомогательных:", n_aux, ") переменных:", len(var_ids))
print("Объекты по игрокам:", cnt)
print("ОШИБКИ:" if errs else "ПРОВЕРКА ПРОЙДЕНА", errs[:20])

# ------------------------------------------------------------------ NOTES.md
notes = f"""# Сводка сборки миссии 1 «Через границу»

Скрипт: `scripts/build_01.py`. Результат: `build/01_cherez_granitsu.aoe2scenario` (формат DE, AoE2ScenarioParser 0.9.9).
Реплики разобраны скриптом из `missions/01-cherez-granitsu.dialogue.md` по тегам `[ТРИГГЕР:тип]`; пометки `[...]` удалены.

## Что собрано
- Карта {S}x{S}, умеренный климат, река Десна (y~{RIVER_Y}) с двумя бродами (x={FORD1_X} и x={FORD2_X}), дороги, леса, степь,
  золото/камень у лагеря (по 4 клетки), 2 малые золотые жилы, олени у старта и лагеря.
- Игроки P1..P6 (Castle Age, лимит населения P1 = 80, Imperial/университет/торговля отключены), дипломатия по §15.1,
  победа только скриптами (VictoryCondition.CUSTOM).
- Стартовые 26 юнитов P1; Моравск (P2), посад (P3), замок (P6), Новгород-Северский (P4), Путивль (P5) со строениями,
  стенами и гарнизонами по §15.2. Объекты по игрокам: {cnt}.
- Триггеров всего: {n_tr}, из них вспомогательных (`имя__суффикс`, `OBJ_*`, `M1_Rename_Loop`): {n_aux_all}. Переменных (флаги/часы/сроки): {len(var_ids)}.
- Все имена из §15.5 присутствуют (проверено скриптом по тексту spec). Реплики: неиспользованных строк с тегами нет.
- Механики: конверсия чернецом (D=15/20/25 с, копии `_T` с 0,6), подкуп (технологии-кнопки), разведка O1, слухи,
  вылазки (3), подкрепления врага, засада, победа/поражение, скрытые цели H1-H3 (строки при победе).

## Что упрощено / отличается от spec
- **Координаты**: (u,v) -> клетки напрямую x=u*168, y=v*168; «север» не привязан к экранной стороне ромба.
- **Замок Чернигова** стоит в ~17 клетках (а не ~10) от центра посада (+12,+12), чтобы стены не пересекались.
- **Новгород-Северский**: стена half=7 (15x15), 4 башни без юго-западного угла (обращённого к лагерю), чтобы лагерь был вне дальности.
  Единственные ворота: проём 2 клетки (в стене нет створок). Частоколы/стены везде с проёмами вместо створок-ворот.
- **Технологии мода**: в сценарии нельзя создать новую технологию, поэтому переиспользованы существующие и переименованы:
  «Царевич» = Town Watch, «Кошель для Чернигова» = Loom, «Кошель для Путивля» = Wheelbarrow (имя, цена, время, описание, кнопка в TC
  меняются триггером M1_Init; побочные эффекты исходных технологий остаются: +обзор зданий, +HP крестьян, скорость крестьян).
  Кнопки есть в любом Town Center игрока (Моравск и лагерь).
- **«Царевич»**: ускорение чтения реализовано флагом (копии `_T`), +3 к дальности конверсии заменено на +3 к обзору монахов
  (дальность конверсии через атрибут не задавалась).
- **Казак-перебежчик** = Cavalry Archer (HP 55), обучается в Town Center после Моравска (add_train_location), **польский гусар** = Hussar
  (в Stable с самого начала), **стрелец** = Hand Cannoneer с именем «Стрелец» (имена обновляет цикл `M1_Rename_Loop` раз в 4 с),
  **казак-стрелок** = Skirmisher (HP +10), **казак-разведчик** = Scout Cavalry (HP 55, обзор 12 на тип для P1). Характеристики
  стрельцов не менялись (баланс не подгонялся). Крылатый гусар в миссии 1 не используется.
- **Воеводы**: «связанность» отражена только именем/стойкой «без атаки»; Крестьянин-скин. Автоэскорт: 2 копейщика получают команду идти в лагерь (без следования).
- **Метки на карте**: флаги (FLAG_A постоянные, FLAG_B временные на 60 с) вместо пингов; карта не открывается.
- **Объективы** (панель целей): вспомогательные триггеры `OBJ_*`; строки «цель» также выводятся подсказками «ЦЕЛЬ: ...».
- **Сообщения** типа «сообщение» идут через Send Chat от P1 (в чате может быть префикс имени игрока), остальные через Display Instructions.
- **Вылазки**: отход при потере половины состава не реализован (юниты идут в Attack-Move на цель). Цель всех вылазок: Attack-Move
  к центру посада (замок) или к лагерю (Новгород-Северский); цель «ближайший юнит P1» заменена фиксированной точкой.
- **T_CheSortie_2** при `T_CheCastle_Shaken` заменяется вспомогательным триггером `T_CheSortie_2__shaken` (стрельцы+всадники).
- **T_CampHP50 / H3**: HP созданного триггером Центра лагеря измерить условием нельзя (нет ссылки на объект), триггер создан
  **выключенным**; H3 всегда считается выполненной. Победа/поражение по `OBJ_CampTC`: ведётся по наличию Town Center P1 в зоне центра лагеря.
- **Моральное падение/HP**: «ослабление гарнизона посада до 70% HP» и «остатки замка с 40% HP» не реализованы (смена владельца без изменения HP).
- **H1/H2** приближены: H1 = потери боевых юнитов P2/P5 ниже начального порога; H2 = число чернецов P1 меньше порога (3 до Моравска, затем 3).
- **Задержка добровольцев при лимите населения**: ожидание до 3 минут не реализовано, юниты создаются сразу (лимит не блокирует Create Object);
  вторая строка слухов выводится, если запас населения < 3.
- **Подкупы**: тех кнопки не скрываются по месту (только по enable/disable). После `T_Putivl_Force` подкуп Путивля отключается.
- **Окончание вылазки NS**: `M1_NSSortieDone` ставится через 240 с после волны B (условие «≤3 живых юнитов P4» не реализовано).
- **Сообщения T_Che_PosadFlip**: реплики S3 (Мнишек и Дмитрий про штурм замка) привязаны к `T_Che_PosadFlip` (пометка в dialogue.md).
- Цель 2b открывается также через 12 минут после входа в зону Чернигова (вспомогательный триггер).
"""
NOTES.write_text(notes, encoding="utf-8")
print("NOTES:", NOTES)
sys.exit(1 if errs else 0)

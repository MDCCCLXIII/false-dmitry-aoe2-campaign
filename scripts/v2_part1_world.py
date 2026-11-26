# Часть 1: карта, высоты, местность, города, декор. Выполняется в общем пространстве имён build_01_v2.py
import json
import math
import random
import re
from collections import Counter, defaultdict, deque

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.heroes import HeroInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.techs import TechInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.datasets.conditions import ConditionId
from AoE2ScenarioParser.datasets.object_support import StartingAge, Civilization
from AoE2ScenarioParser.datasets.trigger_lists import (
    Comparison, Operation, ObjectAttribute, ObjectType, AttackStance, ActionType,
    ButtonLocation, Attribute, DiplomacyState, VictoryCondition, ColorMood,
)

ROOT = HERE.parent
DESIGN = ROOT / "missions" / "01-cherez-granitsu.v2-design.md"
DIALOGUE = ROOT / "missions" / "01-cherez-granitsu.dialogue.v2.md"
OUT = ROOT / "build" / "01_cherez_granitsu_v2.aoe2scenario"
NOTES_V2 = ROOT / "build" / "NOTES_v2.md"
S = 200
rng = random.Random(1604)
G = TerrainId

DSETS = (BuildingInfo, OtherInfo, UnitInfo, HeroInfo)


def K(name):
    for ds in DSETS:
        if hasattr(ds, name):
            return getattr(ds, name).ID
    raise KeyError(name)


# ---------------------------------------------------------------- сценарий
sc = AoE2DEScenario.from_default()
um, tm, pm, mm, msg, opt = (sc.unit_manager, sc.trigger_manager, sc.player_manager,
                            sc.map_manager, sc.message_manager, sc.option_manager)
mm.map_size = S
N = S * S
assert len(mm.terrain) == N


def I(x, y):
    return y * S + x


def inb(x, y, m=0):
    return m <= x < S - m and m <= y < S - m


H = [1] * N
T = [int(G.GRASS_1)] * N
FIXED = bytearray(N)      # клетки, высоту которых сглаживание не меняет (вода, дно оврагов)
LOCK = bytearray(N)       # клетки с особой местностью (вода, дороги, поля): фон и леса их не трогают
WATER = {int(G.WATER_DEEP), int(G.WATER_MEDIUM)}
WALKWATER = {int(G.WATER_SHALLOW), int(G.SHALLOWS), int(G.SWAMP_SHALLOWS), int(G.FOREST_REEDS_SHALLOWS)}
FORESTS = {int(getattr(G, n)) for n in ("FOREST_PINE", "FOREST_AUTUMN", "FOREST_OAK", "FOREST_OAK_GREEN", "FOREST_BIRCH",
                                        "FOREST_SPRUCE", "FOREST_BUSH", "FOREST_OAK_BUSH")}


def setT(x, y, t, lock=False):
    if inb(x, y):
        T[I(x, y)] = int(t)
        if lock:
            LOCK[I(x, y)] = 1


def is_water(x, y):
    return T[I(x, y)] in WATER


# ---------------------------------------------------------------- геометрия рек
def lerp_poly(pts, step=0.7):
    out = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / step))
        for i in range(n):
            out.append((ax + (bx - ax) * i / n, ay + (by - ay) * i / n))
    out.append(pts[-1])
    return out


def dist_field(points, R):
    """Расстояние до ближайшей точки ломаной (в пределах R), inf иначе."""
    INF = 999.0
    d = [INF] * N
    for (px, py) in points:
        x0, x1 = int(px - R), int(px + R) + 1
        y0, y1 = int(py - R), int(py + R) + 1
        for y in range(max(0, y0), min(S, y1 + 1)):
            dy = y - py
            for x in range(max(0, x0), min(S, x1 + 1)):
                dd = math.hypot(x - px, y - py)
                if dd < d[I(x, y)]:
                    d[I(x, y)] = dd
    return d


DESNA_PTS = [(199, 179), (172, 158), (148, 144), (124, 126), (104, 112), (90, 106), (76, 88), (66, 72), (52, 62),
             (32, 48), (12, 34), (8, 30)]


def desna_y(x):
    pts = DESNA_PTS
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if bx <= x <= ax:
            t = (x - bx) / float(ax - bx) if ax != bx else 0
            base = by + (ay - by) * t
            break
    else:
        base = pts[0][1] if x > 199 else pts[-1][1]
    return base + 2.0 * math.sin(2 * math.pi * x / 18.0)


DESNA_C = [(x, desna_y(x)) for x in [i * 0.5 for i in range(16, 400)]]
SEYM_PTS = [(199, 52), (180, 54), (160, 66), (144, 84), (132, 104), (124, 126)]
SEYM_C = lerp_poly(SEYM_PTS)


def seym_y(x):
    pts = SEYM_PTS
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if bx <= x <= ax:
            t = (x - bx) / float(ax - bx)
            return by + (ay - by) * t
    return pts[-1][1]


DD = dist_field(DESNA_C, 14)
DS_ = dist_field(SEYM_C, 12)


def desna_half(x):
    return 3.0 if x < 90 else 2.5


# ---------------------------------------------------------------- вода
for y in range(S):
    for x in range(S):
        i = I(x, y)
        if x <= 4:
            setT(x, y, G.WATER_DEEP, True)
        elif x <= 7:
            setT(x, y, G.WATER_MEDIUM, True)
        elif x == 8:
            setT(x, y, G.WATER_SHALLOW if (y // 5) % 2 == 0 else G.WATER_MEDIUM, True)
        elif x == 9:
            setT(x, y, G.BEACH_WET_GRAVEL, True)
        elif x == 10:
            setT(x, y, G.BEACH_VEGETATION, True)
        d = DD[i]
        half = desna_half(x)
        if x > 9 and d <= half + 1.5:
            if d <= half - 1:
                setT(x, y, G.WATER_MEDIUM, True)
            elif d <= half:
                setT(x, y, G.WATER_SHALLOW, True)
            elif d <= half + 1.0:
                setT(x, y, G.BEACH_WET, True)
            else:
                setT(x, y, G.BEACH_WET_GRAVEL if (x + y) % 3 else G.DIRT_MUD, True)
        d2 = DS_[i]
        if d2 <= 3.5:
            north = y > seym_y(x)
            if d2 <= 1.5:
                setT(x, y, G.WATER_MEDIUM, True)
            elif d2 <= 2.0 and north:
                setT(x, y, G.WATER_SHALLOW, True)
            elif d2 <= 2.5:
                setT(x, y, G.BEACH_WET, True)
            elif d2 <= 3.5 and (x * 7 + y * 3) % 4 == 0:
                setT(x, y, G.BEACH_WET_GRAVEL, True)
# высадка: отмель
for y in range(12, 16):
    for x in range(9, 15):
        setT(x, y, G.BEACH, True)
for y in range(11, 17):
    for x in range(7, 13):
        if T[I(x, y)] in WATER or T[I(x, y)] == int(G.WATER_SHALLOW):
            pass
# Стрижень и малые ручьи (мелководье, проходимы)
STRIZHEN = [(66, 160), (67, 140), (65, 118), (70, 92)]
for (px, py) in lerp_poly(STRIZHEN, 0.6):
    for dx in (0, 1):
        x, y = int(round(px)) + dx, int(round(py))
        if inb(x, y) and T[I(x, y)] not in WATER:
            setT(x, y, G.WATER_SHALLOW, True)
for (px, py) in lerp_poly([(34, 0), (34, 36), (32, 46)], 0.6):          # пограничный ручей (дно R1)
    x, y = int(round(px)), int(round(py))
    setT(x, y, G.WATER_SHALLOW, True)
for pts in ([(150, 180), (150, 164), (154, 152), (156, 146)], [(160, 80), (161, 72), (160, 66)]):
    pass
# броды: (центр, ширина вдоль реки)
FORDS = [("Моравский", (71, 80), 7), ("Верхний", (144, 141), 6), ("Северский", (176, 161), 5)]
for nm, (fx, fy), wd in FORDS:
    for y in range(fy - 9, fy + 10):
        for x in range(fx - 9, fx + 10):
            if not inb(x, y):
                continue
            r = math.hypot(x - fx, y - fy)
            was = T[I(x, y)]
            if r <= wd / 2.0 + 0.6 and was in (int(G.WATER_MEDIUM), int(G.WATER_SHALLOW)):
                setT(x, y, G.WATER_SHALLOW if r <= wd / 4.0 + 1 else G.SHALLOWS, True)
            elif r <= wd / 2.0 + 0.6 and was in (int(G.BEACH_WET), int(G.BEACH_WET_GRAVEL), int(G.DIRT_MUD)):
                setT(x, y, G.SHALLOWS, True)
            elif r <= wd / 2.0 + 4 and DD[I(x, y)] <= desna_half(x) + 4.5 and was not in WALKWATER and was not in WATER:
                setT(x, y, G.DIRT_MUD, True)

# ---------------------------------------------------------------- высоты
BUMPS = [
    ("seg", 32, 0, 36, 40, 3, 9, 3),            # B1 рубежная гряда
    ("pt", 62, 52, 11, 16, 2),                   # B2 Моравск
    ("pt", 72, 126, 17, 25, 3),                  # B3 плато посада
    ("pt", 96, 121, 8, 13, 5),                   # B4 Замковая гора
    ("pt", 52, 128, 6, 11, 4),                   # B5 Елецкая гора
    ("pt", 58, 108, 2, 6, 4), ("pt", 64, 104, 2, 6, 4), ("pt", 70, 100, 2, 6, 4),   # B6
    ("pt", 160, 168, 12, 20, 6),                 # B7 Северская гора
    ("pt", 140, 156, 12, 18, 2),                 # B8 табор
    ("pt", 176, 72, 10, 16, 5),                  # B9 кремль
    ("pt", 169, 91, 14, 20, 4),                  # B9a посад
    ("pt", 192, 76, 5, 9, 4),                    # B10 Молченский
    ("pt", 42, 30, 3, 7, 3),                     # B11 застава
    ("pt", 104, 136, 2, 5, 4),                   # B12 курган
]
for (cx, cy, h, r) in [(40, 70, 2, 8), (30, 100, 3, 10), (100, 60, 2, 10), (120, 80, 2, 9), (100, 172, 3, 12),
                       (60, 170, 2, 12), (130, 190, 3, 10), (192, 120, 3, 9), (158, 40, 2, 10), (110, 30, 2, 12)]:
    BUMPS.append(("pt", cx, cy, r / 3.0, r, h))


def bump_val(b, x, y):
    if b[0] == "seg":
        _, ax, ay, bx, by, rt, rb, h = b
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / float(dx * dx + dy * dy)))
        r = math.hypot(x - (ax + t * dx), y - (ay + t * dy))
    else:
        _, cx, cy, rt, rb, h = b
        r = math.hypot(x - cx, y - cy)
    if r <= rt:
        return h
    if r >= rb:
        return 1
    return 1 + (h - 1) * (rb - r) / float(rb - rt)


for b in BUMPS:
    if b[0] == "seg":
        xs = (min(b[1], b[3]) - b[6], max(b[1], b[3]) + b[6])
        ys = (min(b[2], b[4]) - b[6], max(b[2], b[4]) + b[6])
    else:
        xs = (b[1] - b[4], b[1] + b[4])
        ys = (b[2] - b[4], b[2] + b[4])
    for y in range(max(0, int(ys[0])), min(S, int(ys[1]) + 1)):
        for x in range(max(0, int(xs[0])), min(S, int(xs[1]) + 1)):
            v = bump_val(b, x, y)
            if v > 1:
                H[I(x, y)] = max(H[I(x, y)], int(round(v)))

# пологий фон: низкочастотный шум поднимает часть поля до 2
_ph = [(rng.uniform(0.03, 0.09), rng.uniform(0.03, 0.09), rng.uniform(0, 6.28)) for _ in range(5)]
for y in range(S):
    for x in range(S):
        n = sum(math.sin(fx * x + fy * y + ph) for fx, fy, ph in _ph)
        if n > 0.35:
            H[I(x, y)] = max(H[I(x, y)], 2)
# высокий северный берег Десны и Сейма
for y in range(S):
    for x in range(S):
        i = I(x, y)
        if x >= 60 and DD[i] < 90 and y > desna_y(x):
            de = DD[i] - desna_half(x)
            if de >= 2:
                H[i] = max(H[i], min(3, int(de) - 1))
        if x >= 150 and DS_[i] < 90 and y > seym_y(x):
            de = DS_[i] - 2
            if de >= 2:
                H[i] = max(H[i], min(3, int(de) - 1))
        if DD[i] - desna_half(x) <= 6 and y < desna_y(x) and not (x < 60):
            H[i] = min(H[i], 1)
        elif DD[i] - desna_half(x) <= 6 and y < desna_y(x):
            H[i] = min(H[i], 1)

# плато городов (прямоугольные вершины); значения высот по §2.4
PLATEAUS = [((53, 43, 71, 61), 2),            # Моравск
            ((58, 110, 86, 142), 3),          # посад Чернигова
            ((88, 114, 104, 128), 5),         # замок
            ((149, 162, 173, 185), 6),        # Новгород-Северский
            ((166, 63, 186, 81), 5),          # кремль Путивля
            ((151, 81, 187, 102), 4),         # посад Путивля
            ((46, 122, 58, 134), 4),          # Елецкий
            ((186, 70, 198, 82), 4),          # Молченский
            ((130, 146, 150, 166), 2)]        # табор
for (x0, y0, x1, y1), h in PLATEAUS:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            H[I(x, y)] = max(H[I(x, y)], h)

# вода = 0
for i in range(N):
    if T[i] in WATER or T[i] in WALKWATER:
        H[i] = 0
        FIXED[i] = 1

# овраги
RAVINES = [("R1", [(34, 0), (34, 36), (32, 46)], 3, 2, G.GRASS_2),
           ("R2", [(87, 108), (87, 120), (87, 134)], 2, 2, G.GRASS_DRY),
           ("R3", [(148, 182), (148, 166), (152, 154), (158, 146)], 3, 3, G.UNDERBRUSH),
           ("R4", [(180, 186), (179, 174), (182, 162)], 2, 2, G.GRASS_OTHER),
           ("R5", [(160, 80), (161, 72), (160, 66)], 2, 2, G.GRASS_2),
           ("R6", [(90, 80), (96, 96), (98, 108)], 2, 2, G.UNDERBRUSH_LEAVES),
           ("R7", [(120, 100), (126, 116), (124, 124)], 2, 2, G.UNDERBRUSH),
           ("R8", [(40, 120), (48, 119), (44, 112)], 2, 1, G.UNDERBRUSH),
           ("R9", [(118, 152), (122, 140), (122, 130)], 2, 2, G.UNDERBRUSH)]
RAV_CELLS = {}
for nm, pts, w, depth, bottom in RAVINES:
    dist = dist_field(lerp_poly(pts, 0.6), w / 2.0 + 3.5)
    for i in range(N):
        d = dist[i]
        if d > w / 2.0 + 3.5 or FIXED[i] or T[i] in WATER:
            continue
        x, y = i % S, i // S
        if d <= w / 2.0 + 0.2:
            H[i] = max(0, H[i] - depth)
            FIXED[i] = 2
            if not LOCK[i]:
                T[i] = int(bottom)
            RAV_CELLS[i] = nm
        elif d <= w / 2.0 + 2.2 and not LOCK[i]:
            T[i] = int(G.UNDERBRUSH)
            LOCK[i] = 0

# ---------------------------------------------------------------- здания: учёт занятости
SZ = {}
for n_, s_ in (("TOWN_CENTER", 4), ("MARKET", 4), ("CASTLE", 4), ("MONASTERY", 3), ("BARRACKS", 3), ("STABLE", 3),
               ("ARCHERY_RANGE", 3), ("BLACKSMITH", 3), ("DOCK", 3), ("FARM", 3), ("MILL", 2), ("HOUSE", 2),
               ("LUMBER_CAMP", 2), ("GRANARY", 2), ("FOLWARK", 3), ("CHAPEL", 3), ("DORMITION_CATHEDRAL", 4),
               ("KEEP", 3), ("STORAGE", 2), ("FISH_TRAP", 2), ("GRAIN_STORAGE", 2), ("ARMY_TENT_A", 3),
               ("TENT_A", 2), ("TENT_B", 2), ("TENT_C", 2), ("TENT_D", 2), ("TENT_E", 2), ("BURNED_BUILDING_A", 3),
               ("BURNED_BUILDING_B", 3), ("BURNED_BUILDING_C", 3), ("BURNED_BUILDING_D", 3), ("BURNED_BUILDING_E", 3),
               ("SIEGE_CAMP_EQUIPMENT", 2), ("CAVE_ROCK_1", 2), ("RUBBLE_2_X_2", 2), ("ROCK_FORMATION_1", 2),
               ("HUT_A", 2), ("HUT_B", 2), ("HUT_C", 2), ("HUT_D", 2), ("HUT_E", 2), ("HUT_F", 2), ("HUT_G", 2),
               ("SIEGE_PROPS", 2), ("CART", 1), ("SUPPLY_CART_A", 2), ("SUPPLY_CART_B", 2), ("STAKE_BARRICADE", 1)):
    SZ[K(n_)] = s_
WALL_CONSTS = {K("PALISADE_WALL"), K("FORTIFIED_PALISADE_WALL")}
GATE_NS, GATE_WE = K("PALISADE_GATE_NORTH_TO_SOUTH"), K("PALISADE_GATE_WEST_TO_EAST")
HUTS = [K("HUT_" + c) for c in "ABCDEFG"]
UNIT_NAMES = {}

occ = {}          # клетка -> метка ('b' здание, 'f' ограда, 'w' стена, 'u' декор)
ROAD = set()      # клетки улиц и дорог
REC = []          # следы строений для выравнивания высот
NAMED = {}        # имя -> юнит (для триггеров)
GATES = defaultdict(list)
CNT = defaultdict(Counter)
REG = Counter()      # (игрок, тип) -> число поставленных объектов
QSHORT = []
CUR = ["-"]
UCELLS = set()    # клетки, где стоят юниты (лес не ставим)
FIELD_CELLS = set()   # огороды/пашня (считаются заполнением)
ZONES_DENSITY = {}    # город -> (rect стены) для проверки


def free_cell(x, y):
    if not inb(x, y, 1) or (x, y) in occ or (x, y) in ROAD:
        return False
    t = T[I(x, y)]
    return t not in WATER and t not in WALKWATER


def put(player, const, tlx, tly, size=None, name=None, tag="b", flat=None, rot=0):
    size = size or SZ.get(const, 1)
    for i in range(size):
        for j in range(size):
            occ[(tlx + i, tly + j)] = tag
    if size >= 2 and flat is not False:
        REC.append((tlx, tly, size))
    u = um.add_unit(player, const, x=tlx + size / 2.0, y=tly + size / 2.0, rotation=rot)
    if name:
        NAMED[name] = u
    REG[(player, const)] += 1
    if const not in WALL_CONSTS:
        CNT[CUR[0]]["obj"] += 1
    return u


def fits(tlx, tly, size, rect=None, allow_f=False):
    for i in range(size):
        for j in range(size):
            c = (tlx + i, tly + j)
            if rect and not (rect[0] <= c[0] <= rect[2] and rect[1] <= c[1] <= rect[3]):
                return False
            if allow_f and occ.get(c) == "f":
                continue
            if not free_cell(*c):
                return False
    return True


def place(player, const, tlx, tly, size=None, name=None, rect=None, maxr=7, tag="b"):
    """Ставит строение у желаемой точки; при занятости ищет ближайшее свободное место по спирали."""
    size = size or SZ.get(const, 1)
    for r in range(0, maxr + 1):
        cands = [(tlx + dx, tly + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
        rng.shuffle(cands)
        for (x, y) in cands:
            if fits(x, y, size, rect):
                return put(player, const, x, y, size, name, tag)
    MISSED.append((CUR[0], const, tlx, tly))
    return None


MISSED = []


def put1(player, const, x, y, name=None, tag="u"):
    return put(player, const, x, y, 1, name, tag)


def decor_at(const, x, y, player=0):
    if free_cell(x, y):
        return put(player, const, x, y, 1, tag="u")
    return None


def unit_at(player, const, x, y, name=None):
    u = um.add_unit(player, const, x=x + 0.5, y=y + 0.5)
    UCELLS.add((x, y))
    if name:
        NAMED[name] = u
    return u


def scatter(player, const, n, rect, name_prefix=None, avoid_road=False, cnt_key="units"):
    out = []
    x0, y0, x1, y1 = rect
    tries = 0
    while len(out) < n and tries < n * 400:
        tries += 1
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        if not inb(x, y, 1) or (x, y) in occ or (x, y) in UCELLS:
            continue
        t = T[I(x, y)]
        if t in WATER or t in WALKWATER or t in FORESTS:
            continue
        if avoid_road and (x, y) in ROAD:
            continue
        out.append(unit_at(player, const, x, y))
        CNT[CUR[0]][cnt_key] += 1
    if len(out) < n:
        raise RuntimeError(f"нет места для юнитов {const} в {rect}")
    return out


def paint_rect(rect, t, lock=True, only_land=True):
    for y in range(rect[1], rect[3] + 1):
        for x in range(rect[0], rect[2] + 1):
            if inb(x, y) and (not only_land or (T[I(x, y)] not in WATER and T[I(x, y)] not in WALKWATER)):
                setT(x, y, t, lock)


def road_rect(rect, t=G.ROAD_BROKEN):
    for y in range(rect[1], rect[3] + 1):
        for x in range(rect[0], rect[2] + 1):
            if inb(x, y):
                ROAD.add((x, y))
                if T[I(x, y)] not in WATER or True:
                    setT(x, y, t, True)
                    if T[I(x, y)] in WATER:
                        pass


def road_line(pts, width=2, t=G.ROAD_BROKEN):
    for (px, py) in lerp_poly(pts, 0.5):
        for dx in range(width):
            for dy in range(width):
                x, y = int(round(px)) + dx, int(round(py)) + dy
                if inb(x, y) and T[I(x, y)] not in WATER and T[I(x, y)] not in WALKWATER:
                    if (x, y) not in occ:
                        ROAD.add((x, y))
                        setT(x, y, t, True)
                elif inb(x, y) and T[I(x, y)] in WALKWATER and (x, y) not in occ and t == G.ROAD_BROKEN:
                    ROAD.add((x, y))


# ---------------------------------------------------------------- стены, ворота, башни
def wall_cells(x0, y0, x1, y1, cut=0, skip_side=None):
    cells = []
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if x in (x0, x1) or y in (y0, y1):
                # срезанные углы
                if cut:
                    dx = min(x - x0, x1 - x)
                    dy = min(y - y0, y1 - y)
                    if dx + dy < cut:
                        continue
                    if dx + dy == cut and dx != 0 and dy != 0:
                        pass
                cells.append((x, y))
    if cut:
        for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            for k in range(1, cut):
                cells.append((cx + sx * k, cy + sy * (cut - k)))
    if skip_side:
        cells = [c for c in cells if not skip_side(c)]
    return sorted(set(cells))


def build_wall(player, const, x0, y0, x1, y1, cut=0, gates=(), skip_side=None, gate_player=None):
    gate_cells = {(g[0], g[1]): g for g in gates}
    units = {}
    for (x, y) in wall_cells(x0, y0, x1, y1, cut, skip_side):
        if (x, y) in gate_cells:
            vertical = x in (x0, x1)
            gc = GATE_NS if vertical else GATE_WE
            u = put(gate_player if gate_player is not None else player, gc, x, y, 1, tag="w", flat=False)
            CNT[CUR[0]]["obj"] -= 0
            GATES[gate_player if gate_player is not None else player].append(u)
            REC.append((x - 1, y - 1, 3))
            NAMED[f"gate_{x}_{y}"] = u
        else:
            units[(x, y)] = put(player, const, x, y, 1, tag="w", flat=False)
    return units


def towers(player, const, cells):
    out = []
    for (x, y) in cells:
        if (x, y) in occ:
            # соседняя свободная
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                if (x + dx, y + dy) not in occ and free_cell(x + dx, y + dy):
                    x, y = x + dx, y + dy
                    break
        out.append(put(player, const, x, y, 1, tag="w", flat=False))
    return out


# ---------------------------------------------------------------- дворы и кварталы
AUX = {
    "house": ["HAY_STACK", "BARRELS", "LUMBER", "SMOKE", "BUSH_A", "HAY_STACK"],
    "poor": ["HAY_STACK", "BUSH_B", "PLANT_WEEDS", "SMOKE", "BUSH_C"],
    "granary": ["HAY_STACK", "HAY_STACK", "BARRELS", "SMOKE"],
    "craft": ["BARRELS", "LUMBER", "BENCH_WOODEN", "WEAPON_RACK", "SMOKE", "FURNACE"],
    "merchant": ["GOODS", "GOODS", "BARRELS", "VASES", "STORAGE"],
    "soldier": ["WEAPON_RACK", "WATER_TROUGH", "WEAPON_RACK", "HORSE_A", "SMOKE"],
}
UNIT_AUX = {"HORSE_A", "HORSE_B", "COW_A", "SHEEP", "PIG"}


def try_yard(rect, x, y, w, h, kind, house_owner, ring_const):
    ring, inner = [], []
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            (ring if (xx in (x, x + w - 1) or yy in (y, y + h - 1)) else inner).append((xx, yy))
    for (xx, yy) in inner + ring:
        if not (rect[0] <= xx <= rect[2] and rect[1] <= yy <= rect[3]):
            return False
    for c in inner:
        if not free_cell(*c):
            return False
    for c in ring:
        if occ.get(c) in ("f",) or c in ROAD:
            continue
        if not free_cell(*c):
            return False
    # калитка: клетка ограды ближе всего к дороге
    gap = None
    best = 99
    for c in ring:
        if c in ROAD or occ.get(c) == "f":
            continue
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if (c[0] + dx, c[1] + dy) in ROAD:
                    dd = abs(dx) + abs(dy)
                    if dd < best:
                        best, gap = dd, c
    if gap is None:
        gap = ring[(len(ring) // 2)]
    for c in ring:
        if c == gap or c in ROAD or occ.get(c) == "f":
            continue
        put(0, ring_const, c[0], c[1], 1, tag="f")
    main = {"house": K("HOUSE"), "poor": rng.choice(HUTS), "granary": K("GRANARY"), "craft": K("HOUSE"),
            "merchant": K("HOUSE"), "soldier": K("HOUSE")}[kind]
    owner = 0 if kind == "poor" else house_owner
    if kind == "granary":
        owner = 0
    ix, iy = inner[0]
    put(owner, main, ix, iy, 2)
    free_in = [c for c in inner if c not in occ]
    rng.shuffle(free_in)
    items = AUX[kind][:]
    rng.shuffle(items)
    for c in free_in[:len(items)]:
        nm = items.pop()
        if nm in UNIT_AUX:
            unit_at(0, K(nm), c[0], c[1])
            CNT[CUR[0]]["obj"] += 1
            occ[c] = "u"
        elif nm == "STORAGE":
            put(0, K("HAY_STACK"), c[0], c[1], 1, tag="u")
        else:
            put(0, K(nm), c[0], c[1], 1, tag="u")
    return True


def try_yard3(rect, x, y, w, h, kind, house_owner, ring_const, fx, fy):
    """Компактный двор w x h: дом 2x2 в углу, хозобъекты в остатке, ограда на двух дальних сторонах."""
    def Gc(i, j):
        return (x + (w - 1 - i if fx else i), y + (h - 1 - j if fy else j))
    house = [(0, 0), (1, 0), (0, 1), (1, 1)]
    fence = [(i, j) for i in range(w) for j in range(h) if i == w - 1 or j == h - 1]
    auxc = [(i, j) for i in range(w) for j in range(h) if (i, j) not in house and (i, j) not in fence]
    for (i, j) in house + auxc + fence:
        c = Gc(i, j)
        if not (rect[0] <= c[0] <= rect[2] and rect[1] <= c[1] <= rect[3]):
            return False
    for (i, j) in house + auxc:
        if not free_cell(*Gc(i, j)):
            return False
    for (i, j) in fence:
        c = Gc(i, j)
        if occ.get(c) == "f" or c in ROAD:
            continue
        if not free_cell(*c):
            return False
    fc = [Gc(i, j) for (i, j) in fence if Gc(i, j) not in ROAD and occ.get(Gc(i, j)) != "f"]
    gap = None
    best = 99
    for c in fc:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if (c[0] + dx, c[1] + dy) in ROAD and abs(dx) + abs(dy) < best:
                    best, gap = abs(dx) + abs(dy), c
    if gap is None and fc:
        gap = fc[len(fc) // 2]
    for c in fc:
        if c != gap:
            put(0, ring_const, c[0], c[1], 1, tag="f")
    main = {"house": K("HOUSE"), "poor": rng.choice(HUTS), "granary": K("GRANARY"), "craft": K("HOUSE"),
            "merchant": K("HOUSE"), "soldier": K("HOUSE")}[kind]
    owner = 0 if kind in ("poor", "granary") else house_owner
    hx, hy = Gc(0, 0)
    hx = min(Gc(0, 0)[0], Gc(1, 1)[0])
    hy = min(Gc(0, 0)[1], Gc(1, 1)[1])
    put(owner, main, hx, hy, 2)
    cells = [Gc(i, j) for (i, j) in auxc]
    rng.shuffle(cells)
    items = AUX[kind][:]
    rng.shuffle(items)
    for c in cells:
        if not items:
            break
        nm = items.pop()
        if nm in UNIT_AUX:
            unit_at(0, K(nm), c[0], c[1])
            CNT[CUR[0]]["obj"] += 1
            occ[c] = "u"
        elif nm == "STORAGE":
            put(0, K("HAY_STACK"), c[0], c[1], 1, tag="u")
        else:
            put(0, K(nm), c[0], c[1], 1, tag="u")
    return True


def pack_yards(rect, mix, house_owner=0, ring_const=None, passes=2):
    ring_const = ring_const or K("FENCE")
    kinds = []
    for k, wgt in mix.items():
        kinds += [k] * wgt
    n = 0
    for _ in range(passes):
        for y in range(rect[1], rect[3] + 1):
            for x in range(rect[0], rect[2] + 1):
                if not free_cell(x, y):
                    continue
                sizes = [(3, 3), (3, 3), (4, 3), (3, 4), (4, 4)]
                rng.shuffle(sizes)
                done = False
                for (w, h) in sizes:
                    for fx, fy in rng.sample([(0, 0), (1, 0), (0, 1), (1, 1)], 4):
                        kind = rng.choice(kinds)
                        rc = ring_const
                        if kind == "poor":
                            rc = rng.choice([K("BROKEN_FENCE_A"), K("BROKEN_FENCE_B")])
                        if try_yard3(rect, x, y, w, h, kind, house_owner, rc, fx, fy):
                            n += 1
                            done = True
                            break
                    if done:
                        break
    print("yards", rect, n, "free", len(rect_free_cells(rect)))
    return n


def quota(player, const, target, rects, size=2, label=""):
    """Добирает число зданий до цели: голые строения в любых свободных местах прямоугольников."""
    have = REG[(player, const)]
    for rect in rects:
        for y in range(rect[1], rect[3] + 1):
            for x in range(rect[0], rect[2] + 1):
                if have >= target:
                    return have
                if fits(x, y, size, rect):
                    put(player, const, x, y, size)
                    have += 1
    if have < target:
        QSHORT.append((CUR[0], label or str(const), player, have, target))
    return have


POCKET = ["HAY_STACK", "BARRELS", "BUSH_A", "BUSH_B", "BUSH_C", "TREE_BIRCH", "TREE_OAK_AUTUMN", "LUMBER",
          "PLANT_WEEDS", "HAY_STACK", "BARRELS", "TREE_BIRCH", "GOODS"]


def pockets(rect, p=0.8, extra=None):
    kinds = POCKET + (extra or [])
    for y in range(rect[1], rect[3] + 1):
        for x in range(rect[0], rect[2] + 1):
            if free_cell(x, y) and rng.random() < p:
                put(0, K(rng.choice(kinds)), x, y, 1, tag="u")


def rect_free_cells(rect):
    return [(x, y) for y in range(rect[1], rect[3] + 1) for x in range(rect[0], rect[2] + 1) if free_cell(x, y)]


def scatter_decor(rect, names, n, owner=0):
    cells = rect_free_cells(rect)
    rng.shuffle(cells)
    k = 0
    for (x, y) in cells[:n]:
        put(owner, K(rng.choice(names)), x, y, 1, tag="u")
        k += 1
    return k


def plaza(rect, stalls=0, wells=1, extras=()):
    road_rect(rect, G.ROAD_GRAVEL)
    for y in range(rect[1], rect[3] + 1):
        for x in range(rect[0], rect[2] + 1):
            ROAD.discard((x, y))     # площадь свободна для торга, но не для дворов
            occ.setdefault((x, y), "p")
    for (x, y) in list(occ):
        pass


def plaza_items(rect, stall_n, well_n, goods_n, barrels_n, torch_n, tree_n, owner_stall=0):
    """Расставляет торг на площади (клетки 'p' освобождаются под объекты)."""
    cells = [(x, y) for y in range(rect[1], rect[3] + 1) for x in range(rect[0], rect[2] + 1) if occ.get((x, y)) == "p"]
    rng.shuffle(cells)

    def take(n, const):
        c = 0
        while c < n and cells:
            x, y = cells.pop()
            occ[(x, y)] = "u"
            um.add_unit(0, K(const), x=x + 0.5, y=y + 0.5)
            CNT[CUR[0]]["obj"] += 1
            c += 1
    take(well_n, "WELL")
    take(stall_n, "MARKET_STALL")
    take(goods_n, "GOODS")
    take(barrels_n, "BARRELS")
    take(torch_n, "TORCH_B")
    take(tree_n, "TREE_OAK_AUTUMN")


def fill_stats(rect, plaza_rect=None):
    """Заполнение внутри стены: занято / (площадь − улицы − площадь)."""
    x0, y0, x1, y1 = rect
    area = filled = 0
    for y in range(y0 + 1, y1):
        for x in range(x0 + 1, x1):
            c = (x, y)
            if plaza_rect and plaza_rect[0] <= x <= plaza_rect[2] and plaza_rect[1] <= y <= plaza_rect[3]:
                continue
            if c in ROAD:
                continue
            area += 1
            if occ.get(c) in ("b", "f", "u", "w") or c in FIELD_CELLS:
                filled += 1
    big_hole = 0
    for y in range(y0 + 1, y1 - 4):
        for x in range(x0 + 1, x1 - 4):
            ok = True
            for yy in range(y, y + 5):
                for xx in range(x, x + 5):
                    c = (xx, yy)
                    if occ.get(c) in ("b", "f", "u", "w") or c in FIELD_CELLS or c in ROAD:
                        ok = False
                        break
                    if plaza_rect and plaza_rect[0] <= xx <= plaza_rect[2] and plaza_rect[1] <= yy <= plaza_rect[3]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                big_hole += 1
    return filled, area, big_hole


def farm_field(rect, owner, n_farm, strip_dir="h", mill=None):
    """Поле: FARM (3x3) в сетке + полосы пашни FARM_DEAD, стога."""
    x0, y0, x1, y1 = rect
    placed = 0
    for y in range(y0, y1 - 2, 3):
        for x in range(x0, x1 - 2, 3):
            if placed < n_farm and fits(x, y, 3):
                put(owner, K("FARM"), x, y, 3, tag="b")
                placed += 1
                for i in range(3):
                    for j in range(3):
                        FIELD_CELLS.add((x + i, y + j))
            elif fits(x, y, 3):
                for i in range(3):
                    for j in range(3):
                        c = (x + i, y + j)
                        if free_cell(*c):
                            setT(c[0], c[1], G.FARM_DEAD if (x // 3 + y // 3) % 3 else G.FARM_33, True)
                            FIELD_CELLS.add(c)
    if mill:
        place(owner, K("MILL"), mill[0], mill[1], 2)
    return placed


def graves(n, rect, fence=True):
    cells = rect_free_cells(rect)
    rng.shuffle(cells)
    for (x, y) in cells[:n]:
        put(0, K("GRAVE"), x, y, 1, tag="u")


def shore_spot(x, north_bank):
    """Клетка воды у берега реки Десны: для северного берега water-клетка, с севера от которой суша."""
    for y in range(S - 2, 1, -1) if not north_bank else range(1, S - 2):
        pass
    best = None
    for y in range(2, S - 2):
        t = T[I(x, y)]
        if t in WATER or t in WALKWATER:
            if north_bank:
                # суша выше (больше y)
                if T[I(x, y + 1)] not in WATER and T[I(x, y + 1)] not in WALKWATER:
                    best = y
            else:
                if T[I(x, y - 1)] not in WATER and T[I(x, y - 1)] not in WALKWATER and best is None:
                    best = y
    return best


def dock_at(player, x, north_bank, name=None):
    y = shore_spot(x, north_bank)
    if y is None:
        return None
    # док 3x3: кладём так, чтобы центр был над водой у берега
    ty = y - 1 if north_bank else y - 1
    return put(player, K("DOCK"), x - 1, ty, 3, name, tag="b", rot=0)


def find_land_rect(cx, cy, w, h, maxr=30, margin=1):
    for r in range(0, maxr):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x0, y0 = cx + dx - w // 2, cy + dy - h // 2
                ok = True
                for yy in range(y0 - margin, y0 + h + margin):
                    for xx in range(x0 - margin, x0 + w + margin):
                        if not inb(xx, yy, 1) or T[I(xx, yy)] in WATER or T[I(xx, yy)] in WALKWATER or (xx, yy) in occ                                 or T[I(xx, yy)] in (int(G.BEACH_WET), int(G.BEACH_WET_GRAVEL), int(G.DIRT_MUD)):
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    return (x0, y0, x0 + w - 1, y0 + h - 1)
    return None


USEDW = set()


def ships(player, name, n, x, y):
    k = 0
    for r in range(1, 30):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                c = (x + dx, y + dy)
                if k >= n or max(abs(dx), abs(dy)) != r or c in USEDW or not inb(*c, 2):
                    continue
                if T[I(*c)] == int(G.WATER_MEDIUM) and c not in occ and all(
                        T[I(c[0] + a, c[1] + b)] == int(G.WATER_MEDIUM) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                    USEDW.add(c)
                    boat(player, K(name), *c)
                    k += 1


def water_put(player, const, size, n, x, y):
    k = 0
    for r in range(1, 30):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                tl = (x + dx, y + dy)
                if k >= n or max(abs(dx), abs(dy)) != r or tl in USEDW:
                    continue
                cells = [(tl[0] + a, tl[1] + b) for a in range(size) for b in range(size)]
                if all(inb(*c, 2) and T[I(*c)] in (int(G.WATER_MEDIUM), int(G.WATER_SHALLOW)) and c not in occ for c in cells):
                    for c in cells:
                        occ[c] = "b"
                        USEDW.add(c)
                    um.add_unit(player, const, x=tl[0] + size / 2.0, y=tl[1] + size / 2.0)
                    CNT[CUR[0]]["obj"] += 1
                    k += 1


def boat(player, const, x, y):
    u = um.add_unit(player, const, x=x + 0.5, y=y + 0.5)
    CNT[CUR[0]]["units"] += 1
    return u


def water_cell_near(x, y, r=26):
    for rr in range(0, r):
        for dx in range(-rr, rr + 1):
            for dy in range(-rr, rr + 1):
                if max(abs(dx), abs(dy)) == rr and inb(x + dx, y + dy) and T[I(x + dx, y + dy)] == int(G.WATER_MEDIUM) \
                        and (x + dx, y + dy) not in occ:
                    return (x + dx, y + dy)
    return None


PN = {"Mor": 2, "Che": 3, "NS": 4, "Put": 5, "Cas": 6}
P_ = PN
VILL_M, VILL_F = K("VILLAGER_MALE"), K("VILLAGER_FEMALE")

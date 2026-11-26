# Часть 1d (v3): природа вне городов (деревья, рощи, кусты, камни, берега, овраги, звери и птицы).
# Выполняется после v3_part1c_finish.py. Высоты и местность леса не меняются (кроме болотец), «столбов» высот нет:
# все объекты 1x1 (размер 1, без выравнивания следа).
CUR[0] = "Nature"
NAT_START = sum(NAT.values())

# ---- запретные зоны: старт, табор, ворота, броды, городские прямоугольники, придорожная полоса
BLK = bytearray(N)


def block_circle(cx, cy, r):
    for y in range(max(0, int(cy - r)), min(S, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(S, int(cx + r) + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                BLK[I(x, y)] = 1


def block_rect(x0, y0, x1, y1, m=1):
    for y in range(max(0, y0 - m), min(S, y1 + m + 1)):
        for x in range(max(0, x0 - m), min(S, x1 + m + 1)):
            BLK[I(x, y)] = 1


block_circle(24, 14, 10)
block_circle(140, 156, 12)
block_circle(12, 14, 6)
for pl_, lst_ in GATES.items():
    for g_ in lst_:
        block_circle(int(g_.x), int(g_.y), 7)
for nm_, (fx_, fy_), wd_ in FORDS:
    block_circle(fx_, fy_, 10)
for rc_ in (MW, CW, KW, NW, KRW, PW, YW, MW2, SPW):
    block_rect(*rc_, m=1)
for s_ in SITES:
    block_rect(*s_["rect"], m=0) if s_["kind"] != "church" else None
road_near2 = bytearray(N)
for (x_, y_) in ROAD:
    for dx_ in range(-2, 3):
        for dy_ in range(-2, 3):
            if inb(x_ + dx_, y_ + dy_):
                road_near2[I(x_ + dx_, y_ + dy_)] = 1
MEADOW_T = {int(getattr(G, n_)) for n_ in ("GRASS_1", "GRASS_2", "GRASS_DRY", "GRASS_OTHER", "GRASS_FLOWERS_1", "UNDERBRUSH_LEAVES", "UNDERBRUSH")
            if hasattr(G, n_)}


def solid_ok(x, y):
    i = I(x, y)
    return inb(x, y, 2) and not BLK[i] and not road_near2[i]


def n_(name, x, y, cat, solid=True):
    if solid and not solid_ok(x, y):
        return False
    if not solid and (BLK[I(x, y)] if inb(x, y) else True):
        return False
    return nat(name, x, y, cat)


def meadow(x, y):
    i = I(x, y)
    return inb(x, y, 2) and T[i] in MEADOW_T and not LOCK[i] and i not in RAV_CELLS and (x, y) not in occ


def rand_meadow(n):
    out, t = [], 0
    while len(out) < n and t < n * 60:
        t += 1
        x, y = rng.randint(13, S - 3), rng.randint(3, S - 3)
        if meadow(x, y) and solid_ok(x, y):
            out.append((x, y))
    return out


TREES_M = ["TREE_OAK", "TREE_OAK_AUTUMN", "TREE_OAK_AUTUMN", "TREE_BIRCH", "TREE_OAK_GREEN", "TREE_OAK_AUTUMN", "TREE_BIRCH",
           "TREE_ASIAN_MAPLE_AUTUMN"]
BUSHES = ["BUSH_A", "BUSH_B", "BUSH_C", "BUSH_D", "PLANT_UNDERBRUSH", "PLANT_SHRUB_GREEN", "PLANT_BUSH_GREEN"]

# A. одинокие деревья на лугах (разреженно)
for (x, y) in rand_meadow(430):
    n_(rng.choice(TREES_M), x, y, "одинокие_деревья")
# B. рощи: дубравы, берёзовые и смешанные
GROVE_KINDS = {
    "дубрава": (["TREE_OAK", "TREE_OAK_AUTUMN", "TREE_OAK_GREEN", "TREE_OAK_AUTUMN"], ["BUSH_A", "FERN_PATCH", "STUMP"]),
    "берёзовая": (["TREE_BIRCH", "TREE_BIRCH", "TREE_BIRCH", "TREE_OAK_AUTUMN"], ["BUSH_B", "FLOWERS_2", "PLANT_WEEDS"]),
    "смешанная": (["TREE_OAK", "TREE_BIRCH", "TREE_SPRUCE", "TREE_OAK_AUTUMN", "TREE_ASIAN_MAPLE_AUTUMN"], ["BUSH_C", "FERN_PATCH", "FELLED_TREE"]),
}
for gi in range(105):
    kind = list(GROVE_KINDS)[gi % 3]
    trees, under = GROVE_KINDS[kind]
    c = rand_meadow(1)
    if not c:
        continue
    cx_, cy_ = c[0]
    n_tr = rng.randint(7, 15)
    for _ in range(n_tr):
        n_(rng.choice(trees), cx_ + int(rng.gauss(0, 2.6)), cy_ + int(rng.gauss(0, 2.6)), "рощи")
    for _ in range(rng.randint(4, 8)):
        n_(rng.choice(under), cx_ + int(rng.gauss(0, 3.2)), cy_ + int(rng.gauss(0, 3.2)), "опушки_кусты")
# C. опушки лесов с кустарником
fr_cells = []
for y_ in range(3, S - 3):
    for x_ in range(13, S - 3):
        if meadow(x_, y_) and near_forest(x_, y_, 2):
            fr_cells.append((x_, y_))
rng.shuffle(fr_cells)
EDGE_N = ["TREE_OAK_AUTUMN", "TREE_BIRCH", "TREE_OAK", "BUSH_A", "BUSH_B", "BUSH_C", "FERN_PATCH", "FELLED_TREE", "STUMP", "TREE_OAK_AUTUMN",
          "PLANT_UNDERBRUSH", "BUSH_D", "FALLEN_LEAVES_MAPLE_AUTUMN"]
for (x_, y_) in fr_cells[:1100]:
    if rng.random() < 0.55:
        n_(rng.choice(EDGE_N), x_, y_, "опушки_кусты")
# D. подлесок внутри лесов (папоротник, пни, валежник, замшелые камни, листва)
fcells = [c for c in FOREST_CORE if c not in occ and c not in ROAD and not BLK[I(*c)]]
rng.shuffle(fcells)
for (x_, y_) in fcells[:520]:
    n_(rng.choice(["FERN_PATCH", "STUMP", "FELLED_TREE", "ROCK_MOSSY", "PLANT_WEEDS", "FALLEN_LEAVES_MAPLE_AUTUMN", "BUSH_B", "TREE_DEAD",
                   "FELLED_TREE", "FERN_PATCH"]), x_, y_, "лес_подлесок", solid=False)
# E. берега: ива, тростник, осока, коряги, камни, цветы
shore = [(i % S, i // S) for i in range(N) if water_near[i] and T[i] not in WATER and T[i] not in WALKWATER and T[i] not in FORESTS
         and (i % S) > 12 and not BLK[i]]
rng.shuffle(shore)
SHORE_N = ["TREE_WILLOW", "TREE_REEDS", "TREE_REEDS", "TREE_REEDS", "DRIFTWOOD_GROUND", "BUSH_B", "PLANT_WEEDS", "ROCK_BEACH", "FLOWERS_3",
           "TREE_WILLOW", "PLANT_FLOWERS", "GRASS_GREEN", "TREE_BIRCH", "TREE_OAK_AUTUMN", "TREE_REEDS", "GRASS_PATCH_GREEN"]
k_ = 0
for (x_, y_) in shore:
    if k_ >= 1100:
        break
    if rng.random() < 0.5 and not road_near2[I(x_, y_)] or (rng.random() < 0.15 and (x_, y_) not in ROAD and not BLK[I(x_, y_)]):
        nm_ = rng.choice(SHORE_N)
        if nat(nm_, x_, y_, "берега"):
            k_ += 1
# кувшинки и тростник на воде (вне бродов): у береговой полосы
wl_ = [(i % S, i // S) for i in range(N) if T[i] in (int(G.WATER_MEDIUM), int(G.WATER_SHALLOW)) and not BLK[i] and (i % S) > 14
       and any(T[I(min(S - 1, (i % S) + dx_), min(S - 1, (i // S) + dy_))] not in WATER and T[I(min(S - 1, (i % S) + dx_), min(S - 1, (i // S) + dy_))] not in WALKWATER
               for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)))]
rng.shuffle(wl_)
for (x_, y_) in wl_[:170]:
    if (x_, y_) not in occ and (x_, y_) not in UCELLS:
        um.add_unit(0, K("WATER_LILY"), x=x_ + 0.5, y=y_ + 0.5)
        occ[(x_, y_)] = "u"
        NAT["кувшинки"] += 1
# F. овраги: заросли, камни, поваленные деревья
rav_c = []
for i_ in RAV_CELLS:
    x_, y_ = i_ % S, i_ // S
    for dx_ in range(-2, 3):
        for dy_ in range(-2, 3):
            if inb(x_ + dx_, y_ + dy_):
                rav_c.append((x_ + dx_, y_ + dy_))
rav_c = list(set(rav_c))
rng.shuffle(rav_c)
RAV_N = ["BUSH_A", "BUSH_B", "BUSH_C", "PLANT_UNDERBRUSH", "ROCK_MOSSY", "TREE_OAK_AUTUMN", "FERN_PATCH", "FELLED_TREE", "STUMP", "TREE_BIRCH",
         "ROCK_2", "TREE_DEAD", "PLANT_SHRUB_GREEN"]
k_ = 0
for (x_, y_) in rav_c:
    if k_ >= 600:
        break
    if rng.random() < 0.55 and n_(rng.choice(RAV_N), x_, y_, "овраги"):
        k_ += 1
# G. ряды деревьев вдоль дорог (с разрывами, не ближе 4 клеток к полотну)
k_ = 0
for pts in MAIN_ROADS:
    for (px_, py_, nx_, ny_) in side_points(pts, 2.2):
        side = rng.choice((-1, 1))
        for o_ in (4, 5, 6, 7):
            x_, y_ = int(round(px_ + side * o_ * nx_)), int(round(py_ + side * o_ * ny_))
            if rng.random() < 0.42 and n_(rng.choice(TREES_M + BUSHES), x_, y_, "вдоль_дорог"):
                k_ += 1
                break
# H. камни и валуны (у оврагов, на холмах, на лугах)
for (x_, y_) in rand_meadow(170):
    n_(rng.choice(["ROCK_1", "ROCK_2", "ROCK_3", "ROCK_MOSSY", "ROCK_FORMATION_1", "ROCK_FORMATION_2", "ROCK_FORMATION_3", "ROCK_MOSSY"]), x_, y_, "камни")
for (x_, y_) in rav_c[600:760]:
    n_(rng.choice(["ROCK_1", "ROCK_MOSSY", "ROCK_2", "ROCK_FORMATION_1"]), x_, y_, "камни")
# I. трава, цветы, сорняки на лугах; J. стога; L. пни и поваленные деревья
for (x_, y_) in rand_meadow(900):
    n_(rng.choice(["GRASS_PATCH_GREEN", "GRASS_PATCH_DRY", "FLOWERS_1", "FLOWERS_2", "FLOWERS_3", "FLOWERS_4", "PLANT_FLOWERS", "PLANT_HEATHER",
                   "PLANT_WEEDS", "GRASS_GREEN", "GRASS_DRY", "BUSH_A", "FALLEN_LEAVES_MAPLE_AUTUMN", "PLANT_WEEDS", "FERN_PATCH"]),
       x_, y_, "трава_цветы", solid=False)
fld = [c for c in FIELD_CELLS if c not in occ and not BLK[I(*c)]]
rng.shuffle(fld)
for (x_, y_) in fld[:110]:
    nat("HAY_STACK", x_, y_, "стога")
for (x_, y_) in rand_meadow(60):
    n_("HAY_STACK", x_, y_, "стога")
for (x_, y_) in rand_meadow(160):
    n_(rng.choice(["FELLED_TREE", "STUMP", "TREE_DEAD", "FELLED_TREE"]), x_, y_, "валежник")
# M. болотца
BOGS = 0
for _ in range(400):
    if BOGS >= 9:
        break
    cx_, cy_ = rng.randint(20, 188), rng.randint(10, 172)
    rr_ = rng.randint(3, 5)
    cells_ = [(x_, y_) for y_ in range(cy_ - rr_, cy_ + rr_ + 1) for x_ in range(cx_ - rr_, cx_ + rr_ + 1) if (x_ - cx_) ** 2 + (y_ - cy_) ** 2 <= rr_ * rr_]
    if not all(inb(x_, y_, 3) and meadow(x_, y_) and not BLK[I(x_, y_)] and not road_near2[I(x_, y_)] and H[I(x_, y_)] <= 2 for (x_, y_) in cells_):
        continue
    BOGS += 1
    for (x_, y_) in cells_:
        d_ = math.hypot(x_ - cx_, y_ - cy_)
        T[I(x_, y_)] = int(G.SWAMP_BOGLAND if d_ <= rr_ - 1.5 else G.SWAMP_SHALLOWS)
        LOCK[I(x_, y_)] = 1
        mm.terrain[I(x_, y_)].terrain_id = T[I(x_, y_)]
    for (x_, y_) in cells_[::3]:
        nat(rng.choice(["TREE_REEDS", "TREE_DEAD", "PLANT_WEEDS", "TREE_REEDS", "BUSH_C"]), x_, y_, "болотца")
    for k2 in range(3):
        nat("TREE_WILLOW", cx_ + rng.randint(-rr_ - 1, rr_ + 1), cy_ + rr_ + 2, "болотца")
NAT["_болотец"] = BOGS
# O. звери и птицы
def fauna(name, n, where, cat, groups=1, spread=3):
    k = 0
    for _ in range(groups):
        cs = where(1)
        if not cs:
            continue
        cx_, cy_ = cs[0]
        for _ in range(n * 6):
            if k >= n * groups:
                break
            x_, y_ = cx_ + rng.randint(-spread, spread), cy_ + rng.randint(-spread, spread)
            if inb(x_, y_, 2) and not BLK[I(x_, y_)] and T[I(x_, y_)] not in WATER and T[I(x_, y_)] not in WALKWATER and (x_, y_) not in occ \
                    and (x_, y_) not in UCELLS:
                if nat_unit(0, name, x_, y_, cat):
                    k += 1
    return k


def near_water_cells(n):
    out = []
    pool = [c for c in shore if not road_near2[I(*c)]]
    return rng.sample(pool, min(n, len(pool)))


def forest_edge(n):
    pool = [c for c in fr_cells if solid_ok(*c)]
    return rng.sample(pool, min(n, len(pool)))


fauna("DEER", 5, rand_meadow, "олени", 10, 4)
fauna("ELK", 3, forest_edge, "лоси", 4, 3)
fauna("WILD_BOAR", 3, forest_edge, "кабаны", 8, 3)
fauna("HARE_A", 1, rand_meadow, "зайцы", 22, 5)
fauna("HARE_B", 1, rand_meadow, "зайцы", 18, 5)
fauna("RED_FOX", 1, forest_edge, "лисы", 12, 3)
fauna("PHEASANT", 3, rand_meadow, "птицы", 6, 3)
fauna("RED_CROWN_CRANE", 2, near_water_cells, "журавли", 12, 2)
fauna("STORK", 1, near_water_cells, "аисты", 8, 2)
fauna("GOOSE", 4, near_water_cells, "утки_гуси", 9, 2)
fauna("GREY_WOLF", 2, forest_edge, "волки", 5, 3)
fauna("COW_A", 4, rand_meadow, "стада", 4, 3)
fauna("SHEEP", 5, rand_meadow, "стада", 4, 3)
fauna("HORSE_B", 3, rand_meadow, "стада", 3, 3)
for (px_, py_) in [c["c"] for c in SITE_BY["live"]]:           # стада у живых деревень
    fauna("COW_C", 3, lambda n, px_=px_, py_=py_: [(px_ + 11, py_ - 2)], "стада", 1, 3)
    fauna("SHEEP", 5, lambda n, px_=px_, py_=py_: [(px_ - 11, py_ + 2)], "стада", 1, 3)
    fauna("HORSE_A", 2, lambda n, px_=px_, py_=py_: [(px_ - 4, py_ + 9)], "стада", 1, 2)

NATURE_TOTAL = sum(v for k, v in NAT.items() if not k.startswith("_"))
print("природа вне городов:", NATURE_TOTAL, dict(NAT))

# ---------------------------------------------------------------- проходимость к ресурсам и деревням (суша + SHALLOWS), просеки сквозь лес
BADT = set(BAD_WATER) | {int(G.FOREST_REEDS)}
_GC = {(int(u.x), int(u.y)) for pl_, lst_ in GATES.items() for u in lst_}


def _pass(x, y):
    if not inb(x, y):
        return False
    t_ = T[I(x, y)]
    if t_ in BADT or t_ in FORESTS:
        return False
    return occ.get((x, y)) not in ("b", "w", "f") or (x, y) in _GC


def _bfs():
    seen_ = {(SX, SY)}
    dq_ = deque([(SX, SY)])
    while dq_:
        x_, y_ = dq_.popleft()
        for dx_, dy_ in NB8:
            nx_, ny_ = x_ + dx_, y_ + dy_
            if (nx_, ny_) in seen_ or not _pass(nx_, ny_):
                continue
            if dx_ and dy_ and not (_pass(x_ + dx_, y_) and _pass(x_, y_ + dy_)):
                continue
            seen_.add((nx_, ny_))
            dq_.append((nx_, ny_))
    return seen_


def _near(seen_, c_, r_=2):
    return any((c_[0] + a_, c_[1] + b_) in seen_ for a_ in range(-r_, r_ + 1) for b_ in range(-r_, r_ + 1))


TARGETS = [(n_, c_) for n_, c_ in RES_SPOTS if n_ != "рыба"] + [(f"деревня {s_['idx']}", s_["c"]) for s_ in SITES]
CARVED = 0
for it_ in range(6):
    seen_ = _bfs()
    bad_ = [(n_, c_) for n_, c_ in TARGETS if not _near(seen_, c_)]
    if not bad_:
        break
    for n_, c_ in bad_:
        best_ = None
        for r_ in range(1, 60):
            ring_ = [(c_[0] + dx_, c_[1] + dy_) for dx_ in range(-r_, r_ + 1) for dy_ in range(-r_, r_ + 1)
                     if max(abs(dx_), abs(dy_)) == r_ and (c_[0] + dx_, c_[1] + dy_) in seen_]
            if ring_:
                best_ = min(ring_, key=lambda q: (q[0] - c_[0]) ** 2 + (q[1] - c_[1]) ** 2)
                break
        if not best_:
            continue
        for (px_, py_) in lerp_poly([c_, best_], 0.5):
            x_, y_ = int(round(px_)), int(round(py_))
            for ox_, oy_ in ((0, 0), (1, 0), (0, 1)):
                xx_, yy_ = x_ + ox_, y_ + oy_
                if inb(xx_, yy_, 1) and T[I(xx_, yy_)] in FORESTS | {int(G.FOREST_REEDS)} and occ.get((xx_, yy_)) not in ("b", "w", "f"):
                    T[I(xx_, yy_)] = int(G.DIRT_1)
                    LOCK[I(xx_, yy_)] = 1
                    ROAD.add((xx_, yy_))
                    mm.terrain[I(xx_, yy_)].terrain_id = int(G.DIRT_1)
                    CARVED += 1
seen_ = _bfs()
UNREACH_RES = [(n_, c_) for n_, c_ in TARGETS if not _near(seen_, c_)]
# недостижимые ресурсы и ресурсы вплотную к врагам удаляем
_ENEMY = [(u.x, u.y) for u in um.get_all_units() if u.player in (2, 3, 4, 5, 6, 8)]
_RES_C = {K("GOLD_MINE"), K("STONE_MINE"), K("FORAGE_BUSH")}
_removed = 0
for u in list(um.get_all_units()):
    if u.player == 0 and u.unit_const in _RES_C:
        bad_ = any(abs(u.x - ex_) < 4 and abs(u.y - ey_) < 4 for ex_, ey_ in _ENEMY) or not _near(seen_, (int(u.x), int(u.y)), 2)
        if bad_:
            um.remove_unit(unit=u)
            RES[{K("GOLD_MINE"): "GOLD_MINE", K("STONE_MINE"): "STONE_MINE"}.get(u.unit_const, "FORAGE_BUSH")] -= 1
            _removed += 1
print("просеки к целям (клеток):", CARVED, "недостижимых целей после:", UNREACH_RES, "удалено ресурсов (на врагах/недостижимых):", _removed, dict(RES))

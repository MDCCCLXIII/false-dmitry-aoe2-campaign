# Часть 1c: сглаживание высот, выравнивание следов, фон местности, леса, декор вне городов. Общее пространство имён.
NB8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def raise_pass():
    total = 0
    while True:
        ch = 0
        for y in range(S):
            for x in range(S):
                i = I(x, y)
                if FIXED[i]:
                    continue
                m = 0
                for dx, dy in NB8:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < S and 0 <= yy < S:
                        v = H[yy * S + xx]
                        if v > m:
                            m = v
                if H[i] < m - 1:
                    H[i] = m - 1
                    ch += 1
        total += ch
        if not ch:
            return total


def lower_pass():
    total = 0
    while True:
        ch = 0
        for y in range(S):
            for x in range(S):
                i = I(x, y)
                if FIXED[i] == 1:
                    continue
                m = 99
                for dx, dy in NB8:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < S and 0 <= yy < S:
                        v = H[yy * S + xx]
                        if v < m:
                            m = v
                if H[i] > m + 1:
                    H[i] = m + 1
                    ch += 1
        total += ch
        if not ch:
            return total


raise_pass()
lower_pass()
for it in range(30):
    ch = 0
    for (tx, ty, sz) in REC:
        cells = [I(tx + a, ty + b) for a in range(sz) for b in range(sz) if inb(tx + a, ty + b)]
        if not cells:
            continue
        m = min(H[c] for c in cells)
        for c in cells:
            if FIXED[c] != 1 and H[c] != m:
                H[c] = m
                ch += 1
    if not ch:
        break
    lower_pass()
raise_pass()
lower_pass()
for it in range(10):
    ch = 0
    for (tx, ty, sz) in REC:
        cells = [I(tx + a, ty + b) for a in range(sz) for b in range(sz) if inb(tx + a, ty + b)]
        m = min(H[c] for c in cells) if cells else 0
        for c in cells:
            if FIXED[c] != 1 and H[c] != m:
                H[c] = m
                ch += 1
    if not ch:
        break
    lower_pass()


def height_violations():
    bad = 0
    for y in range(S):
        for x in range(S):
            h = H[I(x, y)]
            for dx, dy in NB8:
                xx, yy = x + dx, y + dy
                if 0 <= xx < S and 0 <= yy < S and abs(H[yy * S + xx] - h) > 1:
                    bad += 1
                    break
    return bad


def footprint_unflat():
    bad = 0
    for (tx, ty, sz) in REC:
        hs = {H[I(tx + a, ty + b)] for a in range(sz) for b in range(sz) if inb(tx + a, ty + b)}
        if len(hs) > 1:
            bad += 1
    return bad


# ---------------------------------------------------------------- фон местности
def blob(cx, cy, r, ttype, only_free=True, lock=False):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            if inb(x, y) and math.hypot(x - cx, y - cy) <= r * (0.8 + 0.2 * math.sin(x * 0.7 + y * 0.9)):
                i = I(x, y)
                if not LOCK[i] and T[i] == int(G.GRASS_1) and (x, y) not in occ:
                    T[i] = int(ttype)


for _ in range(30):
    blob(rng.randrange(S), rng.randrange(S), rng.randint(4, 8), G.GRASS_2)
for _ in range(60):
    cx, cy = rng.randrange(S), rng.randrange(S)
    if cy < desna_y(cx) or cy < 60:
        blob(cx, cy, rng.randint(5, 10), G.GRASS_DRY)
for _ in range(15):
    blob(rng.randrange(S), rng.randrange(S), rng.randint(3, 6), G.GRASS_OTHER)
for (px, py) in rng.sample(DESNA_C + SEYM_C, 10):
    blob(px + rng.randint(-5, 5), py + rng.randint(-5, 5), rng.randint(3, 5), G.GRASS_FLOWERS_1)
for (cx, cy, r) in ((26, 40, 5), (80, 98, 4), (112, 118, 5), (136, 100, 4), (150, 72, 4)):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= r and inb(x, y) and not LOCK[I(x, y)] and (x, y) not in occ and T[I(x, y)] not in WATER:
                setT(x, y, G.SWAMP_BOGLAND if d <= r - 1.5 else G.SWAMP_SHALLOWS, True)
                if d <= r - 1.5:
                    H[I(x, y)] = min(H[I(x, y)], 1)
lower_pass()
# камыш на левом берегу Десны и Сейма
for cen, half, side in ((DESNA_C, 2.5, -1), (SEYM_C, 2.0, -1)):
    k = 0
    for j in range(0, len(cen), 9):
        k += 1
        if k % 2:
            continue
        px, py = cen[j]
        for t in range(4):
            x, y = int(px) + t * 0, int(py) - int(half) - 2 - (t % 2)
            for dx in range(-2, 3):
                xx, yy = int(px) + dx, y
                if inb(xx, yy) and not LOCK[I(xx, yy)] and (xx, yy) not in occ and 10 < xx:
                    setT(xx, yy, G.FOREST_REEDS, True)
for i in range(N):
    if T[i] == int(G.WATER_SHALLOW) and (i % S) % 7 == 3 and (i // S) % 3 == 0 and (i % S) > 12 and (i % S, i // S) not in occ:
        T[i] = int(G.FOREST_REEDS_SHALLOWS)


# ---------------------------------------------------------------- леса
KEEPOUT = [((62, 52), 24), ((72, 126), 28), ((96, 121), 16), ((52, 128), 10), ((140, 156), 20), ((160, 168), 28),
           ((170, 84), 30), ((42, 30), 8), ((12, 14), 10), ((24, 14), 8), ((192, 76), 12)]
for vn, (vx, vy), _c in VILLAGES:
    KEEPOUT.append(((vx, vy), 14))
road_near = bytearray(N)
for (x, y) in ROAD:
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if inb(x + dx, y + dy):
                road_near[I(x + dx, y + dy)] = 1
water_near = bytearray(N)
for i in range(N):
    if T[i] in WATER or T[i] in WALKWATER:
        x, y = i % S, i // S
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if inb(x + dx, y + dy):
                    water_near[I(x + dx, y + dy)] = 1


def forest_ok(x, y):
    if not inb(x, y, 1):
        return False
    i = I(x, y)
    if LOCK[i] or (x, y) in occ or (x, y) in UCELLS or road_near[i] or water_near[i] or i in RAV_CELLS:
        return False
    if T[i] in WATER or T[i] in WALKWATER or T[i] in FORESTS:
        return False
    for (c, r) in KEEPOUT:
        if (x - c[0]) ** 2 + (y - c[1]) ** 2 < r * r:
            return False
    return True


FOREST_CORE = {}


def forest_region(rect, ttype, cover, seed=0.0, ellipse=None):
    ph = [(rng.uniform(0.08, 0.2), rng.uniform(0.08, 0.2), rng.uniform(0, 6.3)) for _ in range(3)]
    n = 0
    for y in range(rect[1], rect[3] + 1):
        for x in range(rect[0], rect[2] + 1):
            if ellipse:
                ex, ey, rx, ry = ellipse
                if ((x - ex) / rx) ** 2 + ((y - ey) / ry) ** 2 > 1.0:
                    continue
            v = sum(math.sin(a * x + b * y + c) for a, b, c in ph) / 3.0 + 0.5
            if v < cover and forest_ok(x, y):
                T[I(x, y)] = int(ttype)
                FOREST_CORE[(x, y)] = int(ttype)
                n += 1
    return n


def ell(cx, cy, rx, ry, t, cover=1.2):
    return forest_region((int(cx - rx), int(cy - ry), int(cx + rx), int(cy + ry)), t, cover, ellipse=(cx, cy, rx, ry))


fc = Counter()
fc["dnepr"] = forest_region((12, 30, 20, 90), G.FOREST_PINE, 0.62)
for (cx, cy, rx, ry) in ((80, 60, 11, 8), (95, 78, 10, 7), (88, 44, 10, 8), (104, 95, 9, 7)):
    fc["zades"] += ell(cx, cy, rx, ry, G.FOREST_PINE, 0.75)
fc["rub1"] = forest_region((24, 2, 31, 37), G.FOREST_AUTUMN, 0.7)
fc["rub2"] = forest_region((38, 2, 45, 37), G.FOREST_AUTUMN, 0.7)
fc["chern"] = forest_region((55, 155, 100, 176), G.FOREST_OAK, 0.78)
fc["bold"] = ell(64, 104, 8, 7, G.FOREST_OAK_GREEN, 0.9)
fc["ambush"] = forest_region((114, 140, 128, 152), G.FOREST_AUTUMN, 1.0)
fc["north"] = forest_region((0, 180, 199, 199), G.FOREST_SPRUCE, 0.80)
fc["north2"] = forest_region((0, 183, 199, 199), G.FOREST_PINE, 0.35)
for (cx, cy) in ((146, 134), (152, 121), (166, 118), (140, 122), (172, 128), (132, 112)):
    fc["birch"] += ell(cx, cy, 4, 4, G.FOREST_BIRCH, 1.2)
for (cx, cy, t) in ((20, 100, G.FOREST_AUTUMN), (38, 84, G.FOREST_AUTUMN), (110, 60, G.FOREST_AUTUMN), (112, 100, G.FOREST_OAK),
                    (130, 70, G.FOREST_AUTUMN), (186, 130, G.FOREST_BIRCH), (190, 150, G.FOREST_PINE), (30, 150, G.FOREST_OAK),
                    (40, 175, G.FOREST_AUTUMN), (120, 175, G.FOREST_OAK), (185, 40, G.FOREST_BIRCH), (150, 30, G.FOREST_PINE),
                    (100, 15, G.FOREST_AUTUMN), (70, 20, G.FOREST_BIRCH), (30, 70, G.FOREST_PINE), (118, 40, G.FOREST_PINE)):
    fc["misc"] += ell(cx, cy, 7, 6, t, 0.9)
# кайма и подлесок
core_set = set(FOREST_CORE)
for (x, y), t in list(FOREST_CORE.items()):
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            c = (x + dx, y + dy)
            if c in core_set or not inb(*c, 1) or LOCK[I(*c)] or c in occ or T[I(*c)] not in (
                    int(G.GRASS_1), int(G.GRASS_2), int(G.GRASS_DRY), int(G.GRASS_OTHER)):
                continue
            d = max(abs(dx), abs(dy))
            if d == 1:
                T[I(*c)] = int(G.FOREST_OAK_BUSH if t in (int(G.FOREST_OAK), int(G.FOREST_OAK_GREEN)) else G.FOREST_BUSH)
            elif d in (2, 3) and T[I(*c)] != int(G.FOREST_BUSH) and T[I(*c)] != int(G.FOREST_OAK_BUSH):
                T[I(*c)] = int(G.UNDERBRUSH_LEAVES if d == 2 else G.UNDERBRUSH)

# ---------------------------------------------------------------- декор вне городов
CUR[0] = "Out"


def open_land(x, y):
    if not free_cell(x, y):
        return False
    i = I(x, y)
    return T[i] not in FORESTS and T[i] not in (int(G.FOREST_REEDS), int(G.FOREST_REEDS_SHALLOWS)) and not LOCK[i] or (
        T[i] in (int(G.DIRT_2), int(G.DIRT_4), int(G.DIRT_MUD)) and False)


def rand_cells(n, pred, tries=200000):
    out = []
    t = 0
    while len(out) < n and t < tries:
        t += 1
        x, y = rng.randrange(14, S - 2), rng.randrange(2, S - 2)
        if pred(x, y):
            out.append((x, y))
    return out


STEPPE = ["BUSH_A", "BUSH_B", "BUSH_C", "PLANT_WEEDS", "GRASS_PATCH_DRY", "GRASS_PATCH_GREEN", "ROCK_1", "ROCK_2", "ROCK_MOSSY",
          "PLANT_HEATHER", "STUMP"]
for (x, y) in rand_cells(360, lambda x, y: open_land(x, y) and (x, y) not in occ):
    put(0, K(rng.choice(STEPPE)), x, y, 1, tag="u")


def near_forest(x, y, r=2):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if inb(x + dx, y + dy) and T[I(x + dx, y + dy)] in FORESTS:
                return True
    return False


EDGE = ["TREE_OAK_AUTUMN", "TREE_BIRCH", "TREE_OAK", "FELLED_TREE", "STUMP", "FERN_PATCH", "TREE_OAK_AUTUMN", "TREE_BIRCH"]
for (x, y) in rand_cells(210, lambda x, y: free_cell(x, y) and not LOCK[I(x, y)] and T[I(x, y)] not in FORESTS and near_forest(x, y, 2)):
    put(0, K(rng.choice(EDGE)), x, y, 1, tag="u")
SHORE = ["TREE_WILLOW", "TREE_REEDS", "DRIFTWOOD_GROUND", "ROCK_BEACH", "TREE_WILLOW"]
shore_cells = [(i % S, i // S) for i in range(N) if T[i] in (int(G.BEACH_WET), int(G.BEACH_WET_GRAVEL), int(G.BEACH_VEGETATION),
                                                              int(G.DIRT_MUD)) and (i % S) > 11]
rng.shuffle(shore_cells)
k = 0
for (x, y) in shore_cells:
    if k >= 85:
        break
    if (x, y) not in occ and (x, y) not in ROAD and T[I(x, y)] != int(G.DIRT_MUD):
        put(0, K(rng.choice(SHORE)), x, y, 1, tag="u")
        k += 1
water_med = [(i % S, i // S) for i in range(N) if T[i] == int(G.WATER_MEDIUM) and (i % S) > 12]
for (x, y) in rng.sample(water_med, 12):
    um.add_unit(0, K("FLOTSAM"), x=x + 0.5, y=y + 0.5)
    CNT["Out"]["obj"] += 1
for (x, y) in rng.sample(water_med, 12):
    um.add_unit(0, K("FISH_PERCH"), x=x + 0.5, y=y + 0.5)
for (x, y) in rng.sample(water_med, 8):
    um.add_unit(0, K("SHORE_FISH"), x=x + 0.5, y=y + 0.5)
rav_list = list(RAV_CELLS)
for i in rng.sample(rav_list, min(55, len(rav_list))):
    x, y = i % S, i // S
    if free_cell(x, y):
        put(0, K(rng.choice(["BUSH_A", "BUSH_B", "BUSH_C", "PLANT_UNDERBRUSH", "ROCK_MOSSY"])), x, y, 1, tag="u")
# следы голода и войны
for nm, n in (("BROKEN_CART", 3), ("DISMANTLED_CART", 2), ("SKELETON", 2)):
    for (x, y) in rand_cells(n, lambda x, y: open_land(x, y) and not road_near[I(x, y)]):
        put(0, K(nm), x, y, 1, tag="u")
if free_cell(100, 60):
    put(0, K("BURNED_BUILDING_A"), 100, 60, 3)
for (x, y) in ((104, 62), (96, 58)):
    if fits(x, y, 2):
        put(0, K("RUBBLE_2_X_2"), x, y, 2)
for (x, y) in ((98, 64), (102, 56), (106, 60)):
    decor_at(K("BROKEN_FENCE_A"), x, y)
# дичь
for g in range(8):
    cs = rand_cells(1, lambda x, y: open_land(x, y) and 20 < x < 195)
    if cs:
        for _ in range(rng.randint(4, 6)):
            u = scatter(0, K("DEER"), 1, (cs[0][0] - 4, cs[0][1] - 4, cs[0][0] + 4, cs[0][1] + 4), cnt_key="game")
for (x, y, nm, n) in ((20, 60, "WILD_BOAR", 2), (110, 70, "WILD_BOAR", 2), (38, 150, "WILD_BOAR", 2), (60, 190, "GREY_WOLF", 2), (140, 192, "GREY_WOLF", 2)):
    try:
        scatter(0, K(nm), n, (x - 6, y - 6, x + 6, y + 6), cnt_key="game")
    except RuntimeError:
        pass
# межевые знаки
for y in range(4, 40, 6):
    x = 34
    if (x, y) in ROAD:
        x = 37
    decor_at(K("STELAE_A"), x, y) or decor_at(K("ROCK_FORMATION_1"), x, y)
# обочины магистралей
for pts in MAIN_ROADS:
    cells = lerp_poly(pts, 8.0)
    for (px, py) in cells:
        for dx, dy in ((0, 3), (0, -2), (3, 0), (-2, 0)):
            x, y = int(px) + dx, int(py) + dy
            if free_cell(x, y) and not LOCK[I(x, y)] and (x, y) not in UCELLS:
                put(0, K(rng.choice(["BUSH_A", "BUSH_B", "BUSH_C", "TREE_OAK_AUTUMN", "TREE_BIRCH", "STUMP", "ROCK_1", "PLANT_WEEDS", "GRASS_PATCH_DRY"])),
                    x, y, 1, tag="u")
                break
for (x, y) in ((34, 15), (42, 27), (53, 50), (72, 88), (86, 133), (104, 141), (144, 143), (150, 124), (156, 108)):
    decor_at(K("SIGN"), x, y)
OUT_DECOR = CNT["Out"]["obj"]

# ---------------------------------------------------------------- запись местности и высот в карту
for i in range(N):
    tl = mm.terrain[i]
    tl.terrain_id = T[i]
    tl.elevation = H[i]
HEIGHT_BAD = height_violations()
FOOT_BAD = footprint_unflat()
land = [i for i in range(N) if T[i] not in WATER and T[i] not in WALKWATER]
HIGH_SHARE = sum(1 for i in land if H[i] > 1) / float(len(land))
print("высоты: нарушений соседства", HEIGHT_BAD, "неровных следов", FOOT_BAD, "доля суши выше 1: %.2f" % HIGH_SHARE,
      "уровни", sorted(set(H)), "типов местности", len(set(T)), "декор вне городов", OUT_DECOR)

# Часть 1b2 (v3): деревни глуши (живые, брошенные, сожжённые), объекты Смуты, ресурсы для экономики.
# Выполняется после v3_part1b_cities.py, до v3_part1c_finish.py. Общее пространство имён.
CUR[0] = "Wild"
NAT = Counter()          # природа по категориям (декоративные объекты вне городов)
SITES = []               # деревни глуши: dict(kind, c, rect, church)
SITE_BY = defaultdict(list)
RES_SPOTS = []           # (название, (x, y)) месторождения, ягоды, дичь: для проверки достижимости

CITY_CENTERS = [((62, 52), 26), ((72, 126), 30), ((96, 121), 20), ((52, 128), 14), ((140, 156), 24), ((160, 168), 30),
                ((176, 72), 28), ((170, 91), 32), ((192, 76), 14), ((42, 30), 12), ((24, 14), 18), ((48, 20), 16),
                ((62, 104), 16), ((110, 144), 18), ((154, 114), 18)]
ROAD_LIST = list(ROAD)


def road_dist(x, y, cap=40):
    best = cap
    for (rx, ry) in ROAD_LIST[::3]:
        d = max(abs(rx - x), abs(ry - y))
        if d < best:
            best = d
    return best


def site_ok(cx, cy, rx=8, ry=6):
    for dx in range(-rx, rx + 1):
        for dy in range(-ry, ry + 1):
            x, y = cx + dx, cy + dy
            if not inb(x, y, 3):
                return False
            i = I(x, y)
            if T[i] in WATER or T[i] in WALKWATER or LOCK[i] or i in RAV_CELLS or (x, y) in occ or (x, y) in ROAD:
                return False
            if H[i] > 4:
                return False
    return True


def nat(name, x, y, cat, player=0):
    """Один декоративный объект природы; не ставится на воду, дороги и занятые клетки."""
    if not inb(x, y, 1) or (x, y) in occ or (x, y) in ROAD:
        return False
    i = I(x, y)
    if T[i] in WATER or T[i] in WALKWATER:
        return False
    put(player, K(name), x, y, 1, tag="u")
    NAT[cat] += 1
    return True


def nat_unit(player, name, x, y, cat):
    if not inb(x, y, 1) or (x, y) in occ or (x, y) in UCELLS:
        return None
    i = I(x, y)
    if T[i] in WATER or T[i] in WALKWATER:
        return None
    u = unit_at(player, K(name), x, y)
    NAT[cat] += 1
    return u


def sprinkle(rect, names, n, cat, player=0, tries_mul=6):
    k, t = 0, 0
    while k < n and t < n * tries_mul:
        t += 1
        x, y = rng.randint(rect[0], rect[2]), rng.randint(rect[1], rect[3])
        if nat(rng.choice(names), x, y, cat, player):
            k += 1
    return k


# ---------------------------------------------------------------- выбор мест
KINDS = ["live", "burned", "abandoned", "live", "hutor", "burned", "abandoned", "live", "abandoned", "hutor", "burned", "live", "church"]
tries = 0
while len(SITES) < len(KINDS) and tries < 60000:
    tries += 1
    kind = KINDS[len(SITES)]
    cx, cy = rng.randint(20, 184), rng.randint(12, 170)
    if any((cx - c[0]) ** 2 + (cy - c[1]) ** 2 < (r + 10) ** 2 for c, r in CITY_CENTERS):
        continue
    if any((cx - s["c"][0]) ** 2 + (cy - s["c"][1]) ** 2 < 28 ** 2 for s in SITES):
        continue
    near_route = len(SITES) < 8                       # первые - вдоль маршрута (9-26 клеток от дорог)
    rd = road_dist(cx, cy)
    if near_route and not (10 <= rd <= 26):
        continue
    if not near_route and rd < 9:
        continue
    if not site_ok(cx, cy, 8 if kind != "church" else 5, 6 if kind != "church" else 4):
        continue
    SITES.append({"kind": kind, "c": (cx, cy), "rect": (cx - 8, cy - 6, cx + 8, cy + 6)})
    SITE_BY[kind].append(SITES[-1])
print("деревни глуши:", [(s["kind"], s["c"]) for s in SITES])


def weeds(rect, n, cat, extra=()):
    sprinkle(rect, ["PLANT_WEEDS", "GRASS_PATCH_DRY", "BUSH_A", "BUSH_B", "PLANT_DEAD", "FERN_PATCH", "STUMP", "TREE_DEAD"] + list(extra), n, cat)


def live_village(s, idx):
    cx, cy = s["c"]
    rect = s["rect"]
    CUR[0] = f"W{idx}"
    street([(x, cy) for x in range(cx - 9, cx + 10)], G.DIRT_1)
    street([(cx + 3, y) for y in range(cy - 5, cy + 6)], G.DIRT_1)
    paint_rect(rect, G.DIRT_2, False)
    ch = place(0, K("CHAPEL"), cx - 1, cy + 1, 3, f"WChurch{idx}", rect=rect)
    s["church"] = (int(ch.x), int(ch.y)) if ch is not None else (cx, cy)
    pack_yards(rect, {"poor": 4, "house": 4}, P7, passes=3)
    quota(P7, K("HOUSE"), 5, [rect], label=f"W{idx} P7 HOUSE")
    pockets(rect, 0.3)
    farm_field((cx - 12, cy + 7, cx + 12, cy + 14), P7, 2)
    farm_field((cx - 12, cy - 15, cx + 10, cy - 8), 0, 0)
    for nm, n in (("WELL", 1), ("HAY_STACK", 6), ("GRANARY", 1), ("WATER_TROUGH", 1), ("TREE_BIRCH", 5), ("SMOKE", 3), ("TREE_OAK", 3),
                  ("FRUIT_BUSH", 4)):
        scatter_decor(rect, [nm], n)
    graves(5, (cx + 5, cy - 6, cx + 8, cy - 2))
    scatter(P7, VILL_M, 3, rect)
    scatter(P7, VILL_F, 3, rect)
    livestock([("COW_A", 2), ("COW_B", 1), ("SHEEP", 4), ("GOOSE", 3), ("HORSE_A", 2), ("PIG", 2)], rect)
    NAT["деревни_живые_скот"] += 12


def abandoned_village(s, idx):
    cx, cy = s["c"]
    rect = s["rect"]
    CUR[0] = f"W{idx}"
    street([(x, cy) for x in range(cx - 9, cx + 10)], G.DIRT_4)
    place(0, K("CHURCH_RUINS"), cx - 1, cy + 1, 3, rect=rect)
    pack_yards(rect, {"poor": 6, "house": 2}, 0, passes=2)
    for y in range(cy + 7, cy + 14, 3):
        farm_field((cx - 12, y, cx + 12, y + 3), 0, 0)
    weeds(rect, 60, "деревни_заброшенные")
    for nm, n in (("ANIMAL_SKELETON", 3), ("SKELETON", 2), ("GRAVE", 8), ("BROKEN_CART", 2), ("DISMANTLED_CART", 1), ("BROKEN_FENCE_A", 8),
                  ("BROKEN_FENCE_B", 6), ("RUBBLE_1_X_1", 5), ("BURNED_BUILDING_B", 0)):
        scatter_decor(rect, [nm], n)
    s["church"] = (cx, cy)
    wolves = []
    for _ in range(3):
        u = nat_unit(0, "GREY_WOLF", cx + rng.randint(-5, 5), cy + rng.randint(-4, 4), "волки")
        if u:
            wolves.append(u)
    s["wolves"] = wolves


def burned_village(s, idx):
    cx, cy = s["c"]
    rect = s["rect"]
    CUR[0] = f"W{idx}"
    street([(x, cy) for x in range(cx - 9, cx + 10)], G.DIRT_4)
    paint_rect((cx - 6, cy - 4, cx + 6, cy + 4), G.DIRT_4, False)
    place(0, K("CHURCH_RUINS"), cx + 2, cy + 1, 3, rect=rect)
    for k in range(7):
        place(0, K(rng.choice(["BURNED_BUILDING_A", "BURNED_BUILDING_B", "BURNED_BUILDING_C", "BURNED_BUILDING_D", "BURNED_BUILDING_E"])),
              cx + rng.randint(-7, 5), cy + rng.randint(-5, 3), 3, rect=rect, maxr=8)
    for nm, n in (("RUBBLE_2_X_2", 5), ("RUBBLE_3_X_3", 2), ("RUBBLE_1_X_1", 12), ("BROKEN_FENCE_A", 10), ("BROKEN_FENCE_B", 8), ("FLAME1", 2),
                  ("FLAME2", 1), ("SMOKE", 6), ("TREE_DEAD", 8), ("GRAVE", 8), ("STELAE_A", 3), ("BROKEN_CART", 2), ("SKELETON", 3),
                  ("ANIMAL_SKELETON", 2), ("WELL", 1), ("BARRELS", 3), ("HAY_STACK", 2), ("STUMP", 5), ("FURNACE", 2)):
        scatter_decor(rect, [nm], n)
    s["church"] = (cx, cy)
    weeds(rect, 25, "деревни_сожжённые")
    NAT["деревни_сожжённые"] += 0


def hutor(s, idx):
    cx, cy = s["c"]
    rect = (cx - 6, cy - 5, cx + 6, cy + 5)
    CUR[0] = f"W{idx}"
    street([(x, cy) for x in range(cx - 8, cx + 8)], G.DIRT_1)
    place(0, rng.choice(HUTS), cx - 2, cy + 1, 2, rect=rect)
    place(0, K("HOUSE"), cx + 2, cy - 3, 2, rect=rect)
    place(0, K("GRANARY"), cx + 4, cy + 1, 2, rect=rect)
    farm_field((cx - 8, cy + 6, cx + 8, cy + 11), 0, 0)
    for nm, n in (("BROKEN_FENCE_A", 6), ("BROKEN_FENCE_B", 5), ("HAY_STACK", 3), ("FELLED_TREE", 3), ("WELL", 1), ("PLANT_WEEDS", 10),
                  ("STUMP", 3), ("SKELETON", 1), ("ANIMAL_SKELETON", 1), ("BROKEN_CART", 1)):
        scatter_decor(rect, [nm], n)
    s["church"] = (cx, cy)


def lone_church(s, idx):
    cx, cy = s["c"]
    rect = (cx - 5, cy - 4, cx + 5, cy + 4)
    CUR[0] = f"W{idx}"
    ch = place(0, K("MONASTERY"), cx - 1, cy - 1, 3, f"WChurch{idx}", rect=rect)
    s["church"] = (int(ch.x), int(ch.y)) if ch is not None else (cx, cy)
    for k in range(10):
        decor_at(K("FENCE"), cx - 4 + k, cy - 4)
    graves(12, (cx - 4, cy + 1, cx + 4, cy + 4))
    for nm, n in (("TREE_BIRCH", 5), ("TREE_OAK_AUTUMN", 3), ("BUSH_A", 4), ("STELAE_B", 2), ("BONFIRE", 1)):
        scatter_decor(rect, [nm], n)
    street([(x, cy + 5) for x in range(cx - 6, cx + 7)], G.DIRT_1)


for idx, s in enumerate(SITES, 1):
    s["idx"] = idx
    {"live": live_village, "abandoned": abandoned_village, "burned": burned_village, "hutor": hutor, "church": lone_church}[s["kind"]](s, idx)
print("деревни глуши расставлены:", Counter(s["kind"] for s in SITES))

# ---------------------------------------------------------------- лагерь лихих людей (у оврага R7, дальше от дорог)
CUR[0] = "Bandits"
BAND_C = None
for (bx, by) in [(112, 108), (114, 100), (110, 112), (116, 104), (108, 96), (112, 92)]:
    if site_ok(bx, by, 5, 5):
        BAND_C = (bx, by)
        break
if BAND_C is None:
    for _ in range(4000):
        bx, by = rng.randint(100, 134), rng.randint(84, 116)
        if site_ok(bx, by, 5, 5):
            BAND_C = (bx, by)
            break
assert BAND_C, "нет места для лагеря лихих людей"
bx, by = BAND_C
paint_rect((bx - 5, by - 5, bx + 5, by + 5), G.DIRT_2, False)
for (dx, dy, nm) in ((-3, -3, "TENT_A"), (2, -3, "TENT_B"), (-3, 2, "TENT_C"), (3, 2, "TENT_D"), (0, 4, "TENT_E")):
    place(0, K(nm), bx + dx, by + dy, 2, rect=(bx - 6, by - 6, bx + 6, by + 6))
for nm, n in (("BONFIRE", 2), ("BARRELS", 4), ("WEAPON_RACK", 2), ("HAY_STACK", 3), ("LOOT", 2), ("TREASURE_CHEST", 2), ("BROKEN_CART", 2),
              ("STAKE_BARRICADE", 6), ("SKELETON", 2), ("FLAG_E", 1)):
    scatter_decor((bx - 5, by - 5, bx + 5, by + 5), [nm], n)
BAND_UNITS = []
BAND_UNITS += scatter(0, K("SPEARMAN"), 4, (bx - 4, by - 4, bx + 4, by + 4), cnt_key="band")
BAND_UNITS += scatter(0, K("ARCHER"), 4, (bx - 4, by - 4, bx + 4, by + 4), cnt_key="band")
BAND_UNITS += scatter(0, K("MAN_AT_ARMS"), 2, (bx - 4, by - 4, bx + 4, by + 4), cnt_key="band")
BAND_UNITS += scatter(0, K("SCOUT_CAVALRY"), 2, (bx - 4, by - 4, bx + 4, by + 4), cnt_key="band")
BAND_ZONE = (bx - 12, by - 12, bx + 12, by + 12)
RES_SPOTS.append(("лагерь лихих людей", BAND_C))

# ---------------------------------------------------------------- приметы Смуты вдоль дорог
CUR[0] = "Smuta"
SMUTA_OBJ = Counter()


def side_points(pts, step):
    """Точки вдоль ломаной с единичной нормалью: (px, py, nx, ny)."""
    out = []
    cells = lerp_poly(pts, float(step))
    for k in range(len(cells) - 1):
        (ax, ay), (bx, by) = cells[k], cells[k + 1]
        d = math.hypot(bx - ax, by - ay) or 1.0
        out.append((ax, ay, -(by - ay) / d, (bx - ax) / d))
    return out


def roadside(pts_list, step, items, off=(4, 6)):
    k = 0
    for pts in pts_list:
        for (px, py, nx, ny) in side_points(pts, step):
            nm, cat = items[k % len(items)]
            k += 1
            side = 1 if k % 2 == 0 else -1
            for o in range(off[0], off[1] + 1):
                x, y = int(round(px + side * o * nx)), int(round(py + side * o * ny))
                if nat(nm, x, y, cat) if inb(x, y, 2) and not (abs(x - 24) < 10 and abs(y - 14) < 10) else False:
                    SMUTA_OBJ[nm] += 1
                    break


roadside(MAIN_ROADS, 7, [("STELAE_A", "кресты"), ("BROKEN_CART", "телеги"), ("ANIMAL_SKELETON", "падшие_кони"), ("GRAVE", "могилы"),
                          ("DISMANTLED_CART", "телеги"), ("SKELETON", "брошенное"), ("STELAE_B", "кресты"), ("ANIMAL_SKELETON", "падшие_кони"),
                          ("SIGN", "брошенное")])
# придорожные часовни
for pts in MAIN_ROADS:
    cells = lerp_poly(pts, 38.0)
    for (px, py) in cells[1:-1]:
        for dx, dy in ((7, 0), (-7, 0), (0, 7), (0, -7)):
            x, y = int(px) + dx, int(py) + dy
            if fits(x, y, 3):
                put(0, K("CHAPEL"), x, y, 3, tag="b")
                SMUTA_OBJ["придорожная_часовня"] += 1
                for ddx in range(-1, 5):
                    nat("GRAVE" if ddx % 2 else "STELAE_A", x + ddx, y + 4, "кресты")
                break

# ---------------------------------------------------------------- ресурсы: ягоды, дичь, рыба, золото, камень
CUR[0] = "Res"
RES = Counter()


def cluster_cells(cx, cy, n, spread=2):
    out, t = [], 0
    while len(out) < n and t < 400:
        t += 1
        x, y = cx + rng.randint(-spread, spread), cy + rng.randint(-spread, spread)
        if (x, y) in out or not inb(x, y, 2):
            continue
        i = I(x, y)
        if (x, y) in occ or (x, y) in ROAD or T[i] in WATER or T[i] in WALKWATER or LOCK[i] or i in RAV_CELLS:
            continue
        out.append((x, y))
    return out


def find_spot(cx, cy, rmin, rmax, check=None, tries=600, spread=2):
    for _ in range(tries):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(rmin, rmax)
        x, y = int(cx + r * math.cos(a)), int(cy + r * math.sin(a))
        if not inb(x, y, 6):
            continue
        if len(cluster_cells(x, y, 6, spread)) < 5:
            continue
        if road_dist(x, y) < 5:
            continue
        if any((x - c[0]) ** 2 + (y - c[1]) ** 2 < (r_ * 0.7) ** 2 for c, r_ in CITY_CENTERS if c != (140, 156) and c != (24, 14)):
            continue
        if check and not check(x, y):
            continue
        return (x, y)
    return None


def mines(name, cx, cy, n, label):
    cells = cluster_cells(cx, cy, n, 2)
    for (x, y) in cells:
        put(0, K(name), x, y, 1, tag="u")
        RES[name] += 1
    if cells:
        RES_SPOTS.append((label, cells[0]))
    return len(cells)


def berries(cx, cy, n=7, label="ягоды"):
    cells = cluster_cells(cx, cy, n, 2)
    for (x, y) in cells:
        put(0, K("FORAGE_BUSH"), x, y, 1, tag="u")
        RES["FORAGE_BUSH"] += 1
    if cells:
        RES_SPOTS.append((label, cells[0]))


def herd(name, cx, cy, n, spread=4, label="дичь"):
    k = 0
    for _ in range(n * 40):
        if k >= n:
            break
        x, y = cx + rng.randint(-spread, spread), cy + rng.randint(-spread, spread)
        if inb(x, y, 2) and T[I(x, y)] not in WATER and T[I(x, y)] not in WALKWATER and T[I(x, y)] not in FORESTS and (x, y) not in UCELLS and (x, y) not in occ:
            unit_at(0, K(name), x, y)
            RES[name] += 1
            NAT["животные_дичь"] += 1
            k += 1
    if k:
        RES_SPOTS.append((label, (cx, cy)))


# у каждого города: золото, камень, ягоды (вне стен, вне подходов к воротам)
CITY_RES = {"Моравск": (62, 52), "Чернигов": (72, 126), "Замок": (96, 121), "Н-Северский": (160, 168), "Путивль": (170, 90)}
for nm, (cx, cy) in CITY_RES.items():
    for what, k in (("GOLD_MINE", 5), ("STONE_MINE", 4)):
        sp = find_spot(cx, cy, 24, 40)
        if sp:
            mines(what, sp[0], sp[1], k, f"{what} у {nm}")
    for _ in range(2):
        sp = find_spot(cx, cy, 16, 36)
        if sp:
            berries(sp[0], sp[1], 7, f"ягоды у {nm}")
# вокруг табора (140,156): богатые месторождения, ягоды, дичь
for what, k, rmin, rmax in (("GOLD_MINE", 6, 12, 22), ("GOLD_MINE", 5, 14, 26), ("STONE_MINE", 5, 12, 22), ("STONE_MINE", 4, 16, 28)):
    sp = find_spot(140, 156, rmin, rmax)
    if sp:
        mines(what, sp[0], sp[1], k, f"{what} у табора")
for _ in range(5):
    sp = find_spot(140, 156, 9, 24)
    if sp:
        berries(sp[0], sp[1], 8, "ягоды у табора")
for _ in range(4):
    sp = find_spot(140, 156, 14, 34)
    if sp:
        herd("DEER", sp[0], sp[1], rng.randint(5, 7), 4, "олени у табора")
for _ in range(3):
    sp = find_spot(140, 156, 16, 36)
    if sp:
        herd("WILD_BOAR", sp[0], sp[1], 3, 3, "кабаны у табора")
# на старте и по маршруту
for (cx, cy, rmin, rmax) in ((24, 14, 9, 22), (24, 14, 12, 26), (48, 30, 8, 22), (62, 80, 8, 24), (90, 100, 8, 26), (110, 138, 8, 26),
                             (130, 120, 8, 26), (100, 60, 10, 28), (36, 60, 8, 26), (150, 130, 10, 26), (120, 170, 10, 28)):
    sp = find_spot(cx, cy, rmin, rmax)
    if sp:
        berries(sp[0], sp[1], 7, "ягоды на маршруте")
for (cx, cy) in ((24, 14), (30, 40), (50, 60), (100, 80), (90, 140), (118, 120), (130, 150), (60, 150), (30, 120), (150, 60), (100, 20),
                 (180, 140), (110, 60), (140, 40), (70, 180), (40, 90)):
    sp = find_spot(cx, cy, 6, 24)
    if sp:
        herd(rng.choice(["DEER", "DEER", "WILD_BOAR", "ELK"]), sp[0], sp[1], rng.randint(3, 6), 4, "дичь на маршруте")
for (cx, cy, nm, k) in ((24, 14, "GOLD_MINE", 5), (24, 14, "STONE_MINE", 4), (40, 70, "GOLD_MINE", 5), (100, 90, "STONE_MINE", 4),
                        (120, 150, "GOLD_MINE", 5), (120, 100, "STONE_MINE", 4), (80, 40, "GOLD_MINE", 4), (140, 120, "GOLD_MINE", 5),
                        (60, 160, "STONE_MINE", 4), (100, 170, "GOLD_MINE", 5), (180, 120, "STONE_MINE", 4), (130, 60, "GOLD_MINE", 4)):
    sp = find_spot(cx, cy, 8, 28)
    if sp:
        mines(nm, sp[0], sp[1], k, f"{nm} по маршруту")

# рыба у берегов (ловушки: P1 строит сам; рыба Gaia в воде)
fish_water = [(i % S, i // S) for i in range(N) if T[i] == int(G.WATER_MEDIUM) and (i % S) > 12 and (i // S) < 190]
rng.shuffle(fish_water)
fish_n = 0
for (x, y) in fish_water:
    if fish_n >= 90:
        break
    if (x, y) in UCELLS:
        continue
    um.add_unit(0, K(rng.choice(["FISH_PERCH", "FISH_PERCH", "SHORE_FISH", "FISH_SALMON"])), x=x + 0.5, y=y + 0.5)
    RES["рыба"] += 1
    fish_n += 1
# рыба у моря-реки около старта и табора обязательно
for (cx, cy, rr) in ((24, 14, 26), (140, 156, 34)):
    near = [(x, y) for (x, y) in fish_water if abs(x - cx) < rr and abs(y - cy) < rr]
    for (x, y) in near[:14]:
        um.add_unit(0, K(rng.choice(["FISH_PERCH", "SHORE_FISH"])), x=x + 0.5, y=y + 0.5)
        RES["рыба"] += 1
        RES_SPOTS.append(("рыба", (x, y)))
# участки для ферм: распаханная земля рядом со станом и стартом
for rc in ((124, 162, 136, 170), (150, 142, 160, 148), (28, 20, 40, 28)):
    for y in range(rc[1], rc[3] + 1):
        for x in range(rc[0], rc[2] + 1):
            if inb(x, y) and T[I(x, y)] in (int(G.GRASS_1), int(G.GRASS_2), int(G.GRASS_DRY), int(G.GRASS_OTHER)) and not LOCK[I(x, y)] \
                    and (x, y) not in occ and (x, y) not in ROAD and I(x, y) not in RAV_CELLS:
                setT(x, y, G.FARM_33 if (x + y) % 3 else G.FARM_DEAD, False)
                FIELD_CELLS.add((x, y))
print("ресурсы:", dict(RES), "приметы Смуты:", dict(SMUTA_OBJ))

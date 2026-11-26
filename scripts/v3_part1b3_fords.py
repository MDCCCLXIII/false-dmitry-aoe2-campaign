# Часть 1b3 (v3): броды и переправы. Проходимы только суша и SHALLOWS (id 4); вода 1, 22, 23, 130 и болотная вода непроходимы.
CUR[0] = "Fords"
ROAD_POLYS = list(MAIN_ROADS) + [[(170, 102), (180, 112), (180, 140), (176, 161), (174, 174)], [(170, 199), (164, 190), (161, 185)],
                                 [(59, 126), (52, 128)]]
BAD_WATER = set(WATER) | {int(G.SWAMP_SHALLOWS), int(G.FOREST_REEDS_SHALLOWS)}
CROSSINGS = []


def ford_disk(cx, cy, r=3.0):
    for y in range(cy - 4, cy + 5):
        for x in range(cx - 4, cx + 5):
            if inb(x, y, 1) and math.hypot(x - cx, y - cy) <= r and T[I(x, y)] in BAD_WATER:
                setT(x, y, G.SHALLOWS, True)
                H[I(x, y)] = 0
                FIXED[I(x, y)] = 1


for pts in ROAD_POLYS:
    for (px, py) in lerp_poly(pts, 0.4):
        x, y = int(round(px)), int(round(py))
        if inb(x, y, 1) and T[I(x, y)] in BAD_WATER:
            ford_disk(x, y)
            ROAD.add((x, y))
            if not CROSSINGS or math.hypot(CROSSINGS[-1][0] - x, CROSSINGS[-1][1] - y) > 3:
                CROSSINGS.append((x, y))
# брод через пограничный ручей у дороги (34, 16): расширяем до 5 клеток
for (cx_, cy_) in ((34, 14), (34, 16), (34, 18)):
    for dx_ in range(-2, 3):
        if T[I(cx_ + dx_, cy_)] in BAD_WATER or T[I(cx_ + dx_, cy_)] == int(G.SHALLOWS):
            setT(cx_ + dx_, cy_, G.SHALLOWS, True)
            H[I(cx_ + dx_, cy_)] = 0
            FIXED[I(cx_ + dx_, cy_)] = 1
FORD_CENTERS = [c for _n, c, _w in FORDS] + [(34, 16)]
for c in CROSSINGS:
    if all(math.hypot(c[0] - f[0], c[1] - f[1]) > 12 for f in FORD_CENTERS):
        FORD_CENTERS.append(c)
FORD_CELLS = set()
for (fx_, fy_) in FORD_CENTERS:
    for y in range(fy_ - 12, fy_ + 13):
        for x in range(fx_ - 12, fx_ + 13):
            if inb(x, y) and T[I(x, y)] == int(G.SHALLOWS):
                FORD_CELLS.add((x, y))
FORD_NEAR = set()
for (x, y) in FORD_CELLS:
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            FORD_NEAR.add((x + dx, y + dy))
# оформление: водяные травы вне полосы брода, камни, колея, брошенная телега, крест
FORD_DECOR = Counter()
for (fx_, fy_) in FORD_CENTERS:
    for y in range(fy_ - 11, fy_ + 12):
        for x in range(fx_ - 11, fx_ + 12):
            if not inb(x, y, 1):
                continue
            d = math.hypot(x - fx_, y - fy_)
            if 6.5 <= d <= 10 and T[I(x, y)] == int(G.WATER_MEDIUM) and (x, y) not in FORD_NEAR and (x + y) % 2 == 0 and not LOCK[I(x, y)]:
                setT(x, y, G.WATER_WEEDS, True)
                FORD_DECOR["водные_травы"] += 1
    spots_ = [(fx_ + dx, fy_ + dy) for dx in range(-10, 11) for dy in range(-10, 11)
              if 5 <= math.hypot(dx, dy) <= 10 and (fx_ + dx, fy_ + dy) not in FORD_NEAR]
    rng.shuffle(spots_)
    todo = ["ROCK_BEACH", "ROCK_BEACH", "ROCK_1", "ROCK_2", "BROKEN_CART", "ANIMAL_SKELETON", "STELAE_A", "TREE_REEDS", "TREE_REEDS", "TREE_REEDS",
            "TREE_WILLOW", "DRIFTWOOD_GROUND", "ROCK_MOSSY", "FLOWERS_3"]
    for (x, y) in spots_:
        if not todo:
            break
        if (x, y) in ROAD or road_dist(x, y) < 3:
            continue
        if nat(todo[0], x, y, "броды_оформление"):
            FORD_DECOR[todo[0]] += 1
            todo.pop(0)
# колея: галька-дорога на подходах (по берегам вокруг центров бродов)
for (fx_, fy_) in FORD_CENTERS:
    for (x, y) in list(ROAD):
        if abs(x - fx_) <= 9 and abs(y - fy_) <= 9 and T[I(x, y)] not in BAD_WATER and T[I(x, y)] != int(G.SHALLOWS) and (x, y) not in occ:
            setT(x, y, G.ROAD_GRAVEL, True)
print("броды и переправы:", FORD_CENTERS, "клеток SHALLOWS у бродов:", len(FORD_CELLS), dict(FORD_DECOR))

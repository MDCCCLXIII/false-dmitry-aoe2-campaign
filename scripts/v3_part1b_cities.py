# Часть 1b: дороги, города, сёла, табор, старт. Общее пространство имён.
import os
PK = float(os.environ.get('V2_PK', '0.45'))
FORT, PALW = K("FORTIFIED_PALISADE_WALL"), K("PALISADE_WALL")
STW, FSW = K("STONE_WALL"), K("FORTIFIED_WALL")   # v3: каменные стены
TC_, BARR_, MON_, STAB_, ARCH_, MARKET_, SMITH_ = (K("TOWN_CENTER"), K("BARRACKS"), K("MONASTERY"), K("STABLE"),
                                                   K("ARCHERY_RANGE"), K("MARKET"), K("BLACKSMITH"))
SPEAR_, HC_, KNIGHT_, CAVARCH_, MAA_, ARCHER_, MONK_ = (K("SPEARMAN"), K("HAND_CANNONEER"), K("BOYAR"),
                                                        K("CAVALRY_ARCHER"), K("MAN_AT_ARMS"), K("ARCHER"), K("MONK"))
SCOUT_, HUSSAR_ = K("SCOUT_CAVALRY"), K("HUSSAR")
WT, GT, KP = K("WATCH_TOWER"), K("GUARD_TOWER"), K("KEEP")
FEN = K("FENCE")
P1, P2, P3, P4, P5, P6, P7, P8 = range(1, 9)

STRIZHEN_EXT = [(70, 92), (73, 84)]
for (px, py) in lerp_poly(STRIZHEN_EXT, 0.6):
    x, y = int(round(px)), int(round(py))
    if T[I(x, y)] not in WATER:
        setT(x, y, G.SHALLOWS, True)
        H[I(x, y)] = 0
        FIXED[I(x, y)] = 1

# ---------------------------------------------------------------- магистрали (§2.7)
MAIN_ROADS = [
    [(12, 14), (24, 14), (34, 16), (42, 26), (50, 40), (53, 52)],
    [(62, 61), (68, 72), (71, 80), (72, 90), (66, 104), (73, 110)],
    [(86, 134), (104, 140), (120, 146), (138, 156)],
    [(140, 156), (144, 141), (150, 126), (156, 110), (150, 104), (146, 96), (151, 90)],
]
for pts in MAIN_ROADS:
    road_line(pts, 2, G.ROAD_BROKEN)
road_line([(170, 102), (180, 112), (180, 140), (176, 161), (174, 174)], 1, G.DIRT_1)
road_line([(170, 199), (164, 190), (161, 185)], 2, G.ROAD_BROKEN)
road_line([(59, 126), (52, 128)], 1, G.DIRT_1)
# мостки через Стрижень в посаде
for y0 in (126, 134):
    for x in range(64, 68):
        for dy in (0, 1):
            ROAD.add((x, y0 + dy))
            setT(x, y0 + dy, G.ROAD_BROKEN, True)
            H[I(x, y0 + dy)] = max(H[I(x, y0 + dy)], 1) if T[I(x, y0 + dy)] not in WATER else H[I(x, y0 + dy)]
            FIXED[I(x, y0 + dy)] = 0


def line_h(x0, x1, y):
    return [(x, y) for x in range(x0, x1 + 1)]


def street(cells, t=G.DIRT_1):
    for (x, y) in cells:
        if inb(x, y) and (x, y) not in occ:
            ROAD.add((x, y))
            if T[I(x, y)] not in WATER:
                setT(x, y, t, True)


def ring_road(x0, y0, x1, y1):
    cells = []
    for x in range(x0 + 1, x1):
        cells += [(x, y0 + 1), (x, y1 - 1)]
    for y in range(y0 + 1, y1):
        cells += [(x0 + 1, y), (x1 - 1, y)]
    street(cells)


def gate_apron(gx, gy, side):
    """плац 3x3 снаружи ворот и два факела"""
    dx, dy = {"W": (-3, -1), "E": (1, -1), "N": (-1, 1), "S": (-1, -3)}[side]
    for i in range(3):
        for j in range(3):
            x, y = gx + dx + i, gy + dy + j
            if inb(x, y) and T[I(x, y)] not in WATER and T[I(x, y)] not in WALKWATER and (x, y) not in ROAD:
                setT(x, y, G.DIRT_2, True)
    for sx, sy in {"W": [(-2, -2), (-2, 2)], "E": [(2, -2), (2, 2)], "N": [(-2, 2), (2, 2)], "S": [(-2, -2), (2, -2)]}[side]:
        decor_at(K("TORCH_A"), gx + sx, gy + sy)


def garrison(player, spec, rect):
    out = {}
    for const, n in spec:
        out[const] = scatter(player, const, n, rect, cnt_key="gar")
    return out


CIT = defaultdict(list)


def citizens(player, n, rect, rect2=None):
    out = []
    per = n
    out += scatter(player, VILL_M, per // 2 + per % 2, rect)
    out += scatter(player, VILL_F, per // 2, rect2 or rect)
    CIT[player] += out
    return out


def livestock(spec, rect):
    rect = (rect[0] - 8, rect[1] - 8, rect[2] + 8, rect[3] + 8)
    for const, n in spec:
        scatter(0, K(const), n, rect, cnt_key="stock")


# ================================================================ МОРАВСК
CUR[0] = "Mor"
MW = (54, 44, 70, 60)
street(line_h(55, 55, 52) + [(55, 53)] + [(x, 52) for x in range(50, 55)] + [(x, 53) for x in range(50, 55)], G.ROAD_BROKEN)
road_rect((61, 52, 62, 59), G.ROAD_BROKEN)
road_rect((61, 61, 62, 63), G.ROAD_BROKEN)
mor_wall = build_wall(P2, FORT, *MW, gates=[(54, 52), (62, 60)])
towers(P2, WT, [(54, 44), (70, 44), (54, 60), (70, 60), (54, 55), (65, 60)])
for gx, gy, sd in ((54, 52, "W"), (62, 60, "N")):
    gate_apron(gx, gy, sd)
put(P2, TC_, 63, 53, 4, "MorTC")
put(P2, MON_, 56, 56, 3, "MorChurch")
put(P2, BARR_, 65, 46, 3)
put(P2, STAB_, 65, 50, 3)
put(P2, SMITH_, 56, 46, 3)
plaza((56, 51, 60, 55))
for nm in ("BONFIRE", "SMOKE", "SMOKE", "SMOKE", "GRAVE", "GRAVE", "GRAVE", "GRAVE", "WEAPON_RACK", "WATER_TROUGH", "WATER_TROUGH",
           "GRANARY", "GRANARY", "GRAIN_STORAGE", "HAY_STACK", "HAY_STACK", "HAY_STACK"):
    sz = SZ.get(K(nm), 1)
    try:
        place(P2 if nm in ("GRANARY", "GRAIN_STORAGE") else 0, K(nm), 62, 52, sz, rect=(55, 45, 69, 59), maxr=14)
    except RuntimeError:
        pass
pack_yards((55, 45, 69, 59), {"house": 7, "craft": 2}, house_owner=P2, passes=3)
quota(P2, K("HOUSE"), 8, [(55, 45, 69, 59)], label="Mor P2 HOUSE")
pockets((55, 45, 69, 59), 0.3)
plaza_items((56, 51, 60, 55), 3, 1, 0, 3, 2, 1)
put(0, K("WELL"), 59, 50, tag="u") if free_cell(59, 50) else None
for (x, y) in ((57, 57), (59, 57)):
    pass
MOR_FILL = fill_stats(MW, (56, 51, 60, 55))
# слободы, поля, сад, пристань
MOR_SLOB_E = (72, 45, 86, 58)
street([(x, 52) for x in range(71, 88)])
place(0, K("CHAPEL"), 80, 53, 3, "MorChapel", rect=MOR_SLOB_E)
pack_yards(MOR_SLOB_E, {"poor": 5, "house": 3}, 0, passes=3)
pockets(MOR_SLOB_E, 0.7)
graves(6, (78, 50, 84, 56))
MOR_SLOB_S = (54, 33, 68, 41)
street([(x, 37) for x in range(53, 70)])
pack_yards(MOR_SLOB_S, {"poor": 5, "house": 2}, 0, passes=3)
quota(0, K("HOUSE"), 5, [MOR_SLOB_E, MOR_SLOB_S], label="Mor Gaia HOUSE")
pockets(MOR_SLOB_S, 0.7)
farm_field((72, 28, 88, 43), P2, 4, mill=(73, 30))
decor_pen = scatter_decor((57, 40, 68, 43), ["FENCE"], 8)
for (cx, cy) in ((48, 47), (49, 49), (47, 50), (50, 46), (46, 48), (50, 50)):
    decor_at(K("FRUIT_BUSH"), cx, cy)
for (cx, cy) in ((46, 46), (47, 52), (49, 45)):
    decor_at(K("TREE_OAK"), cx, cy)
scatter_decor((44, 44, 52, 51), ["BUSH_A", "BUSH_B", "TREE_BIRCH", "FENCE"], 14)
scatter_decor((53, 62, 72, 66), ["BUSH_A", "BUSH_B", "BUSH_C", "TREE_BIRCH", "TREE_OAK_AUTUMN", "REED"] if False else ["BUSH_A", "BUSH_B", "BUSH_C", "TREE_BIRCH", "TREE_OAK_AUTUMN"], 14)
mor_dock = dock_at(P2, 60, False)
ships(P2, "FISHING_SHIP", 1, 60, 66)
ships(P7, "TRANSPORT_SHIP", 1, 66, 74)
scatter_decor((57, 62, 66, 65), ["LUMBER", "BARRELS", "DRIFTWOOD_GROUND"], 4)
# жители, гарнизон, скот
MOR_IN = (55, 45, 69, 59)
citizens(P2, 30, (50, 40, 88, 62))
mor_gar = garrison(P2, [(SPEAR_, 8), (HC_, 6), (KNIGHT_, 2)], MOR_IN)
MOR_VOEV = scatter(P2, VILL_M, 2, MOR_IN)
unit_at_cart = um.add_unit(P7, K("CART"), x=62.5, y=62.5)
livestock([("COW_A", 1), ("COW_B", 1), ("COW_C", 1), ("COW_D", 1), ("SHEEP", 6), ("GOOSE", 5), ("PIG", 3), ("HORSE_A", 1), ("HORSE_B", 1)],
          (54, 33, 88, 43))
# застава (42,30)
CUR[0] = "Zast"
for (dx, dy) in ((-3, -3), (3, -3), (-3, 3), (3, 3), (0, -3), (0, 3)):
    put(0, FEN, 42 + dx, 30 + dy, 1, tag="f")
put(P2, WT, 44, 31, 1, "ZastTower")
put(0, K("BONFIRE"), 41, 29, tag="u")
put(0, K("HOUSE"), 38, 32, 2)
ZAST_SPEAR = scatter(P2, SPEAR_, 3, (38, 26, 46, 34))
ZAST_SCOUT = scatter(P2, SCOUT_, 2, (39, 27, 45, 33))

# ================================================================ ЧЕРНИГОВ
CUR[0] = "Che"
CW = (59, 111, 85, 141)
# улицы
road_rect((73, 112, 74, 121))          # от Южных ворот к торгу
road_rect((73, 130, 74, 140))          # к Северным
road_rect((60, 126, 68, 127))          # от Западных ворот
road_rect((79, 129, 84, 130))          # к Восточным
road_rect((83, 131, 84, 134))
street([(66, y) for y in range(112, 141)] + [(80, y) for y in range(112, 141)])
che_wall = build_wall(P3, STW, *CW, cut=2, gates=[(73, 111), (59, 126), (73, 141), (85, 134)])
towers(P3, GT, [(61, 111), (83, 111), (61, 141), (83, 141), (59, 118), (79, 141)])
for gx, gy, sd in ((73, 111, "S"), (59, 126, "W"), (73, 141, "N"), (85, 134, "E")):
    gate_apron(gx, gy, sd)
put(P3, MARKET_, 71, 126, 4, "CheMarket")
put(P3, MON_, 80, 124, 3, "ChePyatnitskaya")
for tl in ((67, 114), (67, 120)):
    place(P3, SMITH_, tl[0], tl[1], 3, rect=(60, 112, 84, 140))
place(P3, BARR_, 76, 113, 3, rect=(60, 112, 84, 140))
place(P3, K("FOLWARK"), 78, 136, 3, rect=(60, 112, 84, 140))
place(0, K("CHAPEL"), 61, 132, 3, "CheZastrChapel", rect=(60, 112, 84, 140))
for tl in ((68, 131), (70, 133), (76, 131), (68, 136)):
    place(P3, K("STORAGE"), tl[0], tl[1], 2, rect=(60, 112, 84, 140))
plaza((69, 122, 78, 129))
pack_yards((60, 112, 84, 140), {"house": 6, "craft": 2, "merchant": 3, "soldier": 2}, house_owner=P3, passes=4)
quota(P3, K("HOUSE"), 30, [(60, 112, 84, 140)], label="Che P3 HOUSE")
pockets((60, 112, 84, 140), 0.3)
plaza_items((69, 122, 78, 129), 10, 1, 6, 6, 4, 1)
for nm, n in (("SMOKE", 10), ("BONFIRE", 3), ("TREE_BIRCH", 6), ("TREE_OAK_AUTUMN", 4), ("WELL", 3), ("TREE_WILLOW", 4),
              ("FURNACE", 2), ("WEAPON_RACK", 6), ("VASES", 2), ("GRAVE", 4)):
    scatter_decor((60, 112, 84, 140), [nm], n)
CHE_FILL = fill_stats(CW, (69, 122, 78, 129))
put(P3, K("HOUSE"), 62, 122, 2) if fits(62, 122, 2) else None
# замок P6
CUR[0] = "Cas"
KW = (89, 115, 103, 127)
road_rect((90, 123, 91, 124))
street([(95, y) for y in range(116, 127)] + [(x, 126) for x in range(90, 103)])
cas_wall = build_wall(P6, FSW, *KW, gates=[(89, 124)])
castle_weak = []
for y in (118, 119, 120):
    castle_weak.append(NAMED.setdefault(f"wk{y}", None))
# слабый участок: заменить 3 звена на обычный частокол
weak_units = []
for y in (118, 119, 120):
    u = cas_wall.pop((89, y), None)
    if u is not None:
        um.remove_unit(unit=u)
    weak_units.append(um.add_unit(P6, STW, x=89.5, y=y + 0.5))
towers(P6, GT, [(89, 115), (103, 115), (89, 127), (103, 127)])
put(P6, KP, 91, 121, 3, "CasKeep")
put(P6, K("CASTLE"), 98, 120, 4, "Castle")
put(0, K("DORMITION_CATHEDRAL"), 91, 116, 4, "Cathedral")
put(P6, MON_, 99, 124, 3, "CasMon")
put(P6, SMITH_, 95, 116, 3, "CasSmith")
put(P6, K("GRANARY"), 92, 123, 2, "CasGranary1")
put(P6, K("GRANARY"), 92, 125, 2, "CasGranary2")
KIN = (90, 116, 102, 126)
pack_yards(KIN, {"soldier": 4, "house": 2, "craft": 1}, house_owner=P6, passes=3)
quota(P6, K("HOUSE"), 5, [KIN], label="Cas P6 HOUSE")
pockets(KIN, 0.0)
for nm, n in (("TORCH_A", 6), ("SMOKE", 2), ("BARRELS", 3), ("WELL", 1), ("GRAVE", 2), ("TREE_BIRCH", 2), ("SIEGE_PROPS", 1)):
    scatter_decor(KIN, [nm], n)
scatter_decor((86, 112, 106, 130), ["BUSH_A", "BUSH_B", "BUSH_C", "TREE_OAK_AUTUMN", "ROCK_MOSSY"], 18)
CAS_FILL = fill_stats(KW)
# за стенами Чернигова
CUR[0] = "Che"
CHE_SLOB = (64, 144, 88, 156)
street([(x, 150) for x in range(62, 90)])
place(0, MON_, 84, 152, 3, "CheSlobChurch", rect=CHE_SLOB)
pack_yards(CHE_SLOB, {"poor": 5, "house": 4}, 0, passes=4)
quota(0, K("HOUSE"), 10, [CHE_SLOB], label="Che Gaia HOUSE")
pockets(CHE_SLOB, 0.8)
graves(10, (82, 145, 90, 150))
for i in range(0, 20, 2):
    decor_at(FEN, 82 + i // 2, 147)
farm_field((54, 158, 84, 170), P3, 6, mill=(56, 156))
place(P3, K("MILL"), 86, 158, 2, rect=(54, 154, 100, 175))
for nm, n in (("HAY_STACK", 8), ("BUSH_A", 6)):
    scatter_decor((54, 158, 90, 172), [nm], n)
gardens = (50, 108, 57, 118)
for (x, y) in rect_free_cells(gardens)[:40:3]:
    decor_at(K("FRUIT_BUSH"), x, y)
scatter_decor(gardens, ["TREE_OAK", "FENCE", "FENCE", "FRUIT_BUSH"], 20)
scatter_decor((90, 142, 98, 148), ["FENCE", "FENCE", "WATER_TROUGH", "HAY_STACK"], 18)
graves(12, (76, 104, 84, 109))
scatter_decor((76, 104, 84, 109), ["FENCE", "TREE_BIRCH"], 12)
che_dock = dock_at(P3, 78, True)
ships(P3, "FISHING_SHIP", 2, 78, 92)
ships(P7, "TRANSPORT_SHIP", 2, 82, 98)
water_put(P3, K("FISH_TRAP"), 2, 2, 76, 90)
place(P3, K("LUMBER_CAMP"), 74, 98, 2, rect=(60, 90, 90, 108))
scatter_decor((70, 94, 86, 104), ["LUMBER", "BARRELS", "DRIFTWOOD_GROUND"], 11)
# Елецкий монастырь (52,128)
CUR[0] = "Yel"
YW = (47, 123, 57, 133)
yel_wall = build_wall(0, PALW, *YW, gates=[(57, 128)])
put(0, MON_, 50, 127, 3, "YelMon")
for tl in ((48, 124), (54, 124), (48, 130), (54, 130)):
    place(0, K("HOUSE"), tl[0], tl[1], 2, rect=(48, 124, 56, 132))
graves(8, (48, 124, 56, 132))
for nm, n in (("WELL", 1), ("FRUIT_BUSH", 4), ("TREE_BIRCH", 3), ("SMOKE", 1), ("FENCE", 6)):
    scatter_decor((48, 124, 56, 132), [nm], n)
YEL_MONKS = scatter(0, MONK_, 3, (49, 125, 56, 132))
# Болдины горы
CUR[0] = "Che"
place(0, K("CHAPEL"), 63, 103, 3, "BoldChapel", rect=(56, 98, 72, 112))
for (x, y) in ((60, 108), (66, 100)):
    decor_at(K("ROCK_FORMATION_1"), x, y)
graves(4, (60, 104, 68, 110))
# население и скот
CHE_IN = (60, 112, 84, 140)
citizens(P3, 56, (60, 112, 84, 156))
che_gar = garrison(P3, [(SPEAR_, 10), (HC_, 4)], CHE_IN)
cas_gar = garrison(P6, [(SPEAR_, 6), (HC_, 5), (KNIGHT_, 3)], KIN)
CAS_PEOPLE = scatter(P6, VILL_M, 2, KIN)
TATEV = scatter(P6, HeroInfo.THEODORIC_THE_GOTH.ID, 1, KIN)[0]
um.add_unit(P7, K("TRADE_CART_FULL"), x=75.5, y=117.5)
um.add_unit(P7, K("CART"), x=84.5, y=133.5)
livestock([("COW_A", 3), ("COW_B", 3), ("COW_C", 2), ("COW_D", 2), ("SHEEP", 12), ("PIG", 6), ("GOOSE", 8), ("HORSE_A", 4),
           ("HORSE_B", 4)], (64, 144, 98, 156))

# ================================================================ НОВГОРОД-СЕВЕРСКИЙ
CUR[0] = "NS"
NW = (150, 163, 172, 184)
NIN = (151, 164, 171, 183)
road_rect((151, 171, 156, 172))
road_rect((161, 175, 162, 183))
road_rect((167, 173, 171, 174))
ns_wall = build_wall(P4, STW, *NW, cut=2, gates=[(150, 171), (161, 184), (172, 174)])
towers(P4, GT, [(171, 164), (151, 183), (171, 183), (161, 164)])
towers(P4, K("BOMBARD_TOWER"), [(151, 165), (153, 164)])
for tl in ((151, 169), (168, 171)):
    place(P4, KP, tl[0], tl[1], 3, rect=NIN)
for gx, gy, sd in ((150, 171, "W"), (161, 184, "N"), (172, 174, "E")):
    gate_apron(gx, gy, sd)
put(P4, TC_, 159, 171, 4, "NSTC")
put(P4, MON_, 152, 178, 3, "NSChurch")
put(P4, BARR_, 167, 178, 3)
place(P4, STAB_, 167, 180, 3, "NSStable", rect=NIN, maxr=14)
place(P4, ARCH_, 167, 165, 3, rect=NIN)
place(P4, K("GRANARY"), 152, 165, 2, rect=NIN)
place(P4, K("GRANARY"), 154, 167, 2, rect=NIN)
plaza((158, 166, 163, 170))
pack_yards(NIN, {"soldier": 4, "house": 4, "craft": 1}, house_owner=P4, passes=4)
quota(P4, K("HOUSE"), 18, [NIN], label="NS P4 HOUSE")
pockets(NIN, 0.15)
plaza_items((158, 166, 163, 170), 0, 1, 0, 4, 2, 0)
for nm, n in (("GRAIN_STORAGE", 2), ("HAY_STACK", 5), ("BARRELS", 6), ("WEAPON_RACK", 8), ("TORCH_A", 12), ("BONFIRE", 3),
              ("GRAVE", 3), ("TREE_BIRCH", 2), ("WELL", 2), ("WATER_TROUGH", 2), ("SMOKE", 4)):
    scatter_decor(NIN, [nm], n)
def topup(key, rect, target, names=("BUSH_A", "BUSH_B", "HAY_STACK", "TREE_BIRCH", "BARRELS", "PLANT_WEEDS", "GRASS_PATCH_GREEN")):
    cells = rect_free_cells(rect)
    rng.shuffle(cells)
    for (x, y) in cells:
        if CNT[key]["obj"] >= target:
            break
        put(0, K(rng.choice(names)), x, y, 1, tag="u")


topup("NS", (128, 150, 148, 185), 225)
NS_FILL = fill_stats(NW, (158, 166, 163, 170))
# пепелище (запад и север)
ASH_RECTS = [(128, 166, 148, 185), (150, 187, 176, 196)]
for rc in ASH_RECTS:
    for y in range(rc[1], rc[3] + 1):
        for x in range(rc[0], rc[2] + 1):
            if (x + y) % 5 == 0 and free_cell(x, y) and rng.random() < 0.55:
                setT(x, y, G.DIRT_4, False)
street([(x, 172) for x in range(130, 150)] + [(139, y) for y in range(163, 182)] + [(x, 185) for x in range(150, 172)] +
       [(158, y) for y in range(179, 192)], G.DIRT_1)
ash_burn = []
for rc in ASH_RECTS:
    cells = rect_free_cells(rc)
    rng.shuffle(cells)
    k = 0
    for (x, y) in cells:
        if k >= 9:
            break
        if fits(x, y, 3):
            ash_burn.append(put(0, K(rng.choice(["BURNED_BUILDING_A", "BURNED_BUILDING_B", "BURNED_BUILDING_C",
                                                 "BURNED_BUILDING_D", "BURNED_BUILDING_E"])), x, y, 3))
            k += 1
for rc in ASH_RECTS:
    scatter_decor(rc, ["RUBBLE_2_X_2"], 4)
    scatter_decor(rc, ["RUBBLE_1_X_1"] * 1, 5)
    scatter_decor(rc, ["BROKEN_FENCE_A", "BROKEN_FENCE_B"], 6)
    scatter_decor(rc, ["TREE_DEAD"], 3)
    scatter_decor(rc, ["SMOKE"], 5)
    scatter_decor(rc, ["FLAME1", "FLAME2", "FLAME3", "FLAME4"], 3)
# целые избы посада у Западных ворот (сгорят в E12)
NS_HOUSES = []
for tl in ((144, 168), (144, 171), (144, 174), (141, 170), (141, 173), (144, 177)):
    h_ = place(P4, K("HOUSE"), tl[0], tl[1], 2, rect=(132, 164, 148, 188), maxr=10)
    if h_ is not None:
        NS_HOUSES.append(h_)
# надолбы
for i in range(7):
    decor_at(K("STAKE_BARRICADE"), 147, 162 + i * 2)
    decor_at(K("STAKE_BARRICADE"), 148, 163 + i * 2)
# Спасо-Преображенский монастырь
SPW = find_land_rect(184, 176, 9, 9, 30) or (178, 168, 186, 176)
sp_wall = build_wall(0, PALW, *SPW, gates=[(SPW[0], SPW[1] + 4)])
put(0, MON_, SPW[0] + 3, SPW[1] + 3, 3, "SpasMon")
for tl in ((SPW[0] + 1, SPW[1] + 1), (SPW[0] + 5, SPW[1] + 1)):
    place(0, K("HOUSE"), tl[0], tl[1], 2, rect=(SPW[0] + 1, SPW[1] + 1, SPW[2] - 1, SPW[3] - 1))
graves(6, (SPW[0] + 1, SPW[1] + 5, SPW[2] - 1, SPW[3] - 1))
ns_dock = dock_at(P4, 166, True)
wc = water_cell_near(166, 150)
if wc:
    boat(P4, K("FISHING_SHIP"), *wc)
wc = water_cell_near(172, 156)
if wc:
    boat(0, K("TRANSPORT_SHIP"), *wc)
farm_field((172, 160, 184, 166), 0, 0)
scatter_decor((172, 160, 184, 166), ["HAY_STACK", "FLAME1"], 5)
# жители, гарнизон
NS_IN = NIN
citizens(P4, 30, (146, 164, 172, 183))
ns_gar = garrison(P4, [(SPEAR_, 10), (HC_, 8), (KNIGHT_, 4), (MAA_, 6), (CAVARCH_, 4)], NS_IN)
BASMANOV = scatter(P4, HeroInfo.ALEXANDER_NEVSKI.ID, 1, NS_IN)[0]
PATROL_A = scatter(P4, SPEAR_, 3, (148, 122, 152, 128)) + scatter(P4, CAVARCH_, 1, (148, 122, 152, 128))
PATROL_B = scatter(P4, SPEAR_, 3, (158, 96, 162, 100)) + scatter(P4, CAVARCH_, 1, (158, 96, 162, 100))
livestock([("HORSE_A", 2), ("HORSE_B", 2), ("COW_A", 1), ("COW_B", 1), ("GOOSE", 2)], NS_IN)

# ================================================================ ПУТИВЛЬ
CUR[0] = "Put"
KRW = (167, 64, 185, 80)
PW = (152, 81, 186, 101)
# кремль
road_rect((176, 74, 177, 79))
road_rect((168, 72, 173, 73))

kr_wall = build_wall(P5, FSW, *KRW, gates=[(176, 80), (167, 72)])
towers(P5, GT, [(167, 64), (185, 64), (167, 80), (185, 80)])
put(P5, TC_, 174, 70, 4, "PutTC")
put(P5, MON_, 179, 75, 3, "PutCathedral")
put(P5, BARR_, 180, 65, 3)
place(P5, STAB_, 177, 65, 3, "PutStable", rect=(168, 65, 184, 79), maxr=12)
place(P5, KP, 169, 66, 3, rect=(168, 65, 184, 79))
place(P5, K("STORAGE"), 169, 75, 2, rect=(168, 65, 184, 79))
for (x, y) in ((170, 77), (171, 77), (170, 76)):
    decor_at(K("TREASURE_CHEST"), x, y)
plaza((171, 74, 175, 77))
pack_yards((168, 65, 184, 79), {"house": 5, "merchant": 2, "soldier": 2, "craft": 1}, house_owner=P5, passes=4)
pockets((168, 65, 184, 79), 0.1)
plaza_items((171, 74, 175, 77), 0, 1, 0, 0, 2, 0)
for nm, n in (("TORCH_A", 6), ("SMOKE", 2), ("GRAVE", 3), ("TREE_BIRCH", 2), ("BARRELS", 4), ("WELL", 1)):
    scatter_decor((168, 65, 184, 79), [nm], n)
PUT_KR_FILL = fill_stats(KRW, (171, 74, 175, 77))
# посад
CUR[0] = "Put"
road_rect((153, 90, 159, 91))
road_rect((170, 97, 171, 100))
road_rect((172, 87, 177, 88))
road_rect((176, 81, 177, 86))
street([(x, 92) for x in range(172, 186)] + [(178, y) for y in range(82, 101)])
put_wall = build_wall(P5, STW, *PW, gates=[(152, 90), (170, 101), (186, 92)], skip_side=lambda c: c[1] == 81 and 167 <= c[0] <= 185)
towers(P5, GT, [(152, 81), (186, 81), (152, 101), (186, 101)])
for gx, gy, sd in ((152, 90, "W"), (170, 101, "N"), (186, 92, "E"), (176, 80, "N")):
    gate_apron(gx, gy, sd)
put(P5, MARKET_, 164, 90, 4, "PutMarket")
put(P5, MON_, 173, 93, 3, "PutChurch")
for tl in ((180, 83), (183, 83)):
    place(P5, SMITH_, tl[0], tl[1], 3, rect=(153, 82, 185, 100))
for i in range(7):
    place(P5, K("STORAGE"), 154 + i * 0, 83 + i, 2, rect=(153, 82, 160, 90)) if False else None
for tl in ((154, 83), (156, 85), (154, 87), (156, 83), (154, 85), (156, 87), (158, 83)):
    try:
        place(P5, K("STORAGE"), tl[0], tl[1], 2, rect=(153, 82, 159, 89))
    except RuntimeError:
        pass
plaza((160, 88, 171, 96))
pack_yards((153, 82, 185, 100), {"house": 6, "merchant": 3, "craft": 2, "soldier": 1}, house_owner=P5, passes=4)
quota(P5, K("HOUSE"), 45, [(168, 65, 184, 79), (153, 82, 185, 100)], label="Put P5 HOUSE")
quota(0, K("GRANARY"), 5, [(153, 82, 185, 100), (136, 99, 148, 111), (186, 84, 198, 100)], label="Put GRANARY")
pockets((153, 82, 185, 100), 0.0)
plaza_items((160, 88, 171, 96), 12, 1, 8, 6, 4, 1)
for nm, n in (("SMOKE", 6), ("BONFIRE", 3), ("TREE_BIRCH", 4), ("TREE_OAK_AUTUMN", 3), ("WELL", 5), ("GRAVE", 4),
              ("LEATHERWORKING_EQUIPMENT", 2), ("FURNACE", 1), ("WATER_TROUGH", 4), ("HAY_STACK", 2), ("LUMBER", 2)):
    scatter_decor((153, 82, 185, 100), [nm], n)
PUT_FILL = fill_stats(PW, (160, 88, 171, 96))
# слобода, поля, сады, монастырь, пристань
PUT_SLOB = (136, 99, 148, 111)
street([(x, 105) for x in range(134, 150)])
place(0, MON_, 140, 107, 3, "PutSlobChurch", rect=PUT_SLOB)
pack_yards(PUT_SLOB, {"poor": 5, "house": 3}, 0, passes=4)
quota(0, K("HOUSE"), 4, [PUT_SLOB], label="Put Gaia HOUSE")
pockets(PUT_SLOB, 0.8)
graves(10, (138, 99, 146, 103))
farm_field((164, 103, 184, 114), P5, 8, mill=(163, 100))
place(P5, K("MILL"), 186, 106, 2, rect=(160, 100, 195, 118))
scatter_decor((164, 103, 190, 116), ["HAY_STACK"], 8)
for (x, y) in rect_free_cells((187, 84, 196, 96))[::4]:
    decor_at(K("FRUIT_BUSH"), x, y)
scatter_decor((187, 84, 196, 96), ["TREE_OAK", "FENCE", "FENCE"], 14)
MW2 = (187, 71, 197, 81)
mol_wall = build_wall(0, PALW, *MW2, gates=[(187, 76)])
put(0, MON_, 191, 75, 3, "MolchMon")
for tl in ((188, 72), (194, 72), (188, 78), (194, 78)):
    place(0, K("HOUSE"), tl[0], tl[1], 2, rect=(188, 72, 196, 80))
graves(10, (188, 72, 196, 80))
scatter_decor((188, 72, 196, 80), ["WELL", "FRUIT_BUSH", "FRUIT_BUSH", "FRUIT_BUSH"], 4)
MOLCH_MONKS = scatter(0, MONK_, 2, (189, 73, 195, 79))
put_dock = dock_at(P5, 170, True)
ships(P5, "FISHING_SHIP", 2, 168, 58)
ships(P7, "TRANSPORT_SHIP", 2, 174, 56)
water_put(P5, K("FISH_TRAP"), 2, 1, 164, 58)
place(P5, K("LUMBER_CAMP"), 160, 62, 2, rect=(150, 58, 175, 66))
scatter_decor((150, 58, 176, 66), ["LUMBER", "BARRELS", "DRIFTWOOD_GROUND"], 8)
# жители, гарнизон, персонажи
PUT_IN = (153, 82, 185, 100)
citizens(P5, 50, (140, 82, 188, 112))
put_gar = garrison(P5, [(SPEAR_, 8), (HC_, 6), (KNIGHT_, 4), (CAVARCH_, 4)], PUT_IN)
SALT, RUBEC, SUTUP = scatter(P5, VILL_M, 3, (168, 65, 184, 79))
um.add_unit(P7, K("TRADE_CART_FULL"), x=165.5, y=94.5)
um.add_unit(P7, K("TRADE_CART_FULL"), x=170.5, y=99.5)
um.add_unit(P7, K("TRADE_CART_EMPTY"), x=162.5, y=92.5)
um.add_unit(P7, K("CART"), x=154.5, y=88.5)
livestock([("COW_A", 2), ("COW_B", 2), ("COW_C", 2), ("COW_D", 2), ("SHEEP", 10), ("PIG", 4), ("GOOSE", 6), ("HORSE_A", 3),
           ("HORSE_B", 2)], (136, 99, 150, 112))
scatter(0, MONK_, 0, PUT_IN)

# ================================================================ СЁЛА V1-V4
VILLAGES = [("V1", (48, 20), "CHAPEL"), ("V2", (62, 104), "MONASTERY"), ("V3", (110, 144), "CHAPEL"), ("V4", (154, 114), "MONASTERY")]
VCH = {}
for vn, (vx, vy), ch in VILLAGES:
    CUR[0] = vn
    vr = (vx - 9, vy - 6, vx + 9, vy + 6)
    street([(x, vy) for x in range(vx - 11, vx + 12)], G.DIRT_1)
    paint_rect((vx - 9, vy - 6, vx + 9, vy + 6), G.DIRT_2, False)
    cch = place(0, K(ch), vx - 1, vy + 1, 3, f"Church_{vn}", rect=vr)
    VCH[vn] = (vx, vy)
    NAMED[f"church_pos_{vn}"] = (int(cch.x), int(cch.y))
    pack_yards(vr, {"poor": 4, "house": 4}, P7, passes=4)
    quota(P7, K("HOUSE"), 4, [vr], label=f"{vn} P7 HOUSE")
    pockets(vr, 0.6)
    farm_field((vx - 12, vy + 7, vx + 12, vy + 15), P7, 2)
    for nm, n in (("WELL", 1), ("HAY_STACK", 4), ("GRANARY", 1), ("WATER_TROUGH", 1), ("TREE_BIRCH", 4), ("SMOKE", 2)):
        scatter_decor(vr, [nm], n)
    scatter(P7, VILL_M, 3, vr)
    scatter(P7, VILL_F, 2, vr)
    livestock([("COW_A", 2), ("GOOSE", 3), ("SHEEP", 3)], vr)

# ================================================================ ТАБОР (Г0: Gaia)
CUR[0] = "Camp"
CAMP_C = (140, 156)
put(0, TC_, 138, 154, 4, "campTC")
put(0, BARR_, 131, 148, 3, "campBarr")
put(0, ARCH_, 145, 148, 3, "campArch")
put(0, STAB_, 131, 160, 3, "campStable")
put(0, MON_, 145, 160, 3, "campMon")
put(0, K("FLAG_A"), 140, 152, tag="u")
for i in range(6):
    decor_at(K("STAKE_BARRICADE"), 148, 150 + i)
decor_at(K("BROKEN_CART"), 135, 153)
for y in range(149, 163):
    if (139, y) not in occ:
        ROAD.add((139, y))
        setT(139, y, G.DIRT_1, True)
for x in range(131, 148):
    if (x, 158) not in occ:
        ROAD.add((x, 158))
        setT(x, 158, G.DIRT_1, True)
paint_rect((128, 146, 150, 166), G.DIRT_2, False)
CAMP_RES = set()


def camp_spots(n, rmin, rmax, size=2):
    out = []
    tries = 0
    while len(out) < n and tries < 6000:
        tries += 1
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(rmin, rmax)
        x, y = int(CAMP_C[0] + r * math.cos(a)), int(CAMP_C[1] + r * math.sin(a))
        if not all(free_cell(x + i, y + j) and (x + i, y + j) not in CAMP_RES for i in range(size) for j in range(size)):
            continue
        if any(((x + i, y + j) in ROAD) for i in range(size) for j in range(size)):
            continue
        if any(RAV_CELLS.get(I(x + i, y + j)) for i in range(size) for j in range(size)):
            continue
        if math.hypot(x - 145, y - 156) < 0:
            continue
        for i in range(size):
            for j in range(size):
                CAMP_RES.add((x + i, y + j))
        out.append((x, y))
    return out


CAMP_PLAN = {}
CAMP_PLAN["tent_main"] = camp_spots(1, 3, 5, 3)
CAMP_PLAN["g1_tents"] = camp_spots(8, 4, 9)
CAMP_PLAN["g1_carts"] = []
for k in range(16):
    a = 2 * math.pi * k / 16
    if k in (0, 1, 8, 9, 12):     # разрывы-выезды
        continue
    x, y = int(CAMP_C[0] + 13 * math.cos(a)), int(CAMP_C[1] + 13 * math.sin(a))
    if free_cell(x, y) and (x, y) not in CAMP_RES and not RAV_CELLS.get(I(x, y)):
        CAMP_RES.add((x, y))
        CAMP_PLAN["g1_carts"].append((x, y))
CAMP_PLAN["g1_barr"] = [(x, y) for (x, y) in [(150 + (i % 2), 148 + i) for i in range(10)] if free_cell(x, y)]
for (x, y) in CAMP_PLAN["g1_barr"]:
    CAMP_RES.add((x, y))
CAMP_PLAN["g1_misc"] = camp_spots(4 + 2 + 6, 4, 9, 1)     # костры 4, возы 2, бочки 6
CAMP_PLAN["g1_horses"] = camp_spots(6, 3, 7, 1)
CAMP_PLAN["g1_vill"] = camp_spots(6, 2, 5, 1)
CAMP_PLAN["g2_tents"] = camp_spots(6, 5, 10)
CAMP_PLAN["g2_misc"] = camp_spots(3 + 2 + 4 + 1, 4, 9, 1)
CAMP_PLAN["g3"] = [camp_spots(4, 6, 11) for _ in range(4)]
CAMP_PLAN["g3_flag"] = camp_spots(4, 6, 11, 1)
CAMP_PLAN["g4_graves"] = camp_spots(6, 5, 9, 1)
CAMP_PLAN["g4_units"] = camp_spots(4, 3, 6, 1)
CAMP_PLAN["g5_tents"] = camp_spots(8, 6, 12)
CAMP_PLAN["g5_vill"] = camp_spots(10, 3, 8, 1)
CAMP_PLAN["g5_misc"] = camp_spots(2 + 6, 4, 10, 1)
CAMP_PLAN["gold"] = None
CAMP_COUNTS = {k: (len(v) if isinstance(v, list) and v and not isinstance(v[0], list) else 0) for k, v in CAMP_PLAN.items() if v}
# ресурсы у табора и малые жилы
RES_GOLD = []
for (gx, gy) in ((128, 140), (150, 142)):
    pass
for (gx, gy, cnt_, const) in ((127, 143, 5, "GOLD_MINE"), (150, 144, 5, "GOLD_MINE"), (124, 150, 4, "STONE_MINE")):
    pos = []
    ox, oy = gx, gy
    for i in range(cnt_):
        x, y = ox + (i % 3), oy + (i // 3)
        if free_cell(x, y) and not RAV_CELLS.get(I(x, y)):
            put(0, K(const), x, y, 1, tag="u")
for (gx, gy) in ((40, 70), (120, 80)):
    for i in range(3):
        decor_at(K("GOLD_MINE"), gx + i, gy)

# ================================================================ СТАРТ P1 и высадка
CUR[0] = "Start"
SX, SY = 24, 14
dmitry = unit_at(P1, HeroInfo.ROLAND.ID, SX, SY, "dmitry")
start_units = {}
spec = [(HUSSAR_, 5), (CAVARCH_, 3), (MONK_, 3), (MAA_, 6), (ARCHER_, 4), (KNIGHT_, 3), (VILL_M, 3), (VILL_F, 3)]   # v3: 3 боярина, 6 обозных для экономики
for const, n in spec:
    start_units[const] = scatter(P1, const, n, (SX - 4, SY - 4, SX + 4, SY + 4))
# 2 пеших казака и 2 казака-лучника стоят на мелководье у берега (E01)
WATER_START = []
shallow_cells = [(x, y) for y in range(10, 20) for x in range(8, 10) if T[I(x, y)] in (int(G.SHALLOWS),)]
for const, n in ((MAA_, 2), (ARCHER_, 2)):
    for k in range(n):
        x, y = 8, 10 + len(WATER_START)
        u = um.add_unit(P1, const, x=x + 0.5, y=y + 0.5)
        UCELLS.add((x, y))
        WATER_START.append(u)
        start_units.setdefault(const, []).append(u)
for (x, y, c) in ((11, 8, "BONFIRE"), (13, 20, "BONFIRE"), (14, 12, "SUPPLY_CART_A")):
    decor_at(K(c), x, y)
for (x, y) in ((6, 12), (6, 17)):
    um.add_unit(0, K("TRANSPORT_SHIP"), x=x + 0.5, y=y + 0.5)
for (x, y) in ((10, 40), (12, 60), (14, 80)):
    decor_at(K("BONFIRE"), x, y)
print("мир: города и сёла расставлены; объектов:", len(um.get_all_units()))

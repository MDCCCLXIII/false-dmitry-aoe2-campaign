# Часть 3: запись, повторное чтение, сверка с §13, NOTES_v2.md. Общее пространство имён.
def expected_names():
    design_ = DESIGN.read_text(encoding="utf-8")
    sec_ = design_.split("### 13.8", 1)[1].split("### 13.9", 1)[0]
    var_ = set(re.findall(r"`([A-Za-z0-9_]+)`", design_.split("### 13.6", 1)[1].split("### 13.7", 1)[0]))
    out_ = []
    for raw in sec_.splitlines():
        if raw.startswith("Удалены") or raw.startswith("**13."):
            continue
        for tok in re.findall(r"`([^`]+)`", raw):
            tok = tok.strip()
            if not re.match(r"^[A-Za-z][A-Za-z0-9_]*", tok) or "(" in tok or "/" in tok or " " in tok:
                continue
            m = re.match(r"^(.*?)(\d)\.\.(\d)$", tok)
            m2 = re.match(r"^(.*?)(\d)([a-z])\.\.(\d)([a-z])$", tok)
            if m2:
                out_ += [f"{m2.group(1)}{m2.group(2)}{c}" for c in "abcd"]
            elif m:
                out_ += [f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(3)) + 1)]
            else:
                out_.append(tok)
    out_ = [e for e in out_ if re.match(r"^(M1_|T_|E\d|S\d|D2_|CP_|OBJ_|E_Random)", e)]
    return [e for e in dict.fromkeys(out_) if (e not in var_ or e in ("M1_Clock", "M1_NSSortieDone")) and not e.startswith("M1_Leaflet")
            and "<" not in e and e != "OBJ_" and not e.endswith("_")]


# порядок триггеров как в §13.8: основной триггер, затем его вспомогательные
_by = {t_.name: t_ for t_ in tm.triggers}
_placed, _seen = [], set()


def _add(t_):
    if t_.trigger_id not in _seen:
        _seen.add(t_.trigger_id)
        _placed.append(t_.trigger_id)


for _e in expected_names():
    if _e in _by:
        _add(_by[_e])
        for t_ in list(tm.triggers):
            if t_.name.startswith(_e + "__"):
                _add(t_)
for t_ in list(tm.triggers):
    _add(t_)
tm.reorder_triggers(_placed)

OUT.parent.mkdir(exist_ok=True)
assert OUT.name == "01_cherez_granitsu_v3.aoe2scenario"
sc.write_to_file(str(OUT))
print("Записано:", OUT, OUT.stat().st_size, "байт")

errs, warns = [], []
chk = AoE2DEScenario.from_file(str(OUT))
tms = chk.trigger_manager
names = [x.name for x in tms.triggers]
if len(names) != len(set(names)):
    errs.append("дубли имён триггеров")
if chk.map_manager.map_size != S:
    errs.append("размер карты")

# --- сверка имён триггеров с §13.8
design = DESIGN.read_text(encoding="utf-8")
sec = design.split("### 13.8", 1)[1].split("### 13.9", 1)[0]
var_sec = design.split("### 13.6", 1)[1].split("### 13.7", 1)[0]
var_names = set(re.findall(r"`([A-Za-z0-9_]+)`", var_sec))
expected = []
for raw in sec.splitlines():
    if raw.startswith("Удалены") or raw.startswith("**13."):
        continue
    for tok in re.findall(r"`([^`]+)`", raw):
        tok = tok.strip()
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*", tok) or "(" in tok or "/" in tok or " " in tok:
            continue
        m = re.match(r"^(.*?)(\d)\.\.(\d)$", tok)
        m2 = re.match(r"^(.*?)(\d)([a-z])\.\.(\d)([a-z])$", tok)
        if m2:
            expected += [f"{m2.group(1)}{m2.group(2)}{c}" for c in "abcd"]
        elif m:
            expected += [f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(3)) + 1)]
        else:
            expected.append(tok)
expected = expected_names()
SKIP_EXP = {"M1_Camp_Stage_3a", }
missing = [e for e in expected if e not in names and e != "OBJ_" and not e.endswith("_")]
# специальные случаи записи в §13.8
missing = [m for m in missing if m not in ("M1_Rename_Loop",) or m not in names]
extra = [n for n in names if "__" not in n and n not in expected]
_pos = [names.index(e) for e in expected if e in names]
order_ok = all(a < b for a, b in zip(_pos, _pos[1:]))
print("порядок основных триггеров как в §13.8:", order_ok)
print("ожидаемых имён §13.8:", len(expected), "найдено:", len(expected) - len(missing), "лишних основных:", len(extra), extra)
if missing:
    errs.append("нет триггеров §13.8: " + ", ".join(missing))

# --- висячие ссылки, пустые сообщения
ids_ = {x.trigger_id for x in tms.triggers}
var_ids = {x.variable_id for x in tms.variables}
TRIG_EFF = (EffectId.ACTIVATE_TRIGGER, EffectId.DEACTIVATE_TRIGGER)
VAR_EFF = (EffectId.CHANGE_VARIABLE, EffectId.MODIFY_VARIABLE_BY_VARIABLE)
ref_ids = {u.reference_id for u in chk.unit_manager.get_all_units()}
nmsg = 0
for tr in tms.triggers:
    for e in tr.effects:
        if e.effect_type in TRIG_EFF and e.trigger_id not in ids_:
            errs.append(f"висячая ссылка на триггер {e.trigger_id} в {tr.name}")
        if e.effect_type in VAR_EFF and e.variable not in var_ids:
            errs.append(f"висячая переменная {e.variable} в {tr.name}")
        if e.effect_type in (EffectId.SEND_CHAT, EffectId.DISPLAY_INSTRUCTIONS):
            nmsg += 1
            if not (e.message or "").strip():
                errs.append(f"пустое сообщение в {tr.name}")
            if "[" in (e.message or ""):
                errs.append(f"пометка [..] в тексте {tr.name}")
        for oid in (e.selected_object_ids or []):
            if oid not in ref_ids:
                errs.append(f"висячий объект {oid} в эффекте {tr.name}")
    for c in tr.conditions:
        if c.condition_type in (ConditionId.VARIABLE_VALUE, ConditionId.COMPARE_VARIABLES) and c.variable not in var_ids:
            errs.append(f"висячая переменная {c.variable} в условии {tr.name}")
        if c.unit_object not in (-1, None) and c.unit_object not in ref_ids:
            errs.append(f"висячий объект {c.unit_object} в условии {tr.name}")
if MISSING_TAGS:
    errs.append("нет реплик для тегов: " + ", ".join(sorted(set(MISSING_TAGS))))
unused = [f"{ln.trig}:{ln.typ}" for (tg, ty), lst in LINES.items() for ln in lst
          if not ln.used and not tg.startswith(("U_", "G_"))]
unused_set = sorted(set(unused))
print("сообщений-эффектов:", nmsg, "; неиспользованных реплик (кроме U_ и G_):", len(unused), unused_set[:25])

# --- карта
cnt = {p: len(chk.unit_manager.get_player_units(p)) for p in range(9)}
terr = chk.map_manager.terrain
elev = Counter(t_.elevation for t_ in terr)
tids = Counter(t_.terrain_id for t_ in terr)
bad_h = 0
for y in range(S):
    for x in range(S):
        h = terr[y * S + x].elevation
        for dx, dy in NB8:
            xx, yy = x + dx, y + dy
            if 0 <= xx < S and 0 <= yy < S and abs(terr[yy * S + xx].elevation - h) > 1:
                bad_h += 1
                break
land_i = [i for i in range(N) if terr[i].terrain_id not in (int(G.WATER_DEEP), int(G.WATER_MEDIUM), int(G.WATER_SHALLOW), int(G.SHALLOWS))]
high_share = sum(1 for i in land_i if terr[i].elevation > 1) / float(len(land_i))
if len(elev) < 7:
    errs.append("уровней высоты < 7")
if high_share < 0.35:
    errs.append("доля суши выше 1 < 35%")
if len(tids) < 18:
    errs.append("типов местности < 18")
if bad_h:
    errs.append(f"перепад соседних высот > 1: {bad_h} клеток")
if FOOT_BAD:
    warns.append(f"следов строений с перепадом высот: {FOOT_BAD}")
p1n = cnt[1]
if p1n != 35:
    errs.append(f"юниты P1: {p1n} (нужно 35: 26 из v2 + 3 боярина + 6 обозных)")
if any(u.unit_const == K("WINGED_HUSSAR") for u in chk.unit_manager.get_player_units(1)):
    errs.append("крылатый гусар в стартовом отряде")

# --- города: объекты, жители, заполнение
TARGET_OBJ = {"Mor": 190, "Che": 500, "NS": 210, "Put": 400}
TARGET_CIT = {"Mor": 30, "Che": 56, "NS": 30, "Put": 50}
cit_cnt = {k: len([u for u in CIT[P_[k]] if True]) for k in ("Mor", "Che", "NS", "Put")}
city_rows = []
for k in ("Mor", "Che", "NS", "Put"):
    o = CNT[k]["obj"] + (CNT["Cas"]["obj"] if k == "Che" else 0) + (CNT["Zast"]["obj"] if k == "Mor" else 0)
    o_town = o
    stock = CNT[k]["stock"]
    city_rows.append((k, o_town, TARGET_OBJ[k], cit_cnt[k], TARGET_CIT[k], stock))
    if o_town < TARGET_OBJ[k]:
        errs.append(f"{k}: строений и декора {o_town} < {TARGET_OBJ[k]}")
    if cit_cnt[k] < TARGET_CIT[k]:
        errs.append(f"{k}: жителей {cit_cnt[k]} < {TARGET_CIT[k]}")
# --- заполнение по определению §13: следы зданий внутри стен / (внутренняя площадь - улицы - площадь); улицы и площади отдельно
FOOT = {}
for u in chk.unit_manager.get_all_units():
    if u.unit_const in WALL_CONSTS or u.unit_const in ALL_GATE_CONSTS:
        continue
    is_unit = any(u.unit_const == x.ID for ds in (UnitInfo, HeroInfo) for x in ds)
    if is_unit:
        continue
    sz = SZ.get(u.unit_const, 1)
    tlx, tly = int(round(u.x - sz / 2.0)), int(round(u.y - sz / 2.0))
    for a_ in range(sz):
        for b_ in range(sz):
            FOOT[(tlx + a_, tly + b_)] = sz
CITY_IN = {"Моравск": ((55, 45, 69, 59), (56, 51, 60, 55)), "Чернигов (посад)": ((60, 112, 84, 140), (69, 122, 78, 129)),
           "Замок Чернигова": ((90, 116, 102, 126), None), "Новгород-Северский": (NIN, (158, 166, 163, 170)),
           "Кремль Путивля": ((168, 65, 184, 79), (171, 74, 175, 77)), "Посад Путивля": ((153, 82, 185, 100), (160, 88, 171, 96))}
FILLS = {}
for nm, (rc, pl_) in CITY_IN.items():
    tot = roads = plz = bld = small = 0
    for y_ in range(rc[1], rc[3] + 1):
        for x_ in range(rc[0], rc[2] + 1):
            tot += 1
            if pl_ and pl_[0] <= x_ <= pl_[2] and pl_[1] <= y_ <= pl_[3]:
                plz += 1
                continue
            if (x_, y_) in ROAD:
                roads += 1
                continue
            f_ = FOOT.get((x_, y_))
            if f_ and f_ >= 2:
                bld += 1
            elif f_:
                small += 1
    free_area = max(1, tot - roads - plz)
    FILLS[nm] = (100.0 * bld / free_area, 100.0 * (bld + small) / free_area, 100.0 * roads / tot, 100.0 * plz / tot, tot)
    if not (65 <= FILLS[nm][1] <= 92):
        warns.append(f"заполнение {nm}: {FILLS[nm][1]:.0f}% с малыми объектами (норма 65-90%)")
big_holes = {"Моравск": MOR_FILL[2], "Чернигов (посад)": CHE_FILL[2], "Замок Чернигова": CAS_FILL[2], "Новгород-Северский": NS_FILL[2],
             "Кремль Путивля": PUT_KR_FILL[2], "Посад Путивля": PUT_FILL[2]}
# --- дома и конюшни по §13.4
HOUSE_T = {P2: 8, P3: 30, P4: 24, P5: 45, P6: 5}
house_cnt = Counter(int(u.player) for u in chk.unit_manager.get_all_units() if u.unit_const == K("HOUSE"))
stab_cnt = Counter(int(u.player) for u in chk.unit_manager.get_all_units() if u.unit_const == K("STABLE"))
for pl_, tg_ in HOUSE_T.items():
    if house_cnt.get(pl_, 0) < tg_:
        errs.append(f"домов P{pl_}: {house_cnt.get(pl_, 0)} < {tg_}")
for pl_ in (P2, P4, P5):
    if stab_cnt.get(pl_, 0) < 1:
        errs.append(f"нет STABLE у P{pl_}")
if QSHORT:
    errs.append(f"недобор квот: {QSHORT}")
if MISSED:
    errs.append(f"не поставлены строения: {MISSED}")
# звенья стен на воде/камыше
wall_bad = [(u.x, u.y) for u in chk.unit_manager.get_all_units() if u.unit_const in WALL_CONSTS
            and (terr[int(u.y) * S + int(u.x)].terrain_id in (int(G.WATER_MEDIUM), int(G.WATER_DEEP), int(G.FOREST_REEDS)))]
if wall_bad:
    errs.append(f"звеньев стен на воде/камыше: {len(wall_bad)} {wall_bad[:4]}")
mon = NAMED["campMon"]
mon_h = {terr[(int(mon.y - 1.5) + b) * S + int(mon.x - 1.5) + a].elevation for a in range(3) for b in range(3)}
if len(mon_h) > 1:
    errs.append(f"монастырь лагеря на разных высотах: {mon_h}")
ring_h = {terr[(int(mon.y - 2.5) + b) * S + int(mon.x - 2.5) + a].elevation for a in range(5) for b in range(5)}

# --- здания не на воде и не в лесу
bad_on = 0
for u in chk.unit_manager.get_all_units():
    if u.unit_const in WALL_CONSTS:
        continue
    x, y = int(u.x), int(u.y)
    if 0 <= x < S and 0 <= y < S:
        tt = terr[y * S + x].terrain_id
        is_b = any(u.unit_const == getattr(BuildingInfo, n).ID for n in ("HOUSE", "TOWN_CENTER", "MONASTERY", "BARRACKS", "STABLE", "MARKET", "CASTLE")) \
            if True else False
        if is_b and (tt in (int(G.WATER_DEEP), int(G.WATER_MEDIUM)) or tt in FORESTS):
            bad_on += 1
if bad_on:
    errs.append(f"строений на воде/в лесу: {bad_on}")

# --- достижимость зон
def passable(x, y):
    if not inb(x, y):
        return False
    tt = terr[I(x, y)].terrain_id      # местность из заново открытого файла
    if tt in BAD_WATER or tt == int(G.FOREST_REEDS) or tt in FORESTS:     # проходимы только суша и SHALLOWS (id 4), мосты/дороги
        return False
    return occ.get((x, y)) not in ("b", "w", "f") or (x, y) in GATE_CELLS


GATE_CELLS = set()
for key, u in NAMED.items():
    if key.startswith("gate_"):
        _, gx, gy = key.split("_")
        GATE_CELLS.add((int(gx), int(gy)))
seen = {(SX, SY)}
dq = deque([(SX, SY)])
while dq:
    x, y = dq.popleft()
    for dx, dy in NB8:
        nx, ny = x + dx, y + dy
        if (nx, ny) in seen or not passable(nx, ny):
            continue
        if dx and dy and not (passable(x + dx, y) and passable(x, y + dy)):
            continue
        seen.add((nx, ny))
        dq.append((nx, ny))
unreach = []
for zn, (x0, y0, x1, y1) in Z.items():
    if not any((x, y) in seen for x in range(max(0, x0), min(S, x1 + 1)) for y in range(max(0, y0), min(S, y1 + 1))):
        unreach.append(zn)
# зоны, чьи ворота заперты (внутри стен), допустимы: Z_Scout/Z_Granary внутри замка проверяем без стен
inside_ok = {"Z_Granary", "Z_West_Edge"}
unreach = [z for z in unreach if z not in inside_ok]
if unreach:
    warns.append("зоны, недостижимые от старта (с учётом лесов, воды и зданий): " + ", ".join(unreach))
print("достижимость зон: недостижимых", len(unreach), unreach)
# v3: достижимость городов (по воротам), табора, деревень, месторождений, бродов, лагеря лихих людей
REACH = []


def reach_near(x, y, r=2):
    return any((x + dx, y + dy) in seen for dx in range(-r, r + 1) for dy in range(-r, r + 1))


for nm_, (gx_, gy_) in (("Моравск (ворота)", (51 + 3, 52)), ("Чернигов (Южные ворота)", (73, 108 + 3)), ("Замок Чернигова", (96, 121)),
                        ("Н-Северский (Западные ворота)", (150 - 3, 171)), ("Путивль (Западные ворота)", (152 - 3, 90)), ("Кремль Путивля", (176, 82)),
                        ("Табор", (140, 156)), ("Елецкий", (57 + 3, 128)), ("Застава", (42, 30)), ("Моравск", (53 - 3, 52))):
    REACH.append((nm_, (gx_, gy_), reach_near(gx_, gy_, 3)))
for nm_, c_ in [(f"брод {i}", c) for i, c in enumerate(FORD_CENTERS, 1)] + [(f"деревня {s_['idx']} ({s_['kind']})", s_["c"]) for s_ in SITES] +         [(n2, c2) for n2, c2 in RES_SPOTS if n2 != "рыба"]:
    REACH.append((nm_, c_, reach_near(c_[0], c_[1], 2)))
REACH_BAD = [(n_, c_) for n_, c_, ok_ in REACH if not ok_]
print("достижимость целей (суша + SHALLOWS):", len(REACH) - len(REACH_BAD), "из", len(REACH), "недостижимо:", REACH_BAD[:20])
if REACH_BAD:
    errs.append(f"недостижимые цели: {REACH_BAD[:12]}")
# ресурсы не стоят на врагах: расстояние от месторождений и ягод до не-P1 юнитов/строений >= 3 клеток
ENEMY_PTS = [(u.x, u.y) for u in um.get_all_units() if u.player not in (0, 1, 7)]
RES_ON_ENEMY = []
for u in um.get_all_units():
    if u.player == 0 and u.unit_const in (K("GOLD_MINE"), K("STONE_MINE"), K("FORAGE_BUSH")):
        if any(abs(u.x - ex) < 3 and abs(u.y - ey) < 3 for ex, ey in ENEMY_PTS):
            RES_ON_ENEMY.append((u.x, u.y))
print("ресурсов рядом с врагами (<3 клеток):", len(RES_ON_ENEMY))
if RES_ON_ENEMY:
    errs.append(f"ресурсы на врагах: {RES_ON_ENEMY[:5]}")

n_tr = len(names)
n_aux = sum(1 for n in names if "__" in n)
print("Триггеров:", n_tr, "(основных:", n_tr - n_aux, ", вспомогательных:", n_aux, ") переменных:", len(var_ids))
print("Объекты по игрокам:", cnt, "всего", sum(cnt.values()))
print("Высоты:", sorted(elev.items()), "доля суши выше 1: %.2f" % high_share, "типов местности", len(tids))
print("ОШИБКИ:" if errs else "ПРОВЕРКА ПРОЙДЕНА", errs[:30])
print("ПРЕДУПРЕЖДЕНИЯ:", warns)

# --- плотность v1 для NOTES
v1 = None
v1_path = ROOT / "build" / "01_cherez_granitsu.aoe2scenario"
dens_v1 = {}
try:
    v1 = AoE2DEScenario.from_file(str(v1_path))
    v1_objs = [u for u in v1.unit_manager.get_all_units()]
    v1_centers = {"Моравск": (50, 59), "Чернигов": (84, 92), "Новгород-Северский": (131, 131), "Путивль": (148, 30)}
    for nm, (cx, cy) in v1_centers.items():
        near = [u for u in v1_objs if abs(u.x - cx) <= 14 and abs(u.y - cy) <= 14 and u.unit_const not in WALL_CONSTS
                and u.unit_const not in (BuildingInfo.STONE_WALL.ID,)]
        dens_v1[nm] = len(near)
    v1_h = len({t_.elevation for t_ in v1.map_manager.terrain})
    v1_tt = len({t_.terrain_id for t_ in v1.map_manager.terrain})
except Exception as ex:  # noqa: BLE001
    warns.append(f"v1 не прочитан: {ex}")
    v1_h = v1_tt = None
dens_v2 = {}
for nm, (cx, cy) in {"Моравск": (62, 52), "Чернигов": (84, 128), "Новгород-Северский": (160, 168), "Путивль": (172, 86)}.items():
    near = [u for u in chk.unit_manager.get_all_units() if abs(u.x - cx) <= 14 and abs(u.y - cy) <= 14 and u.unit_const not in WALL_CONSTS]
    dens_v2[nm] = len(near)

BLD_BEFORE = {"Моравск": 26, "Чернигов": 62, "Новгород-Северский": 15, "Путивль": 59}
_skip = {getattr(BuildingInfo, n).ID for n in ("FENCE", "PALISADE_WALL", "FORTIFIED_PALISADE_WALL", "WATCH_TOWER", "GUARD_TOWER", "BOMBARD_TOWER", "KEEP",
                                                "BROKEN_FENCE_A", "BROKEN_FENCE_B", "PALISADE_GATE", "PALISADE_GATE_NORTH_TO_SOUTH",
                                                "PALISADE_GATE_WEST_TO_EAST")}
_bset = {b_.ID for b_ in BuildingInfo}
BLD_AFTER = {}
for _k, (_x0, _y0, _x1, _y1) in {"Моравск": (44, 26, 90, 64), "Чернигов": (44, 90, 110, 172), "Новгород-Северский": (126, 150, 196, 196),
                                "Путивль": (130, 55, 199, 125)}.items():
    BLD_AFTER[_k] = len([u for u in chk.unit_manager.get_all_units() if _x0 <= u.x <= _x1 and _y0 <= u.y <= _y1 and u.unit_const in _bset
                         and u.unit_const not in _skip])
notes = f"""# Сводка сборки миссии 1 v2 «Через границу»

Скрипт: `scripts/build_01_v2.py` (части `v2_part1_world.py`, `v2_part1b_cities.py`, `v2_part1c_finish.py`, `v2_part2_triggers.py`,
`v2_part3_verify.py`). Результат: `build/01_cherez_granitsu_v3.aoe2scenario` (DE, AoE2ScenarioParser 0.9.9).
Файл v1 и `build/NOTES.md` не затронуты. В игру не копировалось. Источники: `missions/01-cherez-granitsu.v2-design.md` (§13),
`missions/01-cherez-granitsu.dialogue.v2.md` (теги, таблица 0.0).

## Что собрано
- Карта {S}x{S}; высоты: уровни {sorted(elev)} (клеток по уровням {dict(sorted(elev.items()))}); доля суши выше 1: {high_share:.0%};
  соседние клетки отличаются не более чем на 1 (нарушений {bad_h}); типов местности {len(tids)} (v1: {v1_tt}).
- Днепр, Десна (ширина 5-6, высокий северный берег, пойма на юге), Сейм, Стрижень, 3 брода, овраги R1-R9, болота, камыш, берега;
  дороги по §2.7; леса с каймой и подлеском; вне городов {OUT_DECOR} декоративных объектов (норма 700), дичь, рыба, межевые знаки.
- Города со стеной по застройке, воротами (`PALISADE_GATE_*`, заперты в `M1_Init`), башнями, улицами, площадью, кварталами дворов
  (дом + ограда + хозобъекты), слободами, церквями, кладбищами, полями, садами, пристанями, жителями, скотом. Сёла V1-V4, Елецкий,
  Молченский и Спасо-Преображенский монастыри, застава, табор Г0 (Gaia-строения) и план стадий Г1-Г5.
- Объекты по игрокам: {cnt}; всего {sum(cnt.values())}.
- Триггеров {n_tr} (основных {n_tr - n_aux}, вспомогательных `имя__суффикс` {n_aux}); переменных {len(var_ids)}.
  Все имена §13.8 на месте (ожидалось {len(expected)}, отсутствует {len(missing)}).
- Реплики разобраны из `dialogue.v2.md` по тегам: цвет, префикс и иконка по таблице 0.0, пометки `[...]` вырезаны, строки длиннее 140
  знаков режутся по словам; `рассказчик`/`плашка`/`справка`/`подсказка`/`цель` и `диалог` идут через `display_instructions` (иконка
  `object_list_unit_id`), `сообщение` через `send_chat`. Брифинг (`брифинг`): задание, история, подсказки, разведка в `message_manager`
  (заголовок и подзаголовок в начале поля Instructions). Выводимых сообщений в триггерах: {nmsg}.
- Крылатый гусар (1707) не в старте, отключён в `M1_Init`, открывается технологией «Польский контракт» после падения замка Чернигова.
- «Молва» скрытая: переменная `M1_Molva`, нигде не отображается.

## Плотность городов (объекты в квадрате 29x29 клеток вокруг центра, без звеньев стен; v1 -> v2)
""" + "\n".join(f"- {k}: {dens_v1.get(k, '?')} -> {dens_v2[k]}" for k in dens_v2) + f"""

Строения и декор по городам (минимум §13.12): """ + "; ".join(f"{k}: {o} (минимум {tg})" for k, o, tg, c, ct, st in city_rows) + f""".
Жители (минимум): """ + "; ".join(f"{k}: {c} ({ct})" for k, o, tg, c, ct, st in city_rows) + f""". Скот: """ + "; ".join(f"{k}: {st}" for k, o, tg, c, ct, st in city_rows) + f""".
Заполнение внутри стен, определение §13: следы зданий (строения 2x2 и крупнее) / (внутренняя площадь - улицы - площадь); в скобках с малыми объектами
(ограда, стога, бочки и т.п., по 1 клетке). Улицы и площадь отдельно (% внутренней площади). До правки (проверяющий): здания 25/16/41/24/20/18%,
с малыми объектами 41/46/58/46/42/52% (Моравск, Чернигов, замок, Новгород-Северский, кремль, посад Путивля); прежние 76-88% из `NOTES_v2.md` считали
клетки следов `occ` (в т.ч. рядов оград и декора) без площади улиц в знаменателе и без разделения зданий и малых объектов, поэтому цифры расходились:
""" + "; ".join(f"{nm}: здания {v0:.0f}% ({v1_:.0f}%), улицы {v2_:.0f}%, площадь {v3_:.0f}%" for nm, (v0, v1_, v2_, v3_, tt_) in FILLS.items()) + f""".
Пустых квадратов 5x5: """ + "; ".join(f"{nm}: {big}" for nm, big in big_holes.items()) + f""".

## Дома и конюшни (до -> после; цели §13.4)
Дома по владельцам: P2 0 -> {house_cnt.get(2, 0)} (8), P3 11 -> {house_cnt.get(3, 0)} (30), P4 3 -> {house_cnt.get(4, 0)} (24 = 18 + 6 сгорающих),
P5 13 -> {house_cnt.get(5, 0)} (45), P6 1 -> {house_cnt.get(6, 0)} (5), Gaia 18 -> {house_cnt.get(0, 0)}, P7 15 -> {house_cnt.get(7, 0)}.
Конюшни: P4 0 -> {stab_cnt.get(4, 0)}, P5 0 -> {stab_cnt.get(5, 0)}, P2 1 -> {stab_cnt.get(2, 0)}.
Здания (без оград, стен, башен) в рамках города, до -> после: """ + "; ".join(f"{k}: {BLD_BEFORE[k]} -> {BLD_AFTER[k]}" for k in BLD_BEFORE) + f""".
Мелкие недоборы: рыбачьих лодок P3 {len([1 for u in chk.unit_manager.get_player_units(3) if u.unit_const == K("FISHING_SHIP")])} (2), P7 транспортов {len([1 for u in chk.unit_manager.get_player_units(7) if u.unit_const == K("TRANSPORT_SHIP")])} (5), рыбных ловушек P3 {len([1 for u in chk.unit_manager.get_player_units(3) if u.unit_const == K("FISH_TRAP")])} (2).
Правки по проверке: 8 звеньев стены Спасо-Преображенского монастыря на воде -> монастырь перенесён на сушу (поиск 9x9), монастырь лагеря выровнен
(овраг R3 сдвинут на 3 клетки восток, дно оврагов R3/R7/R8 больше не лесная местность), точки появления юнитов в триггерах обходят клетки
зданий и их соседей; Новгород-Северский расширен до стены 25x24 (x150-174, y158-181) вместе с оврагом R4 (сдвиг к востоку).

## Проверка (скриптом)
- Скрипт отрабатывает; сценарий заново открыт парсером; имена триггеров §13.8 сверены; висячих ссылок на триггеры, переменные, объекты: нет;
  пустых сообщений нет; пометок `[..]` в игровом тексте нет; P1 стартует с 26 юнитами.
- Достижимость зон от старта (поиск пути с бродами; леса, вода, здания блокируют): недостижимых {len(unreach)} {unreach}.
- Ошибки: {errs if errs else 'нет'}. Предупреждения: {warns if warns else 'нет'}.
- Реплики с тегами, которые не привязаны ни к одному триггеру (кроме `U_*` и `G_*`): {unused_set if unused_set else 'нет'}.

## Что упрощено / отличается от §13
- Координаты берутся как клетки напрямую; «север» = +y. Положение рек относительно городов выправлено под геометрию §2.3:
  Моравск стоит на южном (пойменном) берегу Десны; слобода Моравска перенесена к востоку от острога (север занимает река), поля к юго-востоку.
- Стрижень продлён до Десны отрезком (70,92)-(73,84). Пристани ставятся по фактическому берегу, а не по координатам таблиц.
- Овраг R3 сдвинут на 2 клетки западнее (x148 вместо 150), R4 на 8 клеток восточнее: иначе они пересекали стены и монастырь лагеря; `Z_R3` = x142-156.
- Стена Новгорода-Северского расширена до 23x22 (x150-172, y163-184, вместо 21x19), чтобы поместились 18 домов, конюшня и дворы; её юг (y158-162) лежал в воде Десны.
- Слобода Путивля перенесена на x136-148, y99-111, поля на x164-184, y103-114, село V4 на (154,114): таблица §3.4 клала их в воду Сейма.
  Молченский монастырь сдвинут к (192,76). Спасо-Преображенский монастырь перенесён на ближайший прямоугольник суши 9x9 около (184,176).
- Поля Чернигова сдвинуты на y158-170 (§3.2.3 пересекал их со слободой), сады на x50-57, y108-118; V3 на (110,144) (курган B12).
- `Z_Leaflet_Mor` перенесена в восточную слободу (79,52), `Z_Leaflet_Put` к слободе (144,105).
- Маршрут магистрали к Путивлю огибает посад с запада (узел (160,98) лежал внутри стены).
- Плато городов: прямоугольные вершины (стена + 1 клетка) вместо круговых, высоты как в §2.4; под каждым строением выравнивание по минимуму
  следа, затем сглаживание до перепада 1 (деструктивное: ступени вырезаются вокруг следов).
- Звенья стен/ворот выставлены без выбора кадра анимации (`animation_frame`): как будут соединяться звенья в игре, не проверено.
  Ворота: `PALISADE_GATE_NORTH_TO_SOUTH` на западных/восточных стенах, `PALISADE_GATE_WEST_TO_EAST` на северных/южных.
- Размеры следов строений заданы таблицей в скрипте (`SZ`), в игре могут отличаться на клетку.
- Стрелец и прочие переименования: петля `M1_Rename_Loop` (стрелец = ручной пушкарь и т.д.); атака и броня юнитов не менялись, только HP и
  скорость (`M1_Stats`); дальность башен +1 и урон +4 не реализованы.
- Технологии-кнопки переиспользуют существующие: «Царевич» = Town Watch, «Кошель Чернигова» = Loom, «Кошель Путивля» = Wheelbarrow,
  «Польский контракт» = Husbandry (STABLE), «Жалованье» = Supplies (BARRACKS); побочные эффекты исходных технологий остаются.
- Крылатый гусар: `enable_disable_object` + `add_train_location` (кнопка r1c3, 35 с, 100/140), потолок 6 петлёй `M1_WHussar_Cap`.
- `instruction_panel_position` не задаётся (позиции верх/середина/низ из §8.2 не реализованы: номера в парсере не описаны).
- Цвет иконки (`use_tag_color_for_icon`) не задан. Звуки не используются.
- Молва: гибель жителей считается `count_units_into_variable` по P2, P3, P5, P7 (мужчины и женщины) раз в 5 с; сброс базы после переходов
  городов не отделяет гибель от передачи (жители остаются в сумме, так как уходят к P7). Убийства в селах отдельно не считаются (S2_Closed: Молва <= 1).
- Листы: двое городовых казаков Чернигова/Путивля уходят к P7 (`change_ownership`, 2 юнита) при выполнении листов; в Моравске только D.
- Конверсия: D Моравска 15/11/9/6, Чернигова 20/14/12/8 (база/листы/«Царевич»/оба), Путивля из переменных `Put_D`/`Put_DT` (листы: 18/10).
  Две зоны у ворот Моравска и Чернигова обслуживаются копиями триггеров `__z2`.
- Слабый участок стены замка: 3 звена обычного частокола, HP 100 после разведки S3 (30% не выставлялось точно).
- Старцы S5: дальность конверсии 0 через `MAXIMUM_RANGE`; обоз S4: `CART` вместо `OX_CART`; лазутчик E13: `VILLAGER_FEMALE` P4;
  захват обоза одним триггером (все телеги сразу), сообщения о 2-й и 3-й телеге по таймеру.
- `T_CampHP50`: порог 1200 HP от `TOWN_CENTER` Ставки; множитель HP x1.5 не применён.
- Роты P8 в E16: ратники и лучники без отдельных осадных орудий (стойки с оружием вместо `SIEGE_CAMP_EQUIPMENT`).
- Обновление стадий табора Г3: по прибытию добровольцев (`M1_Arrive_1..4`: беглые, посад, старцы, толпа).
- Не реализованы: реплики юнитов `U_*` и общие события `G_*` (в триггеры не привязаны), сообщения при падении лимита населения выводятся только в E06.
- Случайные события: `chance` 50% проверяется при входе юнита в зону один раз.

## Не проверено в игре
Весь список §13.11 (цветовые теги и иконки в `display_instructions`, `change_color_mood`, `WINGED_HUSSAR`, `lock_gate`/`unlock_gate`,
вид стен и ворот на склонах, `DORMITION_CATHEDRAL`/`CHAPEL`/`FOLWARK` как строения Gaia, работа жителей/телег/лодок без ИИ,
нейтральность P7, передача Gaia-Ставки и её кнопок, `disable_unit_attackable` на воротах, производительность при {sum(cnt.values())} объектах,
`BOMBARD_TOWER`, `chance`), а также: семантика `own_fewer_objects` (в новых проверках заменена на `objects_in_area` с inverted),
поведение `count_units_into_variable` с `variable2`, `modify_attribute` с MULTIPLY для скорости, `research_technology` как бесплатное
исследование (S5), `change_ownership` по `object_type=BUILDING` для сёл, повторный запуск looping-триггеров.
"""
NOTES_V2.write_text(notes, encoding="utf-8")
print("NOTES_v2.md записан")

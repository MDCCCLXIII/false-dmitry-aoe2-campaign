# Часть 2: реплики, триггеры §13.8, цели. Общее пространство имён.
ALL = (0, 0, S - 1, S - 1)


def R(cx, cy, r):
    return (max(0, cx - r), max(0, cy - r), min(S - 1, cx + r), min(S - 1, cy + r))


# ---------------------------------------------------------------- зоны §13.5 (с поправками, см. NOTES_v2.md)
Z = {
    "Z_Border": (33, 0, 36, 40), "Z_Zastava": R(42, 30, 12), "Z_Mor_Arrive": R(62, 52, 10),
    "Z_Conv_Mor": (49, 50, 53, 54), "Z_Conv_Mor2": (60, 61, 64, 65), "Z_Leaflet_Mor": R(79, 52, 3),
    "Z_Ford_Mor": R(71, 80, 8), "Z_Che_Approach": R(73, 111, 18), "Z_Conv_Che": (71, 105, 75, 109),
    "Z_Conv_Che2": (53, 124, 57, 128), "Z_Leaflet_Che": R(76, 150, 3), "Z_Castle_Gate": R(89, 124, 8),
    "Z_Castle_Weak": R(89, 119, 6), "Z_Granary": R(92, 124, 2),
    "Z_Scout_1": R(104, 136, 3), "Z_Scout_2": R(106, 124, 3), "Z_Scout_3": R(90, 110, 3),
    "Z_Yelets": R(57, 128, 6), "Z_Ambush": R(120, 146, 8), "Z_NS_Approach": R(160, 168, 40),
    "Z_Camp": (134, 150, 146, 162), "Z_R3": (142, 146, 156, 180), "Z_Conv_Put": (146, 88, 150, 92),
    "Z_Leaflet_Put": R(144, 105, 3), "Z_Put_Near": R(152, 90, 12), "Z_Courier_End": R(170, 104, 4),
    "Z_Ford_North": R(176, 161, 5), "Z_North": (0, 176, 199, 199), "Z_West_Edge": (0, 0, 3, 199),
}
for i, vn in enumerate(("V1", "V2", "V3", "V4"), 1):
    cp = NAMED[f"church_pos_{vn}"]
    Z[f"Z_Village_{i}"] = R(cp[0], cp[1], 3)
Z_MOR, Z_CHE = R(62, 52, 40), R(74, 126, 40)
A_MOR = (30, 20, 100, 90)           # все объекты Моравска и слобод
A_CHE = (44, 90, 110, 175)          # посад
A_CAS = (86, 112, 106, 130)
A_PUT = (130, 55, 199, 125)
CHE_AREA_V = (58, 110, 90, 160)

# ---------------------------------------------------------------- реплики (§13.9)
SPK = {
    "Царевич Димитрий": ("BLUE", "Царевич Димитрий:", "ROLAND"),
    "Пан Мнишек": ("PURPLE", "Пан Мнишек:", "KING"),
    "Ротмистр": ("PURPLE", "Ротмистр:", "HUSSAR"),
    "Чернец": ("AQUA", "Чернец:", "MONK"),
    "Старец": ("YELLOW", "Старец:", "MONK"),
    "Атаман Белешко": ("ORANGE", "Атаман Белешко:", "CAVALRY_ARCHER"),
    "Перебежчик": ("ORANGE", "Перебежчик:", "CAVALRY_ARCHER"),
    "Воевода князь Татев": ("RED", "Воевода князь Татев:", "THEODORIC_THE_GOTH"),
    "Басманов со стены": ("RED", "Басманов со стены:", "ALEXANDER_NEVSKI"),
    "Воевода Салтыков": ("RED", "Воевода Салтыков:", "VILLAGER_MALE"),
    "Староста": ("YELLOW", "Староста:", "VILLAGER_MALE"),
    "Князь Рубец-Масальский": ("YELLOW", "Князь Рубец-Масальский:", "VILLAGER_MALE"),
    "Дьяк Сутупов": ("YELLOW", "Дьяк Сутупов:", "VILLAGER_MALE"),
    "Дозорные": ("RED", "Дозорные:", "SCOUT_CAVALRY"),
}
TAG_RE = re.compile(r"^- \[([A-Za-z0-9_]+):(сообщение|диалог|подсказка|цель|рассказчик|плашка|справка|брифинг|реплика)\]\s*(.*)$")


def clean(text):
    text = re.sub(r"\s*\[[^\]]*\]", "", text)         # [ПРОВЕРИТЬ ...], [ИСТОРИК ...] и любые пометки
    return re.sub(r"\s+", " ", text).strip()


class Line:
    def __init__(self, trig, typ, cond, speaker, text):
        self.trig, self.typ, self.cond, self.speaker, self.text = trig, typ, cond or "", speaker, text
        self.used = False
        m = re.match(r"^\+?(\d+)\s*с", self.cond)
        self.delay = int(m.group(1)) if m else None
        self.variant = "hi" if "Молва ≥ 4" in self.cond else ("lo" if "Молва < 4" in self.cond else None)
        self.need_rubets = "Рубец" in self.cond
        self.need_sutupov = "Сутупов" in self.cond


def parse_dialogue():
    d = {}
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
        if typ == "диалог":
            if ": " not in rest:
                raise ValueError(f"нет говорящего: {raw[:80]}")
            speaker, rest = rest.split(": ", 1)
            if speaker not in SPK:
                raise ValueError(f"говорящий «{speaker}» не из таблицы 0.0")
        d.setdefault((trig, typ), []).append(Line(trig, typ, cond, speaker, rest))
    return d


LINES = parse_dialogue()
MISSING_TAGS = []


def L(trig, typ, cond=None, idx=None, opt=False):
    lst = LINES.get((trig, typ))
    if not lst:
        if not opt:
            MISSING_TAGS.append(f"{trig}:{typ}")
        return []
    if cond is not None:
        lst = [x for x in lst if x.cond and cond in x.cond]
    if idx is not None:
        lst = [lst[idx]]
    for x in lst:
        x.used = True
    return lst


def split140(text):
    if len(text) <= 140:
        return [text]
    out, cur = [], ""
    for w in text.split(" "):
        if len(cur) + len(w) + 1 > 138 and cur:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


FIRST_MN = [True]


def render(line):
    """-> [(текст, иконка_id|None, это_чат)]"""
    typ = line.typ
    if typ == "сообщение":
        return [(c, None, True) for c in split140(line.text)]
    if typ == "диалог":
        tag, pref, icon = SPK[line.speaker]
        if line.speaker == "Пан Мнишек" and FIRST_MN[0]:
            pref = "Пан Юрий Мнишек, воевода сандомирский:"
            FIRST_MN[0] = False
        iid = K(icon)
        body = f"{pref} {line.text}"
        return [(f"<{tag}>{c}", iid, False) for c in split140(body)]
    if typ == "рассказчик":
        body = f"Юрий Мнишек вспоминает: «{line.text}»"
        return [(f"<GREY>{c}", None, False) for c in split140(body)]
    if typ == "плашка":
        return [(f"<YELLOW>{c}", None, False) for c in split140(line.text)]
    if typ == "справка":
        return [(f"<GREY>{c}", None, False) for c in split140("Историческая справка: " + line.text)]
    if typ == "подсказка":
        return [(f"<GREEN>{c}", None, False) for c in split140("Подсказка: " + line.text)]
    if typ == "цель":
        return [(f"<YELLOW>{c}", None, False) for c in split140(line.text)]
    raise ValueError(typ)


def dur(text):
    return int(min(14, max(5, 4 + len(text) / 14.0)))


# ---------------------------------------------------------------- триггеры: помощники
VARS, TRIG = {}, {}


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
    return trig(f"{parent}__{suffix}", **kw)


def c_flag(t, name, val=1, cmp=Comparison.EQUAL):
    t.new_condition.variable_value(quantity=val, variable=v(name), comparison=cmp)


def c_clock(t, secs):
    t.new_condition.variable_value(quantity=int(secs), variable=v("M1_Clock"), comparison=Comparison.LARGER_OR_EQUAL)


def c_dl(t, name):
    t.new_condition.compare_variables(variable=v("M1_Clock"), comparison=Comparison.LARGER_OR_EQUAL, variable2=v(name))


def e_set(t, name, val=1):
    t.new_effect.change_variable(quantity=val, operation=Operation.SET, variable=v(name))


def e_add(t, name, val=1):
    t.new_effect.change_variable(quantity=abs(val), operation=Operation.ADD if val >= 0 else Operation.SUBTRACT, variable=v(name))


def e_dl(t, name, delay):
    t.new_effect.modify_variable_by_variable(variable=v(name), operation=Operation.SET, variable2=v("M1_Clock"))
    t.new_effect.change_variable(quantity=int(delay), operation=Operation.ADD, variable=v(name))


def c_in(t, player, const, area, qty=1, inverted=0, **kw):
    t.new_condition.objects_in_area(quantity=qty, object_list=const, source_player=player, area_x1=area[0], area_y1=area[1],
                                    area_x2=area[2], area_y2=area[3], inverted=inverted, **kw)


def c_mil(t, player, area, qty=1, inverted=0):
    c_in(t, player, -1, area, qty, inverted, object_type=int(ObjectType.MILITARY))


def c_none(t, player, const, area=ALL):
    c_in(t, player, const, area, 1, 1)


def c_dm(t, zone, inverted=0):
    a = Z[zone] if isinstance(zone, str) else zone
    t.new_condition.bring_object_to_area(unit_object=dmitry.reference_id, area_x1=a[0], area_y1=a[1], area_x2=a[2], area_y2=a[3],
                                         inverted=inverted)


def molva_cmp(t, lo=None, hi=None):
    if lo is not None:
        c_flag(t, "M1_Molva", lo, Comparison.LARGER_OR_EQUAL)
    if hi is not None:
        c_flag(t, "M1_Molva", hi, Comparison.LESS_OR_EQUAL)


def effect_for(t, text, icon, chat):
    assert text.strip(), "пустая реплика"
    if chat:
        t.new_effect.send_chat(source_player=P1, message=text)
    else:
        kw = {}
        if icon:
            kw["object_list_unit_id"] = icon
        t.new_effect.display_instructions(source_player=P1, message=text, display_time=dur(text), **kw)


SAYK = {}


def say(t, lines, start=0):
    """Вывод реплик: первая сразу (если нет задержки и вариантов), остальные цепочкой вспомогательных триггеров."""
    if isinstance(lines, Line):
        lines = [lines]
    cum = start
    for ln in lines:
        items = render(ln)
        delay = ln.delay if ln.delay is not None else None
        if delay is not None:
            cum = max(cum, delay)
        for (text, icon, chat) in items:
            if cum == 0 and ln.variant is None and not ln.need_rubets and not ln.need_sutupov:
                effect_for(t, text, icon, chat)
            else:
                SAYK[t.name] = SAYK.get(t.name, 0) + 1
                a = aux(t.name, f"s{SAYK[t.name]}", enabled=False)
                a.new_condition.timer(timer=max(1, int(cum)))
                if ln.variant == "hi":
                    molva_cmp(a, lo=4)
                elif ln.variant == "lo":
                    molva_cmp(a, hi=3)
                if ln.need_rubets:
                    c_flag(a, "M1_RubetsDead", 0)
                if ln.need_sutupov:
                    c_flag(a, "M1_SutupovDead", 0)
                effect_for(a, text, icon, chat)
                t.new_effect.activate_trigger(trigger_id=a.trigger_id)
            if not chat:
                cum += dur(text) + 1
            else:
                cum += 2
    return cum


def Lsay(t, trig_name, types=("плашка", "справка", "рассказчик", "диалог", "сообщение", "подсказка", "цель"), start=0, opt=False):
    ls = []
    for ty in types:
        ls += L(trig_name, ty, opt=opt)
    say(t, ls, start)


def cam(t, xy):
    t.new_effect.change_view(quantity=1, source_player=P1, location_x=xy[0], location_y=xy[1])


def used_spots():
    return set()


USED = set()


def spots(cx, cy, n, r0=0, free_only=True):
    out, r = [], r0
    while len(out) < n and r < 40:
        ring = [(cx + dx, cy + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
        rng.shuffle(ring)
        for c in ring:
            if len(out) >= n:
                break
            if not inb(*c, 1) or c in USED:
                continue
            tt = T[I(*c)]
            if tt in WATER or tt in FORESTS or occ.get(c) in ("b", "w", "f", "u", "p"):
                continue
            if any(occ.get((c[0] + a, c[1] + b)) == "b" for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            USED.add(c)
            out.append(c)
        r += 1
    return out


def create(t, player, const, n, center, r0=0):
    for (x, y) in spots(center[0], center[1], n, r0):
        t.new_effect.create_object(object_list_unit_id=const, source_player=player, location_x=x, location_y=y)


def create_cells(t, player, const, cells):
    for (x, y) in cells:
        t.new_effect.create_object(object_list_unit_id=const, source_player=player, location_x=x, location_y=y)


def transfer(t, src, area, target=P1, **kw):
    t.new_effect.change_ownership(source_player=src, target_player=target, area_x1=area[0], area_y1=area[1], area_x2=area[2],
                                  area_y2=area[3], flash_object=1, **kw)


def villagers_to_p7(t, src, area):
    for c in (VILL_M, VILL_F):
        t.new_effect.change_ownership(object_list_unit_id=c, source_player=src, target_player=P7, area_x1=area[0], area_y1=area[1],
                                      area_x2=area[2], area_y2=area[3])


def heal_all(t):
    t.new_effect.heal_object(quantity=5000, source_player=P1, area_x1=0, area_y1=0, area_x2=S - 1, area_y2=S - 1)


def give(t, food=0, wood=0, gold=0, stone=0):
    for q, a in ((food, Attribute.FOOD_STORAGE), (wood, Attribute.WOOD_STORAGE), (gold, Attribute.GOLD_STORAGE),
                 (stone, Attribute.STONE_STORAGE)):
        if q:
            t.new_effect.modify_resource(quantity=q, tribute_list=a, source_player=P1, operation=Operation.ADD)


def flag_mark(t, xy, temp=False):
    t.new_effect.create_object(object_list_unit_id=K("FLAG_B") if temp else K("FLAG_A"), source_player=P1, location_x=xy[0], location_y=xy[1])


def rename(t, player, const, text, area=ALL):
    t.new_effect.change_object_name(object_list_unit_id=const, source_player=player, message=text, area_x1=area[0], area_y1=area[1],
                                    area_x2=area[2], area_y2=area[3])


def ids(units):
    return [u.reference_id for u in units]


def mood(t, m, secs=3):
    t.new_effect.change_color_mood(quantity=secs, color_mood=int(m))


def los(t, delta, players=range(1, 7)):
    for p in players:
        t.new_effect.modify_attribute(source_player=p, object_list_unit_id=-1, object_type=None, object_attributes=ObjectAttribute.LINE_OF_SIGHT,
                                      operation=Operation.ADD, quantity=delta) if False else None
    for c in (HUSSAR_, KNIGHT_, CAVARCH_, MAA_, ARCHER_, HC_, SPEAR_, MONK_, SCOUT_):
        for p in players:
            t.new_effect.modify_attribute(source_player=p, object_list_unit_id=c, object_attributes=ObjectAttribute.LINE_OF_SIGHT,
                                          operation=Operation.ADD, quantity=delta)


def speed_mul(t, f, players=(1, 6)):
    for c in (HUSSAR_, KNIGHT_, CAVARCH_, MAA_, ARCHER_, HC_, SPEAR_):
        for p in players:
            t.new_effect.modify_attribute(source_player=p, object_list_unit_id=c, object_attributes=ObjectAttribute.MOVEMENT_SPEED,
                                          operation=Operation.MULTIPLY, quantity=f)


def objective(name, text, order, enabled=False):
    return trig(name, enabled=enabled, display_as_objective=True, description=text, short_description=text, description_order=order)


def after(parent, name, flag=None, secs=None, dlvar=None, enabled=True, **kw):
    return trig(name, enabled=enabled, **kw)


def volunteer_variants(name, cond_fn, base_maa, base_arch, area_center, extra_fn=None, lines=None, half=False):
    """Добровольцы с коэффициентом Молвы: >=4: 100%, 2-3: 75%, 0-1: 50% (округление вверх)."""
    out = []
    for suffix, (lo, hi), coef in (("", (4, None), 1.0), ("m23", (2, 3), 0.75), ("m01", (0, 1), 0.5)):
        t = trig(name) if suffix == "" else aux(name, suffix)
        cond_fn(t)
        molva_cmp(t, lo=lo, hi=hi)
        k = 0.5 if half else 1.0
        nm, na = int(math.ceil(base_maa * coef * k)), int(math.ceil(base_arch * coef * k))
        create(t, P1, MAA_, nm, area_center)
        create(t, P1, ARCHER_, na, area_center, 1)
        if extra_fn:
            extra_fn(t)
        if lines:
            say(t, lines)
        out.append(t)
    return out


# ================================================================ 1. ИНИЦИАЛИЗАЦИЯ
# дипломатия на этапе сборки
pm.active_players = 8
for pid in range(1, 9):
    p = pm.players[pid]
    p.starting_age = StartingAge.CASTLE_AGE
    p.civilization = Civilization.POLES if pid in (1, 8) else Civilization.SLAVS
    p.population_cap = 100 if pid == 1 else (50 if pid == 8 else 200)
    p.food = p.wood = p.gold = p.stone = 0
p1 = pm.players[P1]
p1.food, p1.wood, p1.gold, p1.stone = 800, 600, 500, 200
for pid in (P2, P3, P4, P5, P6):
    pm.players[pid].set_player_diplomacy(P1, DiplomacyState.ENEMY)
    pm.players[P1].set_player_diplomacy(pid, DiplomacyState.ENEMY)
    for q in (P2, P3, P4, P5, P6):
        if q != pid:
            pm.players[pid].set_player_diplomacy(q, DiplomacyState.ALLY)
    pm.players[pid].set_player_diplomacy(P7, DiplomacyState.NEUTRAL)
    pm.players[P7].set_player_diplomacy(pid, DiplomacyState.NEUTRAL)
    pm.players[pid].set_player_diplomacy(P8, DiplomacyState.NEUTRAL)
    pm.players[P8].set_player_diplomacy(pid, DiplomacyState.NEUTRAL)
pm.players[P1].set_player_diplomacy(P7, DiplomacyState.NEUTRAL)
pm.players[P7].set_player_diplomacy(P1, DiplomacyState.NEUTRAL)
pm.players[P1].set_player_diplomacy(P8, DiplomacyState.ALLY)
pm.players[P8].set_player_diplomacy(P1, DiplomacyState.ALLY)
opt.victory_condition = VictoryCondition.CUSTOM
DISABLED = [TechInfo.IMPERIAL_AGE, TechInfo.MASONRY, TechInfo.ARCHITECTURE, TechInfo.BALLISTICS, TechInfo.TREADMILL_CRANE,
            TechInfo.HEATED_SHOT, TechInfo.MURDER_HOLES, TechInfo.CHEMISTRY, TechInfo.SIEGE_ENGINEERS, TechInfo.ARROWSLITS,
            TechInfo.HOARDINGS, TechInfo.SAPPERS, TechInfo.CARAVAN, TechInfo.COINAGE, TechInfo.BANKING, TechInfo.GUILDS,
            TechInfo.CARTOGRAPHY]
p1.disabled_techs = [t.ID for t in DISABLED]
p1.disabled_buildings = [BuildingInfo.UNIVERSITY.ID, BuildingInfo.MARKET.ID]
WH = K("WINGED_HUSSAR")

GARR = {P2: [], P3: [], P4: [], P5: [], P6: []}
for pl, gd in ((P2, mor_gar), (P3, che_gar), (P6, cas_gar), (P4, ns_gar), (P5, put_gar)):
    for lst in gd.values():
        GARR[pl] += ids(lst)
GARR[P4] += ids(PATROL_A) + ids(PATROL_B)
GARR[P2] += ids(ZAST_SPEAR) + ids(ZAST_SCOUT)
ALL_GATES = [u.reference_id for pl in (P2, P3, P4, P5, P6) for u in GATES[pl]]
TECH_J = {"tsarevich": TechInfo.TOWN_WATCH.ID, "bribe_c": TechInfo.LOOM.ID, "bribe_p": TechInfo.WHEELBARROW.ID,
          "contract": TechInfo.HUSBANDRY.ID, "pay": TechInfo.SUPPLIES.ID}
TSAR, BRIBE_C, BRIBE_P, CONTRACT, PAYTECH = (TECH_J[k] for k in ("tsarevich", "bribe_c", "bribe_p", "contract", "pay"))

t = trig("M1_Init")
init = t
mood(t, ColorMood.AUTUMN, 1)
for pl, lst in GARR.items():
    if lst:
        t.new_effect.change_object_stance(source_player=pl, attack_stance=AttackStance.STAND_GROUND, selected_object_ids=lst)
t.new_effect.lock_gate(selected_object_ids=ALL_GATES)
t.new_effect.change_object_name(source_player=P1, message="Царевич Димитрий", selected_object_ids=[dmitry.reference_id])
t.new_effect.modify_object_attribute(source_player=P1, object_attributes=ObjectAttribute.HIT_POINTS, selected_object_ids=[dmitry.reference_id],
                                     operation=Operation.SET, quantity=300)
t.new_effect.change_object_name(source_player=P6, message="Князь И. А. Татев", selected_object_ids=[TATEV.reference_id])
t.new_effect.modify_object_attribute(source_player=P6, object_attributes=ObjectAttribute.HIT_POINTS, selected_object_ids=[TATEV.reference_id],
                                     operation=Operation.SET, quantity=150)
t.new_effect.change_object_stance(source_player=P6, attack_stance=AttackStance.NO_ATTACK_STANCE, selected_object_ids=[TATEV.reference_id])
t.new_effect.change_object_name(source_player=P4, message="Пётр Басманов", selected_object_ids=[BASMANOV.reference_id])
t.new_effect.disable_unit_attackable(source_player=P4, selected_object_ids=[BASMANOV.reference_id])
for u, nm in zip(MOR_VOEV, ("Воевода Б. Лодыгин", "Воевода М. Толочанов")):
    t.new_effect.change_object_name(source_player=P2, message=nm, selected_object_ids=[u.reference_id])
    t.new_effect.change_object_stance(source_player=P2, attack_stance=AttackStance.NO_ATTACK_STANCE, selected_object_ids=[u.reference_id])
for u, nm in zip(CAS_PEOPLE, ("Князь Ф. Шаховской", "Воронцов-Вельяминов")):
    t.new_effect.change_object_name(source_player=P6, message=nm, selected_object_ids=[u.reference_id])
    t.new_effect.change_object_stance(source_player=P6, attack_stance=AttackStance.NO_ATTACK_STANCE, selected_object_ids=[u.reference_id])
for u, nm in ((SALT, "Воевода М. Г. Салтыков"), (RUBEC, "Князь В. М. Рубец-Масальский"), (SUTUP, "Дьяк Богдан Сутупов")):
    t.new_effect.change_object_name(source_player=P5, message=nm, selected_object_ids=[u.reference_id])
    t.new_effect.modify_object_attribute(source_player=P5, object_attributes=ObjectAttribute.HIT_POINTS, selected_object_ids=[u.reference_id],
                                         operation=Operation.SET, quantity=60)
    t.new_effect.change_object_stance(source_player=P5, attack_stance=AttackStance.NO_ATTACK_STANCE, selected_object_ids=[u.reference_id])
for lst, dest in ((PATROL_A, (150, 110)), (PATROL_B, (158, 84))):
    t.new_effect.patrol(source_player=P4, location_x=dest[0], location_y=dest[1], selected_object_ids=ids(lst))
t.new_effect.patrol(source_player=P2, location_x=62, location_y=64, selected_object_ids=ids(mor_gar[KNIGHT_]))
# названия технологий-кнопок и обучение (переиспользование существующих технологий, см. NOTES_v2.md)
TJSON = {
    "tsarevich": ("Царевич", "Слово чернецов доходит дальше: чтение грамот у ворот короче. Только для чернецов у ворот.", 400, 0, 300, 30, TSAR, ButtonLocation.r2c3, TC_),
    "bribe_c": ("Кошель для Чернигова", "600 золота посадским за присягу. Быстрее слова чернеца, но казна уйдёт.", 0, 0, 600, 10, BRIBE_C, ButtonLocation.r2c4, TC_),
    "bribe_p": ("Кошель для Путивля", "900 золота путивльским людям за присягу.", 0, 0, 900, 10, BRIBE_P, ButtonLocation.r2c5, TC_),
    "contract": ("Польский контракт", "Хоругвь из Самбора: открывает найм крылатых гусар, не более шести.", 200, 0, 400, 60, CONTRACT, ButtonLocation.r2c1, STAB_),
    "pay": ("Жалованье ротам", "Выплата жалованья польским ротам, чтобы они не ушли из табора.", 0, 0, 400, 10, PAYTECH, ButtonLocation.r2c1, BARR_),
}
for key, (nm, desc, f, w, g, secs, tid, loc, where) in TJSON.items():
    t.new_effect.change_technology_name(source_player=P1, technology=tid, message=nm)
    t.new_effect.change_technology_description(source_player=P1, technology=tid, message=desc)
    t.new_effect.change_technology_cost(source_player=P1, technology=tid, resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=f,
                                        resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=w, resource_3=Attribute.GOLD_STORAGE,
                                        resource_3_quantity=g)
    t.new_effect.change_technology_research_time(source_player=P1, technology=tid, quantity=secs)
    t.new_effect.change_technology_location(source_player=P1, technology=tid, object_list_unit_id_2=where, button_location=loc.value)
    t.new_effect.enable_disable_technology(source_player=P1, technology=tid, enabled=0)
t.new_effect.add_train_location(object_list_unit_id=HUSSAR_, source_player=P1, object_list_unit_id_2=STAB_, button_location=ButtonLocation.r1c1.value, train_time=25)
t.new_effect.change_object_cost(object_list_unit_id=HUSSAR_, source_player=P1, resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=60,
                                resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0, resource_3=Attribute.GOLD_STORAGE, resource_3_quantity=70)
t.new_effect.enable_disable_object(object_list_unit_id=WH, source_player=P1, enabled=0)
flag_mark(t, (62, 52))
e_set(t, "M1_Molva", 2)
e_set(t, "Put_D", 25)
e_set(t, "Put_DT", 15)
e_set(t, "M1_BaseReady", 0)
Lsay(t, "M1_Init", types=("рассказчик", "диалог", "цель", "подсказка"), start=48)

t = trig("M1_Clock", looping=True)
t.new_condition.timer(timer=1)
t.new_effect.change_variable(quantity=1, operation=Operation.ADD, variable=v("M1_Clock"))

t = trig("M1_Names")
for pid, nm in ((1, "Царевич Димитрий"), (2, "Моравск"), (3, "Чернигов (посад)"), (4, "Новгород-Северский"), (5, "Путивль"),
                (6, "Черниговский замок"), (7, "Северские сёла"), (8, "Роты на приступе")):
    t.new_effect.change_player_name(source_player=pid, message=nm)

STATS = [  # (игрок(и), юнит, ХП, скорость)
    ((1,), HUSSAR_, 80, 1.5), ((1,), KNIGHT_, 110, 1.35), ((1,), CAVARCH_, 55, 1.45), ((1,), HC_, 38, 0.96), ((1,), MAA_, 55, 0.9),
    ((1,), ARCHER_, 30, 0.96), ((1,), MONK_, 30, 0.7), ((1,), SCOUT_, 55, 1.55), ((1,), VILL_M, 25, 0.8), ((1,), VILL_F, 25, 0.8),
    ((2, 3, 4, 5, 6), HC_, 40, 0.96), ((2, 3, 4, 5, 6), KNIGHT_, 95, 1.4), ((2, 3, 4, 5, 6), CAVARCH_, 55, 1.4),
    ((2, 3, 4, 5, 6), SPEAR_, 50, 1.0), ((2, 3, 4, 5, 6), MAA_, 55, 0.9), ((2, 3, 4, 5, 6), SCOUT_, 50, 1.55),
]
t = trig("M1_Stats")
for pls, c, hp, sp in STATS:
    for pl in pls:
        t.new_effect.modify_attribute(source_player=pl, object_list_unit_id=c, object_attributes=ObjectAttribute.HIT_POINTS,
                                      operation=Operation.SET, quantity=hp)
        t.new_effect.modify_attribute(source_player=pl, object_list_unit_id=c, object_attributes=ObjectAttribute.MOVEMENT_SPEED,
                                      operation=Operation.SET, quantity=sp)
t.new_effect.modify_attribute(source_player=P1, object_list_unit_id=SCOUT_, object_attributes=ObjectAttribute.LINE_OF_SIGHT,
                              operation=Operation.SET, quantity=12)

t = trig("M1_Rename_Loop", looping=True)
t.new_condition.timer(timer=4)
for pid in (2, 3, 4, 5, 6):
    for c, nm in ((HC_, "Стрелец"), (KNIGHT_, "Сын боярский"), (CAVARCH_, "Сын боярский с луком"), (SPEAR_, "Городовой казак"),
                  (MAA_, "Ратник"), (SCOUT_, "Дозорный")):
        rename(t, pid, c, nm)
rename(t, P4, VILL_M, "Посошной человек")
for c, nm in ((MONK_, "Чернец"), (HUSSAR_, "Польский гусар"), (WH, "Крылатый гусар"), (KNIGHT_, "Шляхтич"), (CAVARCH_, "Казак конный"),
              (HC_, "Казак-стрелок"), (MAA_, "Пеший казак"), (ARCHER_, "Казак-лучник"), (SCOUT_, "Казак-разведчик"),
              (VILL_M, "Обозный человек"), (VILL_F, "Обозная женщина")):
    rename(t, P1, c, nm)
rename(t, P8, MAA_, "Пеший ротник")
t.new_effect.change_object_description(object_list_unit_id=WH, source_player=P1,
                                       message="Тяжёлая хоругвь гусарии. Наёмники Речи Посполитой: дорого, но в поле с ними не спорят.")

CARTS7 = [u for u in um.get_all_units() if u.player == P7 and u.unit_const in (K("TRADE_CART_FULL"), K("TRADE_CART_EMPTY"), K("CART"))]
BOATS7 = [u for u in um.get_all_units() if u.player == P7 and u.unit_const == K("TRANSPORT_SHIP")]
t = trig("M1_TownLife")
for pl, (cx, cy) in ((P2, (62, 52)), (P3, (74, 126)), (P4, (160, 168)), (P5, (170, 90))):
    lst = CIT[pl][:6]
    t.new_effect.patrol(source_player=pl, location_x=cx + 6, location_y=cy + 4, selected_object_ids=ids(lst))
for u in CARTS7 + BOATS7:
    t.new_effect.patrol(source_player=P7, location_x=int(u.x) + (8 if u.unit_const != K("TRANSPORT_SHIP") else 10),
                        location_y=int(u.y) + (0 if u.unit_const != K("TRANSPORT_SHIP") else 6), selected_object_ids=[u.reference_id])
t = trig("M1_LifeLoop", looping=True)
t.new_condition.timer(timer=60)
for u in CARTS7 + BOATS7:
    t.new_effect.patrol(source_player=P7, location_x=int(u.x) + (8 if u.unit_const != K("TRANSPORT_SHIP") else 10),
                        location_y=int(u.y) + (0 if u.unit_const != K("TRANSPORT_SHIP") else 6), selected_object_ids=[u.reference_id])

# ================================================================ 2. ВСТУПЛЕНИЕ И ОБУЧЕНИЕ
t = trig("E01_Crossing")
cam(t, (12, 14))
t.new_effect.task_object(source_player=P1, location_x=SX, location_y=SY + 2, action_type=ActionType.MOVE, selected_object_ids=ids(WATER_START))
Lsay(t, "E01_Crossing", types=("плашка", "рассказчик", "справка", "диалог"))


def once_trigger(name, conds, lines_trig, types=("подсказка",), flags=(), enabled=True, extra=None):
    t = trig(name, enabled=enabled)
    conds(t)
    for f in flags:
        e_set(t, f, 1)
    if extra:
        extra(t)
    if lines_trig:
        Lsay(t, lines_trig, types=types)
    return t


once_trigger("M1_Tut_Move", lambda t: (c_clock(t, 45), c_dm(t, "Z_Border", 1)), "M1_Tut_Move")
once_trigger("M1_Tut_Zastava", lambda t: c_dm(t, "Z_Border"), "M1_Tut_Zastava")
once_trigger("M1_Tut_Chase", lambda t: (c_clock(t, 180), c_flag(t, "M1_S1_Escaped", 0), c_flag(t, "M1_S1_Won", 0), c_flag(t, "M1_E03", 1)),
             "M1_Tut_Chase")
for k, vn in enumerate(("V1", "V2", "V3", "V4"), 1):
    a = trig(f"M1_Tut_Village__near{k}")
    c_in(a, P1, -1, R(*VCH[vn], 14))
    e_set(a, "M1_NearVillage", 1)
once_trigger("M1_Tut_Village", lambda t: c_flag(t, "M1_NearVillage", 1), "M1_Tut_Village", extra=lambda t: e_set(t, "M1_S2_Open", 1))
a = trig("M1_Tut_Gate__near")
c_in(a, P1, -1, R(62, 52, 20))
e_set(a, "M1_NearMor", 1)
once_trigger("M1_Tut_Gate", lambda t: c_flag(t, "M1_NearMor", 1), "M1_Tut_Gate", flags=("M1_Tut_GateDone",))
start_monks = start_units[MONK_]
once_trigger("M1_Tut_Wounded", lambda t: t.new_condition.object_hp(quantity=15, unit_object=start_monks[0].reference_id,
                                                                  comparison=Comparison.LESS), "M1_Tut_Wounded")
once_trigger("M1_Tut_Base", lambda t: c_flag(t, "M1_MoravskDone", 1), "M1_Tut_Base")

HINT_MOR = L("M1_Hint_Mor", "подсказка")
t = trig("M1_Hint_Mor")
c_flag(t, "M1_Tut_GateDone", 1)
c_clock(t, 240)
c_flag(t, "M1_MoravskDone", 0)
say(t, HINT_MOR[0])
for k, tsec in ((1, 480), (2, 720), (3, 960)):
    a = aux("M1_Hint_Mor", f"r{k}")
    c_flag(a, "M1_Tut_GateDone", 1)
    c_clock(a, tsec)
    c_flag(a, "M1_MoravskDone", 0)
    say(a, HINT_MOR[k])


def repeated_hint(name, goal, offsets, done_flag):
    ls = L(name, "подсказка")
    for k, off in enumerate(offsets):
        h = trig(name) if k == 0 else aux(name, f"r{k + 1}")
        c_flag(h, "M1_Goal_" + goal, 1)
        c_dl(h, f"dl_{name}_{k}")
        c_flag(h, done_flag, 0)
        say(h, ls[k])


repeated_hint("M1_Hint_Che", "Che", [240, 540, 840, 1140], "M1_PosadDone")
t = trig("M1_Hint_Camp")
c_flag(t, "M1_Goal_Camp", 1)
c_dl(t, "dl_M1_Hint_Camp_0")
c_flag(t, "M1_CampPlaced", 0)
say(t, L("M1_Hint_Camp", "подсказка"))
repeated_hint("M1_Hint_Put", "Put", [300, 660, 1020], "M1_PutivlDone")
once_trigger("M1_Hint_Tsarevich", lambda t: (c_flag(t, "M1_MoravskDone", 1), c_dl(t, "dl_Hint_Tsarevich"), c_flag(t, "M1_TsarevichOn", 0)),
             "M1_Hint_Tsarevich")
once_trigger("M1_Hint_BribeChe", lambda t: (c_flag(t, "M1_MoravskDone", 1), c_flag(t, "M1_PosadDone", 0),
                                            t.new_condition.accumulate_attribute(quantity=600, attribute=Attribute.GOLD_STORAGE, source_player=P1)),
             "M1_Hint_BribeChe")
once_trigger("M1_Hint_BribePut", lambda t: (c_flag(t, "M1_CampPlaced", 1), c_flag(t, "M1_PutivlDone", 0),
                                            t.new_condition.accumulate_attribute(quantity=900, attribute=Attribute.GOLD_STORAGE, source_player=P1)),
             "M1_Hint_BribePut")

# ================================================================ 3. РУБЕЖ, ЗАСТАВА, СЁЛА, МОЛВА
t = trig("E02_Border")
c_dm(t, "Z_Border")
cam(t, (35, 18))
Lsay(t, "E02_Border", types=("плашка", "диалог", "справка", "цель"))
e_set(t, "M1_S1_Open", 1)
t = trig("E03_Zastava")
c_in(t, P1, -1, Z["Z_Zastava"])
e_set(t, "M1_E03", 1)
t.new_effect.task_object(object_list_unit_id=SCOUT_, source_player=P2, location_x=55, location_y=52, action_type=ActionType.MOVE,
                         area_x1=36, area_y1=24, area_x2=48, area_y2=36)
Lsay(t, "E03_Zastava", types=("диалог", "сообщение"))
t = trig("S1_Win")
c_flag(t, "M1_E03", 1)
c_flag(t, "M1_S1_Escaped", 0)
c_none(t, P2, SCOUT_)
e_set(t, "M1_S1_Won", 1)
give(t, gold=100)
t.new_effect.remove_object(object_list_unit_id=HC_, source_player=P2, area_x1=54, area_y1=44, area_x2=70, area_y2=60, max_units_affected=2)
Lsay(t, "S1_Win", types=("сообщение", "цель", "диалог"))
t = trig("S1_Fail")
c_in(t, P2, SCOUT_, Z["Z_Mor_Arrive"])
e_set(t, "M1_S1_Escaped", 1)
create(t, P2, HC_, 2, (53, 52))
create(t, P2, KNIGHT_, 2, (53, 54))
Lsay(t, "S1_Fail", types=("сообщение", "цель", "диалог"))
t = trig("S2_Open")
c_flag(t, "M1_S2_Open", 1)
Lsay(t, "S2_Open", types=("цель",))
for k, vn in enumerate(("V1", "V2", "V3", "V4"), 1):
    zone = Z[f"Z_Village_{k}"]
    s = aux(f"E04_Village_{k}", "start", looping=True)
    c_flag(s, f"M1_Village_{k}", 0)
    c_flag(s, f"M1_VillStarted_{k}", 0)
    c_flag(s, "M1_Molva", 2, Comparison.LARGER_OR_EQUAL)
    c_in(s, P1, MONK_, zone)
    e_set(s, f"M1_VillStarted_{k}", 1)
    e_dl(s, f"dl_Village_{k}", 6)
    e = trig(f"E04_Village_{k}", looping=True)
    c_flag(e, f"M1_VillStarted_{k}", 1)
    c_flag(e, f"M1_Village_{k}", 0)
    c_dl(e, f"dl_Village_{k}")
    c_in(e, P1, MONK_, zone)
    e_set(e, f"M1_Village_{k}", 1)
    vx, vy = VCH[vn]
    e.new_effect.change_ownership(source_player=P7, target_player=P1, object_type=int(ObjectType.BUILDING), area_x1=vx - 13, area_y1=vy - 8,
                                  area_x2=vx + 13, area_y2=vy + 16, flash_object=1)
    give(e, food=100)
    create(e, P1, MAA_, 1, (vx, vy - 8))
    create(e, P1, ARCHER_, 1, (vx + 2, vy - 8))
    Lsay(e, f"E04_Village_{k}", types=("диалог", "сообщение"))
    b = aux(f"E04_Village_{k}", "reset", looping=True)
    c_flag(b, f"M1_VillStarted_{k}", 1)
    c_flag(b, f"M1_Village_{k}", 0)
    c_dl(b, f"dl_Village_{k}")
    c_in(b, P1, MONK_, zone, inverted=1)
    e_set(b, f"M1_VillStarted_{k}", 0)
    mv = aux(f"E04_Village_{k}", "molva")
    c_flag(mv, f"M1_Village_{k}", 1)
    c_flag(mv, "M1_VillageMolva", 2, Comparison.LESS)
    e_add(mv, "M1_VillageMolva", 1)
    e_add(mv, "M1_Molva", 1)
t = trig("S2_Done")
for k in range(1, 5):
    c_flag(t, f"M1_Village_{k}", 1)
t.new_effect.change_technology_cost(source_player=P1, technology=TSAR, resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=200,
                                    resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0, resource_3=Attribute.GOLD_STORAGE,
                                    resource_3_quantity=150)
create(t, P1, MONK_, 1, (62, 56))
e_set(t, "M1_S2_Done", 1)
Lsay(t, "S2_Done", types=("сообщение", "цель"))
t = trig("S2_Closed")
c_flag(t, "M1_S2_Done", 0)
c_flag(t, "M1_MoravskDone", 1)
c_flag(t, "M1_Molva", 1, Comparison.LESS_OR_EQUAL)
e_set(t, "M1_S2_Closed", 1)
Lsay(t, "S2_Closed", types=("диалог", "цель"))
# Молва: гибель жителей (подсчёт через count_units_into_variable каждые 5 с)
t = trig("M1_Molva_Kill__count", looping=True)
t.new_condition.timer(timer=5)
e_set(t, "VC_new", 0)
for pl in (P2, P3, P5, P7):
    for c in (VILL_M, VILL_F):
        t.new_effect.count_units_into_variable(object_list_unit_id=c, source_player=pl, area_x1=0, area_y1=0, area_x2=S - 1,
                                               area_y2=S - 1, variable2=v(f"VC_{pl}_{c}"))
        t.new_effect.modify_variable_by_variable(variable=v("VC_new"), operation=Operation.ADD, variable2=v(f"VC_{pl}_{c}"))
t = trig("M1_Molva_Kill", looping=True)
c_flag(t, "M1_BaseReady", 1)
t.new_condition.compare_variables(variable=v("VC_prev"), comparison=Comparison.LARGER, variable2=v("VC_new"))
c_dl(t, "dl_KillCool")
c_flag(t, "M1_Molva", 0, Comparison.LARGER)
e_add(t, "M1_Molva", -1)
e_set(t, "M1_H4_Fail", 1)
e_dl(t, "dl_KillCool", 60)
t = aux("M1_Molva_Kill", "sync", looping=True)
t.new_condition.timer(timer=5)
t.new_effect.modify_variable_by_variable(variable=v("VC_prev"), operation=Operation.SET, variable2=v("VC_new"))
e_set(t, "M1_BaseReady", 1)
t = aux("M1_Molva_Kill", "h4only", looping=True)
c_flag(t, "M1_BaseReady", 1)
c_flag(t, "M1_H4_Fail", 0)
t.new_condition.compare_variables(variable=v("VC_prev"), comparison=Comparison.LARGER, variable2=v("VC_new"))
e_set(t, "M1_H4_Fail", 1)

# ================================================================ 4. МОРАВСК, конверсия (spec §5.1)
CONV_D = {"Mor": (15, 11, 9, 6), "Che": (20, 14, 12, 8)}


def conversion(town, zones, done, goal_extra=None, use_vars=False):
    pre = f"M1_{town}_Reading"
    for zi, zn in enumerate(zones):
        zone = Z[zn]
        zs = "" if zi == 0 else f"z{zi + 1}"
        for tsar in (False, True):
            sfx = "_T" if tsar else ""
            variants = [(0, "")] if use_vars else [(0, ""), (1, "L")]
            for leaf, lsfx in variants:
                nm = f"T_{town}_ConvStart{sfx}"
                suffix = zs + lsfx
                start = trig(nm, looping=True) if not suffix else aux(nm, suffix, looping=True)
                c_in(start, P1, MONK_, zone)
                c_flag(start, pre, 0)
                c_flag(start, done, 0)
                c_flag(start, f"M1_{town}_Go", 0)
                c_flag(start, "M1_TsarevichOn", 1 if tsar else 0)
                if not use_vars:
                    c_flag(start, f"M1_Leaflet_{town}", leaf)
                if goal_extra:
                    c_flag(start, goal_extra, 1)
                e_set(start, pre, 1)
                e_set(start, f"M1_{town}_ReadStarted", 1)
                e_set(start, f"M1_{town}_Zone", zi + 1)
                start.new_effect.modify_variable_by_variable(variable=v(f"dl_{town}_Conv"), operation=Operation.SET, variable2=v("M1_Clock"))
                if use_vars:
                    start.new_effect.modify_variable_by_variable(variable=v(f"dl_{town}_Conv"), operation=Operation.ADD,
                                                                 variable2=v("Put_DT" if tsar else "Put_D"))
                else:
                    d0, dl_, dt, dlt = CONV_D[town]
                    d = (dlt if (tsar and leaf) else dt if tsar else dl_ if leaf else d0)
                    start.new_effect.change_variable(quantity=d, operation=Operation.ADD, variable=v(f"dl_{town}_Conv"))
                    start.new_effect.modify_variable_by_variable(variable=v(f"dl_{town}_Conv"), operation=Operation.ADD,
                                                                 variable2=v(f"M1_DPlus_{town}"))
                    start.new_effect.modify_variable_by_variable(variable=v(f"dl_{town}_Conv"), operation=Operation.SUBTRACT,
                                                                 variable2=v(f"M1_DMinus_{town}"))
                if zi == 0:
                    say(start, L(nm, "сообщение"))
            nm = f"T_{town}_ConvCheck{sfx}"
            suffix = zs
            chk = trig(nm, looping=True) if not suffix else aux(nm, suffix, looping=True)
            c_flag(chk, pre, 1)
            c_flag(chk, f"M1_{town}_Zone", zi + 1)
            c_dl(chk, f"dl_{town}_Conv")
            c_flag(chk, "M1_TsarevichOn", 1 if tsar else 0)
            c_in(chk, P1, MONK_, zone)
            e_set(chk, pre, 0)
            e_set(chk, f"M1_{town}_Go", 1)
            fail = aux(nm, ("fail" + zs), looping=True)
            c_flag(fail, pre, 1)
            c_flag(fail, f"M1_{town}_Zone", zi + 1)
            c_dl(fail, f"dl_{town}_Conv")
            c_flag(fail, "M1_TsarevichOn", 1 if tsar else 0)
            c_in(fail, P1, MONK_, zone, inverted=1)
            e_set(fail, pre, 0)
            if zi == 0:
                say(fail, L(nm, "сообщение"))


def leaflet(town, zone_name):
    def cond(t):
        t.new_condition.objects_in_area(quantity=1, object_list=MONK_, source_player=P1, area_x1=Z[zone_name][0], area_y1=Z[zone_name][1],
                                        area_x2=Z[zone_name][2], area_y2=Z[zone_name][3])

    def done(t):
        e_set(t, f"M1_Leaflet_{town}", 1)
        if town == "Put":
            e_set(t, "Put_D", 18)
            e_set(t, "Put_DT", 10)
        Lsay(t, f"T_{town}_Leaflet", types=("сообщение",))
        if town in ("Che", "Put"):
            pl, ar = (P3, A_CHE) if town == "Che" else (P5, A_PUT)
            t.new_effect.change_ownership(object_list_unit_id=SPEAR_, source_player=pl, target_player=P7, area_x1=ar[0], area_y1=ar[1],
                                          area_x2=ar[2], area_y2=ar[3], max_units_affected=2)
    s = trig(f"T_{town}_Leaflet__start", looping=True)
    c_in(s, P1, MONK_, Z[zone_name])
    c_flag(s, f"M1_Leaflet_{town}", 0)
    c_flag(s, f"M1_LeafSt_{town}", 0)
    e_set(s, f"M1_LeafSt_{town}", 1)
    e_dl(s, f"dl_Leaf_{town}", 5)
    m = trig(f"T_{town}_Leaflet", looping=True)
    c_flag(m, f"M1_LeafSt_{town}", 1)
    c_flag(m, f"M1_Leaflet_{town}", 0)
    c_dl(m, f"dl_Leaf_{town}")
    c_in(m, P1, MONK_, Z[zone_name])
    done(m)
    r = aux(f"T_{town}_Leaflet", "reset", looping=True)
    c_flag(r, f"M1_LeafSt_{town}", 1)
    c_flag(r, f"M1_Leaflet_{town}", 0)
    c_dl(r, f"dl_Leaf_{town}")
    c_in(r, P1, MONK_, Z[zone_name], inverted=1)
    e_set(r, f"M1_LeafSt_{town}", 0)
    if town != "Put":
        # листы в Чернигове и Путивле: двое городовых казаков гарнизона «уходят»
        pass
    return m


def bribe(town, tech_id, zones, done):
    paid = trig(f"T_{town}_BribePaid")
    paid.new_condition.research_technology(source_player=P1, technology=tech_id)
    e_set(paid, f"M1_BribePaid_{town}", 1)
    say(paid, L(f"T_{town}_BribePaid", "сообщение"))
    lines = L(f"T_{town}_BribeArrive", "сообщение")
    for zi, zn in enumerate(zones):
        zone = Z[zn]
        sf = "" if zi == 0 else f"z{zi + 1}"
        arr = trig(f"T_{town}_BribeArrive", looping=True) if zi == 0 else aux(f"T_{town}_BribeArrive", sf, looping=True)
        c_flag(arr, f"M1_BribePaid_{town}", 1)
        c_flag(arr, done, 0)
        c_flag(arr, f"M1_{town}_BribeWait", 0)
        c_flag(arr, f"M1_{town}_Go", 0)
        c_in(arr, P1, -1, zone)
        e_set(arr, f"M1_{town}_BribeWait", 1)
        e_dl(arr, f"dl_{town}_Bribe", 5)
        if zi == 0:
            say(arr, lines[0])
        ok = aux(f"T_{town}_BribeArrive", f"ok{sf}", looping=True)
        c_flag(ok, f"M1_{town}_BribeWait", 1)
        c_dl(ok, f"dl_{town}_Bribe")
        c_in(ok, P1, -1, zone)
        e_set(ok, f"M1_{town}_BribeWait", 0)
        e_set(ok, f"M1_{town}_Go", 1)
        bad = aux(f"T_{town}_BribeArrive", f"fail{sf}", looping=True)
        c_flag(bad, f"M1_{town}_BribeWait", 1)
        c_dl(bad, f"dl_{town}_Bribe")
        c_in(bad, P1, -1, zone, inverted=1)
        e_set(bad, f"M1_{town}_BribeWait", 0)
        if zi == 0:
            say(bad, lines[1])


# --- Моравск
leaflet("Mor", "Z_Leaflet_Mor")
conversion("Mor", ["Z_Conv_Mor", "Z_Conv_Mor2"], "M1_MoravskDone")
t = trig("T_Mor_Flip")
c_flag(t, "M1_Mor_Go", 1)
c_flag(t, "M1_MoravskDone", 0)
transfer(t, P2, ALL)
villagers_to_p7(t, P1, A_MOR)
t.new_effect.change_ownership(source_player=P7, target_player=P1, selected_object_ids=ids(MOR_VOEV))
for u in MOR_VOEV:
    t.new_effect.change_object_stance(source_player=P1, attack_stance=AttackStance.NO_ATTACK_STANCE, selected_object_ids=[u.reference_id])
t.new_effect.unlock_gate(selected_object_ids=ids(GATES[P2]))
e_set(t, "M1_MoravskDone", 1)
e_set(t, "M1_Mor_Reading", 0)
e_set(t, "M1_Goal_Che", 1)
create(t, P1, CAVARCH_, 3, (58, 56))
create(t, P1, MONK_, 1, (58, 54))
create(t, P1, SCOUT_, 1, (60, 56))
give(t, food=300, gold=200)
heal_all(t)
for tid in (TSAR, BRIBE_C):
    t.new_effect.enable_disable_technology(source_player=P1, technology=tid, enabled=1)
e_dl(t, "dl_M1_Hint_Che_0", 240)
e_dl(t, "dl_M1_Hint_Che_1", 540)
e_dl(t, "dl_M1_Hint_Che_2", 840)
e_dl(t, "dl_M1_Hint_Che_3", 1140)
e_dl(t, "dl_Defectors", 180)
e_dl(t, "dl_Hint_Tsarevich", 20)
flag_mark(t, (74, 126))
Lsay(t, "T_Mor_Flip", types=("сообщение", "цель", "диалог"))
say(t, L("bribe_chernigov", "сообщение"))
mor_flip = t
a = aux("T_Mor_Flip", "molva")
c_flag(a, "M1_MoravskDone", 1)
c_flag(a, "M1_H1_Fail", 0)
c_flag(a, "M1_MorMolvaDone", 0)
e_set(a, "M1_MorMolvaDone", 1)
e_add(a, "M1_Molva", 1)
e_add(a, "M1_DMinus_Che", 5)       # E08: Моравск взят словом: D посада -5 с
t = trig("E05_MorScene")
c_flag(t, "M1_MoravskDone", 1)
cam(t, (58, 54))
t.new_effect.task_object(object_list_unit_id=VILL_M, source_player=P7, location_x=60, location_y=54, action_type=ActionType.MOVE,
                         area_x1=50, area_y1=40, area_x2=70, area_y2=62, max_units_affected=6)
for u in MOR_VOEV:
    t.new_effect.task_object(source_player=P1, location_x=62, location_y=55, action_type=ActionType.MOVE, selected_object_ids=[u.reference_id])
Lsay(t, "E05_MorScene", types=("плашка", "справка", "диалог", "рассказчик"))
# E06: беглые у рубежа
volunteer_variants("E06_Defectors", lambda t: (c_flag(t, "M1_MoravskDone", 1), c_dl(t, "dl_Defectors")), 4, 2, (44, 24),
                   extra_fn=lambda t: (flag_mark(t, (52, 128), temp=True), e_set(t, "M1_Arrive_1", 1)),
                   lines=L("E06_Defectors", "диалог") + L("E06_Defectors", "сообщение", cond=None)[:1])
a = aux("E06_Defectors", "full")
c_flag(a, "M1_MoravskDone", 1)
c_dl(a, "dl_Defectors")
a.new_condition.accumulate_attribute(quantity=3, attribute=Attribute.POPULATION_HEADROOM, source_player=P1, inverted=1)
say(a, L("E06_Defectors", "сообщение", cond="лимит"))
a = aux("E06_Defectors", "clear")
c_flag(a, "M1_MoravskDone", 1)
a.new_condition.timer(timer=240)
a.new_effect.remove_object(object_list_unit_id=K("FLAG_B"), source_player=P1, area_x1=0, area_y1=0, area_x2=S - 1, area_y2=S - 1)
# технологии
t = trig("M1_TsarevichUnlock")
c_flag(t, "M1_MoravskDone", 1)
t.new_effect.enable_disable_technology(source_player=P1, technology=TSAR, enabled=1)
say(t, L("M1_TsarevichUnlock", "сообщение"))
t = trig("M1_TsarevichDone")
t.new_condition.research_technology(source_player=P1, technology=TSAR)
e_set(t, "M1_TsarevichOn", 1)
t.new_effect.modify_attribute(source_player=P1, object_list_unit_id=MONK_, object_attributes=ObjectAttribute.LINE_OF_SIGHT,
                              operation=Operation.ADD, quantity=3)
say(t, L("M1_TsarevichDone", "сообщение"))
t = trig("M1_CossackUnlock")
c_flag(t, "M1_MoravskDone", 1)
t.new_effect.add_train_location(object_list_unit_id=CAVARCH_, source_player=P1, object_list_unit_id_2=TC_, button_location=ButtonLocation.r2c1.value,
                                train_time=30)
t.new_effect.change_object_cost(object_list_unit_id=CAVARCH_, source_player=P1, resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=50,
                                resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0, resource_3=Attribute.GOLD_STORAGE, resource_3_quantity=45)
say(t, L("M1_CossackUnlock", "сообщение"))

# ================================================================ 6. РАЗВЕДКА S3
t = trig("T_Scout_Spawn")
c_flag(t, "M1_MoravskDone", 1)
e_set(t, "M1_O1Open", 1)
Lsay(t, "T_Scout_Spawn", types=("сообщение", "цель"))
for i in (1, 2, 3):
    t = trig(f"T_Scout_Point_{i}")
    c_flag(t, "M1_O1Open", 1)
    c_in(t, P1, SCOUT_, Z[f"Z_Scout_{i}"])
    e_set(t, f"M1_Scout_{i}", 1)
    say(t, L(f"T_Scout_Point_{i}", "сообщение"))
t = trig("T_Scout_Reward")
for i in (1, 2, 3):
    c_flag(t, f"M1_Scout_{i}", 1)
e_set(t, "M1_O1Done", 1)
t.new_effect.change_object_hp(quantity=100, source_player=P6, operation=Operation.SET, selected_object_ids=ids(weak_units))
flag_mark(t, (88, 119), temp=True)
flag_mark(t, (92, 124), temp=True)
Lsay(t, "T_Scout_Reward", types=("сообщение", "цель", "диалог"))
a = aux("T_Scout_Reward", "clear")
c_flag(a, "M1_O1Done", 1)
a.new_condition.timer(timer=60)
a.new_effect.remove_object(object_list_unit_id=K("FLAG_B"), source_player=P1, area_x1=0, area_y1=0, area_x2=S - 1, area_y2=S - 1)

# ================================================================ 7. ДЕСНА И ЧЕРНИГОВ
E07 = "E07_Fog"
t = trig("E07_Fog")
c_in(t, P1, -1, Z["Z_Ford_Mor"])
e_set(t, "M1_FogOn", 1)
mood(t, ColorMood.MISTY, 5)
los(t, -4)
e_dl(t, "dl_FogEnd", 150)
create(t, P6, HC_, 4, (70, 86))
create(t, P6, SPEAR_, 3, (73, 86), 1)
Lsay(t, "E07_Fog", types=("сообщение", "рассказчик", "диалог"))
t = trig("E07_FogEnd")
c_flag(t, "M1_FogOn", 1)
c_dl(t, "dl_FogEnd")
e_set(t, "M1_FogOn", 2)
mood(t, ColorMood.AUTUMN, 10)
los(t, 4)
for c in (HC_, SPEAR_):
    t.new_effect.task_object(object_list_unit_id=c, source_player=P6, location_x=96, location_y=121, action_type=ActionType.MOVE,
                             area_x1=60, area_y1=80, area_x2=90, area_y2=95)
say(t, L("E07_FogEnd", "сообщение"))
t = trig("E08_ChernigovFires")
c_in(t, P1, -1, R(73, 111, 18))
cam(t, (73, 111))
Lsay(t, "E08_ChernigovFires", types=("плашка", "справка", "диалог", "сообщение"))
leaflet("Che", "Z_Leaflet_Che")
conversion("Che", ["Z_Conv_Che", "Z_Conv_Che2"], "M1_PosadDone", goal_extra="M1_MoravskDone")
bribe("Che", BRIBE_C, ["Z_Conv_Che", "Z_Conv_Che2"], "M1_PosadDone")
t = trig("T_Che_PosadFlip")
c_flag(t, "M1_Che_Go", 1)
c_flag(t, "M1_PosadDone", 0)
transfer(t, P3, ALL)
villagers_to_p7(t, P1, CHE_AREA_V)
t.new_effect.unlock_gate(selected_object_ids=ids(GATES[P3]))
t.new_effect.lock_gate(selected_object_ids=ids(GATES[P6]))
e_set(t, "M1_PosadDone", 1)
e_set(t, "M1_Che_Reading", 0)
e_set(t, "M1_Goal_2b", 1)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_C, enabled=0)
create(t, P1, CAVARCH_, 4, (72, 119))
create(t, P1, HC_, 2, (72, 117), 1)
for (x, y) in spots(74, 124, 8):
    t.new_effect.create_object(object_list_unit_id=MAA_, source_player=P1, location_x=x, location_y=y)
e_dl(t, "dl_Rumor_Che", 120)
e_dl(t, "dl_Open2b", 0)
flag_mark(t, (96, 121))
Lsay(t, "T_Che_PosadFlip", types=("сообщение", "цель"))
t = trig("E09_PosadScene")
c_flag(t, "M1_PosadDone", 1)
cam(t, (74, 126))
Lsay(t, "E09_PosadScene", types=("плашка", "справка", "диалог"))
volunteer_variants("T_Rumor_Che", lambda t: (c_flag(t, "M1_PosadDone", 1), c_flag(t, "M1_BribePaid_Che", 0), c_dl(t, "dl_Rumor_Che")),
                   3, 3, (74, 117), extra_fn=lambda t: e_set(t, "M1_Arrive_2", 1),
                   lines=L("T_Rumor_Che", "сообщение", cond=None)[:1])
a = aux("T_Rumor_Che", "bribe")
c_flag(a, "M1_PosadDone", 1)
c_flag(a, "M1_BribePaid_Che", 1)
c_dl(a, "dl_Rumor_Che")
create(a, P1, MAA_, 2, (74, 117))
create(a, P1, ARCHER_, 1, (74, 117), 1)
e_set(a, "M1_Arrive_2", 1)
say(a, L("T_Rumor_Che", "сообщение")[:1])
a = aux("T_Rumor_Che", "crowd")
c_flag(a, "M1_PosadDone", 1)
c_dl(a, "dl_Rumor_Che")
molva_cmp(a, lo=4)
say(a, L("T_Rumor_Che", "сообщение", cond="Молва ≥ 4"))
t = trig("E09b_Rain")
c_flag(t, "M1_PosadDone", 1)
t.new_condition.timer(timer=120)
mood(t, ColorMood.MURKY, 5)
speed_mul(t, 0.9)
e_dl(t, "dl_RainEnd", 180)
e_set(t, "M1_RainOn", 1)
Lsay(t, "E09b_Rain", types=("сообщение", "диалог"))
t = trig("E09b_RainEnd")
c_flag(t, "M1_RainOn", 1)
c_dl(t, "dl_RainEnd")
e_set(t, "M1_RainOn", 2)
mood(t, ColorMood.AUTUMN, 10)
speed_mul(t, 1 / 0.9)
say(t, L("E09b_RainEnd", "сообщение"))

# --- вылазки замка (spec §8)
GATE_C = (90, 122, 96, 125)
CHE_UNITS = [SPEAR_, HC_, KNIGHT_]
CHE_TARGET = (74, 126)
t = aux("T_CheSortie_1", "enter")
c_flag(t, "M1_CastleFall", 0)
c_mil(t, P1, R(96, 121, 25))
c_flag(t, "M1_CheEntered", 0)
e_set(t, "M1_CheEntered", 1)
e_dl(t, "dl_S1", 120)
e_dl(t, "dl_S1_w30", 90)
e_dl(t, "dl_S1_w60", 60)
e_dl(t, "dl_Open2b", 720)
for key, (extra, wait) in (("", ("M1_O1Done", 0)), ("O1", ("M1_O1Done", 1))):
    w1 = trig("T_CheSortie_1_Warn") if key == "" else aux("T_CheSortie_1_Warn", "O1")
    c_flag(w1, "M1_CheEntered", 1)
    c_flag(w1, extra, wait)
    c_flag(w1, "M1_S1Warned", 0)
    c_flag(w1, "M1_CastleFall", 0)
    c_dl(w1, "dl_S1_w30" if key == "" else "dl_S1_w60")
    e_set(w1, "M1_S1Warned", 1)
    flag_mark(w1, (96, 121), temp=True)
    say(w1, L("T_CheSortie_1_Warn", "сообщение"))
s1 = trig("T_CheSortie_1")
c_flag(s1, "M1_CheEntered", 1)
c_flag(s1, "M1_S1Warned", 1)
c_flag(s1, "M1_CastleFall", 0)
c_dl(s1, "dl_S1")
for c, n in ((SPEAR_, 6), (HC_, 4), (KNIGHT_, 3)):
    for (x, y) in spots(93, 123, n, 0):
        s1.new_effect.create_object(object_list_unit_id=c, source_player=P6, location_x=x, location_y=y)
for c in CHE_UNITS:
    s1.new_effect.attack_move(object_list_unit_id=c, source_player=P6, location_x=CHE_TARGET[0], location_y=CHE_TARGET[1], area_x1=GATE_C[0],
                              area_y1=GATE_C[1], area_x2=GATE_C[2], area_y2=GATE_C[3])
e_dl(s1, "dl_S2", 360)
e_dl(s1, "dl_S2_w30", 330)
e_dl(s1, "dl_S2_w60", 300)
e_set(s1, "M1_S1Fired", 1)
say(s1, L("T_CheSortie_1", "сообщение"))
for key, (wait, dlv) in (("", (0, "dl_S2_w30")), ("O1", (1, "dl_S2_w60"))):
    w2 = trig("T_CheSortie_2_Warn") if key == "" else aux("T_CheSortie_2_Warn", "O1")
    c_flag(w2, "M1_S1Fired", 1)
    c_flag(w2, "M1_O1Done", wait)
    c_flag(w2, "M1_S2Warned", 0)
    c_flag(w2, "M1_CastleFall", 0)
    c_dl(w2, dlv)
    e_set(w2, "M1_S2Warned", 1)
    flag_mark(w2, (96, 121), temp=True)
    say(w2, L("T_CheSortie_2_Warn", "сообщение"))
s2 = trig("T_CheSortie_2")
c_flag(s2, "M1_S2Warned", 1)
c_flag(s2, "M1_CastleFall", 0)
c_flag(s2, "M1_Shaken", 0)
c_dl(s2, "dl_S2")
for c, n in ((SPEAR_, 8), (HC_, 5), (KNIGHT_, 4)):
    for (x, y) in spots(93, 123, n, 0):
        s2.new_effect.create_object(object_list_unit_id=c, source_player=P6, location_x=x, location_y=y)
for c in CHE_UNITS:
    s2.new_effect.attack_move(object_list_unit_id=c, source_player=P6, location_x=CHE_TARGET[0], location_y=CHE_TARGET[1], area_x1=GATE_C[0],
                              area_y1=GATE_C[1], area_x2=GATE_C[2], area_y2=GATE_C[3])
e_set(s2, "M1_S2Fired", 1)
say(s2, L("T_CheSortie_2", "сообщение"))
s2b = aux("T_CheSortie_2", "shaken")
c_flag(s2b, "M1_S2Warned", 1)
c_flag(s2b, "M1_CastleFall", 0)
c_flag(s2b, "M1_Shaken", 1)
c_dl(s2b, "dl_S2")
for c, n in ((HC_, 6), (KNIGHT_, 5)):
    for (x, y) in spots(93, 123, n, 0):
        s2b.new_effect.create_object(object_list_unit_id=c, source_player=P6, location_x=x, location_y=y)
for c in (HC_, KNIGHT_):
    s2b.new_effect.attack_move(object_list_unit_id=c, source_player=P6, location_x=CHE_TARGET[0], location_y=CHE_TARGET[1], area_x1=GATE_C[0],
                               area_y1=GATE_C[1], area_x2=GATE_C[2], area_y2=GATE_C[3])
e_set(s2b, "M1_S2Fired", 1)
t = trig("T_CheCastle_Shaken")
c_flag(t, "M1_PosadDone", 1)
c_flag(t, "M1_S2Fired", 0)
c_flag(t, "M1_Shaken", 0)
e_set(t, "M1_Shaken", 1)
say(t, L("T_CheCastle_Shaken", "сообщение"))
# D2: поджог житниц
gr1, gr2 = NAMED["CasGranary1"], NAMED["CasGranary2"]
t = trig("D2_Granary")
c_flag(t, "M1_PosadDone", 1)
c_flag(t, "M1_Shaken_D2", 0)
t.new_condition.destroy_object(unit_object=gr1.reference_id) if False else None
c_none(t, P6, K("GRANARY"), A_CAS)
e_set(t, "M1_Shaken_D2", 1)
e_set(t, "M1_Shaken", 1)
t.new_effect.damage_object(quantity=10, source_player=P6, object_type=int(ObjectType.MILITARY), area_x1=A_CAS[0], area_y1=A_CAS[1], area_x2=A_CAS[2],
                           area_y2=A_CAS[3])
Lsay(t, "D2_Granary", types=("сообщение", "диалог", "подсказка"))
s = aux("D2_Granary", "start", looping=True)
c_in(s, P1, SCOUT_, Z["Z_Granary"])
c_flag(s, "M1_Shaken_D2", 0)
c_flag(s, "M1_GranSt", 0)
e_set(s, "M1_GranSt", 1)
e_dl(s, "dl_Gran", 10)
t2 = aux("D2_Granary", "scout", looping=True)
c_flag(t2, "M1_GranSt", 1)
c_flag(t2, "M1_Shaken_D2", 0)
c_dl(t2, "dl_Gran")
c_in(t2, P1, SCOUT_, Z["Z_Granary"])
e_set(t2, "M1_Shaken_D2", 1)
e_set(t2, "M1_Shaken", 1)
t2.new_effect.damage_object(quantity=10, source_player=P6, object_type=int(ObjectType.MILITARY), area_x1=A_CAS[0], area_y1=A_CAS[1],
                            area_x2=A_CAS[2], area_y2=A_CAS[3])
say(t2, L("D2_Granary", "сообщение"))
t = trig("T_Che_Storm")
c_flag(t, "M1_PosadDone", 1)
c_flag(t, "M1_CastleFall", 0)
c_flag(t, "M1_StormGo", 0)
c_mil(t, P1, Z["Z_Castle_Gate"], 10)
e_set(t, "M1_StormGo", 1)
for c in (CAVARCH_, HC_, MAA_):
    t.new_effect.attack_move(object_list_unit_id=c, source_player=P1, location_x=96, location_y=121, area_x1=58, area_y1=110, area_x2=86, area_y2=142)
Lsay(t, "T_Che_Storm", types=("диалог", "сообщение", "подсказка"))
t = aux("T_Che_Storm", "weak")
c_flag(t, "M1_PosadDone", 1)
c_flag(t, "M1_CastleFall", 0)
c_flag(t, "M1_StormGo", 0)
c_mil(t, P1, Z["Z_Castle_Weak"], 10)
e_set(t, "M1_StormGo", 1)
for c in (CAVARCH_, HC_, MAA_):
    t.new_effect.attack_move(object_list_unit_id=c, source_player=P1, location_x=96, location_y=121, area_x1=58, area_y1=110, area_x2=86, area_y2=142)
# падение замка
for sfx, setup in (("tatev", lambda a: a.new_condition.destroy_object(unit_object=TATEV.reference_id)),
                   ("castle", lambda a: a.new_condition.destroy_object(unit_object=NAMED["Castle"].reference_id)),
                   ("few", lambda a: c_mil(a, P6, ALL, 4, 1))):
    a = aux("T_CheCastle_Fall", sfx)
    c_flag(a, "M1_PosadDone", 1)
    setup(a)
    e_set(a, "M1_CastleFall_Go", 1)
t = trig("T_CheCastle_Fall")
c_flag(t, "M1_CastleFall_Go", 1)
c_flag(t, "M1_CastleFall", 0)
transfer(t, P6, ALL)
t.new_effect.unlock_gate(selected_object_ids=ids(GATES[P6]))
e_set(t, "M1_CastleFall", 1)
e_set(t, "M1_CastleDone", 1)
e_set(t, "M1_Goal_Camp", 1)
create(t, P1, KNIGHT_, 3, (92, 112))
create(t, P1, MAA_, 6, (90, 112), 1)
give(t, gold=300)
e_dl(t, "dl_M1_Hint_Camp_0", 180)
e_dl(t, "dl_News1", 60)
flag_mark(t, (140, 156))
Lsay(t, "T_CheCastle_Fall", types=("сообщение", "цель", "диалог"))
t = trig("E11_TatevScene")
c_flag(t, "M1_CastleFall", 1)
cam(t, (96, 121))
for u in [TATEV] + list(CAS_PEOPLE):
    t.new_effect.task_object(source_player=P1, location_x=94, location_y=112, action_type=ActionType.MOVE, selected_object_ids=[u.reference_id])
Lsay(t, "E11_TatevScene", types=("плашка", "справка", "диалог", "сообщение"))
t = trig("CP_Chernigov")
c_flag(t, "M1_CastleFall", 1)
heal_all(t)
say(t, L("CP_Chernigov", "сообщение"))
# S5
t = trig("S5_Open")
c_flag(t, "M1_PosadDone", 1)
Lsay(t, "S5_Open", types=("цель", "сообщение"))
t = trig("S5_Join")
c_flag(t, "M1_PosadDone", 1)
c_in(t, P1, -1, Z["Z_Yelets"])
t.new_effect.change_ownership(object_list_unit_id=MONK_, source_player=0, target_player=P1, area_x1=47, area_y1=123, area_x2=57, area_y2=133)
rename(t, P1, MONK_, "Старец", (47, 123, 57, 133))
for u in YEL_MONKS:
    t.new_effect.modify_object_attribute(source_player=P1, object_attributes=ObjectAttribute.MAXIMUM_RANGE, selected_object_ids=[u.reference_id],
                                         operation=Operation.SET, quantity=0)
e_set(t, "M1_S5_Joined", 1)
Lsay(t, "S5_Join", types=("диалог", "сообщение"))
t = trig("S5_Done")
c_flag(t, "M1_S5_Joined", 1)
for u in YEL_MONKS:
    t.new_condition.bring_object_to_area(unit_object=u.reference_id, area_x1=Z["Z_Camp"][0], area_y1=Z["Z_Camp"][1], area_x2=Z["Z_Camp"][2],
                                         area_y2=Z["Z_Camp"][3])
create(t, P1, MONK_, 2, (138, 152))
t.new_effect.research_technology(source_player=P1, technology=TechInfo.SANCTITY.ID, force_research_technology=1)
e_add(t, "M1_Molva", 1)
e_set(t, "M1_S5_Done", 1)
e_set(t, "M1_Arrive_3", 1)
Lsay(t, "S5_Done", types=("цель", "диалог", "сообщение"))
for k, u in enumerate(YEL_MONKS):
    a = aux("S5_Fail", f"m{k}")
    c_flag(a, "M1_S5_Joined", 1)
    a.new_condition.destroy_object(unit_object=u.reference_id)
    e_set(a, "M1_S5_Dead", 1)
t = trig("S5_Fail")
c_flag(t, "M1_S5_Dead", 1)
c_flag(t, "M1_S5_Done", 0)
e_set(t, "M1_S5_Failed", 1)
Lsay(t, "S5_Fail", types=("сообщение", "цель"))
t = trig("E18_News_1")
c_flag(t, "M1_CastleFall", 1)
c_dl(t, "dl_News1")
e_add(t, "Put_D", 5)
e_add(t, "Put_DT", 5)
Lsay(t, "E18_News_1", types=("справка", "диалог"))

# ================================================================ 8. ПОЛЬСКИЙ КОНТРАКТ
t = trig("M1_ContractUnlock")
c_flag(t, "M1_CastleDone", 1)
t.new_effect.enable_disable_technology(source_player=P1, technology=CONTRACT, enabled=1)
Lsay(t, "M1_ContractUnlock", types=("диалог", "сообщение", "подсказка"))
t = trig("M1_Contract_Done")
t.new_condition.research_technology(source_player=P1, technology=CONTRACT)
t.new_effect.enable_disable_object(object_list_unit_id=WH, source_player=P1, enabled=1)
t.new_effect.add_train_location(object_list_unit_id=WH, source_player=P1, object_list_unit_id_2=STAB_, button_location=ButtonLocation.r1c3.value,
                                train_time=35)
t.new_effect.change_object_cost(object_list_unit_id=WH, source_player=P1, resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=100,
                                resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0, resource_3=Attribute.GOLD_STORAGE, resource_3_quantity=140)
e_set(t, "M1_ContractOn", 1)
e_dl(t, "dl_WHArrive", 60)
Lsay(t, "M1_Contract_Done", types=("сообщение", "диалог"))
t = trig("M1_WHussar_Arrive")
c_flag(t, "M1_ContractOn", 1)
c_dl(t, "dl_WHArrive")
create(t, P1, WH, 2, (SX, SY + 3))
for c in (WH,):
    t.new_effect.task_object(object_list_unit_id=c, source_player=P1, location_x=SX, location_y=SY, action_type=ActionType.MOVE,
                             area_x1=SX - 6, area_y1=SY - 6, area_x2=SX + 6, area_y2=SY + 6)
Lsay(t, "M1_WHussar_Arrive", types=("сообщение", "диалог"))
t = trig("M1_WHussar_Cap", looping=True)
c_flag(t, "M1_ContractOn", 1)
c_in(t, P1, WH, ALL, 6)
t.new_effect.enable_disable_object(object_list_unit_id=WH, source_player=P1, enabled=0)
t = aux("M1_WHussar_Cap", "open", looping=True)
c_flag(t, "M1_ContractOn", 1)
c_in(t, P1, WH, ALL, 6, inverted=1)
t.new_effect.enable_disable_object(object_list_unit_id=WH, source_player=P1, enabled=1)

# ================================================================ 9. МАРШ И ТАБОР
t = trig("M1_Ambush")
c_dm(t, "Z_Ambush")
c_flag(t, "M1_AmbushFired", 0)
for c, n in ((SPEAR_, 4), (HC_, 3)):
    for (x, y) in spots(120, 138, n):
        t.new_effect.create_object(object_list_unit_id=c, source_player=P3, location_x=x, location_y=y)
    t.new_effect.attack_move(object_list_unit_id=c, source_player=P3, location_x=118, location_y=146, area_x1=112, area_y1=128, area_x2=128,
                             area_y2=142)
e_set(t, "M1_AmbushFired", 1)
say(t, L("M1_Ambush", "сообщение"))
a = aux("M1_Ambush", "retreat")
c_flag(a, "M1_AmbushFired", 1)
a.new_condition.timer(timer=45)
for c in (SPEAR_, HC_):
    a.new_effect.task_object(object_list_unit_id=c, source_player=P3, location_x=118, location_y=132, action_type=ActionType.MOVE,
                             area_x1=100, area_y1=120, area_x2=140, area_y2=160)
t = trig("E12_PosadBurns")
c_in(t, P1, -1, R(160, 168, 40))
c_flag(t, "M1_E12", 0)
e_set(t, "M1_E12", 1)
cam(t, (146, 168))
for u in NS_HOUSES:
    for dx, dy, fl in ((0, 0, "FLAME1"), (1, 1, "FLAME3")):
        t.new_effect.create_object(object_list_unit_id=K(fl), source_player=0, location_x=int(u.x) + dx, location_y=int(u.y) + dy)
    t.new_effect.create_object(object_list_unit_id=K("SMOKE"), source_player=0, location_x=int(u.x), location_y=int(u.y))
e_dl(t, "dl_Burn", 20)
e_dl(t, "dl_FlamesOff", 360)
Lsay(t, "E12_PosadBurns", types=("плашка", "справка", "диалог", "сообщение"))
a = aux("E12_PosadBurns", "ruins")
c_flag(a, "M1_E12", 1)
c_dl(a, "dl_Burn")
a.new_effect.remove_object(source_player=P4, selected_object_ids=ids(NS_HOUSES))
for k, u in enumerate(NS_HOUSES):
    a.new_effect.create_object(object_list_unit_id=K(["BURNED_BUILDING_A", "BURNED_BUILDING_B", "BURNED_BUILDING_C"][k % 3]), source_player=0,
                               location_x=int(u.x), location_y=int(u.y))
t = trig("E12_FlamesOff")
c_flag(t, "M1_E12", 1)
c_dl(t, "dl_FlamesOff")
for fl in ("FLAME1", "FLAME2", "FLAME3", "FLAME4"):
    t.new_effect.remove_object(object_list_unit_id=K(fl), source_player=0, area_x1=130, area_y1=150, area_x2=160, area_y2=190)
say(t, L("E12_FlamesOff", "сообщение"))

# --- Ставка (табор)
CAMP_BLD = [NAMED[k] for k in ("campTC", "campBarr", "campArch", "campStable", "campMon")]
t = trig("T_CampCheck")
c_dm(t, "Z_Camp")
c_mil(t, P1, Z["Z_Camp"], 15)
t.new_effect.change_ownership(source_player=0, target_player=P1, selected_object_ids=ids(CAMP_BLD), flash_object=1)
create_cells(t, P1, K("ARMY_TENT_A"), CAMP_PLAN["tent_main"])
create_cells(t, P1, K("TENT_A"), CAMP_PLAN["g1_tents"][:3])
create_cells(t, P1, K("TENT_B"), CAMP_PLAN["g1_tents"][3:5])
create_cells(t, P1, K("TENT_C"), CAMP_PLAN["g1_tents"][5:6])
create_cells(t, P1, K("TENT_D"), CAMP_PLAN["g1_tents"][6:7])
create_cells(t, P1, K("TENT_E"), CAMP_PLAN["g1_tents"][7:8])
create_cells(t, 0, K("CART"), CAMP_PLAN["g1_carts"])
create_cells(t, 0, K("STAKE_BARRICADE"), CAMP_PLAN["g1_barr"])
misc = CAMP_PLAN["g1_misc"]
create_cells(t, 0, K("BONFIRE"), misc[:4])
create_cells(t, 0, K("SUPPLY_CART_A"), misc[4:5])
create_cells(t, 0, K("SUPPLY_CART_B"), misc[5:6])
create_cells(t, 0, K("BARRELS"), misc[6:12])
for k, (x, y) in enumerate(CAMP_PLAN["g1_horses"]):
    t.new_effect.create_object(object_list_unit_id=K("HORSE_" + "ABCDE"[k % 5]), source_player=0, location_x=x, location_y=y)
create_cells(t, P1, VILL_M, CAMP_PLAN["g1_vill"])
give(t, food=400, wood=400, gold=300)
heal_all(t)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_P, enabled=1)
e_set(t, "M1_CampPlaced", 1)
e_set(t, "M1_Goal_Put", 1)
e_dl(t, "dl_M1_Hint_Put_0", 300)
e_dl(t, "dl_M1_Hint_Put_1", 660)
e_dl(t, "dl_M1_Hint_Put_2", 1020)
e_dl(t, "dl_NSmin", 480)
e_dl(t, "dl_Camp2", 240)
e_dl(t, "dl_Crowd", 120)
e_dl(t, "dl_News2", 60)
e_dl(t, "dl_E13", 210)
e_dl(t, "dl_E15", 360)
e_dl(t, "dl_E16", 540)
flag_mark(t, (176, 72))
Lsay(t, "T_CampCheck", types=("сообщение", "цель", "диалог"))
say(t, L("bribe_putivl", "сообщение"))
camp_check = t
CAMP_TC_AREA = (138, 154, 141, 157)
t = trig("M1_Camp_Stage_2")
c_flag(t, "M1_CampPlaced", 1)
c_dl(t, "dl_Camp2")
create_cells(t, P1, K("TENT_A"), CAMP_PLAN["g2_tents"][:3])
create_cells(t, P1, K("TENT_B"), CAMP_PLAN["g2_tents"][3:])
m2 = CAMP_PLAN["g2_misc"]
create_cells(t, 0, K("WEAPON_RACK"), m2[:3])
create_cells(t, 0, K("WATER_TROUGH"), m2[3:5])
create_cells(t, 0, K("SMOKE"), m2[5:9])
create_cells(t, 0, K("WEAPON_RACK"), m2[9:10])
say(t, L("M1_Camp_Stage_2", "сообщение"))
for k, sfx in enumerate("abcd"):
    t = trig(f"M1_Camp_Stage_3{sfx}")
    c_flag(t, "M1_CampPlaced", 1)
    c_flag(t, f"M1_Arrive_{k + 1}", 1)
    create_cells(t, P1, K("TENT_C"), CAMP_PLAN["g3"][k])
    create_cells(t, 0, K("FLAG_B"), CAMP_PLAN["g3_flag"][k:k + 1])
    say(t, L(f"M1_Camp_Stage_3{sfx}", "сообщение"))
t = trig("M1_Camp_Stage_4")
c_flag(t, "M1_AssaultDone", 1)
create_cells(t, 0, K("GRAVE"), CAMP_PLAN["g4_graves"])
create_cells(t, P8, MAA_, CAMP_PLAN["g4_units"])
e_dl(t, "dl_WoundedOff", 180)
say(t, L("M1_Camp_Stage_4", "сообщение"))
a = aux("M1_Camp_Stage_4", "off")
c_flag(a, "M1_AssaultDone", 1)
c_dl(a, "dl_WoundedOff")
a.new_effect.remove_object(object_list_unit_id=MAA_, source_player=P8, area_x1=124, area_y1=140, area_x2=160, area_y2=175)
t = trig("M1_Camp_Stage_5")
c_flag(t, "M1_VoevodaArrive", 1)
create_cells(t, P1, K("TENT_D"), CAMP_PLAN["g5_tents"])
create_cells(t, P7, VILL_M, CAMP_PLAN["g5_vill"])
create_cells(t, 0, K("FLAG_A"), CAMP_PLAN["g5_misc"][:2])
create_cells(t, 0, K("TORCH_A"), CAMP_PLAN["g5_misc"][2:8])
say(t, L("M1_Camp_Stage_5", "сообщение"))
t = trig("T_CampHP50")
c_flag(t, "M1_CampPlaced", 1)
t.new_condition.object_hp(quantity=1200, unit_object=NAMED["campTC"].reference_id, comparison=Comparison.LESS)
e_set(t, "M1_H3_Fail", 1)
say(t, L("T_CampHP50", "сообщение"))
volunteer_variants("E06b_Crowd", lambda t: (c_flag(t, "M1_CampPlaced", 1), c_dl(t, "dl_Crowd")), 0, 0, (138, 148),
                   extra_fn=None, lines=None) if False else None
t = trig("E06b_Crowd")
c_flag(t, "M1_CampPlaced", 1)
c_dl(t, "dl_Crowd")
molva_cmp(t, lo=4)
create(t, P1, CAVARCH_, 4, (138, 148))
e_set(t, "M1_Arrive_4", 1)
Lsay(t, "E06b_Crowd", types=("сообщение", "рассказчик", "диалог"))
t = trig("E18_News_2")
c_flag(t, "M1_CampPlaced", 1)
c_dl(t, "dl_News2")
e_set(t, "M1_News2", 1)
Lsay(t, "E18_News_2", types=("справка", "диалог"))
# E13: поджог табора, лазутчик
t = trig("E13_NightFire")
c_flag(t, "M1_CampPlaced", 1)
c_dl(t, "dl_E13")
c_flag(t, "M1_E13", 0)
e_set(t, "M1_E13", 1)
mood(t, ColorMood.NIGHT, 5)
los(t, -3)
e_dl(t, "dl_E13End", 120)
e_dl(t, "dl_E13Fire", 60)
create(t, P4, VILL_F, 1, (131, 156))
t.new_effect.modify_attribute(source_player=P4, object_list_unit_id=VILL_F, object_attributes=ObjectAttribute.MOVEMENT_SPEED, operation=Operation.SET,
                              quantity=1.2)
t.new_effect.task_object(object_list_unit_id=VILL_F, source_player=P4, location_x=150, location_y=171, action_type=ActionType.MOVE,
                         area_x1=126, area_y1=146, area_x2=140, area_y2=162)
e_dl(t, "dl_SpyChk", 40)
Lsay(t, "E13_NightFire", types=("сообщение", "рассказчик", "подсказка"))
t = aux("E13_NightFire", "tick", looping=True)
c_flag(t, "M1_E13", 1)
t.new_condition.timer(timer=5)
c_dl(t, "dl_E13Fire") if False else None
c_flag(t, "M1_E13Fire", 0)
for c in (K("TENT_A"), K("TENT_B"), STAB_):
    t.new_effect.damage_object(quantity=40, object_list_unit_id=c, source_player=P1, area_x1=Z["Z_Camp"][0] - 6, area_y1=Z["Z_Camp"][1] - 4,
                               area_x2=Z["Z_Camp"][2] + 4, area_y2=Z["Z_Camp"][3] + 4, max_units_affected=2)
a = aux("E13_NightFire", "fireoff")
c_flag(a, "M1_E13", 1)
a.new_condition.timer(timer=60)
e_set(a, "M1_E13Fire", 1)
a = aux("E13_NightFire", "end")
c_flag(a, "M1_E13", 1)
c_dl(a, "dl_E13End")
mood(a, ColorMood.AUTUMN, 10)
los(a, 3)
t = trig("E13_SpyEscaped")
c_flag(t, "M1_E13", 1)
c_flag(t, "M1_Spy_Done", 0)
c_in(t, P4, VILL_F, (143, 148, 149, 158))
c_dl(t, "dl_SpyChk")
e_set(t, "M1_Spy_Done", 1)
e_set(t, "M1_Spy_Escaped", 1)
Lsay(t, "E13_SpyEscaped", types=("сообщение", "диалог"))
t = trig("E13_SpyCaught")
c_flag(t, "M1_E13", 1)
c_flag(t, "M1_Spy_Done", 0)
c_dl(t, "dl_SpyChk")
c_in(t, P4, VILL_F, (126, 146, 141, 164), 1, 1)
e_set(t, "M1_Spy_Done", 1)
e_set(t, "M1_Spy_Caught", 1)
Lsay(t, "E13_SpyCaught", types=("сообщение", "диалог"))
# S4: обоз Басманова
t = trig("S4_Open")
c_flag(t, "M1_Spy_Caught", 1)
e_set(t, "M1_S4_Open", 1)
Lsay(t, "S4_Open", types=("цель", "сообщение", "диалог"))
a = aux("S4_Open", "near")
c_in(a, P1, -1, R(170, 90, 24))
c_flag(a, "M1_CampPlaced", 1)
c_flag(a, "M1_S4_Open", 0)
e_set(a, "M1_S4_Open", 1)
t = trig("S4_ConvoyGo")
c_flag(t, "M1_S4_Open", 1)
c_flag(t, "M1_ConvoyOut", 0)
e_set(t, "M1_ConvoyOut", 1)
create(t, P4, K("OX_CART") if False else K("CART"), 3, (170, 104))
create(t, P4, KNIGHT_, 4, (170, 106), 1)
create(t, P4, SPEAR_, 4, (170, 108), 1)
for c in (K("CART"), KNIGHT_, SPEAR_):
    t.new_effect.task_object(object_list_unit_id=c, source_player=P4, location_x=176, location_y=159, action_type=ActionType.MOVE,
                             area_x1=166, area_y1=98, area_x2=176, area_y2=112)
t.new_effect.modify_attribute(source_player=P4, object_list_unit_id=K("CART"), object_attributes=ObjectAttribute.MOVEMENT_SPEED,
                              operation=Operation.SET, quantity=0.8)
say(t, L("S4_ConvoyGo", "сообщение"))
CONVOY_AREA = (160, 100, 190, 170)
for k in (1, 2, 3):
    t = trig(f"S4_CartTake_{k}")
    c_flag(t, "M1_ConvoyOut", 1)
    c_flag(t, "M1_CartTaken", k - 1)
    if k == 1:
        c_none(t, P4, KNIGHT_, CONVOY_AREA)
        c_none(t, P4, SPEAR_, CONVOY_AREA)
        t.new_effect.change_ownership(object_list_unit_id=K("CART"), source_player=P4, target_player=P1, area_x1=CONVOY_AREA[0],
                                      area_y1=CONVOY_AREA[1], area_x2=CONVOY_AREA[2], area_y2=CONVOY_AREA[3])
        t.new_effect.task_object(object_list_unit_id=K("CART"), source_player=P1, location_x=140, location_y=153, action_type=ActionType.MOVE,
                                 area_x1=CONVOY_AREA[0], area_y1=CONVOY_AREA[1], area_x2=CONVOY_AREA[2], area_y2=CONVOY_AREA[3])
        e_dl(t, "dl_CartMsg", 4)
    else:
        c_dl(t, "dl_CartMsg")
        e_dl(t, "dl_CartMsg", 4)
    e_add(t, "M1_CartTaken", 1)
    say(t, L(f"S4_CartTake_{k}", "сообщение"))
t = trig("S4_Win")
c_flag(t, "M1_ConvoyOut", 1)
c_flag(t, "M1_S4_Done", 0)
c_in(t, P1, K("CART"), Z["Z_Camp"], 2)
e_set(t, "M1_S4_Done", 1)
e_set(t, "M1_TreasuryIn", 1)
e_set(t, "M1_Relief3Off", 1)
give(t, gold=500, food=200)
Lsay(t, "S4_Win", types=("цель", "диалог", "сообщение"))
t = trig("S4_Fail")
c_flag(t, "M1_ConvoyOut", 1)
c_flag(t, "M1_S4_Done", 0)
c_in(t, P4, K("CART"), Z["Z_Ford_North"])
e_set(t, "M1_S4_Done", 2)
Lsay(t, "S4_Fail", types=("сообщение", "цель"))
# E15: жалованье
t = trig("E15_Pay")
c_flag(t, "M1_CampPlaced", 1)
c_dl(t, "dl_E15")
e_set(t, "M1_PayOpen", 1)
e_dl(t, "dl_PayEnd", 240)
t.new_effect.enable_disable_technology(source_player=P1, technology=PAYTECH, enabled=1)
Lsay(t, "E15_Pay", types=("сообщение", "диалог"))
t = trig("E15_Paid")
t.new_condition.research_technology(source_player=P1, technology=PAYTECH)
e_set(t, "M1_PayDone", 1)
t.new_effect.change_technology_cost(source_player=P1, technology=CONTRACT, resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=140,
                                    resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0, resource_3=Attribute.GOLD_STORAGE,
                                    resource_3_quantity=280)
Lsay(t, "E15_Paid", types=("сообщение", "диалог"))
t = trig("E15_Leave")
c_flag(t, "M1_PayOpen", 1)
c_flag(t, "M1_PayDone", 0)
c_flag(t, "M1_TreasuryIn", 0)
c_dl(t, "dl_PayEnd")
t.new_effect.remove_object(object_list_unit_id=HUSSAR_, source_player=P1, area_x1=0, area_y1=0, area_x2=S - 1, area_y2=S - 1, max_units_affected=3)
t.new_effect.enable_disable_technology(source_player=P1, technology=PAYTECH, enabled=0)
e_add(t, "M1_Molva", -1)
Lsay(t, "E15_Leave", types=("сообщение", "диалог", "рассказчик"))
a = aux("E15_Leave", "treasury")
c_flag(a, "M1_PayOpen", 1)
c_flag(a, "M1_TreasuryIn", 1)
a.new_effect.enable_disable_technology(source_player=P1, technology=PAYTECH, enabled=0)
t = trig("E20_Sambor")
c_flag(t, "M1_PayOpen", 1)
a = aux("E20_Sambor", "wait")
t.enabled = False
a.enabled = True
c_flag(a, "M1_PayOpen", 1)
a.new_condition.timer(timer=90)
e_set(a, "M1_E20", 1)
a.new_effect.activate_trigger(trigger_id=t.trigger_id)
Lsay(t, "E20_Sambor", types=("диалог", "рассказчик"))
# E16: ночной приступ
t = trig("E16_Assault")
c_flag(t, "M1_CampPlaced", 1)
c_dl(t, "dl_E16")
c_flag(t, "M1_Spy_Done", 1)
c_flag(t, "M1_E16", 0)
e_set(t, "M1_E16", 1)
mood(t, ColorMood.NIGHT, 5)
los(t, -3)
t.new_effect.change_diplomacy(diplomacy=DiplomacyState.ENEMY, source_player=P8, target_player=P4, mutual_diplomacy=1)
t.new_effect.disable_unit_attackable(source_player=P4, selected_object_ids=list(ids(ns_wall.values())) + ids(GATES[P4]))
create(t, P8, MAA_, 10, (142, 169))
create(t, P8, ARCHER_, 6, (142, 172), 1)
create(t, P8, K("SIEGE_CAMP_EQUIPMENT") if False else K("WEAPON_RACK"), 2, (146, 168))
for c in (MAA_, ARCHER_):
    t.new_effect.attack_move(object_list_unit_id=c, source_player=P8, location_x=150, location_y=171, area_x1=136, area_y1=160, area_x2=150,
                             area_y2=175)
e_dl(t, "dl_E16Back", 90)
e_dl(t, "dl_E16Gone", 150)
e_dl(t, "dl_E16End", 150)
Lsay(t, "E16_Assault", types=("плашка", "справка", "рассказчик", "диалог"))
a = aux("E16_Assault", "back")
c_flag(a, "M1_E16", 1)
c_dl(a, "dl_E16Back")
for c in (MAA_, ARCHER_):
    a.new_effect.task_object(object_list_unit_id=c, source_player=P8, location_x=140, location_y=158, action_type=ActionType.MOVE,
                             area_x1=130, area_y1=155, area_x2=158, area_y2=185)
t = trig("E16_End")
c_flag(t, "M1_E16", 1)
c_dl(t, "dl_E16End")
c_flag(t, "M1_AssaultDone", 0)
e_set(t, "M1_AssaultDone", 1)
mood(t, ColorMood.AUTUMN, 10)
los(t, 3)
t.new_effect.remove_object(source_player=P8, area_x1=120, area_y1=140, area_x2=160, area_y2=190, object_type=int(ObjectType.MILITARY))
t.new_effect.enable_unit_attackable(source_player=P4, selected_object_ids=list(ids(ns_wall.values())) + ids(GATES[P4]))
t.new_effect.change_diplomacy(diplomacy=DiplomacyState.NEUTRAL, source_player=P8, target_player=P4, mutual_diplomacy=1)
e_dl(t, "dl_NSL", 150)
e_dl(t, "dl_News3", 0)
Lsay(t, "E16_End", types=("сообщение", "рассказчик", "диалог"))
# вылазка Новгорода-Северского
w = trig("T_NSSortie_1_Warn")
c_flag(w, "M1_AssaultDone", 1)
c_dl(w, "dl_NSL")
c_flag(w, "M1_NSWarned", 0)
e_set(w, "M1_NSWarned", 1)
e_dl(w, "dl_NSLaunch", 30)
flag_mark(w, (160, 176), temp=True)
say(w, L("T_NSSortie_1_Warn", "сообщение"))
ns1 = trig("T_NSSortie_1")
c_flag(ns1, "M1_NSWarned", 1)
c_dl(ns1, "dl_NSLaunch")
c_flag(ns1, "M1_NSAFired", 0)
GATE_N = (152, 169, 158, 173)
NS_UNITS = [MAA_, HC_, KNIGHT_, SPEAR_]
for c, n in ((MAA_, 12), (HC_, 8), (KNIGHT_, 6)):
    for (x, y) in spots(154, 171, n, 0):
        ns1.new_effect.create_object(object_list_unit_id=c, source_player=P4, location_x=x, location_y=y)
for c in NS_UNITS:
    ns1.new_effect.attack_move(object_list_unit_id=c, source_player=P4, location_x=140, location_y=156, area_x1=GATE_N[0] - 4, area_y1=GATE_N[1] - 4,
                               area_x2=GATE_N[2] + 4, area_y2=GATE_N[3] + 4)
e_set(ns1, "M1_NSAFired", 1)
e_dl(ns1, "dl_NSB", 90)
Lsay(ns1, "T_NSSortie_1", types=("диалог",))
say(ns1, L("T_NSSortie_1", "сообщение")[:1])
wb = aux("T_NSSortie_1", "waveB")
c_flag(wb, "M1_NSAFired", 1)
c_flag(wb, "M1_NSBFired", 0)
c_dl(wb, "dl_NSB")
for c, n in ((SPEAR_, 10), (HC_, 4)):
    for (x, y) in spots(154, 171, n, 0):
        wb.new_effect.create_object(object_list_unit_id=c, source_player=P4, location_x=x, location_y=y)
for c in NS_UNITS:
    wb.new_effect.attack_move(object_list_unit_id=c, source_player=P4, location_x=140, location_y=156, area_x1=GATE_N[0] - 4, area_y1=GATE_N[1] - 4,
                              area_x2=GATE_N[2] + 4, area_y2=GATE_N[3] + 4)
e_set(wb, "M1_NSBFired", 1)
e_dl(wb, "dl_NSEnd", 240)
e_dl(wb, "dl_Relief4", 180)
say(wb, L("T_NSSortie_1", "сообщение")[1:2])
wd = trig("M1_NSSortieDone")
c_flag(wd, "M1_NSBFired", 1)
c_dl(wd, "dl_NSEnd")
c_flag(wd, "M1_NSSortieDone", 0)
e_set(wd, "M1_NSSortieDone", 1)
Lsay(wd, "M1_NSSortieDone", types=("сообщение", "диалог"))
# вести 3 и гонец
t = trig("E18_News_3")
c_flag(t, "M1_AssaultDone", 1)
c_flag(t, "M1_NewsDone3", 0)
e_set(t, "M1_NewsDone3", 1)
create(t, P4, SCOUT_, 1, (173, 173))
t.new_effect.task_object(object_list_unit_id=SCOUT_, source_player=P4, location_x=170, location_y=102, action_type=ActionType.MOVE,
                         area_x1=165, area_y1=165, area_x2=180, area_y2=175)
Lsay(t, "E18_News_3", types=("сообщение", "рассказчик"))
t = trig("E18_CourierStopped")
c_flag(t, "M1_NewsDone3", 1)
c_flag(t, "M1_CourierStopped", 0)
c_flag(t, "M1_CourierThrough", 0)
c_dl(t, "dl_NSL") if False else None
t.new_condition.timer(timer=20)
c_none(t, P4, SCOUT_)
e_set(t, "M1_CourierStopped", 1)
Lsay(t, "E18_CourierStopped", types=("сообщение", "диалог"))
a = aux("E18_CourierStopped", "arrived", looping=False)
c_flag(a, "M1_NewsDone3", 1)
c_in(a, P4, SCOUT_, Z["Z_Courier_End"])
e_set(a, "M1_CourierThrough", 1)
# подкрепления
r1 = trig("T_Relief_1")
c_flag(r1, "M1_PosadDone", 1)
c_flag(r1, "M1_CastleFall", 0)
c_flag(r1, "M1_R1Armed", 1)
c_dl(r1, "dl_Relief1")
create(r1, P6, SPEAR_, 4, (93, 123))
create(r1, P6, HC_, 3, (93, 125), 1)
say(r1, L("T_Relief_1", "сообщение", cond="ещё не взят"))
r1b = aux("T_Relief_1", "ns")
c_flag(r1b, "M1_PosadDone", 1)
c_flag(r1b, "M1_CastleFall", 1)
c_flag(r1b, "M1_R1Armed", 1)
c_dl(r1b, "dl_Relief1")
create(r1b, P4, SPEAR_, 4, (155, 171))
create(r1b, P4, HC_, 3, (155, 173), 1)
say(r1b, L("T_Relief_1", "сообщение", cond="если замок взят"))
a = aux("T_Relief_1", "arm")
c_flag(a, "M1_PosadDone", 1)
c_flag(a, "M1_R1Armed", 0)
e_set(a, "M1_R1Armed", 1)
e_dl(a, "dl_Relief1", 240)
r2 = trig("T_Relief_2")
c_flag(r2, "M1_News2", 1)
create(r2, P4, MAA_, 8, (155, 171))
create(r2, P4, HC_, 4, (155, 173), 1)
Lsay(r2, "T_Relief_2", types=("рассказчик", "сообщение"))
r3 = trig("T_Relief_3")
c_flag(r3, "M1_CampPlaced", 1)
c_clock(r3, 99999) if False else None
c_flag(r3, "M1_R3Armed", 1)
c_dl(r3, "dl_Relief3")
c_flag(r3, "M1_Relief3Off", 0)
create(r3, P4, KNIGHT_, 6, (155, 171))
create(r3, P4, HC_, 6, (155, 173), 1)
say(r3, L("T_Relief_3", "сообщение"))
a = aux("T_Relief_3", "arm")
c_flag(a, "M1_CampPlaced", 1)
c_flag(a, "M1_R3Armed", 0)
e_set(a, "M1_R3Armed", 1)
e_dl(a, "dl_Relief3", 360)
t = trig("T_Putivl_Toughen")
c_flag(t, "M1_CourierThrough", 1)
c_flag(t, "M1_PutivlDone", 0)
c_flag(t, "M1_CourierStopped", 0)
c_flag(t, "M1_Putivl_Force", 0)
e_set(t, "Put_D", 40)
e_set(t, "Put_DT", 24)
say(t, L("T_Putivl_Toughen", "сообщение"))
r4 = trig("T_Relief_4")
c_flag(r4, "M1_NSBFired", 1)
c_dl(r4, "dl_Relief4")
create(r4, P4, SPEAR_, 10, (155, 171))
say(r4, L("T_Relief_4", "сообщение", idx=0))
r4b = aux("T_Relief_4", "put")
c_flag(r4b, "M1_NSBFired", 1)
c_dl(r4b, "dl_Relief4")
c_flag(r4b, "M1_PutivlDone", 0)
create(r4b, P5, SPEAR_, 8, (170, 78))
say(r4b, L("T_Relief_4", "сообщение", idx=1))

# ================================================================ 10. ПУТИВЛЬ
leaflet("Put", "Z_Leaflet_Put")
conversion("Put", ["Z_Conv_Put"], "M1_PutivlDone", goal_extra="M1_CampPlaced", use_vars=True)
bribe("Put", BRIBE_P, ["Z_Conv_Put"], "M1_PutivlDone")
a = aux("T_Putivl_Force", "tc")
c_flag(a, "M1_PutivlDone", 0)
a.new_condition.destroy_object(unit_object=NAMED["PutTC"].reference_id)
e_set(a, "M1_PutForce_Go", 1)
a = aux("T_Putivl_Force", "kills")
c_flag(a, "M1_PutivlDone", 0)
c_mil(a, P5, ALL, 7, 1)
c_flag(a, "M1_CampPlaced", 1)
e_set(a, "M1_PutForce_Go", 1)
t = trig("T_Putivl_Force")
c_flag(t, "M1_PutForce_Go", 1)
c_flag(t, "M1_PutivlDone", 0)
c_flag(t, "M1_Putivl_Force", 0)
e_set(t, "M1_Putivl_Force", 1)
e_set(t, "Put_D", 60)
e_set(t, "Put_DT", 60)
e_add(t, "M1_Molva", -2)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_P, enabled=0)
say(t, L("T_Putivl_Force", "сообщение"))
t = trig("T_Putivl_Flip")
c_flag(t, "M1_Put_Go", 1)
c_flag(t, "M1_PutivlDone", 0)
villagers_to_p7(t, P5, A_PUT)
transfer(t, P5, ALL)
t.new_effect.change_ownership(source_player=P7, target_player=P1, selected_object_ids=ids([SALT, RUBEC, SUTUP]))
t.new_effect.unlock_gate(selected_object_ids=ids(GATES[P5]))
e_set(t, "M1_PutivlDone", 1)
e_set(t, "M1_Put_Reading", 0)
t.new_effect.enable_disable_technology(source_player=P1, technology=BRIBE_P, enabled=0)
for u in (SALT, RUBEC, SUTUP):
    t.new_effect.change_object_stance(source_player=P1, attack_stance=AttackStance.NO_ATTACK_STANCE, selected_object_ids=[u.reference_id])
    t.new_effect.task_object(source_player=P1, location_x=140, location_y=153, action_type=ActionType.MOVE, selected_object_ids=[u.reference_id])
create(t, P1, SPEAR_, 2, (176, 90))
t.new_effect.task_object(object_list_unit_id=SPEAR_, source_player=P1, location_x=140, location_y=153, action_type=ActionType.MOVE,
                         area_x1=160, area_y1=82, area_x2=190, area_y2=100)
e_dl(t, "dl_Rumor_Put", 120)
e_set(t, "M1_Goal_Voevoda", 1)
say(t, L("T_Putivl_Flip", "сообщение"))
a = aux("T_Putivl_Flip", "treasury")
c_flag(a, "M1_PutivlDone", 1)
c_flag(a, "M1_Putivl_Force", 0)
c_flag(a, "M1_BribePaid_Put", 0)
c_flag(a, "M1_TrIn", 0)
e_set(a, "M1_TrIn", 1)
give(a, gold=500)
a = aux("T_Putivl_Flip", "molva")
c_flag(a, "M1_PutivlDone", 1)
c_flag(a, "M1_Putivl_Force", 0)
c_flag(a, "M1_BribePaid_Put", 0)
c_flag(a, "M1_H1_Fail", 0)
c_flag(a, "M1_PutMolva", 0)
e_set(a, "M1_PutMolva", 1)
e_add(a, "M1_Molva", 1)
volunteer_variants("T_Rumor_Put", lambda t: (c_flag(t, "M1_PutivlDone", 1), c_flag(t, "M1_BribePaid_Put", 0), c_dl(t, "dl_Rumor_Put")), 3, 3,
                   (136, 150), lines=L("T_Rumor_Put", "сообщение")[:1])
a = aux("T_Rumor_Put", "bribe")
c_flag(a, "M1_PutivlDone", 1)
c_flag(a, "M1_BribePaid_Put", 1)
c_dl(a, "dl_Rumor_Put")
create(a, P1, MAA_, 2, (136, 150))
create(a, P1, ARCHER_, 1, (136, 150), 1)
say(a, L("T_Rumor_Put", "сообщение")[1:2])
# S6
t = trig("S6_Open")
c_flag(t, "M1_CampPlaced", 1)
Lsay(t, "S6_Open", types=("цель",))
a = aux("S6_Done", "sutdead")
a.new_condition.destroy_object(unit_object=SUTUP.reference_id)
e_set(a, "M1_SutupovDead", 1)
t = trig("S6_Done")
c_flag(t, "M1_PutivlDone", 1)
c_flag(t, "M1_Putivl_Force", 0)
c_flag(t, "M1_BribePaid_Put", 0)
c_flag(t, "M1_S6_Done", 0)
t.new_condition.bring_object_to_area(unit_object=SUTUP.reference_id, area_x1=Z["Z_Camp"][0], area_y1=Z["Z_Camp"][1], area_x2=Z["Z_Camp"][2],
                                     area_y2=Z["Z_Camp"][3])
e_set(t, "M1_S6_Done", 1)
e_set(t, "M1_TreasuryIn", 1)
give(t, gold=500, food=300)
Lsay(t, "S6_Done", types=("цель", "справка", "диалог"))
a = aux("M1_VoevodaArrive", "rubets_dead")
a.new_condition.destroy_object(unit_object=RUBEC.reference_id)
e_set(a, "M1_RubetsDead", 1)
t = trig("M1_VoevodaArrive")
c_flag(t, "M1_PutivlDone", 1)
c_flag(t, "M1_VoevodaArrive", 0)
t.new_condition.bring_object_to_area(unit_object=SALT.reference_id, area_x1=Z["Z_Camp"][0], area_y1=Z["Z_Camp"][1], area_x2=Z["Z_Camp"][2],
                                     area_y2=Z["Z_Camp"][3])
c_dm(t, "Z_Camp")
c_in(t, P1, TC_, CAMP_TC_AREA)
e_set(t, "M1_VoevodaArrive", 1)
e_dl(t, "dl_Win", 30)
cam(t, (140, 156))
for u in (SALT, RUBEC):
    t.new_effect.stop_object(source_player=P1, selected_object_ids=[u.reference_id])
Lsay(t, "M1_VoevodaArrive", types=("плашка", "рассказчик", "диалог"))
for hn, flagname, cond_fn in (("h1_mor", "M1_H1_Fail", lambda a: (c_flag(a, "M1_MoravskDone", 0), c_mil(a, P2, ALL, 16, 1))),):
    pass
a = aux("T_Win", "h1_mor")
c_flag(a, "M1_MoravskDone", 0)
c_mil(a, P2, ALL, 15, 1)
e_set(a, "M1_H1_Fail", 1)
a = aux("T_Win", "h1_put")
c_flag(a, "M1_PutivlDone", 0)
c_mil(a, P5, ALL, 17, 1)
e_set(a, "M1_H1_Fail", 1)
a = aux("T_Win", "h1_force")
c_flag(a, "M1_Putivl_Force", 1)
e_set(a, "M1_H1_Fail", 1)
a = aux("T_Win", "h2_pre")
c_flag(a, "M1_MoravskDone", 0)
c_in(a, P1, MONK_, ALL, 3, 1)
e_set(a, "M1_H2_Fail", 1)
a = aux("T_Win", "h2_post")
c_flag(a, "M1_MoravskDone", 1)
c_in(a, P1, MONK_, ALL, 3, 1)
c_flag(a, "M1_TsarevichOn", 0) if False else None
e_set(a, "M1_H2_Fail", 1)
win_lines = L("T_Win", "сообщение")
t = trig("T_Win")
c_flag(t, "M1_VoevodaArrive", 1)
c_dl(t, "dl_Win")
c_flag(t, "M1_NSSortieDone", 1)
c_in(t, P1, TC_, CAMP_TC_AREA)
cum = say(t, L("T_Win", "рассказчик"))
for hname in ("H1", "H2", "H3", "H4"):
    fv = f"M1_{hname}_Fail"
    ok_l = [x for x in win_lines if x.cond.startswith(hname) and "не выполнена" not in x.cond][0]
    bad_l = [x for x in win_lines if x.cond.startswith(hname) and "не выполнена" in x.cond][0]
    for fail, ln in ((0, ok_l), (1, bad_l)):
        a = aux("T_Win", f"{hname}_{'bad' if fail else 'ok'}", enabled=False)
        a.new_condition.timer(timer=int(cum))
        c_flag(a, fv, fail)
        for (text, icon, chat) in render(ln):
            effect_for(a, text, icon, chat)
        t.new_effect.activate_trigger(trigger_id=a.trigger_id)
    cum += 3
cum = say(t, L("T_Win", "справка"), start=int(cum) + 2)
a = aux("T_Win", "victory", enabled=False)
a.new_condition.timer(timer=int(cum) + 4)
a.new_effect.declare_victory(source_player=P1, enabled=1)
t.new_effect.activate_trigger(trigger_id=a.trigger_id)
# H3: «Табор устоял» (H3_Fail из T_CampHP50)

# ================================================================ 11. СЛУЧАЙНЫЕ
def rnd(name, zone, effect_fn, flag_cond=None):
    t = trig(name)
    c_in(t, P1, -1, zone)
    t.new_condition.chance(quantity=50)
    e_set(t, f"M1_{name}", 1)
    effect_fn(t)
    t.looping = False


rnd("E_Random_Wolves", Z["Z_North"], lambda t: (create(t, 0, K("GREY_WOLF"), 2, (60, 188)), Lsay(t, "E_Random_Wolves", types=("сообщение", "рассказчик"))))
rnd("E_Random_Cart", R(100, 60, 10), lambda t: (give(t, wood=100), create(t, 0, K("BROKEN_CART"), 1, (100, 62)),
                                                  Lsay(t, "E_Random_Cart", types=("сообщение", "рассказчик"))))
rnd("E_Random_Leaf", R(*VCH["V3"], 10), lambda t: (e_add(t, "M1_DMinus_Che", 3), e_add(t, "M1_DMinus_Put", 3), Lsay(t, "E_Random_Leaf", types=("диалог", "сообщение"))))
rnd("E_Random_Cows", R(50, 40, 12), lambda t: (create(t, 0, K("COW_A"), 4, (50, 40)), Lsay(t, "E_Random_Cows", types=("сообщение", "диалог"))))

# ================================================================ 12. ПОРАЖЕНИЕ
for name, setup in (("T_Lose_Dmitry", lambda a: a.new_condition.destroy_object(unit_object=dmitry.reference_id)),
                    ("T_Lose_Camp", lambda a: (c_flag(a, "M1_CampPlaced", 1), a.new_condition.objects_in_area(
                        quantity=1, object_list=TC_, source_player=P1, area_x1=CAMP_TC_AREA[0], area_y1=CAMP_TC_AREA[1], area_x2=CAMP_TC_AREA[2],
                        area_y2=CAMP_TC_AREA[3], inverted=1))),
                    ("T_Lose_Voevoda", lambda a: (c_flag(a, "M1_PutivlDone", 1), c_flag(a, "M1_VoevodaArrive", 0),
                                                  a.new_condition.destroy_object(unit_object=SALT.reference_id)))):
    a = trig(name)
    setup(a)
    Lsay(a, name, types=("сообщение", "диалог", "рассказчик"), opt=True)
    a.new_effect.declare_victory(source_player=P2, enabled=1)

# ================================================================ 13. ПАНЕЛЬ ЦЕЛЕЙ
OBJS = [("OBJ_1_Moravsk", "Привести Моравск к присяге", "M1_MoravskDone", True),
        ("OBJ_2_Chernigov", "Взять Чернигов", None, False),
        ("OBJ_2a_Posad", "2a. Склонить посад к присяге", "M1_PosadDone", False),
        ("OBJ_2b_Castle", "2b. Взять замок князя Татева", "M1_CastleFall", False),
        ("OBJ_3_Camp", "Встать табором под Новгородом-Северским: Дмитрий и не менее 15 воинов", "M1_CampPlaced", False),
        ("OBJ_4_Putivl", "Привести Путивль к присяге и довести воеводу Салтыкова до табора живым", "M1_VoevodaArrive", False),
        ("OBJ_S1", "Перехватить заставу", "M1_S1_Won", False),
        ("OBJ_S2", "Крестоцелование сёл", "M1_S2_Done", False),
        ("OBJ_S3", "Разведать замок Чернигова", "M1_O1Done", False),
        ("OBJ_S4", "Обоз Басманова", "M1_S4_Done", False),
        ("OBJ_S5", "Елецкие старцы", "M1_S5_Done", False),
        ("OBJ_S6", "Путивльская казна", "M1_S6_Done", False)]
OBJT = {}
for k, (nm, text, fl, en) in enumerate(OBJS, 1):
    o = objective(nm, text, k, enabled=en)
    if nm == "OBJ_2_Chernigov":
        c_flag(o, "M1_PosadDone", 1)
        c_flag(o, "M1_CastleFall", 1)
    elif fl:
        c_flag(o, fl, 1 if nm != "OBJ_S4" else 1)
    OBJT[nm] = o
for key, src in (("OBJ_2_Chernigov", mor_flip), ("OBJ_2a_Posad", mor_flip), ("OBJ_2b_Castle", TRIG["T_Che_PosadFlip"]),
                 ("OBJ_3_Camp", TRIG["T_CheCastle_Fall"]), ("OBJ_4_Putivl", camp_check), ("OBJ_S1", TRIG["E02_Border"]),
                 ("OBJ_S2", TRIG["S2_Open"]), ("OBJ_S3", TRIG["T_Scout_Spawn"]), ("OBJ_S4", TRIG["S4_Open"]),
                 ("OBJ_S5", TRIG["S5_Open"]), ("OBJ_S6", TRIG["S6_Open"])):
    src.new_effect.activate_trigger(trigger_id=OBJT[key].trigger_id)
a = aux("T_Che_PosadFlip", "open2b_timeout")
c_flag(a, "M1_CheEntered", 1)
c_flag(a, "M1_PosadDone", 0)
c_dl(a, "dl_Open2b")
a.new_effect.activate_trigger(trigger_id=OBJT["OBJ_2b_Castle"].trigger_id)

# ================================================================ БРИФИНГ
brief = {x.cond: x.text for x in LINES[("M1_Briefing", "брифинг")]}
for x in LINES[("M1_Briefing", "брифинг")]:
    x.used = True
msg.instructions = f"{brief['заголовок']}. {brief['подзаголовок']}.\n\n{brief['задание']}"
msg.history = brief["история"]
msg.hints = brief["подсказки"]
msg.scouts = brief["разведка"]
msg.victory = "Путивль присягнул, воевода Салтыков в таборе. Первая часть пути пройдена."
msg.loss = "Поход сорван."
print("триггеров:", len(tm.triggers), "переменных:", len(tm.variables))

# Часть 2b (v3): события Смуты и Великого голода, бояре, экономика P1. Общее пространство имён (после part2).
V3_MISSING = []


def Lv3(trig_name, types, opt_note=True):
    """Реплики v3: отсутствующий тег пропускается без ошибки и записывается в список недостающих."""
    out = []
    for ty in types:
        ls = L(trig_name, ty, opt=True)
        if not ls:
            V3_MISSING.append(f"{trig_name}:{ty}")
        out += ls
    return out


def zone_of(site, r):
    cx, cy = site["c"]
    return R(cx, cy, r)


def smuta(name, cond_fn, types, effects=None, enabled=True):
    t = trig(name, enabled=enabled)
    if cond_fn:
        cond_fn(t)
    if effects:
        effects(t)
    say(t, Lv3(name, types))
    return t


SM = {}
live1, live2 = SITE_BY["live"][0], SITE_BY["live"][1]
burn1 = SITE_BY["burned"][0]
aband1, aband2 = SITE_BY["abandoned"][0], SITE_BY["abandoned"][1]
church1 = SITE_BY["church"][0] if SITE_BY["church"] else live2

# --- знамение: через 150 с хода
t = smuta("T_Smuta_Star", lambda t: c_clock(t, 150), ("плашка", "рассказчик", "справка", "диалог"),
          lambda t: mood(t, ColorMood.AUTUMN, 3))
# --- колонна беженцев у старта (по дороге к Моравску); по подходу войска часть беглых присоединяется (экономика P1)
REF_AREA = (28, 12, 44, 26)
REF_DEST = (46, 36)
t = trig("T_Smuta_Refugees")
c_clock(t, 75)
for c, n in ((VILL_M, 6), (VILL_F, 6), (K("CART"), 3)):
    create(t, P7, c, n, (34, 17))
for c in (VILL_M, VILL_F, K("CART")):
    t.new_effect.task_object(object_list_unit_id=c, source_player=P7, location_x=REF_DEST[0], location_y=REF_DEST[1], action_type=ActionType.MOVE,
                             area_x1=REF_AREA[0], area_y1=REF_AREA[1], area_x2=REF_AREA[2], area_y2=REF_AREA[3])
say(t, Lv3("T_Smuta_Refugees", ("сообщение", "диалог", "подсказка")))
e_set(t, "M1_SmutaRefugees", 1)
t.new_effect.activate_trigger(trigger_id=0) if False else None
j = trig("T_Smuta_Refugees__join")
c_flag(j, "M1_SmutaRefugees", 1)
c_mil(j, P1, (REF_DEST[0] - 7, REF_DEST[1] - 7, REF_DEST[0] + 7, REF_DEST[1] + 7))
for c in (VILL_M, VILL_F):
    j.new_effect.change_ownership(object_list_unit_id=c, source_player=P7, target_player=P1, area_x1=REF_DEST[0] - 9, area_y1=REF_DEST[1] - 9,
                                  area_x2=REF_DEST[0] + 9, area_y2=REF_DEST[1] + 9, flash_object=1, max_units_affected=4)
give(j, food=60)
j.new_effect.send_chat(source_player=P1, message="Беглые остались при обозе: четверо мужчин и четыре женщины будут работать на лагерь.")
# --- сожжённая деревня: находка 50 золота
t = smuta("T_Smuta_Burned", lambda t: c_in(t, P1, -1, zone_of(burn1, 8)), ("сообщение", "рассказчик", "диалог"), lambda t: give(t, gold=50))
# --- голод: брошенные житницы
t = smuta("T_Smuta_Famine", lambda t: c_in(t, P1, -1, zone_of(aband2, 9)), ("сообщение", "справка", "диалог", "подсказка"))
# --- лагерь лихих людей: подход, затем разгром (необязательная цель)
bz = R(BAND_C[0], BAND_C[1], 22)
t = trig("T_Smuta_Bandits")
c_in(t, P1, -1, bz)
e_set(t, "M1_SmutaBandits", 1)
ls_b = Lv3("T_Smuta_Bandits", ("сообщение", "цель", "диалог", "подсказка"))
say(t, [x for x in ls_b if not (x.typ == "сообщение" and "Стан разбит" in x.text)])
flag_mark(t, BAND_C, temp=True)
t = trig("T_Smuta_Bandits__clear")
c_flag(t, "M1_SmutaBandits", 1)
c_mil(t, 0, BAND_ZONE, 1, inverted=1)
give(t, food=100, gold=60)
e_set(t, "M1_SmutaBandits", 2)
say(t, [x for x in ls_b if x.typ == "сообщение" and "Стан разбит" in x.text])
t.new_effect.remove_object(object_list_unit_id=K("FLAG_B"), source_player=P1, area_x1=BAND_ZONE[0], area_y1=BAND_ZONE[1], area_x2=BAND_ZONE[2],
                           area_y2=BAND_ZONE[3])
# --- волки у заброшенной деревни
t = smuta("T_Smuta_Wolves", lambda t: c_in(t, P1, -1, zone_of(aband1, 14)), ("сообщение", "рассказчик", "подсказка"))
# --- дезертиры-стрельцы у дороги к табору: 4 стрельца в отряд
DES_C = (95, 139)
t = smuta("T_Smuta_Deserters", lambda t: c_dm(t, R(DES_C[0], DES_C[1], 9)), ("диалог", "сообщение", "подсказка"),
          lambda t: create(t, P1, HC_, 4, DES_C))
# --- слух «царевич жив»: рядом с живой деревней, связь с Молвой
t = smuta("T_Smuta_Rumor", lambda t: c_in(t, P1, -1, zone_of(live1, 10)), ("сообщение", "диалог", "рассказчик"),
          lambda t: e_add(t, "M1_Molva", 1))
# --- набат в одинокой церкви
t = smuta("T_Smuta_Bell", lambda t: c_in(t, P1, -1, R(church1["church"][0], church1["church"][1], 12)), ("сообщение", "рассказчик", "диалог", "подсказка"),
          lambda t: cam(t, church1["church"]))
# --- хроника Смуты: короткие реплики на марше
for k in range(1, 9):
    g = trig(f"G_Smuta_{k}")
    c_clock(g, 300 + 260 * k)
    say(g, Lv3(f"G_Smuta_{k}", ("сообщение",)))

# --- техническое: лихие люди, волки и беженцы
t = trig("T_Smuta_Init")
t.new_condition.timer(timer=2)
t.new_effect.change_object_name(source_player=0, message="Лихой человек", selected_object_ids=ids(BAND_UNITS))
t.new_effect.change_object_stance(source_player=0, attack_stance=AttackStance.DEFENSIVE_STANCE, selected_object_ids=ids(BAND_UNITS))
for s_ in SITE_BY["abandoned"]:
    if s_.get("wolves"):
        t.new_effect.change_object_name(source_player=0, message="Голодный волк", selected_object_ids=ids(s_["wolves"]))

# --- бояре: вместо рыцарей (KNIGHT_ = BOYAR); P1 получает бояр в войско (3 в старте + 3 у Чернигова), обучение в замке после падения замка Чернигова
CASTLE_ = K("CASTLE")
t = trig("M1_BoyarUnlock")
c_flag(t, "M1_CastleDone", 1)
t.new_effect.enable_disable_object(object_list_unit_id=KNIGHT_, source_player=P1, enabled=1)
t.new_effect.add_train_location(object_list_unit_id=KNIGHT_, source_player=P1, object_list_unit_id_2=CASTLE_, button_location=ButtonLocation.r1c4.value, train_time=40)
t.new_effect.change_object_cost(object_list_unit_id=KNIGHT_, source_player=P1, resource_1=Attribute.FOOD_STORAGE, resource_1_quantity=70,
                                resource_2=Attribute.WOOD_STORAGE, resource_2_quantity=0, resource_3=Attribute.GOLD_STORAGE, resource_3_quantity=90)
t.new_effect.send_chat(source_player=P1, message="Боярская конница: в замке открыт наём бояр (70 еды, 90 золота).")
V3_TRIGGERS = [n for n in TRIG if n.startswith(("T_Smuta", "G_Smuta"))]
print("события Смуты:", V3_TRIGGERS, "недостающие теги v3:", V3_MISSING)
init.new_effect.enable_disable_object(object_list_unit_id=KNIGHT_, source_player=P1, enabled=0)     # бояре P1: только после падения замка

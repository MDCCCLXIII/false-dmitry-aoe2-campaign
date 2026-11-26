"""Этап 1: минимальный тестовый сценарий (проверка осуществимости AoE2ScenarioParser)."""
import sys
from pathlib import Path

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.heroes import HeroInfo
from AoE2ScenarioParser.datasets.players import PlayerId

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "01_test.aoe2scenario"
HINT = "Подсказка: ведите чернецов под защитой воинов."

sc = AoE2DEScenario.from_default()
print("Версия сценария:", sc.scenario_version if hasattr(sc, "scenario_version") else "?")
um, tm, pm, mm, msg = sc.unit_manager, sc.trigger_manager, sc.player_manager, sc.map_manager, sc.message_manager

mm.map_size = 120
pm.active_players = 2
pm.players[PlayerId.ONE].food = 800
pm.players[PlayerId.ONE].wood = 600
pm.players[PlayerId.ONE].gold = 500
pm.players[PlayerId.ONE].stone = 200
msg.instructions = "Тестовый сценарий: Через границу."
msg.hints = HINT

# Игрок 1: Дмитрий и 6 юнитов
dmitry = um.add_unit(PlayerId.ONE, HeroInfo.ROLAND.ID, x=20, y=20)
for i, u in enumerate([UnitInfo.HUSSAR, UnitInfo.HUSSAR, UnitInfo.MAN_AT_ARMS,
                       UnitInfo.MAN_AT_ARMS, UnitInfo.ARCHER, UnitInfo.MONK]):
    um.add_unit(PlayerId.ONE, u.ID, x=22 + i, y=22)
# Игрок 2: город и юниты
tc = um.add_unit(PlayerId.TWO, BuildingInfo.TOWN_CENTER.ID, x=90, y=90)
for i in range(3):
    um.add_unit(PlayerId.TWO, BuildingInfo.HOUSE.ID, x=84 + 3 * i, y=96)
for i, u in enumerate([UnitInfo.SPEARMAN, UnitInfo.SPEARMAN, UnitInfo.CROSSBOWMAN, UnitInfo.KNIGHT]):
    um.add_unit(PlayerId.TWO, u.ID, x=88 + i, y=86)

# Триггеры
t_init = tm.add_trigger("T_Init")
t_init.new_condition.timer(timer=1)
t_init.new_effect.change_object_name(selected_object_ids=[dmitry.reference_id],
                                     source_player=PlayerId.ONE, message="Царевич Димитрий")
t_init.new_effect.display_instructions(source_player=PlayerId.ONE, message=HINT, display_time=15)

t_win = tm.add_trigger("T_Win")
t_win.new_condition.destroy_object(unit_object=tc.reference_id)
t_win.new_effect.declare_victory(source_player=PlayerId.ONE, enabled=1)

t_lose = tm.add_trigger("T_Lose_Dmitry")
t_lose.new_condition.destroy_object(unit_object=dmitry.reference_id)
t_lose.new_effect.declare_victory(source_player=PlayerId.TWO, enabled=1)

OUT.parent.mkdir(exist_ok=True)
sc.write_to_file(str(OUT))
print("Записано:", OUT)

# Проверка: открыть заново
chk = AoE2DEScenario.from_file(str(OUT))
errs = []
if chk.map_manager.map_size != 120: errs.append("размер карты")
if len(chk.unit_manager.get_player_units(PlayerId.ONE)) != 7: errs.append("юниты P1")
if len(chk.unit_manager.get_player_units(PlayerId.TWO)) != 8: errs.append("юниты P2")
names = [t.name for t in chk.trigger_manager.triggers]
for n in ("T_Init", "T_Win", "T_Lose_Dmitry"):
    if n not in names: errs.append("триггер " + n)
if chk.message_manager.hints != HINT: errs.append("подсказка")
if chk.player_manager.players[PlayerId.ONE].gold != 500: errs.append("золото")
eff = chk.trigger_manager.get_trigger(0).effects
if not any(HINT in (e.message or "") for e in eff): errs.append("сообщение в триггере")
print("Триггеры:", names)
print("ОШИБКИ:" if errs else "ПРОВЕРКА ПРОЙДЕНА", errs)
sys.exit(1 if errs else 0)

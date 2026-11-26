"""Превью сценария AoE2 DE: overview.png, zoom_<имя>.png, stats.txt -> build/preview/<имя сценария>/

Запуск (из корня проекта):
  .venv\\Scripts\\python.exe -I -X utf8 scripts\\preview.py build\\01_cherez_granitsu.aoe2scenario ^
      --zoom 40,40,25,lager --zoom 120,120,30,gorod --density 40,40,20,lager
Сценарий только читается, не изменяется.
"""
import argparse
import io
import contextlib
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.heroes import HeroInfo
from AoE2ScenarioParser.datasets.other import OtherInfo

ROOT = Path(__file__).resolve().parent.parent
PCOL = {0: (170, 170, 170), 1: (30, 90, 255), 2: (230, 30, 30), 3: (30, 200, 30), 4: (245, 225, 20),
        5: (0, 220, 220), 6: (170, 40, 220), 7: (130, 130, 130), 8: (255, 140, 0)}
TERRAIN_NAMES = {t.value: t.name for t in TerrainId}

CATS = {
    "water": ("Вода", (30, 70, 170)),
    "shallow": ("Мелководье", (110, 170, 230)),
    "grass": ("Трава", (70, 150, 60)),
    "dry": ("Сухая трава", (160, 170, 70)),
    "dirt": ("Грунт/дорога", (140, 100, 60)),
    "forest": ("Лес", (20, 80, 30)),
    "other": ("Прочее", (130, 130, 130)),
}


def category(tid):
    n = TERRAIN_NAMES.get(tid, "")
    if "FOREST" in n:
        return "forest"
    if "SHALLOW" in n or "BEACH" in n:
        return "shallow"
    if "WATER" in n:
        return "water"
    if n == "GRASS_DRY" or "SAVANNAH" in n:
        return "dry"
    if "GRASS" in n:
        return "grass"
    if "DIRT" in n or "ROAD" in n or "GRAVEL" in n or "FARM" in n:
        return "dirt"
    return "other"


def font(size):
    for f in ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


_name_cache = {}


def unit_name(uid):
    """(имя, это_здание, это_стена)"""
    if uid in _name_cache:
        return _name_cache[uid]
    res = (f"#{uid}", False, False)
    for ds, is_b in ((BuildingInfo, True), (UnitInfo, False), (HeroInfo, False), (OtherInfo, False)):
        try:
            nm = ds.from_id(uid).name
            wall = is_b and ("WALL" in nm or "PALISADE" in nm)
            res = (nm, is_b, wall)
            break
        except Exception:
            continue
    _name_cache[uid] = res
    return res


def short(nm):
    nm = nm.replace("_", " ").title()
    for a, b in (("Town Center", "TC"), ("Palisade Wall", "Palisade"), ("Fortified Wall", "FortWall"),
                 ("Stone Wall", "Wall"), ("Watch Tower", "Watch"), ("Guard Tower", "Guard"),
                 ("Archery Range", "Archery"), ("Monastery", "Monast."), ("Blacksmith", "Smith"),
                 ("Siege Workshop", "Siege W."), ("Mining Camp", "MiningC"), ("Lumber Camp", "LumberC"),
                 ("Outpost", "Outp."), ("Barracks", "Barr.")):
        nm = nm.replace(a, b)
    return nm[:11]


def bsize(nm):
    n = nm.upper()
    if any(k in n for k in ("CASTLE", "TOWN_CENTER", "MONASTERY", "UNIVERSITY", "KREPOST", "DONJON", "WONDER", "FEITORIA")):
        return 4
    if any(k in n for k in ("TOWER", "OUTPOST", "WALL", "PALISADE", "GATE", "DOCK")):
        return 1
    if "HOUSE" in n or "FARM" in n or "MILL" in n or "CAMP" in n:
        return 2
    return 3


def load(path):
    with contextlib.redirect_stdout(io.StringIO()):
        return AoE2DEScenario.from_file(str(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--zoom", action="append", default=[], help="x,y,радиус,название")
    ap.add_argument("--density", action="append", default=[], help="x,y,радиус,название")
    a = ap.parse_args()
    path = Path(a.scenario)
    sc = load(path)
    mm = sc.map_manager
    W = H = mm.map_width
    terr = mm.terrain
    objs = [u for pl in sc.unit_manager.units for u in pl]
    out = ROOT / "build" / "preview" / path.stem
    out.mkdir(parents=True, exist_ok=True)

    elevs = [t.elevation for t in terr]
    emin, emax = min(elevs), max(elevs)

    def tile_rgb(x, y):
        t = terr[y * W + x]
        c = CATS[category(t.terrain_id)][1]
        k = max(0.5, min(1.6, 1.0 + 0.06 * t.elevation))
        return tuple(min(255, int(v * k)) for v in c)

    def draw_objects(d, px, ox, oy, labels=False, bounds=None):
        """px - пикселей на клетку; ox,oy - клетка начала фрагмента"""
        walls = {}
        for u in objs:
            nm, isb, wall = unit_name(u.unit_const)
            if wall:
                walls.setdefault(u.player, []).append((u.x, u.y))
        for pl, pts in walls.items():
            col = PCOL.get(pl, (0, 0, 0))
            S = set((int(x), int(y)) for x, y in pts)
            w = max(2, px // 3)
            for (x, y) in S:
                for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                    if (x + dx, y + dy) in S:
                        d.line([((x + .5 - ox) * px, (y + .5 - oy) * px),
                                ((x + dx + .5 - ox) * px, (y + dy + .5 - oy) * px)], fill=col, width=w)
                cx, cy = (x + .5 - ox) * px, (y + .5 - oy) * px
                d.rectangle([cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2], fill=col)
        lf = font(11)
        for u in objs:
            nm, isb, wall = unit_name(u.unit_const)
            if wall:
                continue
            if bounds and not (bounds[0] <= u.x < bounds[2] and bounds[1] <= u.y < bounds[3]):
                continue
            col = PCOL.get(u.player, (0, 0, 0))
            cx, cy = (u.x - ox) * px, (u.y - oy) * px
            if isb:
                s = bsize(nm) * px / 2
                d.rectangle([cx - s, cy - s, cx + s, cy + s], fill=col, outline=(0, 0, 0))
                if labels:
                    d.text((cx, cy), short(nm), fill=(255, 255, 255), font=lf, anchor="mm",
                           stroke_width=1, stroke_fill=(0, 0, 0))
            else:
                r = max(1.5, px / 6) if not labels else px / 4
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(0, 0, 0) if labels else None)

    # ---------- overview ----------
    PX = 6
    img = Image.new("RGB", (W * PX, H * PX))
    d = ImageDraw.Draw(img)
    for y in range(H):
        for x in range(W):
            d.rectangle([x * PX, y * PX, x * PX + PX - 1, y * PX + PX - 1], fill=tile_rgb(x, y))
    draw_objects(d, PX, 0, 0)
    gf = font(12)
    for g in range(0, W + 1, 20):
        d.line([(g * PX, 0), (g * PX, H * PX)], fill=(255, 255, 255), width=1)
        d.line([(0, g * PX), (W * PX, g * PX)], fill=(255, 255, 255), width=1)
        d.text((g * PX + 2, 2), str(g), fill=(255, 255, 255), font=gf, stroke_width=1, stroke_fill=(0, 0, 0))
        d.text((2, g * PX + 2), str(g), fill=(255, 255, 255), font=gf, stroke_width=1, stroke_fill=(0, 0, 0))
    lf = font(14)
    items = [(c[1], c[0]) for c in CATS.values()] + [(PCOL[i], f"P{i}") for i in range(1, 9)]
    lh = 20
    bw, bh = 190, lh * len(items) + 30
    lx, ly = W * PX - bw - 8, H * PX - bh - 8
    d.rectangle([lx, ly, lx + bw, ly + bh], fill=(0, 0, 0), outline=(255, 255, 255))
    d.text((lx + 6, ly + 4), f"Высоты {emin}..{emax}; светлее = выше", fill=(255, 255, 255), font=font(11))
    for i, (c, t) in enumerate(items):
        yy = ly + 24 + i * lh
        d.rectangle([lx + 6, yy, lx + 22, yy + 14], fill=c)
        d.text((lx + 30, yy), t, fill=(255, 255, 255), font=lf)
    img.save(out / "overview.png")
    made = ["overview.png"]

    # ---------- zoom ----------
    ZP = 20
    for z in a.zoom:
        zx, zy, zr, zn = z.split(",", 3)
        zx, zy, zr = int(zx), int(zy), int(zr)
        x0, y0 = max(0, zx - zr), max(0, zy - zr)
        x1, y1 = min(W, zx + zr + 1), min(H, zy + zr + 1)
        img = Image.new("RGB", ((x1 - x0) * ZP, (y1 - y0) * ZP))
        dd = ImageDraw.Draw(img)
        for y in range(y0, y1):
            for x in range(x0, x1):
                dd.rectangle([(x - x0) * ZP, (y - y0) * ZP, (x - x0 + 1) * ZP - 1, (y - y0 + 1) * ZP - 1],
                             fill=tile_rgb(x, y))
        draw_objects(dd, ZP, x0, y0, labels=True, bounds=(x0, y0, x1, y1))
        for g in range(((x0 + 9) // 10) * 10, x1 + 1, 10):
            dd.line([((g - x0) * ZP, 0), ((g - x0) * ZP, img.height)], fill=(255, 255, 255))
            dd.text(((g - x0) * ZP + 2, 2), str(g), fill=(255, 255, 255), font=gf, stroke_width=1, stroke_fill=(0, 0, 0))
        for g in range(((y0 + 9) // 10) * 10, y1 + 1, 10):
            dd.line([(0, (g - y0) * ZP), (img.width, (g - y0) * ZP)], fill=(255, 255, 255))
            dd.text((2, (g - y0) * ZP + 2), str(g), fill=(255, 255, 255), font=gf, stroke_width=1, stroke_fill=(0, 0, 0))
        fn = f"zoom_{zn}.png"
        img.save(out / fn)
        made.append(fn)

    # ---------- stats ----------
    L = [f"Сценарий: {path}", f"Карта: {W}x{H}", "", "== Terrain id (клеток) =="]
    for tid, n in sorted(Counter(t.terrain_id for t in terr).items(), key=lambda kv: -kv[1]):
        L.append(f"{tid:4d} {TERRAIN_NAMES.get(tid, '?'):28s} [{CATS[category(tid)][0]}] {n}")
    L += ["", "== Высоты ==", f"min={emin} max={emax}"]
    for e, n in sorted(Counter(elevs).items()):
        L.append(f"  elev {e:3d}: {n} клеток ({100 * n / len(elevs):.1f}%)")
    L += ["", "== Объекты по игрокам =="]
    pc = Counter(u.player for u in objs)
    for p in sorted(pc):
        nb = sum(1 for u in objs if u.player == p and unit_name(u.unit_const)[1] and not unit_name(u.unit_const)[2])
        L.append(f"P{p}: всего {pc[p]}, зданий (без стен) {nb}")
    L += ["", "== Топ-30 (игрок, тип) =="]
    for (p, nm), n in Counter((u.player, unit_name(u.unit_const)[0]) for u in objs).most_common(30):
        L.append(f"P{p} {nm}: {n}")
    L += ["", "== Плотность зданий =="]
    for dz in a.density:
        dx, dy, dr, dn = dz.split(",", 3)
        dx, dy, dr = int(dx), int(dy), int(dr)
        inside = [u for u in objs if abs(u.x - dx) <= dr and abs(u.y - dy) <= dr]
        bl = [u for u in inside if unit_name(u.unit_const)[1] and not unit_name(u.unit_const)[2]]
        wl = [u for u in inside if unit_name(u.unit_const)[2]]
        area = (2 * dr + 1) ** 2
        L.append(f"{dn} ({dx},{dy}) r={dr}: зданий {len(bl)} ({1000 * len(bl) / area:.1f} на 1000 клеток), "
                 f"стен {len(wl)}, юнитов/прочего {len(inside) - len(bl) - len(wl)}")
        for (p, nm), n in Counter((u.player, unit_name(u.unit_const)[0]) for u in bl).most_common(8):
            L.append(f"    P{p} {nm}: {n}")
    (out / "stats.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    made.append("stats.txt")
    print("OK ->", out)
    for m in made:
        print("  ", m)


if __name__ == "__main__":
    main()

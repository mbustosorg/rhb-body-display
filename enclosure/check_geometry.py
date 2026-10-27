#!/usr/bin/env python3
"""Geometry audit for dash_enclosure.scad.

check_clearances.py only does arithmetic on the parameters. This one asks
OpenSCAD about the real solids: for every heat-set insert it intersects the
part with a thin ring around the bore and confirms there is plastic there.
A missing boss or flange shows up as an empty ring. The ring is then checked
octant by octant, so a bore that is only partly on its boss -- the classic
result of moving a boss without moving its hole -- fails too.

    python3 check_geometry.py

Needs `openscad` on the PATH. Takes a minute or two.
"""
import math
import re
import subprocess
import sys
import tempfile
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SCAD = HERE / "dash_enclosure.scad"


def params():
    src = re.sub(r"//.*", "", SCAD.read_text().split("// helpers")[0])
    out = {}
    for chunk in src.split(";"):
        m = re.match(r"\s*([a-z_][a-z_0-9]*)\s*=\s*(-?[\d.]+)\s*$", chunk)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def probes(p):
    """(label, part module, x, y, z0, z1, r_in, r_out) for every insert."""
    ow = p["lcd_pcb_w"] + 2 * p["side_gap"] + 2 * p["wall"]
    oh = p["lcd_pcb_h"] + 2 * p["vert_gap"] + 2 * p["wall"]
    d, wall, rim = p["shell_d"], p["wall"], p["rim_w"]
    ex, ey = ow / 2 - wall - rim / 2, oh / 2 - wall - rim / 2
    out = []

    r3 = p["m3_insert_d"] / 2
    for i, (x, y) in enumerate([(-ex, ey), (0, ey), (ex, ey), (-ex, 0), (ex, 0),
                                (-ex, -ey), (0, -ey), (ex, -ey)]):
        out.append((f"backplate insert {i + 1}", "shell", x, y, d - 5, d - 1, r3 + 0.3, r3 + 1.2))

    z_pcb_front = p["front_t"] + p["lcd_post_z"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append((f"LCD boss {'LR'[sx > 0]}{'BT'[sy > 0]}", "shell",
                        sx * p["lcd_hole_dx"] / 2, sy * p["lcd_hole_dy"] / 2,
                        p["front_t"] + 0.5, z_pcb_front - 0.5, r3 + 0.3, r3 + 0.4 + 0.8))

    r25 = p["m25_insert_d"] / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append((f"Pi standoff {'LR'[sx > 0]}{'BT'[sy > 0]}", "backplate",
                        p["pi_cx"] + sx * p["pi_hole_dx"] / 2, p["pi_cy"] + sy * p["pi_hole_dy"] / 2,
                        d - p["pi_standoff_z"] + 0.5, d - 0.5, r25 + 0.3, r25 + 1.2))
    for sx in (-1, 1):
        out.append((f"buck ear insert {'LR'[sx > 0]}", "backplate",
                    p["buck_cx"] + sx * p["buck_ear_dx"] / 2, p["buck_cy"],
                    d - p["buck_pad_t"], d - 1, r3 + 0.3, r3 + 1.2))
    return out


def ring(x, y, z0, z1, ri, ro):
    return (f"translate([{x},{y},{z0}]) difference() {{ cylinder(r={ro}, h={z1 - z0}, $fn=24);"
            f" translate([0,0,-1]) cylinder(r={ri}, h={z1 - z0 + 2}, $fn=24); }}")


def vertices(stl):
    txt = stl.read_text(errors="replace")
    return [tuple(map(float, m.groups()))
            for m in re.finditer(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", txt)]


def main():
    p = params()
    rows = probes(p)
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for module in ("shell", "backplate"):
            mine = [r for r in rows if r[1] == module]
            scad = tmp / f"probe_{module}.scad"
            scad.write_text(f"use <{SCAD}>\nintersection() {{ {module}(); union() {{\n"
                            + "\n".join(ring(*r[2:]) for r in mine) + "\n} }\n")
            stl = tmp / f"probe_{module}.stl"
            subprocess.run(["openscad", "-o", str(stl), str(scad)],
                           capture_output=True, text=True)
            verts = vertices(stl) if stl.exists() else []
            for label, _, x, y, z0, z1, ri, ro in mine:
                near = [(vx, vy) for vx, vy, vz in verts
                        if abs(vx - x) <= ro + 0.05 and abs(vy - y) <= ro + 0.05
                        and z0 - 0.05 <= vz <= z1 + 0.05]
                octants = {int((math.atan2(vy - y, vx - x) + math.pi)
                               / (math.pi / 4)) % 8 for vx, vy in near}
                hit = len(octants) == 8
                if not hit:
                    fails.append(label)
                note = "" if hit else f"  (material in {len(octants)}/8 octants)"
                print(f"  [{'OK ' if hit else 'FAIL'}] {module:<9} {label}{note}")
    print()
    if fails:
        print(f"{len(fails)} insert(s) are not fully surrounded by plastic: " + ", ".join(fails))
        return 1
    print("ALL INSERTS HAVE MATERIAL")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Clearance audit for dash_enclosure.scad.

Reads the parameter block straight out of the .scad file, so it stays honest
when you change a dimension. Run it after any edit:

    python3 check_clearances.py

Exits non-zero if anything collides or runs out of room.
"""
import re
import sys
import pathlib

SCAD = pathlib.Path(__file__).with_name("dash_enclosure.scad")

FAN_BODY_Z    = 10.0   # how far a 40x40x10 fan protrudes inward


def params():
    src = SCAD.read_text().split("// helpers")[0]
    src = re.sub(r"//.*", "", src)
    out = {}
    for chunk in src.split(";"):
        m = re.match(r"\s*([a-z_][a-z_0-9]*)\s*=\s*(-?[\d.]+)\s*$", chunk)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def main():
    p = params()
    g = p.__getitem__

    ow = g("lcd_pcb_w") + 2 * g("side_gap") + 2 * g("wall")
    oh = g("lcd_pcb_h") + 2 * g("vert_gap") + 2 * g("wall")
    depth, wall = g("shell_d"), g("wall")
    ix, iy = ow / 2 - wall, oh / 2 - wall          # interior half-extents

    z_pcb_front = g("front_t") + g("lcd_post_z")
    z_pcb_back = z_pcb_front + g("lcd_pcb_t")
    z_lcd_max = z_pcb_back + g("lcd_rear_z")
    z_pi_pcb = depth - g("pi_standoff_z")
    z_hat_pcb = z_pi_pcb - g("pi_pcb_t") - g("hat_rise") - g("hat_pcb_t")
    z_term = z_hat_pcb - g("hat_term_z")
    z_buck = depth - g("buck_pad_t") - g("buck_z")   # front face of the buck body

    fails = []

    def chk(label, val, lo=0.0):
        ok = val >= lo
        if not ok:
            fails.append(label)
        print(f"  [{'OK ' if ok else 'FAIL'}] {label:<48} {val:7.2f}  (need >= {lo})")

    print(f"Envelope  {ow:.2f} W x {oh:.2f} H x {depth + g('back_t'):.2f} D mm"
          f"   (+{g('pad_t'):.0f} mount pad)\n")

    print("Depth stack (z from the bezel face):")
    for name, z in [("bezel outer face", 0.0),
                    ("glass front", z_pcb_front - g("lcd_glass_t")),
                    ("LCD PCB back", z_pcb_back),
                    ("LCD rear max (HDMI shell)", z_lcd_max),
                    ("CAN HAT terminals (frontmost)", z_term),
                    ("HAT PCB", z_hat_pcb),
                    ("buck body front face", z_buck),
                    ("Pi PCB", z_pi_pcb),
                    ("shell rear", depth)]:
        print(f"    {name:<32} z = {z:6.2f}")

    print("\nClearances:")
    chk("LCD rear -> CAN HAT terminals", z_term - z_lcd_max, 8)
    chk("LCD rear -> buck body", z_buck - z_lcd_max, 8)
    # the board is shifted so the picture lands centred in the bezel
    off_x, off_y = -g("aa_off_x"), -g("aa_off_y")
    chk("LCD edge -> side wall (HDMI plug room)",
        min(ix - abs(off_x) - g("lcd_pcb_w") / 2, ix - abs(off_x) - g("lcd_pcb_w") / 2), 12)
    chk("LCD edge -> top/bottom wall", iy - abs(off_y) - g("lcd_pcb_h") / 2, 3)

    # the window must clear every pixel but still land on glass
    win_w = g("aa_w") + 2 * g("window_margin")
    win_h = g("aa_h") + 2 * g("window_margin")
    chk("window clears the active area", g("window_margin"), 0.3)
    chk("window lip on glass, left",   g("aa_glass_left")  - g("window_margin"), 0.5)
    chk("window lip on glass, right",  g("aa_glass_right") - g("window_margin"), 0.5)
    chk("window lip on glass, top",    g("aa_glass_top")   - g("window_margin"), 0.5)
    chk("window lip on glass, bottom", g("aa_glass_bot")   - g("window_margin"), 0.5)

    pi_x = (g("pi_cx") - g("pi_w") / 2, g("pi_cx") + g("pi_w") / 2)
    pi_y = (g("pi_cy") - g("pi_h") / 2, g("pi_cy") + g("pi_h") / 2)
    buck_span_x, buck_span_y = g("buck_pad_a"), g("buck_pad_b")
    bk_x = (g("buck_cx") - buck_span_x / 2, g("buck_cx") + buck_span_x / 2)
    bk_y = (g("buck_cy") - buck_span_y / 2, g("buck_cy") + buck_span_y / 2)
    chk("Pi inside interior (worst margin)",
        min(pi_x[0] + ix, ix - pi_x[1], pi_y[0] + iy, iy - pi_y[1]), 2)
    chk("buck pad inside interior (worst margin)",
        min(bk_x[0] + ix, ix - bk_x[1], bk_y[0] + iy, iy - bk_y[1]), 2)
    # Pi and buck pad may be separated along either axis -- require a real gap
    gap_x = max(bk_x[0] - pi_x[1], pi_x[0] - bk_x[1])
    gap_y = max(bk_y[0] - pi_y[1], pi_y[0] - bk_y[1])
    chk("Pi <-> buck pad clearance (best axis)", max(gap_x, gap_y), 3)
    chk("ear inserts inboard of pad edge", (g("buck_pad_a") - g("buck_ear_dx")) / 2, 6)
    chk("buck body fits on pad (a/X)", (g("buck_pad_a") - g("buck_body_a")) / 2, 2)
    chk("buck body fits on pad (b/Y)", (g("buck_pad_b") - g("buck_body_b")) / 2, 2)
    chk("insert depth vs pad + plate", g("buck_pad_t") + g("back_t") - g("m3_insert_z"), 1.5)

    fz = (g("fan_z") - g("fan_size") / 2, g("fan_z") + g("fan_size") / 2)
    chk("fan front face -> LCD rear (z)", fz[0] - z_lcd_max, 2)
    chk("fan rear face -> shell rear (z)", depth - fz[1], 0)
    chk("fan top edge -> Pi bottom edge (y)", pi_y[0] - (-iy + FAN_BODY_Z), 1)


    # spacing is judged on the holes as actually cut, i.e. with compensation
    comp = g("bottom_hole_comp")
    feats = [("OBD gland", g("obd_x"), g("obd_gland_d") + comp),
             ("RJ45", g("rj45_x"), g("rj45_d") + comp),
             ("power", g("pwr_x"), g("pwr_d") + comp),
             ("fan", g("fan_x"), g("fan_size"))]
    feats.sort(key=lambda f: f[1])
    print("\nBottom-wall spacing:")
    prev = -ix
    for name, x, width in feats:
        chk(f"gap before {name}", x - width / 2 - prev, 2)
        prev = max(prev, x + width / 2)
    chk("gap after fan", ix - prev, 2)
    chk("gland <-> RJ45 locknut room",
        (g("rj45_x") - g("rj45_d") / 2) - (g("obd_x") + g("obd_gland_d") / 2 + comp), 16)

    print("\nBezel:")
    print(f"    window             {win_w:.2f} x {win_h:.2f} mm "
          f"(active {g('aa_w'):.2f} x {g('aa_h'):.2f} + {g('window_margin')} all round)")
    print(f"    border sides       {(ow - win_w) / 2:.2f} mm")
    print(f"    border top/bottom  {(oh - win_h) / 2:.2f} mm")
    print(f"    board offset       {off_x:+.2f}, {off_y:+.2f} mm "
          f"(mirrors the active-area offset, so the picture is centred)")

    print()
    if fails:
        print(f"{len(fails)} FAILURE(S): " + ", ".join(fails))
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

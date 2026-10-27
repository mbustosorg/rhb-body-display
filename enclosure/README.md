# MT-55 dash enclosure

3D-printed enclosure for a dash-mounted Raspberry Pi display in the MT-55.

Houses:

| Part | Outline | Mount holes |
|---|---|---|
| Waveshare 7inch HDMI LCD (H) Rev4.1 | 164.90 × 124.27 mm | 4 × M3 @ 156.90 × 114.96 |
| Raspberry Pi 4B | 85 × 56 mm | 58 × 49, M2.5 |
| Waveshare 2-CH CAN FD HAT | 65 × 56.5 mm | stacks on the Pi |
| YIPIN HEXHA 12/24 V → 5 V 6 A dual USB-C buck | ~34 × 42 × 21 mm body | 2 × M3 through its ears |
| 40 × 40 × 10 intake fan | — | 32 × 32 |

**Finished envelope:** 212.9 W × 154.3 H × 74 D mm, plus an 8 mm mount pad at the
back. **The shell needs a bed of at least 220 × 160 mm**, and at 212.9 mm it leaves
only ~3.5 mm each side on a 220 mm bed — too tight for a brim or skirt. Print it
on a 250 mm bed if you have one.

## Build the files

```bash
python3 check_clearances.py
```

```bash
python3 check_geometry.py
```

Run both after changing anything. `check_clearances.py` reads the parameter block
straight out of the `.scad` and fails if something collides or runs out of depth.
`check_geometry.py` asks OpenSCAD about the real solids: it confirms there's
plastic around every heat-set insert, so a boss or flange that silently got cut
away fails loudly instead of turning up after a 14-hour print.

```bash
for p in shell back fitcheck; do openscad -o stl/$p.stl -D "part=\"$p\"" dash_enclosure.scad; done
```

## Print this first

`fitcheck.stl` is a test frame (~25 g, ~1.5 h) that checks the one thing the
panel drawing can't settle on its own: **where the picture sits relative to the
four mounting holes.**

The panel outline drawing gives the active area exactly — 157.08 × 88.92 mm — and
shows that it is *not* centred on the glass: only 1.41 mm of glass to the left of
it and 1.52 mm above, against 4.89 mm right and 6.23 mm below. The window is
therefore sized to the active area plus 0.5 mm all round (158.08 × 89.92), which
leaves barely 0.9 mm of glass lip on the left and 1.0 mm on top. There is no room
to be sloppy about position.

The drawing's datum crosshair puts the active-area centre dead on it in X and
1.90 mm below it in Y, so the board is shifted +1.90 mm up in the box
(`lcd_holes_off_y`) to bring the picture back to the centre of the bezel. That
reading is the part worth confirming.

Print it, drop the LCD in, and check:

- no active pixels are clipped at any edge, especially left and top
- the bezel still lands on glass all the way round — if you can see bare PCB at
  the left or top edge, `aa_off_x` / `aa_off_y` need adjusting
- the LCD board seats fully on all four posts
- all four M3 posts line up with the board's corner holes

Adjust `aa_off_x` / `aa_off_y` if needed — the window position and the board
placement are both derived from them, so they move together and cannot drift
apart. Then print the shell. It is a ~14-hour print; do not skip this.

## Material

**Print this in ASA.** Not PLA. A dashboard in direct sun runs well past PLA's
~60 °C glass transition — the bezel will sag and the screen will fall out of it.
ASA is UV-stable (this thing lives behind a windscreen) and good to ~105 °C.
PETG at ~80 °C is the marginal fallback; polycarbonate is better than both if you
can print it.

### Settings

| Part | Orientation | Notes |
|---|---|---|
| `shell` | bezel face **down** on the bed | Gives a smooth visible face. No supports needed; the OBD cutout bridges fine. |
| `back` | mount pad **up** | Standoffs print as short towers. |
| `fitcheck` | flat, face down | — |

4 perimeters, 30 % infill, and for ASA an enclosure (or at least no draught) or
the corners will lift.

## Bill of materials

### Fasteners

| Qty | Insert (bore in part) | Screw | Where |
|---|---|---|---|
| 4 | M3 brass, Ø4.0 × 6 mm | M3 × 8 pan | LCD → shell posts (through 2 mm PCB) |
| 8 | M3 brass, Ø4.0 × 6 mm | M3 × 10 **countersunk** | backplate → shell rim |
| 4 | M2.5 brass, Ø3.6 × 5.5 mm | M2.5 × 6 pan | Pi → backplate standoffs |
| 2 | M3 brass, Ø4.0 × 6 mm | M3 × 8 pan | buck ears → backplate pad |
| 4 or 8 | M4 brass, Ø5.6 × 8 mm | M4 × 12 | RAM/AMPS or VESA bracket → rear pad |
| 4 | — (Ø3.4 clearance) | M3 × 16 self-tapping | fan → bottom wall, from outside |
| 2 | — (Ø3.4 clearance) | M3 × 12 + nyloc | OBD socket ears → bottom wall |
| — | — | their own nuts | RJ45 and GX16 bulkheads |
| 1 | — | — | 3 mm closed-cell foam tape, bezel-to-glass gasket |

Totals: **14 × M3 inserts, 4 × M2.5, 8 × M4** (only 4 of the M4 get used — pick
either the AMPS or the VESA pattern; the other four bores can stay empty).

Countersinks in the backplate are cut at 90° for DIN 7991 flat heads. Screw
lengths above assume the head sits flush, so engagement is length minus the 4 mm
plate: M3 × 10 gives the full 6 mm of insert.

### Panel connectors (bottom wall)

| Item | Cutout | Verify |
|---|---|---|
| 1/2" cable gland, OBD-II extension through it | Ø12.7 mm | hole prints ~0.2–0.4 mm undersize |
| IP67 bulkhead RJ45 coupler | Ø22 mm | yes |
| GX16 2-pin power bulkhead | Ø16 mm | yes |

Each cutout is a parameter at the top of the `.scad`. Measure the parts you
actually buy and update `obd_gland_d`, `rj45_d`, `pwr_d` before
printing the shell.

### Electronics

- **YIPIN HEXHA 12/24 V → 5 V 6 A 30 W dual USB-C buck** (ASIN B0BCP86XPY).
  10–32 V in, potted, two captive USB-C **male** leads (31 cm), **3 A per port**,
  6 A total. Pi on one lead, display on the other — no splicing.
- USB-C → micro-USB cable or adapter, for the display's *Power Only* port.
- Inline ATC fuse on the 12 V feed, close to the source. 5 A is about right.
- Right-angle HDMI plug or a flat ribbon HDMI cable — the shell allows 15 mm
  beside the LCD, which a straight plug with strain relief will not clear.
- Short USB-A → micro-USB for the LCD touch port, and a second one for its
  power-only port.
- 40 × 40 × 10 mm 5 V fan.

## Power

12 V from the GX16 bulkhead, through an inline fuse, splits two ways: to the
buck's red/black input leads, and to the CAN FD HAT's DC terminal for its
isolated CAN side. (The HAT Rev2.1+ can power the Pi from that terminal on its
own, but its regulator won't carry a Pi 4 plus the display — that's what the buck
is for.)

The buck has **two** captive USB-C male leads, 3 A each. Plug one into the Pi
and run the other through a USB-C → micro-USB cable to the display's *Power Only*
port. Nothing needs cutting or splicing, and each lead carries its own CC
resistors so the Pi negotiates full current normally.

Load: the Pi's port sees the Pi plus the touch USB (~100 mA), well inside 3 A —
the official Pi 4 supply is 5.1 V/3 A. The display's port sees 0.85 A. Total ~4 A
of the module's 6 A.

**Watch the 10 V input floor.** Cranking a diesel can drag the bus to 9–10 V, and
this module drops out there where an 8 V-minimum part would ride through. If the
box is live during cranking, expect an occasional reboot. Feed it from a circuit
that's dead during crank, add a hold-up capacitor across the 12 V input, or live
with it.

The OBD-II connector carries 12 V on pin 16 and ground on pins 4/5, so you *can*
power the whole unit off the OBD port and skip the separate power connector. I'd advise
against it: on most vehicles that pin is unswitched battery, so the box would draw
2–3 A continuously with the key out. Use the GX16 on a switched feed and leave OBD
pin 16 unconnected, or fit an ignition-sensing relay.

## Cooling

40 mm intake fan low in the bottom wall, louvred exhaust across the top — air
rises past the Pi and the buck and leaves at the top, which is the direction it
wants to go anyway.

**Unfiltered by choice.** There is no filter element and no tray; the fan draws
straight through a bare 38 mm hole. That trades dust ingress for simplicity and
one less thing to service. Expect to blow the inside out with compressed air
periodically, and keep the backplate seam taped so the fan hole is the only way
in.

This is the part of the design most likely to need attention in the field. A Pi 4
under sustained load on a sunlit dash is a genuinely hard thermal problem, and a
40 mm fan is a modest amount of airflow. Put a heatsink on the
SoC, and watch `vcgencmd measure_temp` for throttling on the first hot day.

## Mounting

The rear pad carries **both** patterns:

- **VESA 75 × 75** — any cheap monitor arm
- **AMPS 38.1 × 30.0** — any RAM ball plate

For a vehicle use the RAM ball. The rubber ball damps vibration, which matters
more than it sounds for a 74 mm-deep box cantilevered off a dashboard, and the
arm lets you kill windscreen glare by angling the screen.

## Assembly order

1. Heat-set every insert while the parts are still clean and flat.
2. Fit the panel connectors into the bottom wall of the shell.
3. Foam-tape gasket onto the inside of the bezel face, LCD in face-down, 4 × M3.
4. Pi + HAT onto the backplate. Buck sits flat on its raised pad, 2 × M3 down
   through its moulded ears.
5. Wire it up with the backplate still off the shell — everything is reachable.
6. Fan into the bottom wall, blowing **inward**.
7. Foam tape round the rear seam, backplate on, 8 × M3.

## Gasket gap

`lcd_post_z` (7.5 mm) sets the LCD post height and therefore how far the glass
sits behind the bezel face. With the glass at 4.5 mm that leaves a **3.0 mm gap**
for foam tape. Change `lcd_post_z` and the gap follows automatically — the two are
derived from one number, so they can't drift apart.

## Open items

- **The buck's ear hole spacing is a placeholder and it is now load-bearing.**
  `buck_ear_dx` is 37.0 mm, scaled off the product photo against the published
  43.9 mm across-the-ears width. Call it ±2 mm. Unlike the clamp bar it replaced,
  a fixed pair of inserts has no tolerance — if the real spacing differs, the
  screws will not line up. **Measure the ears before printing `back`.** The pad is
  58 × 50 mm and solid 5 mm, so as a fallback you can drill and self-tap anywhere
  on it. `buck_body_a/b` (34 × 42) and `buck_z` (21) are estimates from the same
  photo; they only affect clearance, not fit.
- Active-area offset (`aa_off_x` / `aa_off_y`) — confirm with `fitcheck` (above).
  Taken from the datum crosshair on the panel drawing. Note the drawing's own
  numbers don't quite close in X: the glass centre reads ~1.7 mm right of that
  crosshair, which would hang the glass ~1 mm off a 164.90 mm board. So there is
  about 1 mm of unexplained slop in X, and only ~0.9 mm of glass lip to absorb it.
- `ports_on_right` assumes the LCD's HDMI/USB edge is on the right viewed from the
  front, mirrored from Waveshare's component-side photo. If your board has the OSD
  buttons on the right instead, flip the flag and re-export; the OSD access holes
  move with it.
- Gland hole is a straight Ø12.7 (1/2"). Its axis is parallel to the bed when
  the shell prints face down, so expect it ~0.2–0.4 mm undersize; open up
  `obd_gland_d` if the gland is a tight push.

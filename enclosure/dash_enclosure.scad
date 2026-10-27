// RHB body display -- dashboard enclosure for the MT-55
//
//   Waveshare 7inch HDMI LCD (H) Rev4.1  +  Raspberry Pi 4B  +  Waveshare 2-CH CAN FD HAT
//
// Parts:
//   part = "fitcheck" test print (~25g, ~1.5h). Validates the window opening and the LCD
//                     bolt circle BEFORE you commit to the long shell print. PRINT THIS FIRST.
//   part = "shell"    front bezel + walls + connector panel. Print FACE DOWN.
//   part = "back"     rear plate: Pi standoffs, buck cradle, VESA/AMPS mount pad.
//   part = "assembly" / "section"   on-screen fit checking only.
//
// Coordinates: viewed from the FRONT of the screen. +X right, +Y up,
// +Z toward the rear (into the box). z=0 is the outer face of the bezel.
//
// Units: mm. Print in ASA -- see README.md for why PLA will fail here.

part = "shell   ";

$fn = 64;

// ---------------------------------------------------------------------------
// Waveshare 7inch HDMI LCD (H), Rev4.1
// Outline and bolt circle are taken from the vendor outline drawing; both are exact.
// ---------------------------------------------------------------------------
lcd_pcb_w      = 164.90;   // overall, across the corner tabs
lcd_pcb_h      = 124.27;   // overall, across the corner tabs
lcd_hole_dx    = 156.90;   // bolt circle
lcd_hole_dy    = 114.96;
lcd_pcb_t      =   2.00;
lcd_glass_t    =   4.50;   // LCD + touch panel, proud of the PCB front face
lcd_glass_w    = 163.49;   // cover glass outline, from the panel drawing
lcd_glass_h    =  96.69;
lcd_rear_z     =   6.90;   // tallest thing behind the PCB (the HDMI shell)

// ---------------------------------------------------------------------------
// Active area and where it actually sits. All of this is read off the panel
// outline drawing -- the active area is NOT centred on the glass.
// ---------------------------------------------------------------------------
aa_w           = 157.08;   // active (viewing) area
aa_h           =  88.92;

// glass left beyond the active area on each side -- note how little there is
// on the left and top; that is what limits how big the window can be
aa_glass_left  =   1.41;
aa_glass_right =   4.89;
aa_glass_top   =   1.52;
aa_glass_bot   =   6.23;

// Active-area centre relative to the bolt-circle centre, taken from the datum
// crosshair on the drawing: X lands exactly on it, Y sits 1.90 below.
// *** CONFIRM WITH part="fitcheck" BEFORE PRINTING THE SHELL ***
aa_off_x       =   0.00;
aa_off_y       =  -1.90;

// Where the board sits in the box. The default is the mirror of aa_off, which
// puts the picture dead centre in the bezel.
lcd_holes_off_x = -aa_off_x;
lcd_holes_off_y = -aa_off_y;

// The window is DERIVED from the board placement plus the active-area offset,
// so the two can never drift out of alignment.
window_margin  =   0.5;
window_w       = aa_w + 2*window_margin;
window_h       = aa_h + 2*window_margin;
window_off_x   = lcd_holes_off_x + aa_off_x;
window_off_y   = lcd_holes_off_y + aa_off_y;

// Which edge the LCD's own connectors are on, seen from the FRONT.
// The vendor's component-side photo shows HDMI/Touch/Power/HP/VGA on the left
// of that image and the five OSD buttons on the right; viewed from the front
// that mirrors to ports-right. Flip if your board disagrees.
ports_on_right = true;

// ---------------------------------------------------------------------------
// Raspberry Pi 4B + 2-CH CAN FD HAT
// ---------------------------------------------------------------------------
pi_w           = 85.0;
pi_h           = 56.0;
pi_hole_dx     = 58.0;
pi_hole_dy     = 49.0;
pi_pcb_t       =  1.40;
pi_conn_z      = 16.0;     // Ethernet / USB stack above the Pi PCB
pi_standoff_z  =  5.0;     // Pi PCB above the backplate inner face

hat_rise       = 12.0;     // HAT PCB above the Pi PCB, with a stacking header
hat_pcb_t      =  1.60;
hat_w          = 65.0;
hat_h          = 56.5;
hat_term_z     = 11.0;     // green screw terminals above the HAT PCB

// 12V -> 5V buck: YIPIN HEXHA 12/24V -> 5V 6A 30W dual USB-C (ASIN B0BCP86XPY).
// Potted brick, two moulded ears, two captive USB-C male leads (3A each).
//
// *** PLACEHOLDER DIMENSIONS -- MEASURE THE REAL PART BEFORE PRINTING "back" ***
// Amazon lists 43.9 x 41.9 x 21.1 mm, but the 43.9 is measured across the ears.
// The body below is scaled off the product photo (body spans 79% of the overall
// ear width), so treat it as +/-2mm. The clamp bar tolerates that; the ribs are
// deliberately loose and foam tape under the bar takes up the height error.
buck_body_a    = 34.0;     // ear axis (X); body only, ears excluded
buck_body_b    = 42.0;     // the other footprint axis (Y)
buck_z         = 21.0;     // body height above the pad
buck_ear_dx    = 37.0;     // *** ear mounting-hole spacing -- MEASURE THIS ***
buck_pad_t     =  5.0;     // raised pad: gives the M3 inserts somewhere to live
buck_pad_a     = 50.0;     // pad is oversized so you can drill your own holes
buck_pad_b     = 50.0;     // if the real ear spacing differs from buck_ear_dx

// board placement on the backplate (box coordinates)
pi_cx   = -20;  pi_cy   = -28;
buck_cx =  55;  buck_cy =  35;   // clear of the Pi in X, not stacked above it

// ---------------------------------------------------------------------------
// Envelope
// ---------------------------------------------------------------------------
wall           =  4.0;
front_t        =  4.0;     // bezel face thickness
lcd_post_z     =  7.5;     // bezel inner face -> front face of the LCD PCB.
                           // This IS the LCD post height. Measured off the
                           // fitcheck print; whatever is left over after the
                           // glass is the gasket gap below.
gasket_t       = lcd_post_z - lcd_glass_t;   // foam tape gap, bezel to glass
corner_r       =  8.0;

side_gap       = 20.0;     // clearance each side of the LCD: right-angle HDMI
                           // plug on one side, OSD buttons on the other
vert_gap       = 11.0;

shell_d        = 70.0;     // shell depth, z = 0 .. shell_d
back_t         =  4.0;     // backplate, sits outboard of the shell
rim_w          =  7.0;     // inward flange at the rear carrying the backplate screws
rim_z          = 10.0;

ow = lcd_pcb_w + 2*side_gap + 2*wall;   // 212.90
oh = lcd_pcb_h + 2*vert_gap + 2*wall;   // 154.27

// Depth landmarks
z_glass_front = z_pcb_front - lcd_glass_t;        // front face of the glass
z_pcb_front   = front_t + lcd_post_z;             // top of the LCD posts
z_pcb_back    = z_pcb_front + lcd_pcb_t;
z_lcd_max     = z_pcb_back + lcd_rear_z;
z_pi_pcb      = shell_d - pi_standoff_z;          // front face of the Pi PCB

// ---------------------------------------------------------------------------
// Fasteners
// ---------------------------------------------------------------------------
m3_insert_d    = 4.0;      // brass heat-set insert bore
m3_insert_z    = 6.0;
m3_free_d      = 3.4;
m3_head_d      = 6.2;
m4_insert_d    = 5.6;
m4_insert_z    = 8.0;
m25_insert_d   = 3.6;
m25_insert_z   = 5.5;

// ---------------------------------------------------------------------------
// Bottom wall: every connector plus the intake fan, so cables drop toward the
// dash and grit falls out rather than in.
//   *** Confirm each cutout against the part you actually buy. ***
//
// Every hole here has its axis parallel to the bed when the shell is printed
// face down, so they all come out undersize with some droop at the top of the
// bore. bottom_hole_comp is added to each diameter to compensate. Dial it to
// your printer: measure a printed hole and adjust by the difference.
// ---------------------------------------------------------------------------
bottom_hole_comp = 0.35;
// OBD-II feed leaves through a cable gland, not a panel socket -- a round hole
// is a dimension I can actually get right, and it seals far better than a
// rectangular cutout. Run an off-the-shelf OBD-II extension through it.
// 12.7 = a straight 1/2" hole, as specified.
// NOTE: this hole's axis lies parallel to the bed when the shell is printed
// face down, so it will come out slightly undersize and a little out of round
// -- typically 0.2-0.4mm. Open obd_gland_d up if your gland is a tight push.
obd_gland_d    =  12.7;
obd_x          = -30.0;
obd_z          =  40.0;

rj45_d         = 22.0;     // IP67 bulkhead RJ45 coupler
rj45_x         =  0.0;
rj45_z         =  40.0;

pwr_d          = 12.7;     // GX16 (or similar) 2-pin power bulkhead
pwr_x          =  30.0;
pwr_z          =  40.0;

fan_size       = 40.0;     // 40x40x10 intake fan, inside the bottom wall
fan_bore       = 38.0;
fan_hole_dx    = 32.0;
fan_x          =  65.0;
fan_z          =  40.0;

// VESA 75 and AMPS share one raised rear pad
pad_w  = 100.0;  pad_h = 100.0;  pad_t = 8.0;
vesa   =  75.0;
amps_dx = 38.1;  amps_dy = 30.0;

// ===========================================================================
// helpers
// ===========================================================================
module rrect(w, h, r) {
    hull() for (sx = [-1, 1], sy = [-1, 1])
        translate([sx*(w/2 - r), sy*(h/2 - r)]) circle(r = r);
}

module rbox(w, h, d, r) { linear_extrude(height = d) rrect(w, h, r); }

// blind bore for a heat-set insert, drilled from +Z downward
module insert_bore_down(d, z) { translate([0, 0, -z]) cylinder(d = d, h = z + 0.01); }
// ... and one drilled from -Z upward (for the inward-facing standoffs)
module insert_bore_up(d, z)   { translate([0, 0, -0.01]) cylinder(d = d, h = z + 0.01); }

module lcd_holes()  { for (sx=[-1,1], sy=[-1,1])
    translate([lcd_holes_off_x + sx*lcd_hole_dx/2, lcd_holes_off_y + sy*lcd_hole_dy/2]) children(); }
module pi_holes()   { for (sx=[-1,1], sy=[-1,1]) translate([sx*pi_hole_dx/2,   sy*pi_hole_dy/2])   children(); }
module buck_ears() { for (sx=[-1,1]) translate([buck_cx + sx*buck_ear_dx/2, buck_cy]) children(); }

// a cut made through the bottom wall, pointing inward
module bottom_cut(x, z) {
    translate([x, -oh/2, z]) rotate([90, 0, 0]) translate([0, 0, -wall - 1]) children();
}

// eight screws hold the backplate on
back_screw_pts = [
    [-ow/2 + wall + rim_w/2,  oh/2 - wall - rim_w/2], [0,  oh/2 - wall - rim_w/2], [ow/2 - wall - rim_w/2,  oh/2 - wall - rim_w/2],
    [-ow/2 + wall + rim_w/2,  0],                                                  [ow/2 - wall - rim_w/2,  0],
    [-ow/2 + wall + rim_w/2, -oh/2 + wall + rim_w/2], [0, -oh/2 + wall + rim_w/2], [ow/2 - wall - rim_w/2, -oh/2 + wall + rim_w/2],
];

// ===========================================================================
// SHELL -- bezel, walls, connector panel. Print face down.
// ===========================================================================
module shell() {
    difference() {
        union() {
            // hollow the box first, so the internal features added below
            // survive -- cutting the cavity last would delete them
            difference() {
                rbox(ow, oh, shell_d, corner_r);
                translate([0, 0, front_t])
                    rbox(ow - 2*wall, oh - 2*wall, shell_d, max(corner_r - wall, 1));
            }

            // LCD standoffs: the PCB lands on these, the glass then sits proud
            // into the bezel recess
            lcd_holes() translate([0, 0, front_t - 0.01])
                cylinder(d = 9, h = z_pcb_front - front_t + 0.01);

            // rear flange carrying the backplate inserts, overlapping the walls
            // slightly so it fuses to them
            translate([0, 0, shell_d - rim_z])
                linear_extrude(rim_z) difference() {
                    rrect(ow - 2*wall + 0.4, oh - 2*wall + 0.4, max(corner_r - wall, 1));
                    rrect(ow - 2*wall - 2*rim_w, oh - 2*wall - 2*rim_w, 2);
                }
        }

        // ---- viewing window, chamfered on the outside ----
        translate([window_off_x, window_off_y, -0.01])
            linear_extrude(front_t + 0.02) rrect(window_w, window_h, 3);
        translate([window_off_x, window_off_y, -0.01])
            linear_extrude(1.6, scale = [(window_w - 3.2)/window_w,
                                         (window_h - 3.2)/window_h])
                rrect(window_w, window_h, 3);

        // ---- glass relief: the panel is larger than the window ----
        translate([window_off_x + (aa_glass_right - aa_glass_left)/2,
                   window_off_y + (aa_glass_top - aa_glass_bot)/2, front_t])
            linear_extrude(gasket_t + lcd_glass_t + 0.2)
                rrect(lcd_glass_w + 1.0, lcd_glass_h + 1.0, 3);

        // ---- LCD mounting inserts ----
        lcd_holes() translate([0, 0, z_pcb_front]) insert_bore_down(m3_insert_d, m3_insert_z);

        // ---- backplate inserts ----
        for (p = back_screw_pts)
            translate([p[0], p[1], shell_d]) insert_bore_down(m3_insert_d, m3_insert_z);

        bottom_panel();
        top_louvres();
        osd_access();
    }
}

// J1962, RJ45, power and the fan, all in the bottom wall
module bottom_panel() {
    // OBD-II cable gland
    bottom_cut(obd_x, obd_z) cylinder(d = obd_gland_d + bottom_hole_comp, h = wall + 2);

    bottom_cut(rj45_x, rj45_z) cylinder(d = rj45_d + bottom_hole_comp, h = wall + 2);
    bottom_cut(pwr_x,  pwr_z)  cylinder(d = pwr_d  + bottom_hole_comp, h = wall + 2);

    // fan bore and its four screws
    bottom_cut(fan_x, fan_z) cylinder(d = fan_bore + bottom_hole_comp, h = wall + 2);
    for (sx = [-1, 1], sy = [-1, 1])
        bottom_cut(fan_x + sx*fan_hole_dx/2, fan_z + sy*fan_hole_dx/2)
            cylinder(d = m3_free_d + bottom_hole_comp, h = wall + 2);
}

// angled slots across the top, so nothing falls straight in
module top_louvres() {
    n = 9;
    for (i = [0 : n - 1], row = [0, 1])
        translate([-72 + i*18, oh/2 - wall/2, shell_d - 26 + row*8])
            rotate([30, 0, 0]) cube([11, wall*3, 3.0], center = true);
}

// five holes lined up with the LCD's OSD buttons, so the backlight can be
// dropped at night without opening the box
module osd_access() {
    sx = ports_on_right ? -1 : 1;
    for (i = [0 : 4])
        translate([sx*(ow/2 - wall/2), lcd_holes_off_y + 24 - i*12, z_pcb_back + 3])
            rotate([0, 90, 0]) cylinder(d = 4.0, h = wall*3, center = true);
}

// ===========================================================================
// BACKPLATE -- carries the Pi stack, the buck and the mount pad
// ===========================================================================
module backplate() {
    difference() {
        union() {
            translate([0, 0, shell_d]) rbox(ow, oh, back_t, corner_r);
            translate([0, 0, shell_d + back_t]) rbox(pad_w, pad_h, pad_t, 10);

            // inward standoffs
            translate([pi_cx,   pi_cy,   shell_d - pi_standoff_z])
                pi_holes() cylinder(d = 7, h = pi_standoff_z);
            // buck mounting pad -- the module's moulded ears bolt straight
            // down onto this, two M3 into heat-set inserts
            translate([buck_cx, buck_cy, shell_d - buck_pad_t])
                rbox(buck_pad_a, buck_pad_b, buck_pad_t, 4);
        }

        // backplate fixing screws, countersunk from outside
        for (p = back_screw_pts) {
            translate([p[0], p[1], shell_d - 0.01]) cylinder(d = m3_free_d, h = back_t + 0.02);
            // 90-degree countersink: depth = (head_d - free_d)/2, so a DIN 7991
            // flat head seats on the cone instead of sinking past it
            translate([p[0], p[1], shell_d + back_t - (m3_head_d - m3_free_d)/2])
                cylinder(d1 = m3_free_d, d2 = m3_head_d,
                         h = (m3_head_d - m3_free_d)/2 + 0.01);
        }

        // standoff bores, drilled from the free (inward) end
        translate([pi_cx, pi_cy, shell_d - pi_standoff_z])
            pi_holes() insert_bore_up(m25_insert_d, m25_insert_z);
        buck_ears() translate([0, 0, shell_d - buck_pad_t])
            insert_bore_up(m3_insert_d, m3_insert_z);

        // VESA 75 + AMPS, blind from the outside so nothing breaks through
        for (sx = [-1, 1], sy = [-1, 1]) {
            translate([sx*vesa/2,    sy*vesa/2,    shell_d + back_t + pad_t]) insert_bore_down(m4_insert_d, m4_insert_z);
            translate([sx*amps_dx/2, sy*amps_dy/2, shell_d + back_t + pad_t]) insert_bore_down(m4_insert_d, m4_insert_z);
        }
    }
}

// ===========================================================================
// FITCHECK -- print this first. Confirms the window opening, the bolt circle
// and the glass relief in ~20 minutes and ~8g of filament.
// ===========================================================================
module fitcheck() {
    fw = lcd_pcb_w + 2*wall + 4;
    fh = lcd_pcb_h + 2*wall + 4;
    difference() {
        union() {
            rbox(fw, fh, front_t, corner_r);
            lcd_holes() translate([0, 0, front_t]) cylinder(d = 9, h = z_pcb_front - front_t);
        }
        translate([0, window_off_y, -0.01])
            linear_extrude(front_t + 0.02) rrect(window_w, window_h, 3);
        translate([window_off_x + (aa_glass_right - aa_glass_left)/2,
                   window_off_y + (aa_glass_top - aa_glass_bot)/2, front_t])
            linear_extrude(gasket_t + lcd_glass_t + 0.2)
                rrect(lcd_glass_w + 1.0, lcd_glass_h + 1.0, 3);
        lcd_holes() translate([0, 0, z_pcb_front]) insert_bore_down(m3_insert_d, m3_insert_z);
    }
}

// ===========================================================================
// Mock-ups, for on-screen fit checking only
// ===========================================================================
module mock_lcd() {
    color("#1b3a5c") translate([lcd_holes_off_x, lcd_holes_off_y, z_pcb_front])
        linear_extrude(lcd_pcb_t) rrect(lcd_pcb_w, lcd_pcb_h, 4);
    color("#0b0b0b") translate([window_off_x + (aa_glass_right - aa_glass_left)/2,
                                window_off_y + (aa_glass_top - aa_glass_bot)/2, z_glass_front])
        linear_extrude(lcd_glass_t) rrect(lcd_glass_w, lcd_glass_h, 2);
    color("#1a3a6a") translate([window_off_x, window_off_y, z_glass_front + lcd_glass_t - 0.1])
        linear_extrude(0.2) square([aa_w, aa_h], center = true);
    color("#777") translate([lcd_holes_off_x, lcd_holes_off_y, z_pcb_back])
        linear_extrude(lcd_rear_z) rrect(120, 90, 2);
}

module mock_pi() {
    translate([pi_cx, pi_cy, 0]) {
        color("#2a7d3f") translate([0, 0, z_pi_pcb - pi_pcb_t]) linear_extrude(pi_pcb_t) square([pi_w, pi_h], center = true);
        color("#b0b0b0") translate([0, 0, z_pi_pcb - pi_pcb_t - pi_conn_z]) linear_extrude(pi_conn_z) square([42, pi_h - 6], center = true);
        color("#1b3a5c") translate([0, 0, z_pi_pcb - pi_pcb_t - hat_rise - hat_pcb_t]) linear_extrude(hat_pcb_t) square([hat_w, hat_h], center = true);
        color("#3aa050") translate([0, hat_h/2 - 7, z_pi_pcb - pi_pcb_t - hat_rise - hat_pcb_t - hat_term_z]) linear_extrude(hat_term_z) square([hat_w - 10, 12], center = true);
    }
}

module mock_buck() {
    color("#8a2222") translate([buck_cx, buck_cy, shell_d - buck_pad_t - buck_z])
        linear_extrude(buck_z) square([buck_body_a, buck_body_b], center = true);
    color("#444") translate([buck_cx, buck_cy, shell_d - buck_pad_t - 3])
        linear_extrude(3) square([buck_ear_dx + 10, 14], center = true);
}

module mock_fan() {
    color("#333") translate([fan_x, -oh/2 + wall + 5, fan_z]) rotate([90, 0, 0])
        difference() {
            cube([fan_size, fan_size, 10], center = true);
            cylinder(d = fan_bore, h = 12, center = true);
        }
}

// ===========================================================================
if      (part == "shell")    shell();
else if (part == "back")     backplate();
else if (part == "fitcheck") fitcheck();
else if (part == "assembly") {
    color("#cdd2d7") shell();
    color("#b6bcc2") backplate();
    mock_lcd(); mock_pi(); mock_buck(); mock_fan();
} else if (part == "section") {
    difference() {
        union() {
            color("#cdd2d7") shell();
            color("#b6bcc2") backplate();
            mock_lcd(); mock_pi(); mock_buck(); mock_fan();
        }
        translate([-ow, -oh, -10]) cube([2*ow, oh, 200]);
    }
}

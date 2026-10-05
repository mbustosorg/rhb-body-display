"""
 Copyright (C) 2020 Mauricio Bustos (m@bustos.org)
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""Renders an excursion report as a self contained page of inline SVG"""

import datetime
import html
import math
import statistics

# Speed bands, echoing the colours the body display uses for the live track
SPEED_BANDS = ((0.0, 2.0, "under 2"), (2.0, 5.0, "2 - 5"), (5.0, 10.0, "5 - 10"),
               (10.0, 15.0, "10 - 15"), (15.0, None, "15+"))

MAP_WIDTH = 900.0
# Poofs closer together than this are counted as one place on the density map
POOF_CELL_FT = 250
POOF_MIN_RADIUS = 4.0
POOF_MAX_RADIUS = 26.0
CHART_WIDTH = 900.0
CHART_HEIGHT = 264.0
PLOT_MARGIN = (28.0, 18.0, 34.0, 52.0)  # top, right, bottom, left

STYLE = """
:root { color-scheme: light dark; }
.viz-root {
  color-scheme: light;
  --page: #f9f9f7;
  --surface-1: #fcfcfb;
  --text-primary: #0b0b0b;
  --text-secondary: #52514e;
  --text-muted: #898781;
  --grid: #e1e0d9;
  --axis: #c3c2b7;
  --border: rgba(11,11,11,0.10);
  --wash: rgba(11,11,11,0.05);
  --series-1: #2a78d6;
  --series-2: #a8483a;
  --series-3: #1a9b83;
  /* Beverly is a fire extinguisher, so the accent is her red, held back a long way
     from the real thing -- this is a log book, not a flyer */
  --brand: #a8483a;
  --brand-ink: #8f3b2f;
  --good: #0ca30c;
  --warning: #fab219;
  --critical: #d03b3b;
  --speed-1: #86b6ef;
  --speed-2: #5598e7;
  --speed-3: #2a78d6;
  --speed-4: #1c5cab;
  --speed-5: #0d366b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --page: #0d0d0d;
    --surface-1: #1a1a19;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #898781;
    --grid: #2c2c2a;
    --axis: #383835;
    --border: rgba(255,255,255,0.10);
    --wash: rgba(255,255,255,0.06);
    --series-1: #3987e5;
    --series-2: #b8503f;
    --series-3: #25a08d;
    --brand: #b8503f;
    --brand-ink: #c9614f;
    --speed-1: #184f95;
    --speed-2: #256abf;
    --speed-3: #3987e5;
    --speed-4: #86b6ef;
    --speed-5: #cde2fb;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --page: #0d0d0d;
  --surface-1: #1a1a19;
  --text-primary: #ffffff;
  --text-secondary: #c3c2b7;
  --text-muted: #898781;
  --grid: #2c2c2a;
  --axis: #383835;
  --border: rgba(255,255,255,0.10);
  --wash: rgba(255,255,255,0.06);
  --series-1: #3987e5;
  --series-2: #b8503f;
  --series-3: #25a08d;
  --brand: #b8503f;
  --brand-ink: #c9614f;
  --speed-1: #184f95;
  --speed-2: #256abf;
  --speed-3: #3987e5;
  --speed-4: #86b6ef;
  --speed-5: #cde2fb;
}
* { box-sizing: border-box; }
body { margin: 0; }
.viz-root {
  background: var(--page);
  color: var(--text-primary);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 15px;
  line-height: 1.55;
  padding: 32px 20px 64px;
}
.wrap { max-width: 1060px; margin: 0 auto; }
header.masthead { margin-bottom: 28px; }
.brandmark {
  display: flex; align-items: center; gap: 9px; margin: 0 0 12px;
  font-size: 13px; font-weight: 640; letter-spacing: 0.11em;
  text-transform: uppercase; color: var(--brand-ink);
}
/* A stub of her body, stood on end */
.brandmark .canister {
  width: 7px; height: 17px; border-radius: 2px 2px 3px 3px;
  background: var(--brand); flex: none;
}
.brandmark .tagline { color: var(--text-muted); font-weight: 500; letter-spacing: 0.06em; }
.eyebrow {
  font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--text-muted); margin: 0 0 6px;
}
h1 { font-size: 30px; line-height: 1.2; margin: 0 0 6px; font-weight: 640; }
.subhead { color: var(--text-secondary); margin: 0; }
section { margin-top: 34px; }
h2 { font-size: 18px; margin: 0 0 4px; font-weight: 620; }
h3 { font-size: 15px; margin: 24px 0 6px; font-weight: 600; }
.note { color: var(--text-secondary); margin: 0 0 14px; max-width: 68ch; }
.note.after { margin-top: 20px; }
.card {
  background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 14px; padding: 18px;
}
.hero { display: flex; flex-wrap: wrap; gap: 28px; align-items: flex-end; }
.hero-figure { line-height: 1; }
.hero-figure .value { font-size: 64px; font-weight: 640; letter-spacing: -0.02em; }
.hero-figure .unit { font-size: 20px; color: var(--text-secondary); margin-left: 10px; }
.hero-figure .label { color: var(--text-secondary); font-size: 14px; margin-top: 8px; }
.summary { flex: 1 1 380px; color: var(--text-secondary); min-width: 300px; }
.summary strong { color: var(--text-primary); font-weight: 600; }
.tiles {
  display: grid; gap: 12px; margin-top: 20px;
  grid-template-columns: repeat(auto-fit, minmax(168px, 1fr));
}
.tile {
  background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 16px;
}
.tile .label { color: var(--text-secondary); font-size: 13px; }
.tile .value { font-size: 26px; font-weight: 620; margin-top: 2px; }
.tile .foot { color: var(--text-muted); font-size: 12px; margin-top: 2px; }
.chart { width: 100%; height: auto; display: block; overflow: visible; }
.tiles + .chart { margin-top: 22px; }
.chart text { font-family: inherit; }
.tick { font-size: 11px; fill: var(--text-muted); font-variant-numeric: tabular-nums; }
.axis-title { font-size: 11px; fill: var(--text-muted); }
.mark-label { font-size: 11px; fill: var(--text-secondary); font-weight: 600; }
/* Map labels sit on top of the track, so they carry a halo of the surface colour */
.map-label { paint-order: stroke; stroke: var(--surface-1); stroke-width: 3px; stroke-linejoin: round; }
.gridline { stroke: var(--grid); stroke-width: 1; }
.baseline { stroke: var(--axis); stroke-width: 1; }
.hit { fill: transparent; cursor: crosshair; }
.hit:hover { fill: var(--wash); }
.legend {
  display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 12px 0 0;
  color: var(--text-secondary); font-size: 13px; list-style: none; padding: 0;
}
.legend li { display: flex; align-items: center; gap: 7px; }
.swatch { width: 14px; height: 8px; border-radius: 2px; display: inline-block; }
.swatch.dot { width: 10px; height: 10px; border-radius: 50%; }
.chip {
  display: inline-block; font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase;
  padding: 2px 8px; border-radius: 999px; border: 1px solid var(--border); color: var(--text-secondary);
}
.chip.playa { border-color: var(--series-2); color: var(--series-2); }
.meter {
  display: block; height: 6px; border-radius: 3px; background: var(--wash); min-width: 60px;
}
.meter span { display: block; height: 100%; border-radius: 3px; background: var(--series-1); }
tr.night td { vertical-align: middle; }
tr.night a { color: var(--text-primary); text-decoration: none; font-weight: 600; }
tr.night a:hover, tr.night a:focus-visible { text-decoration: underline; }
a:focus-visible, summary:focus-visible { outline: 2px solid var(--series-1); outline-offset: 2px; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }
th { color: var(--text-secondary); font-weight: 600; font-size: 12px;
     letter-spacing: 0.04em; text-transform: uppercase; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.scroll { overflow-x: auto; }
/* Some monospace faces ligate "--" into a dash, which mangles the flags */
code { font-variant-ligatures: none; }
details { margin-top: 12px; }
summary {
  cursor: pointer; color: var(--text-secondary); font-size: 13px;
  padding: 4px 0; width: fit-content;
}
details[open] summary { margin-bottom: 6px; }
.empty {
  color: var(--text-secondary); background: var(--wash); border-radius: 10px;
  padding: 12px 14px; font-size: 14px;
}
.flag { display: inline-flex; align-items: center; gap: 7px; }
.flag .dot { width: 9px; height: 9px; border-radius: 50%; flex: none; }
#tip {
  position: fixed; z-index: 20; pointer-events: none; max-width: 260px;
  background: var(--surface-1); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 9px; padding: 7px 10px;
  font-size: 13px; line-height: 1.4; box-shadow: 0 6px 22px rgba(0,0,0,0.16);
}
#tip[hidden] { display: none; }
footer.colophon {
  margin-top: 44px; padding-top: 16px; border-top: 1px solid var(--border);
  color: var(--text-muted); font-size: 13px;
}
@media (max-width: 640px) {
  h1 { font-size: 24px; }
  .hero-figure .value { font-size: 48px; }
}
"""

SCRIPT = """
(function () {
  var tip = document.getElementById('tip');
  function show(target) {
    tip.innerHTML = target.getAttribute('data-tip');
    tip.hidden = false;
  }
  function place(x, y) {
    var left = Math.min(window.innerWidth - tip.offsetWidth - 12, x + 14);
    tip.style.left = Math.max(8, left) + 'px';
    tip.style.top = Math.max(8, y - tip.offsetHeight - 14) + 'px';
  }
  document.addEventListener('mouseover', function (event) {
    var target = event.target.closest('[data-tip]');
    if (target) { show(target); place(event.clientX, event.clientY); }
  });
  document.addEventListener('mousemove', function (event) {
    if (!tip.hidden) { place(event.clientX, event.clientY); }
  });
  document.addEventListener('mouseout', function (event) {
    if (event.target.closest('[data-tip]')) { tip.hidden = true; }
  });
  document.addEventListener('focusin', function (event) {
    var target = event.target.closest('[data-tip]');
    if (!target) { return; }
    var box = target.getBoundingClientRect();
    show(target);
    place(box.left + box.width / 2, box.top);
  });
  document.addEventListener('focusout', function () { tip.hidden = true; });
})();
"""


# ------------------------------------------------------------------ formatting


def esc(text):
    return html.escape(str(text), quote=True)


def clock_time(moment):
    """A moment as people say it out loud"""
    hour = moment.hour % 12 or 12
    return "%d:%02d %s" % (hour, moment.minute, "am" if moment.hour < 12 else "pm")


def duration(seconds):
    """A span as hours and minutes"""
    seconds = int(round(seconds))
    hours, minutes = seconds // 3600, (seconds % 3600) // 60
    if hours and minutes:
        return "%dh %dm" % (hours, minutes)
    if hours:
        return "%dh" % hours
    if minutes:
        return "%dm" % minutes
    return "%ds" % seconds


def commas(value):
    return format(int(round(value)), ",")


def nice_bounds(low, high, steps=4):
    """Axis bounds and a step that land the ticks on round numbers"""
    if high - low < 1e-9:
        low, high = low - 1.0, high + 1.0
    raw = (high - low) / steps
    magnitude = 10.0 ** math.floor(math.log10(raw))
    step = magnitude * 10.0
    for candidate in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw <= candidate * magnitude:
            step = candidate * magnitude
            break
    floor = math.floor(low / step) * step
    ceiling = floor + step * steps
    while ceiling < high:
        ceiling += step
    return floor, ceiling, step


def nice_ceiling(value, steps=4):
    """A round axis maximum at or above the data"""
    if value <= 0:
        return 1.0
    raw = value / steps
    magnitude = 10.0 ** math.floor(math.log10(raw))
    for candidate in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw <= candidate * magnitude:
            return candidate * magnitude * steps
    return 10.0 * magnitude * steps


def speed_band(mph):
    """Index of the speed band a leg falls in"""
    for index, (low, high, _) in enumerate(SPEED_BANDS):
        if mph >= low and (high is None or mph < high):
            return index
    return len(SPEED_BANDS) - 1


# ----------------------------------------------------------------- plot helpers


class Plot:
    """A rectangular plotting area with linear scales"""

    def __init__(self, width, height, x_range, y_range, margin=PLOT_MARGIN):
        self.width, self.height = width, height
        self.top, self.right, self.bottom, self.left = margin
        self.x0, self.x1 = x_range
        self.y0, self.y1 = y_range
        self.inner_w = width - self.left - self.right
        self.inner_h = height - self.top - self.bottom

    def x(self, value):
        if self.x1 == self.x0:
            return self.left
        return self.left + (value - self.x0) / (self.x1 - self.x0) * self.inner_w

    def y(self, value):
        if self.y1 == self.y0:
            return self.top + self.inner_h
        return self.top + self.inner_h - (value - self.y0) / (self.y1 - self.y0) * self.inner_h

    def frame(self, y_ticks, y_format=commas, y_title=""):
        """Horizontal gridlines, their labels and the baseline"""
        parts = []
        for value in y_ticks:
            y = self.y(value)
            parts.append('<line class="gridline" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                         % (self.left, y, self.left + self.inner_w, y))
            parts.append('<text class="tick" x="%.1f" y="%.1f" text-anchor="end">%s</text>'
                         % (self.left - 8, y + 4, esc(y_format(value))))
        parts.append('<line class="baseline" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     % (self.left, self.y(self.y0), self.left + self.inner_w, self.y(self.y0)))
        if y_title:
            # Sits above the topmost tick label rather than beside it
            parts.append('<text class="axis-title" x="%.1f" y="%.1f">%s</text>'
                         % (self.left - 44, self.top - 12, esc(y_title)))
        return "".join(parts)

    def hour_axis(self, start, end):
        """Two hourly ticks along the bottom"""
        parts = []
        tick = start.replace(minute=0, second=0, microsecond=0)
        if tick < start:
            tick += datetime.timedelta(hours=1)
        while tick <= end:
            if tick.hour % 2 == 0 or tick == start:
                x = self.x((tick - start).total_seconds())
                parts.append('<text class="tick" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                             % (x, self.top + self.inner_h + 18, esc(clock_time(tick))))
            tick += datetime.timedelta(hours=1)
        return "".join(parts)


def star_path(x, y, size):
    """A five pointed star, points up, centred on the position"""
    points = []
    for step in range(10):
        angle = math.radians(-90.0 + step * 36.0)
        radius = size if step % 2 == 0 else size * 0.42
        points.append("%.1f,%.1f" % (x + radius * math.cos(angle), y + radius * math.sin(angle)))
    return "M%s Z" % " L".join(points)


def flame_path(x, y, size):
    """A teardrop with a kicked tip, which reads as a flame even a few millimetres across"""
    tip, half, base = size * 1.25, size * 0.62, size * 0.55
    return ("M%.1f,%.1f C%.1f,%.1f %.1f,%.1f %.1f,%.1f "
            "C%.1f,%.1f %.1f,%.1f %.1f,%.1f "
            "C%.1f,%.1f %.1f,%.1f %.1f,%.1f Z"
            % (x, y - tip,
               x + half * 0.55, y - tip * 0.35, x + half, y - base * 0.1, x + half, y + base * 0.25,
               x + half, y + base * 1.25, x + half * 0.5, y + base * 1.6, x, y + base * 1.6,
               x - half * 0.5, y + base * 1.6, x - half, y + base * 1.25, x - half, y + base * 0.25))


def svg(width, height, body, label):
    return ('<svg class="chart" viewBox="0 0 %.0f %.0f" role="img" aria-label="%s" '
            'preserveAspectRatio="xMidYMid meet">%s</svg>' % (width, height, esc(label), body))


# ---------------------------------------------------------------------- the map


class MapFrame:
    """A square-ground window onto the night, shared by every map the report draws"""

    DEGREES_PER_FOOT = 1.0 / 364000.0  # a degree of latitude is about 364,000 ft

    def __init__(self, report, aspect=None, focus=None):
        self.report = report
        # Framing on a handful of fixes zooms the window onto them; the rest of the track is
        # still drawn and simply runs out of the frame, which is what a close up wants
        framed = focus or report.trusted
        lats = [fix.lat for fix in framed]
        lons = [fix.lon for fix in framed]
        self.stretch = math.cos(math.radians((min(lats) + max(lats)) / 2.0))
        xs = [lon * self.stretch for lon in lons]
        span_x, span_y = max(xs) - min(xs), max(lats) - min(lats)
        # Never blow a short hop up to fill the frame
        floor = 0.0075
        span_x, span_y = max(span_x, floor), max(span_y, floor * 0.6)
        mid_x, mid_y = (min(xs) + max(xs)) / 2, (min(lats) + max(lats)) / 2
        pad_x, pad_y = span_x * 0.10, span_y * 0.12
        self.x0, self.x1 = mid_x - span_x / 2 - pad_x, mid_x + span_x / 2 + pad_x
        self.y0, self.y1 = mid_y - span_y / 2 - pad_y, mid_y + span_y / 2 + pad_y
        # The book gives every map the same square hole to sit in, so it asks for the shape
        # it wants and the squaring below widens the ground to suit
        self.height = (MAP_WIDTH * aspect if aspect
                       else max(360.0, min(760.0, MAP_WIDTH * (self.y1 - self.y0) / (self.x1 - self.x0))))
        # Grow the short side so the ground stays square
        view_ratio = self.height / MAP_WIDTH
        if (self.y1 - self.y0) / (self.x1 - self.x0) < view_ratio:
            grow = ((self.x1 - self.x0) * view_ratio - (self.y1 - self.y0)) / 2
            self.y0, self.y1 = self.y0 - grow, self.y1 + grow
        else:
            grow = ((self.y1 - self.y0) / view_ratio - (self.x1 - self.x0)) / 2
            self.x0, self.x1 = self.x0 - grow, self.x1 + grow

    def project(self, lon, lat):
        return ((lon * self.stretch - self.x0) / (self.x1 - self.x0) * MAP_WIDTH,
                self.height - (lat - self.y0) / (self.y1 - self.y0) * self.height)

    def cell(self, lat, lon, feet):
        """Grid square a position falls in, for counting things by neighbourhood"""
        size = feet * self.DEGREES_PER_FOOT
        return int(lon * self.stretch / size), int(lat / size)

    def open(self, clip_id):
        return ('<clipPath id="%s"><rect x="0" y="0" width="%.0f" height="%.0f" rx="10"/></clipPath>'
                '<rect x="0" y="0" width="%.0f" height="%.0f" rx="10" fill="var(--surface-1)" '
                'stroke="var(--border)"/><g clip-path="url(#%s)">'
                % (clip_id, MAP_WIDTH, self.height, MAP_WIDTH, self.height, clip_id))

    def streets(self, colour):
        drawn = []
        for line in self.report.city.streets:
            if len(line) < 2:
                continue
            if not any(self.x0 <= lon * self.stretch <= self.x1 and self.y0 <= lat <= self.y1 for lon, lat in line):
                continue
            drawn.append('<polyline points="%s"/>'
                         % " ".join("%.1f,%.1f" % self.project(lon, lat) for lon, lat in line))
        return '<g fill="none" stroke="%s" stroke-width="1.5">%s</g>' % (colour, "".join(drawn))

    def man(self):
        city = self.report.city
        ring = " ".join("%.1f,%.1f" % self.project(lon, lat) for lon, lat in city.man_ring)
        x, y = self.project(city.man_lon, city.man_lat)
        return ('<polygon points="%s" fill="none" stroke="var(--axis)" stroke-width="2"/>'
                '<circle cx="%.1f" cy="%.1f" r="3" fill="var(--text-muted)"/>'
                '<text class="tick map-label" x="%.1f" y="%.1f" text-anchor="middle">the Man</text>'
                % (ring, x, y, x, y - 9))

    def runs(self, band_of=None):
        """The track as polylines, split wherever the grouping value changes"""
        runs = []
        for segment in self.report.segments:
            band = band_of(segment) if band_of else 0
            if runs and runs[-1][0] == band and runs[-1][1][-1] is segment.start:
                runs[-1][1].append(segment.end)
            else:
                runs.append((band, [segment.start, segment.end]))
        drawn = [(band, " ".join("%.1f,%.1f" % self.project(fix.lon, fix.lat) for fix in points))
                 for band, points in runs]
        return drawn if band_of else [points for _, points in drawn]

    def places(self, size=9.0):
        """Our own two marks: a star on the camp and a flame out at the fence

        Drawn under everything else the maps put on top, so a night's track and its stops
        still read first -- these say where the season was pitched, not what it did.
        """
        drawn = []
        for name, glyph, lon, lat in getattr(self.report.city, "places", ()):
            x, y = self.project(lon, lat)
            shape = star_path(x, y, size) if glyph == "star" else flame_path(x, y, size)
            drawn.append('<g><path d="%s" fill="var(--brand)" fill-opacity="0.85" '
                         'stroke="var(--surface-1)" stroke-width="1.2" stroke-linejoin="round"/>'
                         '<text class="tick map-label" x="%.1f" y="%.1f" text-anchor="middle" '
                         'fill="var(--brand-ink)">%s</text></g>'
                         % (shape, x, y + size + 11.0, esc(name)))
        return "".join(drawn)

    def scale_bar(self):
        """A thousand foot rule in the corner so distances on the map can be read"""
        length = 1000.0 * self.DEGREES_PER_FOOT / (self.x1 - self.x0) * MAP_WIDTH
        x, y = 24.0, self.height - 26.0
        return ('<g><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="baseline" stroke-width="2"/>'
                '<text class="tick map-label" x="%.1f" y="%.1f">1,000 ft</text></g>'
                % (x, y, x + length, y, x, y - 6))


def map_chart(report, aspect=None, focus=None, key="route", marks=()):
    """The night's track drawn over this year's streets

    The book puts every map in one document, so the clip needs an id of its own or they all
    resolve to whichever was defined first. Marks are (lat, lon, label) for anything on the
    ground worth naming -- an art piece the night was spent at, say.
    """
    frame = MapFrame(report, aspect, focus)
    clip = "%sframe" % key
    parts = [frame.open(clip)]
    if report.on_playa:
        parts.append(frame.streets("var(--grid)"))
        parts.append(frame.man())
        parts.append(frame.places())

    for band, points in frame.runs(lambda segment: speed_band(segment.mph)):
        parts.append('<polyline points="%s" fill="none" stroke="var(--speed-%d)" stroke-width="2.5" '
                     'stroke-linecap="round" stroke-linejoin="round"/>' % (points, band + 1))

    for index, stop in enumerate(report.stops, start=1):
        x, y = frame.project(stop.lon, stop.lat)
        tip = "<b>Stop %d &middot; %s</b><br>%s for %s%s" % (
            index, esc(stop.address), esc(clock_time(stop.start)), esc(duration(stop.seconds)),
            "<br>%d poofs here" % stop.poofs if stop.poofs else "")
        parts.append('<g tabindex="0" data-tip="%s"><circle cx="%.1f" cy="%.1f" r="11" fill="transparent"/>'
                     '<circle cx="%.1f" cy="%.1f" r="5.5" fill="var(--surface-1)" stroke="var(--series-2)" '
                     'stroke-width="2.5"/></g>' % (esc(tip), x, y, x, y))

    for fix, label, colour in ((report.first_fix, "roll out", "var(--series-3)"),
                               (report.last_fix, "last fix", "var(--text-secondary)")):
        x, y = frame.project(fix.lon, fix.lat)
        parts.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s" stroke="var(--surface-1)" stroke-width="2"/>'
                     % (x, y, colour))
        anchor = "start" if x < MAP_WIDTH / 2 else "end"
        offset = 10 if anchor == "start" else -10
        parts.append('<text class="mark-label map-label" x="%.1f" y="%.1f" text-anchor="%s">%s %s</text>'
                     % (x + offset, y + 4, anchor, esc(label), esc(clock_time(fix.timestamp))))

    for lat, lon, label in marks:
        x, y = frame.project(lon, lat)
        anchor = "start" if x < MAP_WIDTH / 2 else "end"
        offset = 14 if anchor == "start" else -14
        parts.append('<g><circle cx="%.1f" cy="%.1f" r="9" fill="none" stroke="var(--brand)" '
                     'stroke-width="2"/><circle cx="%.1f" cy="%.1f" r="2.5" fill="var(--brand)"/>'
                     '<text class="mark-label map-label" x="%.1f" y="%.1f" text-anchor="%s" '
                     'fill="var(--brand-ink)">%s</text></g>'
                     % (x, y, x, y, x + offset, y + 4, anchor, esc(label)))

    parts.append("</g>")
    parts.append(frame.scale_bar())
    return svg(MAP_WIDTH, frame.height, "".join(parts), "Map of the night's route through Black Rock City")


def poof_map(report, aspect=None, key="poof"):
    """Where the poofer fired, as a density over the night's track

    Takes its shape and its clip id the same way the route map does, so the book can give
    it a page of its own without every map in the document sharing one clip.
    """
    located = [poof for poof in report.poofs if poof.lat is not None]
    if not located:
        return ""
    frame = MapFrame(report, aspect)
    parts = [frame.open("%sframe" % key)]
    if report.on_playa:
        parts.append(frame.streets("var(--grid)"))
        parts.append(frame.man())
        parts.append(frame.places())
    # The track recedes to context so the density is the thing being read
    for run in frame.runs():
        parts.append('<polyline points="%s" fill="none" stroke="var(--axis)" stroke-width="1.5" '
                     'stroke-linecap="round" stroke-linejoin="round"/>' % run)

    cells = {}
    for poof in located:
        key = frame.cell(poof.lat, poof.lon, POOF_CELL_FT)
        cells.setdefault(key, []).append(poof)
    busiest = max(len(group) for group in cells.values())
    for (column, row), group in sorted(cells.items(), key=lambda item: len(item[1])):
        lat = sum(poof.lat for poof in group) / len(group)
        lon = sum(poof.lon for poof in group) / len(group)
        x, y = frame.project(lon, lat)
        # Area carries the count, so the radius goes as its root
        radius = POOF_MIN_RADIUS + (POOF_MAX_RADIUS - POOF_MIN_RADIUS) * math.sqrt(len(group) / busiest)
        tip = "<b>%d poof%s here</b><br>%s<br>%s &ndash; %s" % (
            len(group), "" if len(group) == 1 else "s",
            esc(report.city.address(lat, lon)) if report.on_playa else "",
            esc(clock_time(min(poof.timestamp for poof in group))),
            esc(clock_time(max(poof.timestamp for poof in group))))
        parts.append('<g tabindex="0" data-tip="%s"><circle cx="%.1f" cy="%.1f" r="%.1f" fill="var(--series-2)" '
                     'fill-opacity="0.30" stroke="var(--series-2)" stroke-width="1.5"/></g>'
                     % (tip, x, y, radius))
    parts.append("</g>")
    parts.append(frame.scale_bar())
    return svg(MAP_WIDTH, frame.height, "".join(parts), "Map of where the poofer fired through the night")


def poof_map_legend(report):
    located = [poof for poof in report.poofs if poof.lat is not None]
    missing = len(report.poofs) - len(located)
    items = ['<li><span class="swatch dot" style="background: var(--series-2); opacity: 0.5"></span>'
             'poofs within %d ft of each other, sized by how many</li>' % POOF_CELL_FT,
             '<li><span class="swatch" style="background: var(--axis)"></span>the night\'s track</li>']
    if missing:
        items.append('<li>%d poof%s left off, fired where no position was logged</li>'
                     % (missing, "" if missing == 1 else "s"))
    return '<ul class="legend">%s</ul>' % "".join(items)


def speed_legend(report=None):
    """The key to the track's colours

    Given a report it keys only the bands that night actually reached. The car tops out
    around 10 mph, so the fastest band is one no night can ever use, and a key to a speed
    the vehicle cannot do is worse than no key at all.
    """
    used = {speed_band(segment.mph) for segment in report.segments} if report else None
    items = []
    for index, (_, _, label) in enumerate(SPEED_BANDS, start=1):
        if used is not None and index - 1 not in used:
            continue
        items.append('<li><span class="swatch" style="background: var(--speed-%d)"></span>%s mph</li>' % (index, esc(label)))
    items.append('<li><span class="swatch dot" style="background: var(--surface-1); '
                 'box-shadow: inset 0 0 0 2px var(--series-2)"></span>stop</li>')
    items.append('<li><span class="swatch dot" style="background: var(--series-3)"></span>roll out</li>')
    return '<ul class="legend">%s</ul>' % "".join(items)


# ------------------------------------------------------------------- timelines


def speed_chart(report):
    """Speed minute by minute, with the parked stretches shaded"""
    span = (report.end - report.start).total_seconds()
    paced = [mph for _, mph in report.speed_series if mph is not None]
    top = nice_ceiling(max(paced) if paced else 1.0)
    plot = Plot(CHART_WIDTH, CHART_HEIGHT, (0.0, span), (0.0, top))
    parts = []

    for index, stop in enumerate(report.stops, start=1):
        x0 = plot.x(max(0.0, (stop.start - report.start).total_seconds()))
        x1 = plot.x(min(span, (stop.end - report.start).total_seconds()))
        parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="var(--wash)"/>'
                     % (x0, plot.top, max(1.5, x1 - x0), plot.inner_h))

    ticks = [top * step / 4.0 for step in range(5)]
    parts.append(plot.frame(ticks, lambda value: "%g" % round(value, 1), "mph"))

    # The line breaks wherever the logger went quiet rather than bridging the hole
    current, paths = [], []
    for moment, mph in report.speed_series + [(None, None)]:
        if mph is None:
            if len(current) > 1:
                paths.append(current)
            current = []
            continue
        current.append((plot.x((moment - report.start).total_seconds()), plot.y(mph)))
    for path in paths:
        area = "M%.1f,%.1f " % (path[0][0], plot.y(0.0))
        area += " ".join("L%.1f,%.1f" % point for point in path)
        area += " L%.1f,%.1f Z" % (path[-1][0], plot.y(0.0))
        parts.append('<path d="%s" fill="var(--series-1)" fill-opacity="0.10"/>' % area)
        line = "M" + " L".join("%.1f,%.1f" % point for point in path)
        parts.append('<path d="%s" fill="none" stroke="var(--series-1)" stroke-width="2" '
                     'stroke-linejoin="round" stroke-linecap="round"/>' % line)

    fastest = report.fastest
    if fastest:
        x, y = plot.x((fastest[0] - report.start).total_seconds()), plot.y(fastest[1])
        parts.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="var(--series-1)" '
                     'stroke="var(--surface-1)" stroke-width="2"/>' % (x, y))
        anchor = "start" if x < CHART_WIDTH * 0.7 else "end"
        parts.append('<text class="mark-label" x="%.1f" y="%.1f" text-anchor="%s">%.1f mph at %s</text>'
                     % (x + (9 if anchor == "start" else -9), y - 8, anchor, fastest[1], clock_time(fastest[0])))

    parts.append(plot.hour_axis(report.start, report.end))
    parts.append(hover_bands(plot, report, span))
    return svg(CHART_WIDTH, CHART_HEIGHT, "".join(parts), "Speed through the night")


def hover_bands(plot, report, span, minutes=15):
    """Quarter hour hit areas carrying the readout for the speed chart"""
    parts = []
    step = minutes * 60.0
    lookup = {moment: mph for moment, mph in report.speed_series}
    edge = 0.0
    while edge < span:
        window = [mph for moment, mph in lookup.items()
                  if mph is not None and edge <= (moment - report.start).total_seconds() < edge + step]
        begin = report.start + datetime.timedelta(seconds=edge)
        finish = begin + datetime.timedelta(seconds=step)
        if window:
            body = "%.1f mph average, %.1f mph best minute" % (sum(window) / len(window), max(window))
        else:
            body = "nothing logged"
        tip = "<b>%s &ndash; %s</b><br>%s" % (esc(clock_time(begin)), esc(clock_time(finish)), esc(body))
        parts.append('<rect class="hit" tabindex="0" data-tip="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                     % (tip, plot.x(edge), plot.top, plot.x(min(span, edge + step)) - plot.x(edge), plot.inner_h))
        edge += step
    return "".join(parts)


def poof_chart(report):
    """Poofs per quarter hour"""
    span = (report.end - report.start).total_seconds()
    counts = [count for _, count in report.poof_bins]
    top = nice_ceiling(max(counts) if counts else 1.0)
    plot = Plot(CHART_WIDTH, 220.0, (0.0, span), (0.0, top))
    slot = plot.inner_w / max(1, len(report.poof_bins))
    thickness = min(24.0, slot - 2.0)
    parts = [plot.frame([top * step / 4.0 for step in range(5)], lambda value: "%g" % round(value), "poofs")]

    busiest = max(range(len(report.poof_bins)), key=lambda index: report.poof_bins[index][1]) if counts else None
    # Hit areas go on last so a bar never shadows its own readout
    hits = []
    for index, (edge, count) in enumerate(report.poof_bins):
        left = plot.x((edge - report.start).total_seconds()) + (slot - thickness) / 2.0
        finish = edge + datetime.timedelta(minutes=15)
        tip = "<b>%s &ndash; %s</b><br>%d poof%s" % (esc(clock_time(edge)), esc(clock_time(finish)),
                                                     count, "" if count == 1 else "s")
        hits.append('<rect class="hit" tabindex="0" data-tip="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                    % (tip, plot.x((edge - report.start).total_seconds()), plot.top, slot, plot.inner_h))
        if not count:
            continue
        y = plot.y(count)
        parts.append('<path d="M%.1f,%.1f v%.1f a4,4 0 0 1 4,-4 h%.1f a4,4 0 0 1 4,4 v%.1f Z" fill="var(--series-1)"/>'
                     % (left, plot.y(0.0), -(plot.y(0.0) - y - 4.0), thickness - 8.0, plot.y(0.0) - y - 4.0))
        if index == busiest:
            parts.append('<text class="mark-label" x="%.1f" y="%.1f" text-anchor="middle">%d</text>'
                         % (left + thickness / 2.0, y - 7, count))
    parts.append(plot.hour_axis(report.start, report.end))
    parts.extend(hits)
    return svg(CHART_WIDTH, 220.0, "".join(parts), "Poofs per quarter hour through the night")


def line_chart(report, series, unit, label, colour="var(--series-1)", decimals=0, height=200.0,
               right=None):
    """A plain timeline for one sensor, and optionally a second against its own axis

    The book asks for a shorter one than the page does, having less room to give it.
    `right` is (series, unit, colour, name, own name) for a second line read off a
    right hand axis; the two are then named in a key rather than by their closing values.
    """
    span = (report.end - report.start).total_seconds()
    values = [value for _, value in series]
    floor, ceiling, step = nice_bounds(min(values), max(values))
    # Room on the right for the closing value, which rides the end of the line, or for the
    # second axis' labels, and room at the top for the key when there are two lines
    margin = (44.0, 52.0, 34.0, 52.0) if right else (28.0, 74.0, 34.0, 52.0)
    plot = Plot(CHART_WIDTH, height, (0.0, span), (floor, ceiling), margin=margin)
    ticks = [floor + step * index for index in range(int(round((ceiling - floor) / step)) + 1)]
    parts = [plot.frame(ticks, lambda value: "%.*f" % (decimals, value), unit)]

    def x_of(moment):
        return plot.x((moment - report.start).total_seconds())

    if right:
        right_series, right_unit, right_colour, right_name, own_name = right
        right_values = [value for _, value in right_series]
        r_floor, r_ceiling, r_step = nice_bounds(min(0.0, min(right_values)), max(right_values))
        r_plot = Plot(CHART_WIDTH, height, (0.0, span), (r_floor, r_ceiling), margin=margin)
        for index in range(len(ticks)):
            value = r_floor + (r_ceiling - r_floor) * index / (len(ticks) - 1)
            parts.append('<text class="tick" x="%.1f" y="%.1f" text-anchor="start">%g</text>'
                         % (plot.left + plot.inner_w + 8, plot.y(ticks[index]) + 4, round(value, 1)))
        parts.append('<text class="axis-title" x="%.1f" y="%.1f" text-anchor="end">%s</text>'
                     % (CHART_WIDTH - 4, plot.top - 12, esc(right_unit)))
        # A gap in the log is a break in the line, not a straight run across it
        runs, previous = [], None
        for moment, value in right_series:
            point = "%.1f,%.1f" % (x_of(moment), r_plot.y(value))
            if previous is None or (moment - previous).total_seconds() > 300:
                runs.append([point])
            else:
                runs[-1].append(point)
            previous = moment
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.25" stroke-linejoin="round" '
                     'stroke-linecap="round"/>' % (" ".join("M" + " L".join(run) for run in runs), right_colour))
        key_x = plot.left
        for name, swatch in ((own_name, colour), (right_name, right_colour)):
            parts.append('<rect x="%.1f" y="%.1f" width="14" height="3" rx="1.5" fill="%s"/>'
                         % (key_x, 8.0, swatch))
            parts.append('<text class="tick" x="%.1f" y="%.1f">%s</text>' % (key_x + 20, 13.0, esc(name)))
            key_x += 34 + 5.6 * len(name)

    points = [(x_of(moment), plot.y(value)) for moment, value in series]
    parts.append('<path d="M%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round" '
                 'stroke-linecap="round"/>' % (" L".join("%.1f,%.1f" % point for point in points), colour))
    parts.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s" stroke="var(--surface-1)" stroke-width="2"/>'
                 % (points[-1][0], points[-1][1], colour))
    if not right:
        parts.append('<text class="mark-label" x="%.1f" y="%.1f">%.*f %s</text>'
                     % (points[-1][0] + 10, points[-1][1] + 4, decimals, series[-1][1], esc(unit)))
    parts.append(plot.hour_axis(report.start, report.end))
    return svg(CHART_WIDTH, height, "".join(parts), esc(label))


# ------------------------------------------------------------------ page pieces


def tile(label, value, foot=""):
    return ('<div class="tile"><div class="label">%s</div><div class="value">%s</div>'
            '<div class="foot">%s</div></div>' % (esc(label), value, esc(foot)))


def narrative(report):
    """The night in a few sentences"""
    lines = []
    first, last = report.first_fix, report.last_fix
    where = report.city.address(first.lat, first.lon) if report.on_playa else "the yard"
    lines.append("First fix at <strong>%s</strong> from %s, last at <strong>%s</strong>."
                 % (esc(clock_time(first.timestamp)), esc(where), esc(clock_time(last.timestamp))))
    lines.append("The car covered <strong>%.1f miles</strong>, rolling for %s and parked for %s across %d stop%s."
                 % (report.miles, esc(duration(report.rolling_seconds)), esc(duration(report.parked_seconds)),
                    len(report.stops), "" if len(report.stops) == 1 else "s"))
    longest = report.longest_stop
    if longest:
        lines.append("The longest stop was <strong>%s</strong> at %s%s, starting %s."
                     % (esc(duration(longest.seconds)), esc(longest.address),
                        " (by %s)" % esc(longest.landmark[0]) if longest.landmark else "",
                        esc(clock_time(longest.start))))
    if report.poofs:
        busiest = report.busiest_poof_hour
        parked = sum(1 for poof in report.poofs if poof.parked)
        lines.append("The poofer fired <strong>%s times</strong>, busiest in the %s hour with %d; %d of them "
                     "while parked." % (commas(len(report.poofs)), esc(clock_time(busiest[0])), busiest[1], parked))
    farthest = report.farthest
    if farthest:
        lines.append("Furthest point from the Man was <strong>%s ft</strong> out, at %s."
                     % (esc(commas(farthest[1])), esc(report.city.address(farthest[0].lat, farthest[0].lon))))
    return " ".join(lines)


def tiles(report):
    parts = []
    parts.append(tile("Rolling", esc(duration(report.rolling_seconds)),
                      "%.1f mph average while moving" % (report.miles / (report.rolling_seconds / 3600.0)
                                                         if report.rolling_seconds else 0.0)))
    parts.append(tile("Parked", esc(duration(report.parked_seconds)),
                      "%d stop%s over 5 minutes" % (len(report.stops), "" if len(report.stops) == 1 else "s")))
    fastest = report.fastest
    parts.append(tile("Fastest minute", "%.1f<span style=\"font-size:15px;color:var(--text-secondary)\"> mph</span>"
                      % (fastest[1] if fastest else 0.0), "at %s" % clock_time(fastest[0]) if fastest else ""))
    parts.append(tile("Poofs", esc(commas(len(report.poofs))),
                      "%.0f per hour of the night" % (len(report.poofs) / max(1.0, (report.end - report.start).total_seconds() / 3600.0))))
    farthest = report.farthest
    if farthest:
        parts.append(tile("Furthest from the Man", "%s<span style=\"font-size:15px;color:var(--text-secondary)\"> ft</span>"
                          % esc(commas(farthest[1])), report.city.clock(farthest[0].lat, farthest[0].lon)))
    parts.append(tile("Positions logged", esc(commas(report.counts.get("positions", 0))),
                      "%d dropped as GPS noise" % report.glitches))
    return '<div class="tiles">%s</div>' % "".join(parts)


def stops_table(report):
    if not report.stops:
        return '<p class="empty">No stop longer than five minutes -- the car kept rolling all night.</p>'
    rows = []
    for index, stop in enumerate(report.stops, start=1):
        rows.append("<tr><td class=\"num\">%d</td><td>%s</td><td class=\"num\">%s</td><td>%s</td>"
                    "<td>%s</td><td class=\"num\">%s</td></tr>"
                    % (index, esc(clock_time(stop.start)), esc(duration(stop.seconds)), esc(stop.address),
                       esc("%s, %d ft" % stop.landmark) if stop.landmark else "&mdash;",
                       esc(commas(stop.poofs)) if stop.poofs else "&mdash;"))
    return ('<div class="scroll"><table><thead><tr><th class="num">#</th><th>Arrived</th>'
            '<th class="num">Stayed</th><th>Address</th><th>Nearest landmark</th><th class="num">Poofs</th>'
            '</tr></thead><tbody>%s</tbody></table></div>' % "".join(rows))


def speed_table(report):
    rows = []
    for moment, mph in report.speed_series:
        if moment.minute % 15:
            continue
        rows.append("<tr><td>%s</td><td class=\"num\">%s</td></tr>"
                    % (esc(clock_time(moment)), "%.1f" % mph if mph is not None else "&mdash;"))
    return ('<details><summary>Table view &mdash; speed every 15 minutes</summary><div class="scroll">'
            '<table><thead><tr><th>Time</th><th class="num">mph</th></tr></thead><tbody>%s</tbody></table>'
            '</div></details>' % "".join(rows))


def poof_table(report):
    rows = []
    for edge, count in report.poof_bins:
        rows.append("<tr><td>%s</td><td class=\"num\">%d</td></tr>" % (esc(clock_time(edge)), count))
    return ('<details><summary>Table view &mdash; poofs per quarter hour</summary><div class="scroll">'
            '<table><thead><tr><th>Quarter hour</th><th class="num">Poofs</th></tr></thead><tbody>%s</tbody>'
            '</table></div></details>' % "".join(rows))


def poof_detail(report):
    if report.chattering:
        return ('<p class="empty">No poof count for this night. The pressure sensor spent it flipping between '
                'two readings about five psi apart, ten times a second, which is electrics rather than gas '
                '&mdash; the accumulator cannot move that fast. Read literally it would report tens of '
                'thousands of poofs, so the trace is set aside instead.</p>')
    if not report.poofs:
        return ('<p class="empty">No poofs detected. Either the poofer stayed quiet or the pressure sensor '
                'logged nothing this night.</p>')
    drops = sorted(poof.drop for poof in report.poofs)
    falls = sorted(poof.seconds for poof in report.poofs)
    middle = len(drops) // 2
    biggest = max(report.poofs, key=lambda poof: poof.drop)
    parked = sum(1 for poof in report.poofs if poof.parked)
    return ('<div class="tiles">%s%s%s%s</div>'
            % (tile("Median drop", "%.0f<span style=\"font-size:15px;color:var(--text-secondary)\"> psi</span>"
                    % drops[middle], "biggest %.0f psi at %s" % (biggest.drop, clock_time(biggest.timestamp))),
               tile("Median burst", "%.1f<span style=\"font-size:15px;color:var(--text-secondary)\"> s</span>"
                    % falls[len(falls) // 2], "time from full to empty"),
               tile("While parked", esc(commas(parked)), "%.0f%% of the night's poofs"
                    % (100.0 * parked / len(report.poofs))),
               tile("While rolling", esc(commas(len(report.poofs) - parked)), "%.0f%% of the night's poofs"
                    % (100.0 * (len(report.poofs) - parked) / len(report.poofs)))))


def propane_section(report):
    """What the pressure trace says about how much gas went out of the accumulator"""
    if not report.poofs:
        return ""
    parts = []
    pounds = report.pounds_drawn
    recoveries = sorted(poof.recovery for poof in report.poofs if poof.recovery is not None)
    trend = report.supply_trend

    half = report.half_gone
    tiles = [tile("Half gone by", esc(clock_time(half)) if half else "&mdash;",
                  "of the night's load")]
    if pounds is not None:
        tiles.append(tile("That is about", "%.0f<span style=\"font-size:15px;color:var(--text-secondary)\"> lb"
                          "</span>" % pounds, "on a %g gallon accumulator" % report.accumulator_gallons))
    if recoveries:
        tiles.append(tile("Recharge", "%.0f<span style=\"font-size:15px;color:var(--text-secondary)\"> s</span>"
                          % statistics.median(recoveries), "median time back to pressure"))
    parts.append('<div class="tiles">%s</div>' % "".join(tiles))

    if trend:
        opened, closed = trend
        change = closed - opened
        if change < -6:
            verdict = ("The supply sagged <strong>%.0f psi</strong> over the night, from %.0f down to %.0f. "
                       "That is the tank emptying, going cold under heavy draw, or both." % (-change, opened, closed))
        elif change > 6:
            verdict = ("The supply climbed <strong>%.0f psi</strong>, from %.0f up to %.0f -- a tank warming "
                       "through the night rather than running down." % (change, opened, closed))
        else:
            verdict = ("The supply held steady around <strong>%.0f psi</strong> all night, so the tank kept up "
                       "with everything the poofer asked of it." % ((opened + closed) / 2))
        if recoveries:
            early = [poof.recovery for poof in report.poofs[:len(report.poofs) // 2] if poof.recovery]
            late = [poof.recovery for poof in report.poofs[len(report.poofs) // 2:] if poof.recovery]
            if early and late:
                verdict += (" Recharging took %.0fs early on and %.0fs by the end."
                            % (statistics.median(early), statistics.median(late)))
        parts.append('<p class="note after">%s</p>' % verdict)

    parts.append("<h3>Propane through the night</h3>")
    parts.append('<p class="note">Full at roll-out, empty at the last poof. Each poof empties part of a '
                 'fixed-volume accumulator, so the pressure it draws is proportional to the gas released; '
                 'running those backwards from the night\'s total gives a gauge. The steeper it falls, the '
                 'harder the poofer was working. It paces the load rather than measuring the tanks -- nothing '
                 'on the car does that -- so a night that came home with gas to spare still ends at empty.%s</p>'
                 % ("" if pounds is not None else
                    " Pass <code>--accumulator-gallons</code> to read it in pounds instead."))
    parts.append(line_chart(report, report.remaining_series, "", "Propane remaining", "var(--series-2)"))

    parts.append("<h3>Supply pressure through the night</h3>")
    parts.append('<p class="note">What the accumulator had recovered to each time the poofer fired, as a rolling '
                 'median over %d poofs. Firing again before it has caught up reads as a deep spike, so the raw '
                 'trace is all noise -- the median is the trend underneath it.</p>' % report.supply_window)
    parts.append(line_chart(report, report.supply_series, "psi", "Supply pressure through the night",
                            "var(--series-1)"))
    return "".join(parts)


def health_section(report):
    parts = []
    if report.temperature:
        values = [value for _, value in report.temperature]
        parts.append("<h3>Tub water</h3>")
        parts.append('<p class="note">Ranged %.0f&deg;F to %.0f&deg;F, ending the night at %.0f&deg;F.</p>'
                     % (min(values), max(values), values[-1]))
        parts.append(line_chart(report, report.temperature, "°F", "Tub water temperature", "var(--series-2)"))
    else:
        parts.append('<p class="empty">Tub water: nothing logged this night '
                     '(the <code>temp</code> and <code>water</code> streams are empty).</p>')
    rows = []
    for name, count in sorted(report.counts.items()):
        state = ("good", "logging") if count else ("critical", "silent")
        rows.append('<tr><td>%s</td><td class="num">%s</td><td><span class="flag">'
                    '<span class="dot" style="background: var(--%s)"></span>%s</span></td></tr>'
                    % (esc(name), esc(commas(count)), state[0], esc(state[1])))
    parts.append("<h3>Streams</h3>")
    parts.append('<div class="scroll"><table><thead><tr><th>Stream</th><th class="num">Rows</th>'
                 '<th>State</th></tr></thead><tbody>%s</tbody></table></div>' % "".join(rows))

    if report.gaps:
        rows = []
        for start, end, seconds in report.gaps:
            rows.append("<tr><td>%s</td><td>%s</td><td class=\"num\">%s</td></tr>"
                        % (esc(clock_time(start)), esc(clock_time(end)), esc(duration(seconds))))
        parts.append("<h3>Position gaps</h3>")
        parts.append('<p class="note">Stretches where the car moved but nothing was logged, so the route '
                     'between them is drawn as a straight line.</p>')
        parts.append('<div class="scroll"><table><thead><tr><th>From</th><th>To</th><th class="num">Length</th>'
                     '</tr></thead><tbody>%s</tbody></table></div>' % "".join(rows))
    else:
        parts.append('<p class="note after">No gaps in the position log &mdash; the track is continuous from '
                     'roll out to the last fix.</p>')
    return "".join(parts)


def summarize(report, name):
    """The handful of numbers the index needs from a night"""
    return {"night": report.night, "file": name, "on_playa": report.on_playa, "miles": report.miles,
            "rolling": report.rolling_seconds, "stops": len(report.stops), "poofs": len(report.poofs),
            "chattering": report.chattering,
            "first": report.first_fix.timestamp, "last": report.last_fix.timestamp}


def index_rows(nights, widest, fragment=False):
    rows = []
    for night in nights:
        published = "//" in night["file"]
        label = esc(night["night"].strftime("%a %b %-d"))
        if published:
            # A published report lives on another origin, so it opens in its own tab
            link = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(night["file"]), label)
        elif fragment:
            # A published index cannot reach the copies sitting beside the script, so those
            # nights keep their row and their numbers but are not offered as a link
            link = label
        else:
            link = '<a href="%s">%s</a>' % (esc(night["file"]), label)
        rows.append(
            '<tr class="night"><td>%s</td><td>%s &rarr; %s</td>'
            '<td class="num">%.1f</td><td style="width: 22%%" aria-hidden="true"><span class="meter">'
            '<span style="width: %.0f%%"></span></span></td>'
            '<td class="num">%s</td><td class="num">%d</td><td class="num">%s</td></tr>'
            % (link,
               esc(clock_time(night["first"])), esc(clock_time(night["last"])), night["miles"],
               100.0 * night["miles"] / widest if widest else 0.0,
               esc(duration(night["rolling"])), night["stops"],
               # A sensor that chattered all night is unknown, not zero
               "&mdash;" if night.get("chattering") else esc(commas(night["poofs"]))))
    return "".join(rows)


def render_index(summaries, fragment=False):
    """A contact sheet over every night that has a report"""
    widest = max(night["miles"] for night in summaries)
    miles = sum(night["miles"] for night in summaries)
    poofs = sum(night["poofs"] for night in summaries)
    rolling = sum(night["rolling"] for night in summaries)
    playa = [night for night in summaries if night["on_playa"]]
    newest, oldest = summaries[0]["night"], summaries[-1]["night"]

    body = ['<div class="viz-root"><div class="wrap">']
    # With the shakedowns dropped the log is the playa and nothing else, and says so
    headline = "Every night on the playa" if len(playa) == len(summaries) else "Every night the car went out"
    body.append('<header class="masthead"><p class="brandmark"><span class="canister" aria-hidden="true"></span>Red Hot Beverly<span class="tagline">the fire extinguisher</span></p><p class="eyebrow">Excursion log</p><h1>%s'
                '</h1><p class="subhead">%s nights between %s and %s, from the sensor monitor logs</p>'
                '</header>' % (esc(headline), len(summaries),
                               esc(oldest.strftime("%B %-d, %Y")), esc(newest.strftime("%B %-d, %Y"))))
    if len(playa) == len(summaries):
        mix = "Every one of these nights was out on the playa."
    else:
        mix = ("%d of these nights were on the playa, the rest shakedowns and test drives closer to home."
               % len(playa))
    body.append('<div class="hero"><div class="hero-figure"><div class="value">%s<span class="unit">miles</span>'
                '</div><div class="label">across every logged night</div></div>'
                '<p class="summary">%s The longest was <strong>%s</strong> at %.1f miles; the busiest poofer '
                'night was <strong>%s</strong> with %s.</p></div>'
                % (commas(miles), mix,
                   esc(max(summaries, key=lambda night: night["miles"])["night"].strftime("%a %b %-d, %Y")), widest,
                   esc(max(summaries, key=lambda night: night["poofs"])["night"].strftime("%a %b %-d, %Y")),
                   commas(max(night["poofs"] for night in summaries))))
    # "20 on the playa" under a count of 20 says nothing, so fall back to the span of seasons
    if len(playa) == len(summaries):
        counted = "across %d seasons" % len({night["night"].year for night in summaries})
    else:
        counted = "%d on the playa" % len(playa)
    body.append('<div class="tiles">%s%s%s%s</div>'
                % (tile("Nights logged", esc(commas(len(summaries))), counted),
                   tile("Time rolling", esc(duration(rolling)), "wheels actually turning"),
                   tile("Poofs", esc(commas(poofs)), "across every night"),
                   tile("Stops", esc(commas(sum(night["stops"] for night in summaries))), "of five minutes or more")))

    seasons = {}
    for night in summaries:
        seasons.setdefault(night["night"].year, []).append(night)
    for year in sorted(seasons, reverse=True):
        nights = seasons[year]
        body.append('<section><h2>%d</h2><p class="note">%d nights, %.1f miles, %s poofs.</p>'
                    % (year, len(nights), sum(item["miles"] for item in nights),
                       commas(sum(item["poofs"] for item in nights))))
        body.append('<div class="scroll"><table><thead><tr><th>Night</th><th>Out and back</th>'
                    '<th class="num">Miles</th><th aria-hidden="true"></th><th class="num">Rolling</th>'
                    '<th class="num">Stops</th>'
                    '<th class="num">Poofs</th></tr></thead><tbody>%s</tbody></table></div></section>'
                    % index_rows(nights, widest, fragment))

    published = any("//" in night["file"] for night in summaries)
    body.append('<footer class="colophon">Generated by <code>reporting/excursion_report.py --all</code> from the '
                'rhb-sensor-monitor logs. Each night links to its own report%s.</footer>'
                % (", which opens in a new tab" if published else ""))
    body.append("</div></div>")
    inner = "".join(body)
    if fragment:
        return "<style>%s</style>%s" % (STYLE, inner)
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Red Hot Beverly &mdash; excursion log</title><style>%s</style></head><body>%s</body></html>\n'
            % (STYLE, inner))


def render(report, fragment=False):
    """The whole report as one page"""
    night_end = report.night + datetime.timedelta(days=1)
    title = "Red Hot Beverly &mdash; night of %s" % report.night.strftime("%a %b %-d, %Y")
    body = ['<div class="viz-root"><div class="wrap">']
    body.append('<header class="masthead"><p class="brandmark"><span class="canister" aria-hidden="true"></span>Red Hot Beverly<span class="tagline">the fire extinguisher</span></p><p class="eyebrow">After excursion report</p>'
                '<h1>%s &rarr; %s</h1><p class="subhead">%s to %s, from the sensor monitor logs</p></header>'
                % (esc(report.night.strftime("%A, %B %-d")), esc(night_end.strftime("%A, %B %-d, %Y")),
                   esc(clock_time(report.start)), esc(clock_time(report.end))))

    body.append('<div class="hero"><div class="hero-figure"><div class="value">%.1f<span class="unit">miles</span>'
                '</div><div class="label">driven over the night</div></div>'
                '<p class="summary">%s</p></div>' % (report.miles, narrative(report)))
    if report.clock_shift:
        logged = report.night - report.clock_shift
        body.append('<p class="note after">The Pi carried no realtime clock this season, so it logged the night as '
                    '<strong>%s</strong> &mdash; %d days behind. The dates here are corrected against the burn: '
                    'the car crossed inside the perimeter and parked 897 ft from the Man on the night the log '
                    'called August 21, which can only be after he came down, so that night is Saturday '
                    'September 3.</p>'
                    % (esc(logged.strftime("%A, %B %-d")), report.clock_shift.days))
    body.append(tiles(report))

    body.append('<section><h2>Where it went</h2><p class="note">The night\'s track over this year\'s streets, '
                'coloured by how fast the car was moving. Red rings mark stops of five minutes or more.</p>')
    body.append(map_chart(report))
    body.append(speed_legend(report))
    body.append(stops_table(report))
    body.append('</section>')

    body.append('<section><h2>How it moved</h2><p class="note">Speed minute by minute. Shaded bands are the '
                'stops.</p>')
    body.append(speed_chart(report))
    body.append(speed_table(report))
    body.append('</section>')

    body.append('<section><h2>Poofs</h2><p class="note">Counted off the accumulator pressure trace, which the '
                'monitor samples at 10Hz around every burst: a poof is a sharp drop of at least %g psi followed '
                'by a recharge.%s</p>'
                % (report.poof_threshold,
                   # Early seasons went into the log as raw ADC counts and are converted here
                   ' This season the monitor logged the sensor raw and only converted it for the '
                   'display, so the trace has been put back into psi with the monitor\'s own calibration.'
                   if report.calibrated else ''))
    body.append(poof_detail(report))
    if report.poofs:
        body.append(poof_chart(report))
        body.append(poof_table(report))
    body.append('</section>')

    density = poof_map(report)
    if density:
        body.append('<section><h2>Where it poofed</h2><p class="note">Every poof placed on the track by its '
                    'timestamp, then grouped by neighbourhood. Bigger circles are where the poofer fired '
                    'hardest.</p>')
        body.append(density)
        body.append(poof_map_legend(report))
        body.append('</section>')

    propane = propane_section(report)
    if propane:
        body.append('<section><h2>Propane</h2><p class="note">How much gas went out through the poofer, and '
                    'whether the supply kept up.</p>')
        body.append(propane)
        body.append('</section>')

    body.append('<section><h2>Systems</h2><p class="note">What the rest of the car had to say for itself.</p>')
    body.append(health_section(report))
    body.append('</section>')

    body.append('<footer class="colophon">Generated by <code>reporting/excursion_report.py</code> from the '
                'rhb-sensor-monitor logs. Playa addresses are read off this year\'s map layers, with 12:00 at '
                '%.1f&deg; true.</footer>' % report.city.bearing_12)
    body.append('</div></div><div id="tip" hidden></div>')
    body.append('<script>%s</script>' % SCRIPT)
    inner = "".join(body)

    if fragment:
        return "<style>%s</style>%s" % (STYLE, inner)
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s</title><style>%s</style></head><body>%s</body></html>\n' % (title, STYLE, inner))
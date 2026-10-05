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

"""The excursion log as a printed book: one spread a night, gathered by season

Every page is laid out at its finished size rather than left to reflow, so the page a
thing lands on is known here and can be numbered and put in the contents. Nothing is
lazy, nothing hovers, and the palette is the light one whatever the screen is set to --
this is ink.
"""

import datetime
import statistics

import report_render as web
from report_render import clock_time, commas, duration, esc

TITLE = "Red Hot Beverly"
EDITION = "Version 2.0"

# US Letter, portrait. The inner margin carries the gutter, so a page knows its own hand
PAGE_W_IN = 8.5
PAGE_H_IN = 11.0
MARGIN_TOP_IN = 0.7
MARGIN_BOTTOM_IN = 0.8
MARGIN_OUTER_IN = 0.65
MARGIN_INNER_IN = 0.9

# Each map has a page of its own, so it can be nearly square again
MAP_ASPECT = 1.05
# The stop list has a page to itself now, so it is no longer trimmed in practice
STOPS_ON_PAGE = 20
# Taller again now the pressure shares the curve's chart and the supply card is gone
PROPANE_CHART_HEIGHT = 260.0

# Water in a tub in the desert in August does not get near freezing. 2023 never reads below
# 57F and 2025 never below 54, but 2022 runs continuously down to exactly 32.0 -- zero
# Celsius, clamped -- with half its readings under 50 and the same nights also claiming 109.
# That is the probe failing toward zero, not the water, so the low ones are dropped and a
# night that loses too many of them is reported as unusable rather than drawn full of holes
TUB_MIN_F = 50.0
TUB_MIN_USABLE = 0.5
# Shorter than propane's, sharing the page with it and the stop list
TUB_CHART_HEIGHT = 170.0

# The book is the logs and nothing else. The two written pieces -- the night at the art
# piece, and the night the licence went -- are built and ready but not assembled in; set
# this True to put them back. Everything else in the book is derived from the sensors.
INCLUDE_NARRATIVE = False

# The art piece the crew built and the car spent a night holding a party at. Where it stood
# is not in any map layer, so it is taken from the ground: the car parked at it for nine and
# a half hours, and that stop is the piece.
ART_NIGHT = datetime.date(2024, 8, 26)
ART_NAME = "Love Shines Down"
ART_CREW = "TODO: the crew that built it"
ART_ARTISTS = "TODO: the artists, comma separated"

# The night the licence was pulled, and the two it cost
GROUNDING_NIGHT = datetime.date(2024, 8, 28)
# Inside this of the Man is the circle that was crossed
MAN_CIRCLE_FT = 800.0
# The speed the crew were accused of holding through the circle, and the reason the licence
# went. The car's own log of the crossing is the answer to it
ALLEGED_MPH = 15.0
# The story sits above the close up, so the map takes what is left of the page
CIRCLE_MAP_ASPECT = 0.58


STYLE = """
@page { size: %(pw).2fin %(ph).2fin; margin: 0; }
:root {
  --page: #ffffff;
  --surface-1: #ffffff;
  --paper: #faf9f6;
  --text-primary: #14130f;
  --text-secondary: #4a4843;
  --text-muted: #86837b;
  --grid: #d9d7cd;
  --axis: #b4b1a5;
  --border: rgba(20,19,15,0.16);
  --wash: rgba(20,19,15,0.05);
  --rule: rgba(20,19,15,0.65);
  --series-1: #2a78d6;
  --series-2: #a8483a;
  --series-3: #1a9b83;
  --brand: #a8483a;
  --brand-ink: #8f3b2f;
  --good: #0ca30c;
  --warning: #fab219;
  --critical: #d03b3b;
  /* On paper the palest step vanishes, so the ramp starts further up than on screen */
  --speed-1: #9dc2f0;
  --speed-2: #5f9ce8;
  --speed-3: #2a78d6;
  --speed-4: #1a55a0;
  --speed-5: #0b2f5e;
}
* { box-sizing: border-box; }
/* Chrome drops background colour when it prints unless told not to, which would take the
   cream off the cover and the dividers and the red out of the brand bar */
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; background: #6b6b6b; }
@media print {
  /* The grey is the desk the pages are laid out on; on paper there is no desk */
  html, body { background: #ffffff; }
  .page { margin: 0; box-shadow: none; }
}
body {
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  color: var(--text-primary);
  font-size: 10.5pt;
  line-height: 1.5;
}
.page {
  position: relative;
  width: %(pw).2fin; height: %(ph).2fin;
  background: var(--page);
  overflow: hidden;
  page-break-after: always;
  break-after: page;
  margin: 0 auto 18px;
  box-shadow: 0 2px 14px rgba(0,0,0,0.35);
}
.page:last-child { page-break-after: auto; break-after: auto; }
/* Recto carries its gutter on the left, verso on the right */
.page .body {
  position: absolute;
  top: %(mt).2fin; bottom: %(mb).2fin;
  left: %(mi).2fin; right: %(mo).2fin;
}
.page.verso .body { left: %(mo).2fin; right: %(mi).2fin; }
.folio {
  position: absolute; bottom: 0.45in;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 8pt; letter-spacing: 0.08em; color: var(--text-muted);
}
.page .folio { right: %(mo).2fin; }
.page.verso .folio { left: %(mo).2fin; right: auto; }
.runner {
  position: absolute; bottom: 0.45in;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 8pt; letter-spacing: 0.10em; text-transform: uppercase; color: var(--text-muted);
}
.page .runner { left: %(mi).2fin; }
.page.verso .runner { right: %(mi).2fin; left: auto; text-align: right; }

/* ------------------------------------------------------------------ furniture */
.brandmark {
  display: flex; align-items: center; gap: 8px; margin: 0 0 10px;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 8.5pt; font-weight: 640; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--brand-ink);
}
.brandmark .canister {
  width: 6px; height: 15px; border-radius: 2px 2px 3px 3px;
  background: var(--brand); flex: none;
}
.eyebrow {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 8pt; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--text-muted); margin: 0 0 4px;
}
h1 { font-size: 25pt; line-height: 1.12; margin: 0 0 4px; font-weight: 600; letter-spacing: -0.01em; }
h2 { font-size: 15pt; margin: 0 0 3px; font-weight: 600; }
h3 {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 8pt; letter-spacing: 0.13em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 640; margin: 0 0 5px;
}
.lede { color: var(--text-secondary); margin: 0; }
.note { color: var(--text-secondary); margin: 0 0 10px; font-size: 9.5pt; }
.rule { border: 0; border-top: 1px solid var(--rule); margin: 9px 0 12px; }
.thin { border: 0; border-top: 1px solid var(--border); margin: 10px 0; }
/* Where a sensor has nothing to say, the saying so is set apart from the reading of it */
.empty {
  color: var(--text-secondary); background: var(--wash); border-radius: 8px;
  padding: 9px 11px; margin: 0; font-size: 9.5pt;
}

/* ------------------------------------------------------------------ the cover */
.cover { background: var(--paper); }
.cover .body { display: flex; flex-direction: column; }
.cover .stack { margin-top: 1.6in; }
.cover h1 { font-size: 46pt; line-height: 1.02; letter-spacing: -0.02em; margin: 0; }
.cover .sub {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 11pt; letter-spacing: 0.20em; text-transform: uppercase;
  color: var(--brand-ink); margin: 14px 0 0; font-weight: 640;
}
.cover .years {
  margin-top: auto; font-family: system-ui, -apple-system, sans-serif;
  font-size: 10pt; letter-spacing: 0.16em; color: var(--text-secondary);
}
.cover .bar { width: 1.5in; height: 5px; background: var(--brand); margin: 26px 0 0; border-radius: 2px; }

/* ------------------------------------------------------------------ the tiles */
.figures { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; }
.figures.two { grid-template-columns: repeat(2, 1fr); }
.figures.four { grid-template-columns: repeat(4, 1fr); }
.fig { border-top: 1.5px solid var(--rule); padding-top: 5px; }
.fig .label {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 7.5pt; letter-spacing: 0.09em; text-transform: uppercase; color: var(--text-muted);
}
.fig .value { font-size: 17pt; font-weight: 620; line-height: 1.15; margin-top: 1px; }
.fig .value .unit { font-size: 9pt; color: var(--text-secondary); font-weight: 500; margin-left: 2px; }
.fig .foot { font-size: 8pt; color: var(--text-muted); line-height: 1.3; }

/* ------------------------------------------------------------------- the night */
.mapwrap { margin-top: 10px; }
.chart { width: 100%%; height: auto; display: block; overflow: visible; }
.chart text { font-family: system-ui, -apple-system, sans-serif; }
.tick { font-size: 11px; fill: var(--text-muted); }
.axis-title { font-size: 11px; fill: var(--text-muted); }
.mark-label { font-size: 12px; fill: var(--text-secondary); font-weight: 600; }
.map-label { paint-order: stroke; stroke: var(--surface-1); stroke-width: 3px; stroke-linejoin: round; }
.gridline { stroke: var(--grid); stroke-width: 1; }
.baseline { stroke: var(--axis); stroke-width: 1; }
/* Hover targets are meaningless on paper */
.hit, #tip { display: none; }
.legend {
  display: flex; flex-wrap: wrap; gap: 3px 14px; margin: 7px 0 0; padding: 0;
  font-family: system-ui, -apple-system, sans-serif;
  color: var(--text-secondary); font-size: 8pt; list-style: none;
}
.legend li { display: flex; align-items: center; gap: 5px; }
.swatch { width: 13px; height: 7px; border-radius: 2px; display: inline-block; }
.swatch.dot { width: 9px; height: 9px; border-radius: 50%%; }
table { border-collapse: collapse; width: 100%%; font-size: 8.5pt; }
th, td { text-align: left; padding: 3.5px 7px 3.5px 0; border-bottom: 1px solid var(--border); }
th {
  font-family: system-ui, -apple-system, sans-serif;
  color: var(--text-muted); font-weight: 640; font-size: 7pt;
  letter-spacing: 0.09em; text-transform: uppercase;
}
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.tallies { font-size: 8pt; color: var(--text-muted); margin: 5px 0 0; }
/* How far off the named thing was, set quieter than the name itself */
.away { color: var(--text-muted); font-size: 7.5pt; }

/* ------------------------------------------------------------------ dividers */
.divider { background: var(--paper); }
.divider .body { display: flex; flex-direction: column; }
.divider .year {
  /* These pages measure two pixels long, which is the flex auto-margin rounding and not
     content: every child still ends on the body's own bottom edge, well above the folio */
  font-size: 92pt; font-weight: 620; line-height: 0.9; letter-spacing: -0.03em;
  color: var(--brand); margin: 1.1in 0 0;
}
.divider .season { margin-top: 16px; max-width: 4.6in; color: var(--text-secondary); }
.divider .figures { margin-top: auto; }

/* ------------------------------------------------------------------ contents */
.toc { width: 100%%; font-size: 9pt; }
/* The leaders take the slack, so a night's name never breaks across two lines */
/* Tight enough that five seasons of nights fit on the one page */
.toc td { border: 0; padding: 0.5px 0; white-space: nowrap; }
.toc td:first-child { padding-right: 8px; }
.toc td.dots { padding: 0.5px 8px; }
.toc .yr {
  font-family: system-ui, -apple-system, sans-serif; font-weight: 700;
  font-size: 8.5pt; letter-spacing: 0.12em; padding-top: 9px; color: var(--brand-ink);
}
.toc .dots { border-bottom: 1px dotted var(--border); width: 100%%; }
.toc .pg { text-align: right; font-variant-numeric: tabular-nums; color: var(--text-secondary); }
.toc td.feat { padding-left: 16px; color: var(--brand-ink); font-style: italic; }
.feature {
  border-left: 3px solid var(--brand); background: var(--wash);
  padding: 10px 12px; margin-top: 12px; border-radius: 0 6px 6px 0;
}
.feature h3 { color: var(--brand-ink); margin-bottom: 3px; }
.feature p { margin: 0; font-size: 9.5pt; color: var(--text-secondary); }
.feature .credit {
  font-family: system-ui, -apple-system, sans-serif; font-size: 8pt;
  color: var(--text-muted); margin-bottom: 6px; line-height: 1.4;
}
.feature strong { color: var(--text-primary); font-weight: 620; }
.colophon .body { font-size: 9.5pt; }
.colophon p { color: var(--text-secondary); margin: 0 0 9px; }
.colophon strong { color: var(--text-primary); font-weight: 620; }
""" % {"pw": PAGE_W_IN, "ph": PAGE_H_IN, "mt": MARGIN_TOP_IN, "mb": MARGIN_BOTTOM_IN,
       "mo": MARGIN_OUTER_IN, "mi": MARGIN_INNER_IN}


class Book:
    """Pages in order, each one numbered as it is added"""

    def __init__(self):
        self.pages = []

    @staticmethod
    def _page(number, body, kind="", runner="", folio=True):
        # Page one is a recto, and the hand alternates from there
        verso = number % 2 == 0
        classes = " ".join(part for part in ("page", "verso" if verso else "", kind) if part)
        furniture = ""
        if folio:
            furniture += '<div class="folio">%d</div>' % number
            if runner:
                furniture += '<div class="runner">%s</div>' % esc(runner)
        return '<div class="%s"><div class="body">%s</div>%s</div>' % (classes, body, furniture)

    def add(self, body, kind="", runner="", folio=True):
        number = len(self.pages) + 1
        self.pages.append(self._page(number, body, kind, runner, folio))
        return number

    def reserve(self):
        """Hold a page back for something that cannot be written until the rest is placed"""
        return self.add("")

    def fill(self, number, body, kind="", runner="", folio=True):
        """Write a reserved page, keeping the number and the hand it was given"""
        self.pages[number - 1] = self._page(number, body, kind, runner, folio)

    def blank(self):
        self.pages.append('<div class="page%s"></div>'
                          % (" verso" if (len(self.pages) + 1) % 2 == 0 else ""))

    def align_recto(self):
        """Start the next page on a right hand page, the way a section should open"""
        if len(self.pages) % 2:
            self.blank()

    def align_verso(self):
        """Start the next page on a left hand page

        A spread is only a spread if its two halves face each other, which means the first
        of them has to be a verso. Landing it on a recto instead would put the map and its
        numbers on opposite sides of the same leaf, where they can never be seen together.
        """
        if len(self.pages) % 2 == 0:
            self.blank()

    def html(self, title):
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                '<title>%s</title><style>%s</style></head><body>%s</body></html>\n'
                % (esc(title), STYLE, "".join(self.pages)))


def figure(label, value, unit="", foot=""):
    unit_html = '<span class="unit">%s</span>' % esc(unit) if unit else ""
    return ('<div class="fig"><div class="label">%s</div><div class="value">%s%s</div>'
            '<div class="foot">%s</div></div>' % (esc(label), value, unit_html, esc(foot)))


def top_speed(report):
    return max((segment.mph for segment in report.segments), default=0.0)


# ------------------------------------------------------------------- front matter


def cover(book, seasons):
    body = ('<div class="stack">'
            '<p class="brandmark"><span class="canister"></span>The fire extinguisher</p>'
            '<h1>Red Hot<br>Beverly</h1>'
            '<div class="bar"></div>'
            '<p class="sub">%s</p></div>'
            '<div class="years">Every night on the playa &middot; %d &ndash; %d</div>'
            % (esc(EDITION), min(seasons), max(seasons)))
    book.add(body, kind="cover", folio=False)
    book.blank()


def title_page(book, nights, miles, poofs):
    seasons = sorted({night.night.year for night in nights})
    body = ('<p class="eyebrow">After excursion log</p>'
            '<h1>Red Hot Beverly</h1>'
            '<p class="lede">%s &mdash; every night the art car went out on the playa, '
            'as her own sensors recorded it.</p>'
            '<hr class="rule">'
            '<div class="figures four">%s%s%s%s</div>'
            '<hr class="thin">'
            '<p class="note">Reconstructed from the position, pressure and temperature logs '
            'the on-board monitor wrote to a Raspberry Pi, one line at a time, across '
            '%d seasons. Every night is addressed against the map of the year it was driven, '
            'because Black Rock City is surveyed afresh each year and never lands twice in '
            'the same place.</p>'
            % (esc(EDITION),
               figure("Nights", commas(len(nights)), "", "out on the playa"),
               figure("Distance", "%.0f" % miles, "mi", "wheels turning"),
               figure("Poofs", commas(poofs), "", "counted off the pressure trace"),
               figure("Seasons", "%d" % len(seasons), "", "%d to %d" % (seasons[0], seasons[-1])),
               len(seasons)))
    book.add(body, folio=False)
    book.blank()


def contents_body(entries, seasons, features=()):
    rows = []
    extra = {night: (label, page) for night, label, page in features}
    # A contents follows the page order, and the book reads forwards through the years
    for year in sorted(seasons):
        rows.append('<tr><td class="yr" colspan="3">%d</td></tr>' % year)
        rows.append('<tr><td>The season</td><td class="dots"></td><td class="pg">%d</td></tr>'
                    % seasons[year])
        for night, page in entries:
            if night.year != year:
                continue
            rows.append('<tr><td>%s</td><td class="dots"></td><td class="pg">%d</td></tr>'
                        % (esc(night.strftime("%A %-d %B")), page))
            # A feature sits under the night it belongs to, indented, so the run reads straight
            if night in extra:
                label, feature_page = extra[night]
                rows.append('<tr><td class="feat">%s</td><td class="dots"></td>'
                            '<td class="pg">%d</td></tr>' % (esc(label), feature_page))
    return ('<p class="eyebrow">Contents</p><h2>The nights</h2><hr class="rule">'
            '<table class="toc">%s</table>' % "".join(rows))


# -------------------------------------------------------------------- the season


def season_divider(book, year, reports):
    miles = sum(report.miles for report in reports)
    poofs = sum(len(report.poofs) for report in reports)
    stops = sum(len(report.stops) for report in reports)
    rolling = sum(report.rolling_seconds for report in reports)
    longest = max(reports, key=lambda report: report.miles)
    busiest = max(reports, key=lambda report: len(report.poofs))
    body = ('<div class="year">%d</div>'
            '<p class="season">%d nights out, %.1f miles between them. The longest run was '
            '<strong>%s</strong> at %.1f miles; the poofer worked hardest on '
            '<strong>%s</strong>, firing %s times.</p>'
            '<div class="figures four">%s%s%s%s</div>'
            % (year, len(reports), miles,
               esc(longest.night.strftime("%A %-d %B")), longest.miles,
               esc(busiest.night.strftime("%A %-d %B")), commas(len(busiest.poofs)),
               figure("Nights", "%d" % len(reports)),
               figure("Distance", "%.1f" % miles, "mi"),
               figure("Poofs", commas(poofs)),
               figure("Rolling", duration(rolling))))
    return book.add(body, kind="divider", runner="%d" % year)


# --------------------------------------------------------------------- the night


def art_stop(report):
    """The stop that is the art piece, on the night the car spent at it"""
    if report.night != ART_NIGHT or not report.stops:
        return None
    return max(report.stops, key=lambda stop: stop.seconds)


def art_note(report):
    """What the night at the piece looked like from the car's own logs"""
    held = art_stop(report)
    if not held:
        return ""
    together = [stop for stop in report.stops
                if abs(report.city.feet_from_man(stop.lat, stop.lon)
                       - report.city.feet_from_man(held.lat, held.lon)) < 60.0]
    seconds = sum(stop.seconds for stop in together)
    poofs = sum(stop.poofs for stop in together)
    return ('<div class="feature"><h3>%s</h3>'
            '<p class="credit">Built by %s<br>%s</p>'
            '<p>The crew put the piece up and the car spent the night at it. It stands at '
            '<strong>%s</strong>, which is not a location any map layer carries &mdash; it is '
            'taken from the ground, because the car parked on it for <strong>%s</strong> and '
            'fired <strong>%s of the night\'s %s poofs</strong> while it sat there.</p></div>'
            % (esc(ART_NAME), esc(ART_CREW), esc(ART_ARTISTS), esc(held.address),
               esc(duration(seconds)), esc(commas(poofs)), esc(commas(len(report.poofs)))))


def propane_block(report):
    """How the night's load was paced, and whether the supply kept up

    Nothing on the car measures what is in the tanks, so the curve is the night's own draw
    read backwards: 100 at roll-out, 0 at the last poof. It says how the gas was spent, not
    how close the car came to running dry.
    """
    remaining = report.remaining_series
    if not remaining:
        return ""
    recoveries = sorted(poof.recovery for poof in report.poofs if poof.recovery is not None)
    figures = [figure("Half gone by", esc(clock_time(report.half_gone)) if report.half_gone else "&mdash;",
                      "", "of the night's load")]
    if recoveries:
        figures.append(figure("Recharge", "%.0f" % statistics.median(recoveries), "s",
                              "median time back to pressure"))
    # The pressure itself, rather than a start and end figure for it, because a summary of
    # two numbers misses the night the tank ran down to nothing at five in the morning
    pressure = None
    if report.pressure_series:
        pressure = (report.pressure_series, "psi", "var(--series-1)",
                    "accumulator pressure, highest each minute", "load left, % of the night's")
    return ('<h3>Propane</h3><div class="figures %s">%s</div>%s'
            % ("two" if len(figures) == 2 else "", "".join(figures),
               web.line_chart(report, remaining, "%" if pressure else "",
                              "Propane remaining and accumulator pressure through the night",
                              "var(--series-2)", height=PROPANE_CHART_HEIGHT, right=pressure)))


def tub_block(report):
    """What the water in the tub was doing, where the probe was telling the truth"""
    if not report.temperature:
        return ('<hr class="thin"><h3>Tub water</h3>'
                '<p class="empty">Nothing logged this night &mdash; the <code>temp</code> and '
                '<code>water</code> streams are empty.</p>')
    plausible = [(when, value) for when, value in report.temperature if value >= TUB_MIN_F]
    if len(plausible) < TUB_MIN_USABLE * len(report.temperature):
        return ('<hr class="thin"><h3>Tub water</h3>'
                '<p class="empty">%s of the night\'s %s readings came back under %g&deg;F, which '
                'water in a tub in August does not do. The probe was failing rather than the water '
                'cooling, so the night is left without a reading.</p>'
                % (commas(len(report.temperature) - len(plausible)),
                   commas(len(report.temperature)), TUB_MIN_F))
    values = [value for _, value in plausible]
    dropped = len(report.temperature) - len(plausible)
    note = (" %s reading%s under %g&deg;F left out as probe error."
            % (commas(dropped), "" if dropped == 1 else "s", TUB_MIN_F)) if dropped else ""
    return ('<hr class="thin"><h3>Tub water</h3>'
            '<p class="note">Ranged %.0f&deg;F to %.0f&deg;F, ending the night at %.0f&deg;F.%s</p>%s'
            % (min(values), max(values), values[-1], note,
               web.line_chart(report, plausible, "°F", "Tub water temperature",
                              "var(--series-3)", height=TUB_CHART_HEIGHT)))


def map_page(report, chart, caption, legend):
    """A map given a page of its own, with its key and a line saying what it is"""
    return ('<p class="eyebrow">%s</p><h2>%s</h2><hr class="rule">'
            '<div class="mapwrap">%s</div>%s'
            '<p class="note" style="margin-top:8px">%s</p>'
            % (esc(report.night.strftime("%B %Y")),
               esc(report.night.strftime("%A %-d %B")), chart, legend, esc(caption)))


def route_page(report):
    marks = []
    held = art_stop(report) if INCLUDE_NARRATIVE else None
    if held:
        marks.append((held.lat, held.lon, ART_NAME))
    caption = ("Rolled out at %s, last fix at %s. Coloured by speed; red rings are stops of "
               "five minutes or more."
               % (clock_time(report.first_fix.timestamp), clock_time(report.last_fix.timestamp)))
    return map_page(report,
                    web.map_chart(report, aspect=MAP_ASPECT,
                                  key="n%s" % report.night.strftime("%Y%m%d"), marks=marks),
                    caption, web.speed_legend(report))


def poof_page(report):
    located = [poof for poof in report.poofs if poof.lat is not None]
    if len(located) == len(report.poofs):
        placed = "all %s of the night's were placed." % commas(len(report.poofs))
    else:
        placed = "%s of the night's %s were placed." % (commas(len(located)), commas(len(report.poofs)))
    caption = ("Every poof placed on the track by its timestamp, then grouped by "
               "neighbourhood. Bigger circles are where the poofer fired hardest; " + placed)
    return map_page(report,
                    web.poof_map(report, aspect=MAP_ASPECT,
                                 key="p%s" % report.night.strftime("%Y%m%d")),
                    caption, web.poof_map_legend(report))


def stops_block(report):
    if not report.stops:
        return ""
    rows = []
    for index, stop in enumerate(report.stops[:STOPS_ON_PAGE], start=1):
        # The distance is what makes the name mean anything: 40 ft is parked at it, 280 is
        # merely the nearest thing that had a name
        beside = ("%s <span class=\"away\">%s ft</span>"
                  % (esc(stop.landmark[0]), commas(int(round(stop.landmark[1]))))
                  if stop.landmark else "&mdash;")
        rows.append('<tr><td class="num">%d</td><td>%s</td><td class="num">%s</td>'
                    '<td>%s</td><td>%s</td><td class="num">%s</td></tr>'
                    % (index, esc(clock_time(stop.start)), esc(duration(stop.seconds)),
                       esc(stop.address) if report.on_playa else "&mdash;", beside,
                       esc(commas(stop.poofs)) if stop.poofs else "&mdash;"))
    extra = ('<p class="tallies">and %d more, shorter.</p>' % (len(report.stops) - STOPS_ON_PAGE)
             if len(report.stops) > STOPS_ON_PAGE else "")
    return ('<hr class="thin"><h3>Where it stopped</h3>'
            '<table><thead><tr><th class="num">#</th><th>From</th><th class="num">Stayed</th>'
            '<th>Address</th><th>Beside</th><th class="num">Poofs</th></tr></thead>'
            '<tbody>%s</tbody></table>%s' % ("".join(rows), extra))


def numbers_page(report):
    """The night as figures, with speed and the poofer's timeline under them"""
    furthest = max((report.city.feet_from_man(fix.lat, fix.lon) for fix in report.trusted), default=0)
    parts = ['<div class="figures four">%s%s%s%s</div>'
             % (figure("Distance", "%.1f" % report.miles, "mi",
                       "%.1f mph while moving" % (report.miles / (report.rolling_seconds / 3600.0)
                                                  if report.rolling_seconds else 0)),
                figure("Rolling", duration(report.rolling_seconds), "",
                       "%s parked" % duration(report.parked_seconds)),
                figure("Poofs", "&mdash;" if report.chattering else commas(len(report.poofs)), "",
                       "sensor unusable" if report.chattering else "off the pressure trace"),
                figure("Furthest out", commas(int(round(furthest, -1))), "ft", "from the Man"))]
    parts.append('<hr class="thin"><h3>Speed through the night</h3>')
    parts.append(web.speed_chart(report))
    if report.poofs:
        parts.append('<hr class="thin"><h3>Poofs per quarter hour</h3>')
        parts.append(web.poof_chart(report))
    else:
        # Nothing else is coming for this night, so the rest of it belongs here
        parts.append(tub_block(report))
        parts.append(stops_block(report))
    return "".join(parts)


def propane_page(report):
    """What the load did, and the places the night was spent"""
    parts = propane_block(report)
    if parts and INCLUDE_NARRATIVE:
        parts += art_note(report)
    return parts + tub_block(report) + stops_block(report)


def circle_pass(report):
    """The stretch of the night spent inside the Man circle, and how fast it was taken"""
    inside = [fix for fix in report.trusted
              if report.city.feet_from_man(fix.lat, fix.lon) < MAN_CIRCLE_FT]
    if not inside:
        return None
    speeds = sorted(segment.mph for segment in report.segments
                    if report.city.feet_from_man(segment.end.lat, segment.end.lon) < MAN_CIRCLE_FT)
    closest = min((report.city.feet_from_man(fix.lat, fix.lon) for fix in inside))
    return {"fixes": inside,
            "seconds": (inside[-1].timestamp - inside[0].timestamp).total_seconds(),
            "from": inside[0].timestamp, "to": inside[-1].timestamp,
            "closest": closest,
            # How many readings the claim has to get past, which is the weight of the answer
            "samples": len(inside),
            "median": statistics.median(speeds) if speeds else 0.0,
            "top": max(speeds) if speeds else 0.0}


def exact_span(seconds):
    """Minutes and seconds both, for a figure that is being offered as evidence

    The usual duration drops the seconds once there is a minute to show, which turns three
    minutes and forty nine into "3m" -- a quarter of the crossing given away for tidiness.
    """
    seconds = int(round(seconds))
    minutes, rest = seconds // 60, seconds % 60
    if minutes and rest:
        return "%dm %ds" % (minutes, rest)
    return "%dm" % minutes if minutes else "%ds" % rest


def grounding_left(report, passage):
    """The story, and the crossing drawn as the receiver recorded it"""
    return ('<p class="eyebrow">%s</p><h2>Grounded</h2><hr class="rule">'
            '<p class="note">The charge was <strong>%g mph through the Man circle</strong>, and it '
            'cost Beverly her licence. She did not get it back that year.</p>'
            '<p class="note">The crossing is not in dispute. She went inside the circle and came '
            'out the other side, and it is drawn below exactly as the receiver recorded it. That '
            'was a boundary she should not have crossed and the crew has never said otherwise.</p>'
            '<p class="note">The speed is another matter, and the answer to it had been running '
            'all night in her own logs. What those say is on the facing page.</p>'
            '<div class="mapwrap">%s</div>'
            '<p class="note" style="margin-top:8px">The pass through the circle, %s to %s, '
            'closest approach %s ft from the Man. The rest of the night runs out of the frame.</p>'
            % (esc(report.night.strftime("%A %-d %B %Y")), ALLEGED_MPH,
               web.map_chart(report, aspect=CIRCLE_MAP_ASPECT, focus=passage["fixes"], key="circle"),
               esc(clock_time(passage["from"])), esc(clock_time(passage["to"])),
               esc(commas(int(round(passage["closest"]))))))


def grounding_right(report, passage, after):
    parts = ['<div class="figures four">%s%s%s%s</div>'
             % (figure("Alleged", "%g" % ALLEGED_MPH, "mph", "through the circle"),
                figure("Fastest recorded", "%.1f" % passage["top"], "mph",
                       "across %d fixes inside it" % passage["samples"]),
                figure("Median", "%.1f" % passage["median"], "mph", "for the whole crossing"),
                figure("Inside the circle", exact_span(passage["seconds"]), "",
                       "closest %s ft" % commas(int(round(passage["closest"])))))]

    parts.append('<hr class="thin"><h3>What the log holds</h3>')
    parts.append('<p class="note">She was inside for %s and the receiver caught <strong>%d fixes</strong> '
                 'across it. The fastest is <strong>%.1f mph</strong>. The median is %.1f. Not one of '
                 'them reaches ten, let alone %g. Beverly does about ten flat out on open playa; %g is '
                 'not a speed she was doing that night, because it is not a speed she can do.</p>'
                 % (exact_span(passage["seconds"]), passage["samples"], passage["top"],
                    passage["median"], ALLEGED_MPH, ALLEGED_MPH))
    parts.append(web.speed_chart(report))
    parts.append('<p class="note">Every sample of the night. The circle is crossed at %s.</p>'
                 % esc(clock_time(passage["from"])))

    parts.append('<hr class="thin"><h3>What it cost</h3>')
    if after:
        rows = "".join('<tr><td>%s</td><td class="num">%.1f</td><td class="num">%s</td>'
                       '<td class="num">%s</td></tr>'
                       % (esc(item.night.strftime("%A %-d %B")), item.miles,
                          esc(duration(item.rolling_seconds)), esc(commas(len(item.poofs))))
                       for item in after)
        parts.append('<table><thead><tr><th>Night</th><th class="num">Miles</th>'
                     '<th class="num">Rolling</th><th class="num">Poofs</th></tr></thead>'
                     '<tbody>%s</tbody></table>' % rows)
    parts.append('<p class="note" style="margin-top:10px">None of the above was weighed. The sentence '
                 'rested on what somebody believed they saw, and once it had been said it became the '
                 'fact of the matter. A minor infraction of a boundary was answered with the whole '
                 'week, on a charge the car itself could disprove and was never asked to.</p>')
    parts.append('<p class="note">What is hard to carry is not the ruling. It is being handled as a '
                 'danger at the one event whose whole ethos we came to meet &mdash; bringing '
                 'authenticity and energy and love to it &mdash; and being answered that night with '
                 'authority, a rulebook and somebody\'s impression. That was heartbreaking. It is set '
                 'down here because it belongs to her record as much as the miles do.</p>')
    return "".join(parts)


def grounding_spread(book, report, after):
    passage = circle_pass(report)
    if not passage:
        return None
    book.align_verso()
    left = book.add(grounding_left(report, passage), runner="Grounded")
    book.add(grounding_right(report, passage, after), runner="Grounded")
    return left


def night_spread(book, report):
    """A night is two spreads when the poofer worked, and one when it did not

    The second pair has nothing to carry on a night with no poofs, so those nights keep the
    old shape and their stops move up onto the numbers page.
    """
    runner = report.night.strftime("%a %-d %b %Y")
    first = book.add(route_page(report), runner=runner)
    book.add(numbers_page(report), runner=runner)
    if any(poof.lat is not None for poof in report.poofs):
        book.add(poof_page(report), runner=runner)
        book.add(propane_page(report), runner=runner)
    return first


# -------------------------------------------------------------------- back matter


def colophon(book):
    body = ('<p class="eyebrow">How the numbers were made</p><h2>On the reckoning</h2>'
            '<hr class="rule">'
            '<p><strong>Distance and speed</strong> come from the gaps between consecutive '
            'fixes. Half a mile an hour is the line between moving and standing: a parked '
            'receiver wanders a few metres a minute, and counting that as travel once had a '
            'night in the yard reporting a mile the car never drove.</p>'
            '<p><strong>Stops</strong> are runs of five minutes or more below that line. Two '
            'of them less than five minutes apart and within 300 ft of each other are folded '
            'together, so nudging forward in a crowd stays one stop.</p>'
            '<p><strong>Poofs</strong> are read out of the accumulator pressure trace, which '
            'the monitor samples at 10Hz around every burst: a poof is a fall of at least '
            'five psi inside three seconds followed by a recharge. The counter on the car is '
            'not kept, so this is a reconstruction rather than a readback. Through 2022 the '
            'monitor logged the sensor raw and it has been put back into psi here with the '
            'monitor&rsquo;s own calibration.</p>'
            '<p><strong>Nothing outside the trash fence was the car.</strong> The 2022 '
            'receiver would set off in a straight line at a steady five miles an hour and '
            'reappear where the car really was, half an hour later. The speed gives nothing '
            'away; where it ends up does, two and three times further out than a fence that '
            'cannot be driven through.</p>'
            '<p><strong>The clock is corrected where the Pi had none.</strong> Without a '
            'realtime clock it woke wherever the clock had been left, and stamped the 2022 '
            'season thirteen days behind. The anchor is the burn: on the night the log calls '
            '21 August the car crosses inside the perimeter and parks 897 ft from the Man, '
            'which cannot happen until he is down. That is Saturday 3 September 2022, and the '
            'season is dated from it.</p>'
            '<hr class="thin">'
            '<p class="note">Built from the <code>rhb-sensor-monitor</code> logs by '
            '<code>reporting/book_render.py</code>. Maps are the official Black Rock City '
            'survey for each year.</p>')
    book.add(body, runner="Colophon")


def render_book(reports):
    """The whole book, newest season last so it reads forwards through the years"""
    reports = sorted(reports, key=lambda report: report.night)
    seasons = {}
    for report in reports:
        seasons.setdefault(report.night.year, []).append(report)

    book = Book()
    cover(book, seasons)
    title_page(book, reports, sum(r.miles for r in reports), sum(len(r.poofs) for r in reports))
    # The contents cannot be written until every page has a number, so it is held back
    contents = book.reserve()

    entries, divider_pages, features = [], {}, []
    for year in sorted(seasons):
        book.align_recto()
        divider_pages[year] = season_divider(book, year, seasons[year])
        for report in seasons[year]:
            book.align_verso()
            entries.append((report.night, night_spread(book, report)))
            # The grounding follows the night that caused it, while it is still in hand
            if INCLUDE_NARRATIVE and report.night == GROUNDING_NIGHT:
                after = [item for item in seasons[year] if item.night > report.night][:2]
                page = grounding_spread(book, report, after)
                if page:
                    features.append((report.night, "Grounded", page))
    book.align_recto()
    colophon(book)

    book.fill(contents, contents_body(entries, divider_pages, features), runner="Contents")
    return book.html("%s %s" % (TITLE, EDITION))

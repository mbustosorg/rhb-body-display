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

"""After-excursion report for a night of driving, built from the sensor monitor logs"""

import argparse
import bisect
import csv
import datetime
import io
import json
import math
import os
import re
import statistics
import zipfile
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import report_render

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
# The sensor monitor is a sibling checkout; the map layers ship with the display
DEFAULT_DATA = os.path.normpath(os.path.join(REPO, os.pardir, "rhb-sensor-monitor", "data"))
DEFAULT_MAP = os.path.join(REPO, "rhbbodydisplay", "data")
# The city is surveyed afresh every year and does not land in the same place twice: the Man
# moved some 600 yards between 2025 and 2026, further than the gap between two rings. So a
# night is addressed against the map of the year it was driven, where kml_parsing has one
YEAR_MAPS = os.path.join(REPO, "kml_parsing")
YEAR_LAYERS = "layers"

# The car rolls out in the evening and comes home after sunrise
NIGHT_START_HOUR = 21
NIGHT_END_HOUR = 9

# The Pi carried no realtime clock in the early seasons, so booting away from a network it
# picked up wherever the clock had been left and stamped the whole season in its own time.
# 2022 came back thirteen days behind. The anchor is the night the log calls 2022-08-21:
# the car crosses inside the burn perimeter at 23:19 and parks 897 ft from the Man, which
# cannot happen until the Man has come down, and it is also that season's longest drive,
# its heaviest poofing and its most time spent at the Man. That is Saturday 3 September
# 2022. Adding thirteen days puts all five playa nights inside the event, the Temple burn
# on the Sunday and the drive home on the Tuesday of exodus.
#
# The Pi was powered off for the drive each way, so its clock lost those hours as well and
# the shift is exact only between them: the Oakland nights either side of the trip are
# right to within about half a day.
CLOCK_CORRECTIONS = {2022: datetime.timedelta(days=13)}

EARTH_RADIUS_MI = 3958.7613
FEET_PER_MILE = 5280.0

# A fix implying more than this is a GPS glitch, not the art car. The number is the car's,
# not the receiver's: Beverly tops out around 10 mph on open playa, so anything past 12 is
# something the vehicle cannot do however confident the fix looks. It used to be 45, which
# was only ever a guard against gross jumps and let through a 43 mph sample on the night
# the licence was pulled -- a reading that was never the car and should not have stood.
MAX_PLAUSIBLE_MPH = 12.0

# The 2022 receiver had a slower failure than a jump, and one the limit above lets past: it
# would set off in a straight line at a steady five miles an hour, sometimes for half an
# hour, and then reappear where the car really was. Nothing about the speed gives it away.
# What does is where it ends up -- two and three times further out than the trash fence,
# which is a real barrier the car cannot drive through. So a fix beyond the edge of the
# map, on a night that was out on the playa, was not the car. The margin is for the gap
# between a surveyed fence and a receiver's idea of one: the furthest any other season
# ever got is 8,171 ft against a fence at 8,436, while 2022 runs out past 23,000
OFF_MAP_MARGIN = 1.05

# Under this the car is not going anywhere: parked GPS wanders by a few metres a
# minute, which reads as a tenth of a mile an hour, so anything slower is noise
# rather than travel. Distance, rolling time and stops all hang off this one line.
MOVING_MPH = 0.5
# A parked cluster has to hold this long, within this radius, to count as a stop
STOP_MIN_SECONDS = 300.0
STOP_RADIUS_FT = 120.0
# Nudging forward mid stop should not split it into two
STOP_MERGE_SECONDS = 300.0
STOP_MERGE_FT = 300.0
# Positions are only logged when they change, so silence alone is not a data gap
GAP_SECONDS = 300.0
# A poof drops the accumulator by tens of psi in about a second
POOF_DROP_PSI = 5.0
POOF_FALL_SECONDS = 3.0
POOF_RECOVERY_PSI = 1.0
# Samples further apart than this belong to separate poof episodes
POOF_EPISODE_GAP = 2.0
# The accumulator counts as recharged once it is back to this much of where it started
POOF_RECOVERY_FRACTION = 0.9
POOF_RECOVERY_LIMIT = 120.0
# Poofs to smooth the supply pressure across when drawing its trend
SUPPLY_WINDOW = 15

# Until midway through 2023 the monitor logged the accumulator as raw ADS1115 counts and
# only converted them for the display; after that it logged calibrated psi. The 2022 season
# is all counts, and reading them as psi turned sensor noise into tens of thousands of
# poofs. These are the monitor's own calibration (PoofTrack.pressure_from_raw), which puts
# the sensor's zero at about -2000 counts.
RAW_COUNTS_PER_PSI = 200.0
RAW_PSI_AT_ZERO_COUNT = 10.0
# The gauge tops out around 65 psi and is clamped at zero, so a trace that leaves this
# range is still in counts. Files never mix the two, so the whole night is judged together
MAX_PLAUSIBLE_PSI = 100.0

# On some 2022 nights the sensor sat flipping between two levels about five psi apart, ten
# times a second, which is electrical and not pressure -- no accumulator moves that fast.
# Read as poofs it made 39,000 of them on the drive up, with the poofer off the whole way.
# A real night puts a poof's worth of step between well under one sample pair in a hundred
PRESSURE_CHATTER_FRACTION = 0.02
# Below this the fraction is too few samples to mean anything either way
PRESSURE_CHATTER_SAMPLES = 1000

# Propane released by one poof is the pressure it drew out of a fixed volume, so
# n = dP.V / RT. Without the accumulator's volume the draw is only proportional to
# mass, which is why pounds are opt-in rather than assumed.
PASCALS_PER_PSI = 6894.757
CUBIC_M_PER_GALLON = 0.00378541
GAS_CONSTANT = 8.314462
PROPANE_KG_PER_MOL = 0.0441
POUNDS_PER_KG = 2.20462
ASSUMED_KELVIN = 293.15

# The monitor used to roll a file an hour and now rolls one whenever it restarts, so a
# name carries either the hour alone or the hour and the minute. The 2022 season is all
# of the older kind, and a pattern that only knew the newer one made it invisible
FILE_PATTERN = re.compile(r"^(?P<stream>[a-z_]+)_(?P<stamp>\d{8}_\d{2}(?:_\d{2})?)\.csv$")
STAMP_FORMATS = ("%Y%m%d_%H_%M", "%Y%m%d_%H")


# ---------------------------------------------------------------- data loading


def corrected(moment):
    """A logged moment in real time, for the seasons the Pi's clock was adrift

    Applied to file names and rows alike, so everything downstream -- which night a row
    belongs to, which files a window pulls in -- is already in the time the car was driven.
    """
    shift = CLOCK_CORRECTIONS.get(moment.year)
    return moment + shift if shift else moment


def stamp_of(name):
    """Persist time encoded in a log file name, or None if it is not one"""
    match = FILE_PATTERN.match(os.path.basename(name))
    if not match:
        return None
    for layout in STAMP_FORMATS:
        try:
            return corrected(datetime.datetime.strptime(match.group("stamp"), layout))
        except ValueError:
            continue
    return None


def parse_timestamp(value):
    """Parse a logged timestamp, tolerating the duplicated header rows some files carry"""
    if not value:
        return None
    try:
        return corrected(datetime.datetime.strptime(value[:26], "%Y-%m-%dT%H:%M:%S.%f"))
    except ValueError:
        try:
            return corrected(datetime.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return None


def number(row, key):
    """Float value of a column, or None when it is missing or blank"""
    try:
        return float(row[key])
    except (TypeError, ValueError, KeyError):
        return None


def read_rows(handle, start, end):
    """Rows of an open log file that fall inside the window"""
    rows = []
    for row in csv.DictReader(handle):
        stamp = parse_timestamp(row.get("timestamp"))
        if stamp is None or not start <= stamp < end:
            continue
        row["timestamp"] = stamp
        rows.append(row)
    return rows


def load_stream(root, stream, start, end):
    """Rows of one sensor stream, from loose CSVs or from the season archives"""
    rows = []
    # A file is named for the moment it was persisted, so it holds the preceding interval
    margin = datetime.timedelta(days=1)
    prefix = stream + "_"
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        if entry.startswith(prefix) and entry.endswith(".zip"):
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    stamp = stamp_of(name)
                    if stamp is None or not start - margin <= stamp <= end + margin:
                        continue
                    if not os.path.basename(name).startswith(prefix):
                        continue
                    with archive.open(name) as member:
                        rows.extend(read_rows(io.TextIOWrapper(member, "utf-8"), start, end))
        elif entry.startswith(prefix) and entry.endswith(".csv"):
            stamp = stamp_of(entry)
            if stamp is not None and not start - margin <= stamp <= end + margin:
                continue
            with open(path, newline="") as handle:
                rows.extend(read_rows(handle, start, end))
    rows.sort(key=lambda row: row["timestamp"])
    return rows


def available_nights(root):
    """Dates that have position data, counted by the night they belong to"""
    nights = {}
    prefix = "positions_"
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        handles = []
        if entry.startswith(prefix) and entry.endswith(".zip"):
            archive = zipfile.ZipFile(path)
            handles = [(name, archive) for name in archive.namelist()
                       if os.path.basename(name).startswith(prefix) and stamp_of(name)]
        elif entry.startswith(prefix) and entry.endswith(".csv") and stamp_of(entry):
            handles = [(path, None)]
        for name, archive in handles:
            if archive is None:
                stream = open(name, newline="")
            else:
                stream = io.TextIOWrapper(archive.open(name), "utf-8")
            with stream:
                for row in csv.DictReader(stream):
                    stamp = parse_timestamp(row.get("timestamp"))
                    if stamp is None or number(row, "lat") is None:
                        continue
                    night = night_of(stamp)
                    if night is not None:
                        nights[night] = nights.get(night, 0) + 1
    return nights


def night_of(stamp):
    """The night a moment belongs to, or None if it happened in daylight"""
    if stamp.hour < NIGHT_END_HOUR:
        return (stamp - datetime.timedelta(days=1)).date()
    if stamp.hour >= NIGHT_START_HOUR:
        return stamp.date()
    return None


def night_window(night):
    """Start and end of a night"""
    start = datetime.datetime.combine(night, datetime.time(NIGHT_START_HOUR))
    end = datetime.datetime.combine(night + datetime.timedelta(days=1), datetime.time(NIGHT_END_HOUR))
    return start, end


# ------------------------------------------------------------------- geography


def haversine_mi(lat1, lon1, lat2, lon2):
    """Great circle distance in miles"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_MI * math.asin(min(1.0, math.sqrt(a)))


def load_places(path):
    """Our own marked places as (name, glyph, lon, lat), if the season has any"""
    places = []
    if not os.path.exists(path):
        return places
    with open(path, newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 4:
                continue
            try:
                places.append((row[0].strip(), row[1].strip(), float(row[2]), float(row[3])))
            except ValueError:
                continue
    return places


def load_named_points(path):
    """A layer of named places as (name, lon, lat), for the ones worth calling by name

    Missing is not an error: a season with no art layer simply has nothing to name stops
    after. Names may carry commas, so the coordinates are read off the end of the row.
    """
    points = []
    if not os.path.exists(path):
        return points
    with open(path, newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 3:
                continue
            try:
                lon, lat = float(row[-2]), float(row[-1])
            except ValueError:
                continue
            name = ",".join(row[:-2]).strip()
            if name:
                points.append((name, lon, lat))
    return points


def load_polylines(path):
    """Polylines of a map layer as lists of (lon, lat), split on the blank separator rows"""
    lines = [[]]
    with open(path) as handle:
        for text in handle:
            text = text.strip()
            if not text:
                if lines[-1]:
                    lines.append([])
                continue
            parts = text.split(",")
            if len(parts) < 2:
                continue
            try:
                lines[-1].append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return [line for line in lines if line]


def mean_bearing(bearings):
    """Circular mean of a set of bearings in degrees"""
    x = sum(math.cos(math.radians(b)) for b in bearings)
    y = sum(math.sin(math.radians(b)) for b in bearings)
    return math.degrees(math.atan2(y, x)) % 360


class BlackRockCity:
    """The city's geometry, derived from the same map layers the display draws"""

    LANDMARKS = (("portos", "toilets.csv"), ("first aid", "first_aid.csv"), ("a Ranger station", "ranger.csv"))
    # Art is what a night was spent at; portos are what it happened to be near. So a piece
    # within a short walk wins even when a row of toilets is closer. Built by fetch_art.py
    # from Burning Man's own open data, which places each season's art by name
    ART_FILE = "art.csv"
    ART_LIMIT_FT = 300.0
    # Our camp and the burn out at the fence, marked on every map of the city
    PLACES_FILE = "places.csv"

    def __init__(self, map_root):
        self.streets = load_polylines(os.path.join(map_root, "lines.csv"))
        ring = [point for line in load_polylines(os.path.join(map_root, "man_ring.csv")) for point in line]
        self.man_ring = ring
        self.man_lon = sum(point[0] for point in ring) / len(ring)
        self.man_lat = sum(point[1] for point in ring) / len(ring)
        self.bearing_12 = self._twelve_oclock(map_root)
        self.landmarks = []
        for label, name in self.LANDMARKS:
            path = os.path.join(map_root, name)
            if os.path.exists(path):
                points = [point for line in load_polylines(path) for point in line]
                self.landmarks.append((label, points))
        self.art = load_named_points(os.path.join(map_root, self.ART_FILE))
        # Our own two places, written by mark_places.py: (name, glyph, lon, lat)
        self.places = load_places(os.path.join(map_root, self.PLACES_FILE))
        # The city sits inside this box; anything else is a test drive somewhere at home
        lons = [point[0] for line in self.streets for point in line]
        lats = [point[1] for line in self.streets for point in line]
        self.bounds = (min(lons), min(lats), max(lons), max(lats))
        # How far the map itself goes, which is the trash fence at its corners. The fence is
        # a real barrier, so nothing beyond this was the car
        self.reach = max(self.feet_from_man(point[1], point[0])
                         for line in self.streets for point in line)

    def _twelve_oclock(self, map_root):
        """Bearing of 12:00, read off the 2:00 and 10:00 radials of this year's map"""
        references = []
        for name, hour in (("2_00.csv", 2), ("10_00.csv", 10)):
            path = os.path.join(map_root, name)
            if not os.path.exists(path):
                continue
            points = [point for line in load_polylines(path) for point in line]
            if not points:
                continue
            radial = mean_bearing([self.bearing(lat, lon) for lon, lat in points])
            references.append((radial - hour * 30.0) % 360)
        if not references:
            # The city has been laid out with 12:00 to the northeast for decades
            return 45.0
        return mean_bearing(references)

    def bearing(self, lat, lon):
        """Bearing from the Man, in degrees clockwise from true north"""
        east = (lon - self.man_lon) * math.cos(math.radians(self.man_lat))
        north = lat - self.man_lat
        return math.degrees(math.atan2(east, north)) % 360

    def clock(self, lat, lon):
        """Position on the city clock, as seen from the Man"""
        hours = ((self.bearing(lat, lon) - self.bearing_12) % 360) / 30.0
        hour = int(hours)
        minute = int(round((hours - hour) * 60))
        if minute == 60:
            hour, minute = hour + 1, 0
        hour = hour % 12 or 12
        return "%d:%02d" % (hour, minute)

    def feet_from_man(self, lat, lon):
        """Radial distance from the Man in feet"""
        return haversine_mi(lat, lon, self.man_lat, self.man_lon) * FEET_PER_MILE

    def address(self, lat, lon):
        """Human readable playa address"""
        return "%s & %s ft" % (self.clock(lat, lon), format(int(round(self.feet_from_man(lat, lon), -1)), ","))

    def nearest_art(self, lat, lon, limit_ft=None):
        """The named piece of art a position was parked at, if it was parked at one"""
        limit = self.ART_LIMIT_FT if limit_ft is None else limit_ft
        best = None
        for name, lon_p, lat_p in self.art:
            feet = haversine_mi(lat, lon, lat_p, lon_p) * FEET_PER_MILE
            if feet <= limit and (best is None or feet < best[1]):
                best = (name, feet)
        return best

    def nearest_landmark(self, lat, lon, limit_ft=400.0):
        """Closest thing worth naming: the art it was at, or failing that the infrastructure

        A piece of art is somewhere the car went on purpose, so it takes precedence over a
        row of portos that happens to be nearer.
        """
        art = self.nearest_art(lat, lon)
        if art:
            return art
        best = None
        for label, points in self.landmarks:
            for lon_p, lat_p in points:
                feet = haversine_mi(lat, lon, lat_p, lon_p) * FEET_PER_MILE
                if feet <= limit_ft and (best is None or feet < best[1]):
                    best = (label, feet)
        return best

    def contains(self, lat, lon):
        """Is this position on the playa at all?"""
        min_lon, min_lat, max_lon, max_lat = self.bounds
        pad = 0.05
        return min_lon - pad <= lon <= max_lon + pad and min_lat - pad <= lat <= max_lat + pad


# --------------------------------------------------------------------- the ride


@dataclass
class Fix:
    timestamp: datetime.datetime
    lat: float
    lon: float
    alt: Optional[float]
    # Set when the receiver put the car somewhere it could not have reached
    glitch: bool = False


@dataclass
class Segment:
    start: Fix
    end: Fix
    seconds: float
    miles: float
    mph: float


@dataclass
class Stop:
    start: datetime.datetime
    end: datetime.datetime
    seconds: float
    lat: float
    lon: float
    address: str
    landmark: Optional[Tuple[str, float]]
    poofs: int = 0


@dataclass
class Poof:
    timestamp: datetime.datetime
    drop: float
    seconds: float
    supply: float
    recovery: Optional[float] = None
    parked: bool = False
    lat: Optional[float] = None
    lon: Optional[float] = None


@dataclass
class Report:
    night: datetime.date
    start: datetime.datetime
    end: datetime.datetime
    city: BlackRockCity
    on_playa: bool
    fixes: List[Fix]
    segments: List[Segment]
    stops: List[Stop]
    poofs: List[Poof]
    speed_series: List[Tuple[datetime.datetime, Optional[float]]]
    poof_bins: List[Tuple[datetime.datetime, int]]
    temperature: List[Tuple[datetime.datetime, float]] = field(default_factory=list)
    gaps: List[Tuple[datetime.datetime, datetime.datetime, float]] = field(default_factory=list)
    glitches: int = 0
    # The pressure trace arrived as raw ADC counts and was converted to psi here
    calibrated: bool = False
    # The pressure sensor was oscillating, so there is no poof count to be had
    chattering: bool = False
    # How far the logged clock was put back to reach the night the car was really driven
    clock_shift: Optional[datetime.timedelta] = None
    counts: dict = field(default_factory=dict)
    poof_threshold: float = POOF_DROP_PSI
    supply_window: int = SUPPLY_WINDOW
    accumulator_gallons: Optional[float] = None

    @property
    def miles(self):
        """Ground actually covered -- drift while parked is not distance driven"""
        return sum(segment.miles for segment in self.segments if segment.mph >= MOVING_MPH)

    @property
    def rolling_seconds(self):
        return sum(segment.seconds for segment in self.segments if segment.mph >= MOVING_MPH)

    @property
    def parked_seconds(self):
        return sum(stop.seconds for stop in self.stops)

    @property
    def first_fix(self):
        return self.fixes[0] if self.fixes else None

    @property
    def last_fix(self):
        return self.fixes[-1] if self.fixes else None

    @property
    def fastest(self):
        """Fastest minute of the night, as (moment, mph)"""
        paced = [(when, mph) for when, mph in self.speed_series if mph is not None]
        return max(paced, key=lambda pair: pair[1]) if paced else None

    @property
    def trusted(self):
        """Fixes the car could actually have been at, which is what the maps are drawn from"""
        return [fix for fix in self.fixes if not fix.glitch] or self.fixes

    @property
    def farthest(self):
        """Fix furthest from the Man, as (fix, feet)"""
        if not self.fixes or not self.on_playa:
            return None
        return max(((fix, self.city.feet_from_man(fix.lat, fix.lon)) for fix in self.trusted),
                   key=lambda pair: pair[1])

    @property
    def longest_stop(self):
        return max(self.stops, key=lambda stop: stop.seconds) if self.stops else None

    @property
    def psi_drawn(self):
        """Total pressure pulled out of the accumulator, proportional to propane burned"""
        return sum(poof.drop for poof in self.poofs)

    @property
    def pounds_drawn(self):
        """That draw as propane, once someone says how big the accumulator is"""
        if not self.accumulator_gallons:
            return None
        return propane_pounds(self.psi_drawn, self.accumulator_gallons)

    @property
    def drawn_series(self):
        """Propane drawn so far, poof by poof, as (moment, running total)"""
        running = 0.0
        series = []
        for poof in self.poofs:
            running += poof.drop
            series.append((poof.timestamp, running))
        return series

    @property
    def remaining_series(self):
        """What is left to burn, as an index of the night's load: 100 at roll-out, 0 at the end

        Nothing on the car measures how much propane is in the tanks, so this is the night's
        own draw read backwards -- the same curve as drawn_series, turned the way a fuel gauge
        reads. It says how the load was paced, not how close the car came to running dry.
        """
        total = self.psi_drawn
        if not total:
            return []
        series = [(self.start, 100.0)]
        running = 0.0
        for poof in self.poofs:
            running += poof.drop
            series.append((poof.timestamp, 100.0 * (1.0 - running / total)))
        return series

    @property
    def half_gone(self):
        """When the night's load was half burned"""
        for when, left in self.remaining_series:
            if left <= 50.0:
                return when
        return None

    @property
    def supply_series(self):
        """Supply pressure over the night, smoothed across neighbouring poofs

        A poof fired before the accumulator has recovered reads as a deep spike, which
        is true but drowns the trend, so the run is carried by a rolling median.
        """
        supply = [poof.supply for poof in self.poofs]
        if len(supply) < SUPPLY_WINDOW:
            return [(poof.timestamp, poof.supply) for poof in self.poofs]
        series = []
        half = SUPPLY_WINDOW // 2
        for index, poof in enumerate(self.poofs):
            window = supply[max(0, index - half):index + half + 1]
            series.append((poof.timestamp, statistics.median(window)))
        return series

    @property
    def supply_trend(self):
        """Supply pressure at the start and end of the night, smoothed over five poofs"""
        supply = [poof.supply for poof in self.poofs]
        if len(supply) < 5:
            return None
        window = max(5, len(supply) // 10)
        return (statistics.median(supply[:window]), statistics.median(supply[-window:]))

    @property
    def busiest_poof_hour(self):
        if not self.poofs:
            return None
        hours = {}
        for poof in self.poofs:
            hour = poof.timestamp.replace(minute=0, second=0, microsecond=0)
            hours[hour] = hours.get(hour, 0) + 1
        return max(hours.items(), key=lambda pair: pair[1])


def collect_fixes(rows):
    """Position rows turned into fixes, dropping the empty and the repeated"""
    fixes = []
    for row in rows:
        lat, lon = number(row, "lat"), number(row, "lon")
        if lat is None or lon is None or (lat == 0.0 and lon == 0.0):
            continue
        if fixes and fixes[-1].timestamp == row["timestamp"]:
            continue
        fixes.append(Fix(row["timestamp"], lat, lon, number(row, "alt")))
    return fixes


def mark_off_map(fixes, city):
    """Flag the fixes that put the car outside the trash fence, which it cannot be

    Only the part of an excursion that is past the fence gets dropped. Following it back
    inside by how straight it runs was tried and is wrong: out on the open playa a straight
    line for half a mile is just driving, and the test threw away real nights of it.
    """
    limit = city.reach * OFF_MAP_MARGIN
    for fix in fixes:
        if city.feet_from_man(fix.lat, fix.lon) > limit:
            fix.glitch = True


def build_segments(fixes):
    """Legs between consecutive fixes, with GPS jumps and logger silences separated out"""
    segments, gaps, glitches = [], [], 0
    # Each fix is judged against the last one the car could actually have been at, not
    # against whatever came before it. A receiver that wanders off does not always come
    # back in one hop -- the 2025 logs have it stepping east for a couple of minutes at
    # 137 mph -- and anchoring on the previous fix would call that excursion a real one
    # the moment its own steps looked plausible
    # An excursion can also open the night, so the anchor is the first fix that is the car
    first = next((index for index, fix in enumerate(fixes) if not fix.glitch), None)
    if first is None:
        return segments, gaps, sum(1 for fix in fixes if fix.glitch)
    previous = fixes[first]
    lost = False
    for current in fixes[first + 1:]:
        seconds = (current.timestamp - previous.timestamp).total_seconds()
        if seconds <= 0:
            continue
        miles = haversine_mi(previous.lat, previous.lon, current.lat, current.lon)
        mph = miles / seconds * 3600.0
        # Either the fix is too far to have been reached, or it is already known not to be
        # the car. Both leave it somewhere unknown until it turns up inside the fence again
        if mph > MAX_PLAUSIBLE_MPH or current.glitch:
            current.glitch = True
            glitches += 1
            lost = True
            continue
        if lost:
            # Wherever the car went while the receiver was off inventing positions, it is
            # not the straight line back to where it turned up. Take the fix as the new
            # anchor and report the hole, rather than bank the join as ground covered
            gaps.append((previous.timestamp, current.timestamp, seconds))
            previous, lost = current, False
            continue
        # Positions are only written when they move, so a quiet stretch that stayed
        # put is the car parked; one that covered ground is a hole in the log
        if seconds > GAP_SECONDS and miles * FEET_PER_MILE > STOP_RADIUS_FT:
            gaps.append((previous.timestamp, current.timestamp, seconds))
        segments.append(Segment(previous, current, seconds, miles, mph))
        previous = current

    # A fix that joined no leg at either end is a straggler dropped on the way out of a
    # glitch or back into one: reachable on its own, but connected to nothing. Two of them
    # were enough to stretch the 2025-08-25 map to four times the ground the car covered
    joined = {id(fix) for segment in segments for fix in (segment.start, segment.end)}
    if joined:
        for fix in fixes:
            if id(fix) not in joined:
                fix.glitch = True
    # The report calls this "dropped as GPS noise" against the positions logged, so count
    # the fixes thrown away rather than the legs they failed to make
    return segments, gaps, sum(1 for fix in fixes if fix.glitch)


def find_stops(segments, city):
    """Runs of going nowhere long enough to call a stop"""
    stops = []
    run = []
    for segment in segments + [None]:
        if segment is not None and segment.mph < MOVING_MPH:
            run.append(segment)
            continue
        if run:
            seconds = (run[-1].end.timestamp - run[0].start.timestamp).total_seconds()
            if seconds >= STOP_MIN_SECONDS:
                points = [leg.start for leg in run] + [run[-1].end]
                stops.append((run[0].start.timestamp, run[-1].end.timestamp,
                              sum(point.lat for point in points) / len(points),
                              sum(point.lon for point in points) / len(points)))
        run = []
    return [Stop(start, end, (end - start).total_seconds(), lat, lon, city.address(lat, lon),
                 city.nearest_landmark(lat, lon))
            for start, end, lat, lon in merge_stops(stops)]


def merge_stops(stops):
    """Fold a stop the car nudged its way out of and straight back into"""
    merged = []
    for start, end, lat, lon in stops:
        if merged:
            last_start, last_end, last_lat, last_lon = merged[-1]
            apart = haversine_mi(lat, lon, last_lat, last_lon) * FEET_PER_MILE
            if (start - last_end).total_seconds() <= STOP_MERGE_SECONDS and apart <= STOP_MERGE_FT:
                merged[-1] = (last_start, end, (lat + last_lat) / 2.0, (lon + last_lon) / 2.0)
                continue
        merged.append((start, end, lat, lon))
    return merged


def pace(segments, start, end, step=60):
    """Speed of the car minute by minute, or None where nothing was logged"""
    span = int((end - start).total_seconds() // step)
    miles = [0.0] * span
    seconds = [0.0] * span
    for segment in segments:
        begin = (segment.start.timestamp - start).total_seconds()
        finish = (segment.end.timestamp - start).total_seconds()
        first, last = int(begin // step), int(min(finish, span * step - 1) // step)
        for index in range(max(0, first), min(span, last + 1)):
            overlap = min(finish, (index + 1) * step) - max(begin, index * step)
            if overlap <= 0:
                continue
            share = overlap / segment.seconds
            miles[index] += segment.miles * share
            seconds[index] += overlap
    series = []
    for index in range(span):
        moment = start + datetime.timedelta(seconds=index * step)
        series.append((moment, miles[index] / seconds[index] * 3600.0 if seconds[index] > 0 else None))
    return series


def calibrated_pressure(rows):
    """The pressure trace in psi, converting the seasons that were logged as raw counts

    A calibrated reading is clamped at zero and never leaves the gauge's range, so a trace
    that carries a negative or an implausibly large value is still in ADC counts.
    """
    levels = [level for level in (number(row, "level") for row in rows) if level is not None]
    raw = any(level < 0.0 or level > MAX_PLAUSIBLE_PSI for level in levels)
    if not raw:
        return rows, False
    for row in rows:
        level = number(row, "level")
        if level is None:
            continue
        row["level"] = max(level / RAW_COUNTS_PER_PSI + RAW_PSI_AT_ZERO_COUNT, 0.0)
    return rows, True


def pressure_chattering(rows):
    """Is the pressure trace oscillating faster than the accumulator could?

    A poof empties the accumulator over about a second and it recharges over tens of them,
    so a full poof's worth of step between one sample and the next is rare in a night that
    was really driven. When it is the norm the sensor is chattering and nothing can be read
    off the trace at all.
    """
    levels = [level for level in (number(row, "level") for row in rows) if level is not None]
    if len(levels) < PRESSURE_CHATTER_SAMPLES:
        return False
    steps = sum(1 for index in range(len(levels) - 1)
                if abs(levels[index + 1] - levels[index]) >= POOF_DROP_PSI)
    return steps > PRESSURE_CHATTER_FRACTION * (len(levels) - 1)


def find_poofs(rows):
    """Poofs read out of the accumulator pressure trace

    The monitor samples pressure at 10Hz around every burst, so a poof shows up as a
    sharp fall of tens of psi inside a second followed by a slow recharge.
    """
    samples = [(row["timestamp"], number(row, "level")) for row in rows]
    samples = [sample for sample in samples if sample[1] is not None]
    poofs = []
    marks = []
    peak = None
    falling = False
    bottom = None
    for index, (when, level) in enumerate(samples):
        if index and (when - samples[index - 1][0]).total_seconds() > POOF_EPISODE_GAP:
            peak, falling = (when, level), False
        if peak is None:
            peak = (when, level)
            continue
        if level >= peak[1] and not falling:
            peak = (when, level)
            continue
        if not falling:
            if peak[1] - level >= POOF_DROP_PSI and (when - peak[0]).total_seconds() <= POOF_FALL_SECONDS:
                falling, bottom = True, (when, level)
            continue
        if level < bottom[1]:
            bottom = (when, level)
        elif level > bottom[1] + POOF_RECOVERY_PSI:
            # The pressure it fell from is the supply the poofer had to draw on
            poofs.append(Poof(peak[0], peak[1] - bottom[1], (bottom[0] - peak[0]).total_seconds(), peak[1]))
            marks.append(index)
            falling, peak = False, (when, level)
    measure_recovery(poofs, marks, samples)
    return poofs


def measure_recovery(poofs, marks, samples):
    """How long the accumulator took to build back up after each poof"""
    for poof, index in zip(poofs, marks):
        target = poof.supply * POOF_RECOVERY_FRACTION
        for when, level in samples[index:]:
            elapsed = (when - poof.timestamp).total_seconds()
            if elapsed > POOF_RECOVERY_LIMIT:
                break
            if level >= target and elapsed > poof.seconds:
                poof.recovery = elapsed
                break


def locate_poofs(poofs, fixes):
    """Put each poof on the map, interpolated between the fixes either side of it"""
    if not fixes:
        return
    stamps = [fix.timestamp for fix in fixes]
    for poof in poofs:
        index = bisect.bisect_left(stamps, poof.timestamp)
        before = fixes[index - 1] if index else None
        after = fixes[index] if index < len(fixes) else None
        if before is None or after is None:
            nearest = after or before
            if abs((nearest.timestamp - poof.timestamp).total_seconds()) <= GAP_SECONDS:
                poof.lat, poof.lon = nearest.lat, nearest.lon
            continue
        span = (after.timestamp - before.timestamp).total_seconds()
        if span > GAP_SECONDS:
            # Straddling a hole in the position log, so where it happened is a guess
            continue
        share = (poof.timestamp - before.timestamp).total_seconds() / span if span else 0.0
        poof.lat = before.lat + (after.lat - before.lat) * share
        poof.lon = before.lon + (after.lon - before.lon) * share


def propane_pounds(psi_drawn, gallons, kelvin=ASSUMED_KELVIN):
    """Mass behind a total accumulator draw, given the accumulator's volume"""
    moles = psi_drawn * PASCALS_PER_PSI * gallons * CUBIC_M_PER_GALLON / (GAS_CONSTANT * kelvin)
    return moles * PROPANE_KG_PER_MOL * POUNDS_PER_KG


def bin_poofs(poofs, start, end, minutes=15):
    """Poof counts bucketed for the timeline"""
    step = datetime.timedelta(minutes=minutes)
    bins = []
    edge = start
    while edge < end:
        bins.append([edge, 0])
        edge += step
    for poof in poofs:
        index = int((poof.timestamp - start).total_seconds() // (minutes * 60))
        if 0 <= index < len(bins):
            bins[index][1] += 1
    return [(edge, count) for edge, count in bins]


def series_of(rows, column):
    """A named column as a timestamped series"""
    series = []
    for row in rows:
        value = number(row, column)
        if value is not None:
            series.append((row["timestamp"], value))
    return series


def map_for_night(night, override=None):
    """Map layers to address a night against: its own year's, unless one was asked for"""
    if override:
        return override
    layers = os.path.join(YEAR_MAPS, str(night.year), YEAR_LAYERS)
    if os.path.isdir(layers):
        return layers
    # Better the map the display is carrying than no addresses at all
    return DEFAULT_MAP


_cities = {}


def city_for(map_root):
    """The geometry of a map directory, read once however many nights are reported on"""
    if map_root not in _cities:
        _cities[map_root] = BlackRockCity(map_root)
    return _cities[map_root]


def build_report(data_root, map_root, night, accumulator_gallons=None):
    """Everything worth saying about one night"""
    start, end = night_window(night)
    city = city_for(map_root)
    positions = load_stream(data_root, "positions", start, end)
    fixes = collect_fixes(positions)
    on_playa = bool(fixes) and city.contains(
        statistics.median([fix.lat for fix in fixes]), statistics.median([fix.lon for fix in fixes]))
    # Only a playa night has a fence to be outside of; a shakedown at home ranges anywhere
    if on_playa:
        mark_off_map(fixes, city)
    segments, gaps, glitches = build_segments(fixes)
    stops = find_stops(segments, city)

    pressure, calibrated = calibrated_pressure(load_stream(data_root, "pressure", start, end))
    # A chattering sensor reads as thousands of poofs a night, so say nothing rather than that
    chattering = pressure_chattering(pressure)
    poofs = [] if chattering else find_poofs(pressure)
    locate_poofs(poofs, fixes)
    for poof in poofs:
        for stop in stops:
            if stop.start <= poof.timestamp <= stop.end:
                poof.parked = True
                stop.poofs += 1
                break

    temperature = load_stream(data_root, "temp", start, end)
    heading = load_stream(data_root, "heading", start, end)

    return Report(
        night=night, start=start, end=end, city=city, on_playa=on_playa,
        fixes=fixes, segments=segments, stops=stops, poofs=poofs,
        speed_series=pace(segments, start, end),
        poof_bins=bin_poofs(poofs, start, end),
        temperature=series_of(temperature, "temp_f"),
        gaps=gaps, glitches=glitches, calibrated=calibrated, chattering=chattering,
        # A correction is days, not months, so a corrected night is still in its own season
        clock_shift=CLOCK_CORRECTIONS.get(night.year),
        accumulator_gallons=accumulator_gallons,
        counts={"positions": len(positions), "pressure": len(pressure), "heading": len(heading),
                "temp": len(temperature)})


def main():
    parser = argparse.ArgumentParser(
        description="Summarise a night of driving from the sensor monitor logs")
    parser.add_argument("--night", help="night to report on, as YYYY-MM-DD (defaults to the most recent)")
    parser.add_argument("--data", default=DEFAULT_DATA, help="sensor monitor log directory")
    parser.add_argument("--map", help="map layers to use for every night, instead of each year's own")
    parser.add_argument("--output", help="file to write (defaults to excursion_<night>.html beside this script)")
    parser.add_argument("--fragment", action="store_true", help="emit the body only, without the page wrapper")
    parser.add_argument("--all", action="store_true",
                        help="report on every night that has data, and write an index over them")
    parser.add_argument("--playa-only", action="store_true",
                        help="with --all, skip the shakedowns and keep the nights out on the playa")
    parser.add_argument("--links", help="JSON map of YYYY-MM-DD to URL, for an index over published copies")
    parser.add_argument("--accumulator-gallons", type=float,
                        help="volume of the poofer accumulator, to report the draw as pounds of propane")
    parser.add_argument("--list", action="store_true", help="list the nights that have data and exit")
    arguments = parser.parse_args()

    if not os.path.isdir(arguments.data):
        raise SystemExit("no log directory at %s -- point --data at the sensor monitor logs" % arguments.data)

    if arguments.list or arguments.all or not arguments.night:
        nights = available_nights(arguments.data)
        if not nights:
            raise SystemExit("no position data found in %s" % arguments.data)
        if arguments.list:
            for night in sorted(nights):
                print("%s  %6d fixes" % (night, nights[night]))
            return
    else:
        nights = None

    if arguments.all:
        report_all(arguments, sorted(nights, reverse=True))
        return

    night = max(nights) if nights else datetime.datetime.strptime(arguments.night, "%Y-%m-%d").date()
    report = build_report(arguments.data, map_for_night(night, arguments.map), night,
                          arguments.accumulator_gallons)
    if not report.fixes:
        raise SystemExit("no positions logged for the night of %s" % night)

    output = arguments.output or os.path.join(HERE, report_name(night))
    with open(output, "w") as handle:
        handle.write(report_render.render(report, fragment=arguments.fragment))
    print("%s -- %.1f miles, %d stops, %d poofs" % (output, report.miles, len(report.stops), len(report.poofs)))


def report_name(night):
    """File a night's report is written to"""
    return "excursion_%s.html" % night.strftime("%Y%m%d")


def report_all(arguments, nights):
    """One report per night, plus an index over the lot"""
    directory = arguments.output or HERE
    if not os.path.isdir(directory):
        raise SystemExit("--output must be a directory when reporting on every night")
    links = {}
    if arguments.links:
        with open(arguments.links) as handle:
            links = json.load(handle)
    summaries = []
    for night in nights:
        report = build_report(arguments.data, map_for_night(night, arguments.map), night,
                              arguments.accumulator_gallons)
        if not report.fixes:
            print("%s -- skipped, nothing logged" % night)
            continue
        if arguments.playa_only and not report.on_playa:
            print("%s -- skipped, not on the playa" % night)
            continue
        name = report_name(night)
        suffix = "_artifact" if arguments.fragment else ""
        with open(os.path.join(directory, name.replace(".html", suffix + ".html")), "w") as handle:
            handle.write(report_render.render(report, fragment=arguments.fragment))
        summaries.append(report_render.summarize(report, links.get(str(night), name)))
        print("%s -- %.1f miles, %d stops, %d poofs" % (name, report.miles, len(report.stops), len(report.poofs)))
    if not summaries:
        raise SystemExit("no night had anything to report on")
    index = os.path.join(directory, "index_fragment.html" if arguments.fragment else "index.html")
    with open(index, "w") as handle:
        handle.write(report_render.render_index(summaries, fragment=arguments.fragment))
    print("%s -- %d nights" % (index, len(summaries)))


if __name__ == "__main__":
    main()
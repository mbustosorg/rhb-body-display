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

"""Writes the two places of our own onto each season's map layers

    python3 mark_places.py

The camp is the corner of 9:45 and F, which every season's KML names outright. The burn is
the far end of the 9:30 line -- the outermost point of the radial itself, where the drawn
street stops, not the trash fence out beyond it. Those are a long way apart: the 9:30 line
ends around 5,830 ft in 2022 and 6,785 in 2024, while the fence on that bearing is at
8,160 and 8,415. The city is surveyed afresh every year, so both marks are resolved per
season rather than carried over.
"""

import argparse
import csv
import io
import math
import os
import zipfile

from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
KML = {"b": "http://www.opengis.net/kml/2.2"}
SOURCES = ("brc.kml", "brc-kml/brc.kml", "brc.kmz", "brc.zip")
SEASONS = (2022, 2023, 2024, 2025, 2026)
DESTINATION = os.path.join("layers", "places.csv")

CAMP_INTERSECTION = "9:45&F"
BURN_RADIAL = "9:30"


def source(year):
    for name in SOURCES:
        path = os.path.join(HERE, str(year), name)
        if os.path.exists(path):
            return path
    raise SystemExit("no map source for %d" % year)


def parse(path):
    if path.endswith((".kmz", ".zip")):
        with zipfile.ZipFile(path) as archive:
            inner = next(name for name in archive.namelist() if name.endswith(".kml"))
            return etree.parse(io.BytesIO(archive.read(inner))).getroot()
    return etree.parse(path).getroot()


def points_of(element):
    found = []
    for text in element.xpath(".//b:coordinates/text()", namespaces=KML):
        for token in text.split():
            parts = token.split(",")
            if len(parts) >= 2:
                found.append((float(parts[0]), float(parts[1])))
    return found


def man_of(year):
    path = os.path.join(HERE, str(year), "layers", "man_ring.csv")
    ring = [(float(row[0]), float(row[1])) for row in csv.reader(open(path)) if len(row) >= 2]
    return sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)


def places(year):
    root = parse(source(year))
    man_lon, man_lat = man_of(year)
    stretch = math.cos(math.radians(man_lat))

    def feet(point):
        return math.hypot((point[1] - man_lat) * 364000.0, (point[0] - man_lon) * 364000.0 * stretch)

    found = []
    corner = root.xpath('.//b:Placemark[b:name="%s"]' % CAMP_INTERSECTION, namespaces=KML)
    if corner:
        lon, lat = points_of(corner[0])[0]
        found.append(("camp", "star", lon, lat, feet((lon, lat))))

    radial = root.xpath('.//b:Placemark[b:name="%s"]' % BURN_RADIAL, namespaces=KML)
    if radial:
        # The end of the line as drawn. Casting on out to the fence was tried and is not
        # what is wanted: the fence is a mile or so further than the street ever goes
        out = max(points_of(radial[0]), key=feet)
        found.append(("burn", "flame", out[0], out[1], feet(out)))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, help="one season, instead of every one")
    arguments = parser.parse_args()
    for year in ((arguments.year,) if arguments.year else SEASONS):
        found = places(year)
        path = os.path.join(HERE, str(year), DESTINATION)
        with open(path, "w", newline="") as handle:
            writer = csv.writer(handle)
            for name, glyph, lon, lat, _ in found:
                writer.writerow([name, glyph, "%.7f" % lon, "%.7f" % lat])
        print("%s -- %s" % (path, ", ".join("%s %s at %s ft"
                                            % (n, g, format(int(round(d, -1)), ","))
                                            for n, g, _, _, d in found)))


if __name__ == "__main__":
    main()

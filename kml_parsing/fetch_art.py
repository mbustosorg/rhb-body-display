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

"""Pulls the placed art for a season out of Burning Man's open data and lays it beside the
map layers, so a night's stops can be told what they were parked next to

    python3 fetch_art.py --year 2024
    python3 fetch_art.py            # every season the report covers

The archive is public and needs no key. Only the name and the position are kept: the rest
of each record is description, images and contact details the report has no use for. About
one piece in twenty is registered without coordinates and is dropped, since a piece that
cannot be placed cannot label anything.

    https://innovate.burningman.org/datasets-page/
"""

import argparse
import csv
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = "https://bm-innovate.s3.amazonaws.com/archive/%d/art.json"
DESTINATION = os.path.join("layers", "art.csv")
SEASONS = (2022, 2023, 2024, 2025, 2026)


# Registrations that were never given a position carry 0.0, 0.0 rather than nothing, which
# is a point in the Atlantic. Test entries sit there too. A piece has to be in the desert
BLACK_ROCK = (40.0, 41.5, -120.5, -118.5)  # min lat, max lat, min lon, max lon


def placed(records):
    """Name and position of every piece the archive puts on the playa"""
    min_lat, max_lat, min_lon, max_lon = BLACK_ROCK
    for record in records:
        location = record.get("location") or {}
        lat, lon = location.get("gps_latitude"), location.get("gps_longitude")
        name = (record.get("name") or "").strip()
        if not name or lat is None or lon is None:
            continue
        lat, lon = float(lat), float(lon)
        if min_lat < lat < max_lat and min_lon < lon < max_lon:
            yield name, lon, lat


def fetch(year):
    with urllib.request.urlopen(ARCHIVE % year, timeout=90) as response:
        return json.load(response)


def write(year, rows):
    directory = os.path.join(HERE, str(year), "layers")
    if not os.path.isdir(directory):
        raise SystemExit("no layers directory for %d -- run read_xml.py --year %d first"
                         % (year, year))
    path = os.path.join(HERE, str(year), DESTINATION)
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        for name, lon, lat in sorted(rows):
            writer.writerow([name, "%.7f" % lon, "%.7f" % lat])
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, help="one season, instead of every one")
    arguments = parser.parse_args()
    for year in ((arguments.year,) if arguments.year else SEASONS):
        records = fetch(year)
        rows = list(placed(records))
        path = write(year, rows)
        print("%s -- %d of %d pieces placed" % (path, len(rows), len(records)))


if __name__ == "__main__":
    main()

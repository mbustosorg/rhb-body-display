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

import argparse
import io
import math
import os
import zipfile

import lxml.etree

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = '../rhbbodydisplay/data/brc.kml'
DESTINATION = '../rhbbodydisplay/data/'
KML = {'b': 'http://www.opengis.net/kml/2.2'}
GPX = 'http://www.topografix.com/GPX/1/0'
# A season's map has been filed under its year in a few shapes over the years
YEAR_SOURCES = ('brc.kml', 'brc-kml/brc.kml', 'brc.kmz', 'brc.zip')
# Layers for a past season are generated beside the KML they came from, rather than
# over the top of the ones the display is currently carrying
YEAR_DESTINATION = 'layers'


def load(path):
    """Parse the map, transparently unwrapping a .kmz archive"""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            name = next(n for n in archive.namelist() if n.endswith('.kml'))
            root = lxml.etree.parse(io.BytesIO(archive.read(name)))
    else:
        root = lxml.etree.parse(path)
    namespace = lxml.etree.QName(root.getroot()).namespace
    if namespace == GPX:
        raise SystemExit(f'{path} is a GPX track, not a KML map. '
                         'The KML is inside the matching brc.kmz archive.')
    if namespace != KML['b']:
        raise SystemExit(f'{path} is not KML (root namespace {namespace})')
    return root


def placemarks(root, folder, condition='true()'):
    """Placemarks of the given folder, narrowed by an optional name condition"""
    return root.xpath(f'./b:Document/b:Folder[b:name="{folder}"]/b:Placemark[{condition}]',
                      namespaces=KML)


def sections(placemark):
    """Every coordinate run of a placemark, as lists of "longitude,latitude" strings"""
    return [section.text.split()
            for section in placemark.findall('.//b:coordinates', namespaces=KML)]


def outer_street(root):
    """Initial of the outermost lettered street, read off the 10:00 intersections.
    It is renamed every year (Kelter in 2024, Kundalini in 2026) so it cannot be matched
    by name, and the city has not always run out to the same letter -- 2019 reached L --
    so take the furthest one the map actually names rather than assuming K"""
    letters = [name.split('&')[1] for name in
               root.xpath('./b:Document/b:Folder[b:name="Intersections"]/b:Placemark/b:name/text()',
                          namespaces=KML)
               if name.startswith('10:00&')]
    letters = [letter for letter in letters if len(letter) == 1 and letter.isalpha()]
    if not letters:
        raise SystemExit('no lettered 10:00 intersections in the map, so the outer street is unknown')
    return max(letters)


def write(destination, name, runs, separate=False):
    """Write coordinate runs, optionally leaving a blank line between them"""
    with open(os.path.join(destination, name), 'w') as file:
        for run in runs:
            for coordinate in run:
                lon, lat = coordinate.split(',')[:2]
                file.write(f'{lon},{lat}\n')
            if separate:
                file.write('\n')


def centroid(run):
    """Mean position of a coordinate run"""
    points = [tuple(map(float, c.split(',')[:2])) for c in run]
    return (sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points))


def intersection(root, name):
    """Position of a named street intersection"""
    return centroid(sections(placemarks(root, 'Intersections', f'b:name="{name}"')[0])[0])


def street(root, condition, anchor):
    """The single street matching the condition, drawn outwards from the anchor intersection.
    The sketch chains these four files into one closed city boundary, so their direction
    matters and the map does not always digitize them the same way from year to year"""
    run = [coordinate for placemark in placemarks(root, 'Streets', condition)
           for section in sections(placemark) for coordinate in section]
    start = intersection(root, anchor)
    if math.dist(centroid([run[0]]), start) > math.dist(centroid([run[-1]]), start):
        run.reverse()
    return [run]


def convert(source, destination):
    """Write every layer the display and the reports read out of one season's map"""
    root = load(source)
    outer = outer_street(root)
    os.makedirs(destination, exist_ok=True)

    streets = placemarks(root, 'Streets')
    # The fence is published both at the top level and inside "Boundries", so keep the first only
    fences = root.xpath('./b:Document//b:Placemark[b:name="Fence"]', namespaces=KML)[:1]
    write(destination, 'lines.csv',
          [run for placemark in streets + fences for run in sections(placemark)],
          separate=True)

    write(destination, 'toilets.csv',
          [run for placemark in placemarks(root, 'Toilets') for run in sections(placemark)])
    write(destination, 'first_aid.csv',
          [run for placemark in placemarks(root, 'POIs', 'contains(b:name,"First")')
           for run in sections(placemark)])
    write(destination, 'ranger.csv',
          [run for placemark in placemarks(root, 'POIs', 'contains(b:name,"Ranger")')
           for run in sections(placemark)])

    write(destination, '10_00.csv', street(root, 'b:name="10:00"', f'10:00&{outer}'))
    write(destination, '2_00.csv', street(root, 'b:name="2:00"', f'2:00&{outer}'))
    write(destination, 'city_bounds.csv', street(root, 'contains(b:name,"Esplanade")', '10:00&Esp'))
    write(destination, 'kelter.csv',
          street(root, f'starts-with(b:name,"{outer}")', f'10:00&{outer}'))

    # The ring around the Man is the unnamed plaza centred on him
    man = centroid(sections(placemarks(root, 'POIs', 'b:name="The Man"')[0])[0])
    rings = [run for placemark in placemarks(root, 'Plazas') for run in sections(placemark)]
    write(destination, 'man_ring.csv',
          [min(rings, key=lambda run: math.dist(centroid(run), man))])
    return outer


def year_source(year):
    """The map filed under a season's year, whichever shape it was saved in"""
    for name in YEAR_SOURCES:
        path = os.path.join(HERE, year, name)
        if os.path.exists(path):
            return path
    raise SystemExit(f'no map under {os.path.join(HERE, year)} -- looked for ' + ', '.join(YEAR_SOURCES))


def main():
    parser = argparse.ArgumentParser(
        description="Convert a season's BRC map into the layers the display and reports read")
    parser.add_argument('--year', help='a season filed under kml_parsing, written to its layers directory')
    parser.add_argument('--source', help='KML, KMZ or zipped map to read')
    parser.add_argument('--destination', help='directory to write the layers to')
    arguments = parser.parse_args()

    if arguments.year:
        source = arguments.source or year_source(arguments.year)
        destination = arguments.destination or os.path.join(HERE, arguments.year, YEAR_DESTINATION)
    else:
        source = arguments.source or SOURCE
        destination = arguments.destination or DESTINATION

    outer = convert(source, destination)
    print(f'{source} -> {destination} (outer street {outer})')


if __name__ == '__main__':
    main()
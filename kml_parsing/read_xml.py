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

import io
import math
import zipfile

import lxml.etree

SOURCE = '../rhbbodydisplay/data/brc.kml'
DESTINATION = '../rhbbodydisplay/data/'
KML = {'b': 'http://www.opengis.net/kml/2.2'}
GPX = 'http://www.topografix.com/GPX/1/0'
# The outermost lettered street is renamed every year (Kelter in 2024, Kundalini in 2026),
# so it is matched by its initial rather than by name
OUTER_STREET = 'K'


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


def write(name, runs, separate=False):
    """Write coordinate runs, optionally leaving a blank line between them"""
    with open(DESTINATION + name, 'w') as file:
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


root = load(SOURCE)

streets = placemarks(root, 'Streets')
# The fence is published both at the top level and inside "Boundries", so keep the first only
fences = root.xpath('./b:Document//b:Placemark[b:name="Fence"]', namespaces=KML)[:1]
write('lines.csv',
      [run for placemark in streets + fences for run in sections(placemark)],
      separate=True)

write('toilets.csv',
      [run for placemark in placemarks(root, 'Toilets') for run in sections(placemark)])
write('first_aid.csv',
      [run for placemark in placemarks(root, 'POIs', 'contains(b:name,"First")')
       for run in sections(placemark)])
write('ranger.csv',
      [run for placemark in placemarks(root, 'POIs', 'contains(b:name,"Ranger")')
       for run in sections(placemark)])


def intersection(name):
    """Position of a named street intersection"""
    return centroid(sections(placemarks(root, 'Intersections', f'b:name="{name}"')[0])[0])


def street(condition, anchor):
    """The single street matching the condition, drawn outwards from the anchor intersection.
    The sketch chains these four files into one closed city boundary, so their direction
    matters and the map does not always digitize them the same way from year to year"""
    run = [coordinate for placemark in placemarks(root, 'Streets', condition)
           for section in sections(placemark) for coordinate in section]
    start = intersection(anchor)
    if math.dist(centroid([run[0]]), start) > math.dist(centroid([run[-1]]), start):
        run.reverse()
    return [run]


write('10_00.csv', street('b:name="10:00"', f'10:00&{OUTER_STREET}'))
write('2_00.csv', street('b:name="2:00"', f'2:00&{OUTER_STREET}'))
write('city_bounds.csv', street('contains(b:name,"Esplanade")', '10:00&Esp'))
write('kelter.csv', street(f'starts-with(b:name,"{OUTER_STREET}")', f'10:00&{OUTER_STREET}'))

# The ring around the Man is the unnamed plaza centred on him
man = centroid(sections(placemarks(root, 'POIs', 'b:name="The Man"')[0])[0])
rings = [run for placemark in placemarks(root, 'Plazas') for run in sections(placemark)]
write('man_ring.csv',
      [min(rings, key=lambda run: math.dist(centroid(run), man))])
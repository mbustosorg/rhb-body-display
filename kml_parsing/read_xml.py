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

import lxml.etree
root = lxml.etree.parse('../rhbbodydisplay/data/brc.kml')
namespaces = {'b' : 'http://www.opengis.net/kml/2.2'}
with open('../rhbbodydisplay/data/lines.csv', 'w') as file:
    file.write("Streets\n")
    for item in root.findall('./b:Document/b:Folder/b:name[.="Streets"]...', namespaces=namespaces):
        for section in item.findall('b:Placemark/b:MultiGeometry/b:LineString/b:coordinates', namespaces=namespaces):
            for coordinate in section.text.split(' '):
                lat, lon = coordinate.split(',')
                file.write(coordinate + '\n')
    file.write('Fence\n')
    for item in root.findall('./b:Document/b:Folder//b:name[.="Fence"]...', namespaces=namespaces):
        for section in item.findall('b:MultiGeometry/b:LineString/b:coordinates', namespaces=namespaces):
            for coordinate in section.text.split(' '):
                lat, lon = coordinate.split(',')
                file.write(coordinate + '\n')
with open('../rhbbodydisplay/data/points.csv', 'w') as file:
    file.write('Toilets\n')
    for item in root.findall('./b:Document/b:Folder//b:name[.="Toilets"]...', namespaces=namespaces):
        for section in item.findall('b:Placemark/b:Point/b:coordinates', namespaces=namespaces):
            for coordinate in section.text.split(' '):
                lat, lon = coordinate.split(',')
                file.write(coordinate + '\n')
    file.write('First Aid\n')
    for item in root.xpath('./b:Document/b:Folder//b:name[contains(text(),"First")]/..', namespaces=namespaces):
        for section in item.xpath('./b:Point/b:coordinates', namespaces=namespaces):
            for coordinate in section.text.split(' '):
                lat, lon = coordinate.split(',')
                file.write(coordinate + '\n')

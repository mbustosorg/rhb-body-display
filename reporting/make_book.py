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

"""Builds the printed book: one spread a night, gathered by season, and a PDF of it

    python3 make_book.py                  # book.html and Red Hot Beverly v<edition>.pdf
    python3 make_book.py --no-pdf         # just the HTML, to look at in a browser
"""

import argparse
import os
import subprocess
import sys

import book_render
import excursion_report as report_lib

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HTML = os.path.join(HERE, "book.html")
DEFAULT_PDF = os.path.join(HERE, "%s v%s.pdf" % (book_render.TITLE, book_render.EDITION.split()[-1]))

# Chrome renders the @page size and the fixed page boxes faithfully; nothing else on hand does
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_FALLBACKS = (
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
)


def browser():
    for path in (CHROME,) + CHROME_FALLBACKS:
        if os.path.exists(path):
            return path
    return None


def gather(data_root, map_override=None):
    """Every playa night, oldest first -- the shakedowns are not part of the book"""
    reports = []
    for night in sorted(report_lib.available_nights(data_root)):
        report = report_lib.build_report(
            data_root, report_lib.map_for_night(night, map_override), night)
        if not report.fixes or not report.on_playa:
            continue
        reports.append(report)
        print("  %s  %5.1f mi  %4d poofs" % (night, report.miles, len(report.poofs)))
    return reports


def to_pdf(html_path, pdf_path):
    """Print the book through headless Chrome, which honours the page boxes"""
    engine = browser()
    if engine is None:
        raise SystemExit("no Chrome to print with -- pass --no-pdf and print the HTML yourself")
    # A stale PDF left in place would read as success if Chrome fell over
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    # --no-pdf-header-footer keeps Chrome's own furniture off; the book carries its own
    command = [engine, "--headless", "--disable-gpu", "--no-pdf-header-footer",
               "--print-to-pdf=%s" % pdf_path, "--virtual-time-budget=20000",
               "file://%s" % html_path]
    finished = subprocess.run(command, capture_output=True, text=True)
    if not os.path.exists(pdf_path):
        sys.stderr.write(finished.stderr or "")
        raise SystemExit("Chrome did not write a PDF")
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=report_lib.DEFAULT_DATA, help="sensor monitor log directory")
    parser.add_argument("--map", help="map layers to use for every night, instead of each year's own")
    parser.add_argument("--html", default=DEFAULT_HTML, help="where to write the book HTML")
    parser.add_argument("--pdf", default=DEFAULT_PDF, help="where to write the PDF")
    parser.add_argument("--no-pdf", action="store_true", help="write the HTML and stop there")
    arguments = parser.parse_args()

    if not os.path.isdir(arguments.data):
        raise SystemExit("no log directory at %s" % arguments.data)

    print("Gathering the playa nights")
    reports = gather(arguments.data, arguments.map)
    if not reports:
        raise SystemExit("no playa night had anything to report on")

    html = book_render.render_book(reports)
    with open(arguments.html, "w") as handle:
        handle.write(html)
    print("\n%s -- %d nights over %d pages" % (arguments.html, len(reports), html.count('<div class="page')))

    if arguments.no_pdf:
        print("Open it in Chrome and print with margins set to None to get the PDF.")
        return
    to_pdf(arguments.html, arguments.pdf)
    print("%s" % arguments.pdf)


if __name__ == "__main__":
    main()

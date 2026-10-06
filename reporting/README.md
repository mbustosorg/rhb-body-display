After Excursion Report
======================

Summarises one night of driving as a single self contained HTML page: where the car
went, where it stopped, how much the poofer fired and what the rest of the systems
had to say for themselves.

    python3 excursion_report.py --list
    python3 excursion_report.py --night 2024-08-28
    python3 excursion_report.py --all

The report lands beside the script as `excursion_<night>.html` and opens in any
browser -- everything, including the charts, is inline, so it can be handed round
off playa without a server. `--all` reports on every night that has data and writes
an `index.html` over the lot, which is the one to hand round.

A night is the 24 hours from 5pm, so an outing that rolls out before dark or comes home
after lunch is not cut off at either end. Pass `--night` the evening date.

The book
--------

    python3 make_book.py

Gathers every playa night -- the shakedowns are not part of it -- and lays them out as a
printed book, `book.html` beside the script and `Red Hot Beverly.pdf` next to it.
US Letter portrait. Seasons run forwards, 2022 first, each opening on a right hand page
behind a divider carrying the year's totals.

The seasons are gathered by car, as `PARTS` in `book_render.py` sets out: everything up
to 2025 is Red Hot Beverly 1.0 and everything from 2026 is Red Hot Beverly 2.0. Each part
opens on its own divider with that car's totals, and the contents is grouped the same way.
The book carries no edition number of its own -- the title page is dated with the day it
was built instead.

A night is two spreads. The first is where it went: the route map on the left with the
speed key, and facing it the night's figures, its speed trace and its poofs per quarter
hour. The second is where it poofed: the density map on the left, and facing it the
propane, the tub water and the full stop list. Both maps get nearly a page each and are
close to square.

**Tub water is drawn where the probe was telling the truth.** Water in a tub in the desert
in August does not approach freezing: 2023 never reads below 57F and 2025 never below 54,
but 2022 runs continuously down to exactly 32.0 -- zero Celsius, clamped -- with half its
readings under 50 on nights that also claim 109. Readings under 50F are dropped as probe
error and the page says how many; a night that loses more than half of them is reported as
unusable rather than drawn full of holes. Of the twenty five nights, thirteen get a trace,
two are set aside that way, and ten never logged the stream at all -- the whole of 2024
among them.

Five of the twenty five nights never fired the poofer, so there is nothing for the second
spread to carry; those nights keep the old two page shape and their stops move up onto the
numbers page. Page counts stay even either way, which is what keeps every map on a verso
facing its own numbers.

Nothing reflows. Every page is laid out at its finished size, so the page a thing lands
on is known while the book is being built and can be numbered and put in the contents.
That is also why the spread works: a night's first page is forced onto a verso, because
a map on a recto would face its own numbers across a leaf, where they can never be seen
together.

The PDF is printed through headless Chrome, which is the only thing to hand that honours
a fixed page box. `--no-pdf` stops at the HTML if you would rather print it yourself --
open it in Chrome, set margins to None and leave background graphics on. Colour is
forced to print with `print-color-adjust`, without which Chrome quietly drops the cream
off the cover and the dividers and the red out of the brandmark.

The book is the logs
--------------------

Two written pieces were built and are not assembled in: the night the car spent at the
art piece its crew put up, and the night the licence went. Both are still in
`book_render.py` behind `INCLUDE_NARRATIVE`, which is `False`. Turn it on and they come
back, the contents makes room for them and the page count goes from 105 to 107.

What is left is the logs and what can be derived from them. The season summaries are
arithmetic over the nights, the captions name what the colours mean, and the colophon
explains the reckoning. Nothing in the book asserts anything the sensors did not record.

Where the numbers come from
---------------------------

Sensor logs are read from the sibling `rhb-sensor-monitor` checkout, either as loose
CSVs or straight out of the season archives (`positions_2024.zip` and friends). Point
`--data` somewhere else to report on logs copied off the Pi. The monitor used to roll a
file an hour (`positions_20220819_03.csv`) and now rolls one whenever it restarts
(`positions_20250724_13_08.csv`); both names are read.

**The clock is corrected where the Pi had none.** Without a realtime clock it booted to
wherever the clock had been left, so an early season is stamped in its own drifted time.
2022 came back thirteen days behind, and `CLOCK_CORRECTIONS` puts it back. The anchor is
the burn: on the night the log calls 2022-08-21 the car crosses inside the perimeter at
23:19 and parks 897 ft from the Man, which cannot happen until he is down, and it is also
that season's longest drive, heaviest poofing and most time at the Man -- so it is
Saturday 3 September 2022. The correction lands all five playa nights inside the event,
the Temple on the Sunday and the drive home on the Tuesday. The Pi was off for the drive
each way and its clock lost those hours too, so the shift is exact only between them and
the Oakland nights either side are right to within about half a day.

Since 2026 the Pi comes up with its clock about seven hours fast -- the UTC time read as
if it were Pacific -- until the first GPS fix sets it right, a second or two later. The
fix shows in each log file as the time going backwards between one row and the next, and
the rows before it are put back by the size of that step, timed on the heading stream,
which is logged ten times a second. It is a handful of rows a night, but one of them is a
pressure reading, and stamped seven hours late it landed among the dregs of the tank at
dawn and made nine poofs on 2026-08-30 that never happened.

Each night is addressed against the map of the year it was driven, taken from
`kml_parsing/<year>/layers`, falling back to whatever the display is carrying in
`rhbbodydisplay/data` for a year with no map. This matters more than it sounds: the
city is surveyed afresh every year and does not land in the same place twice, and the
Man moved some 600 yards between 2025 and 2026 -- further than the gap between two
rings. Addressing the 2024 nights on the 2026 map pushed them 1,200 ft too far out,
some beyond the trash fence. `--map` overrides the lot with one directory.

The clock frame is read off the 2:00 and 10:00 radials rather than assumed. Run
`python3 read_xml.py --year 2024` in `kml_parsing` to build a season's layers from
its official KML; with no arguments it writes the layers the display itself draws.

**Stops are named after the art they were parked at.** `python3 fetch_art.py` in
`kml_parsing` pulls each season's placed art out of Burning Man's open data and writes
`<year>/layers/art.csv` -- name, longitude, latitude, and nothing else of the record. A
stop within 300 ft of a piece is labelled with it, and a piece beats a row of portos even
when the portos are closer, because art is somewhere the car went on purpose. The distance
is printed beside the name, so 47 ft reads as parked at it and 280 ft reads as merely the
nearest thing that had a name. Of the 130 stops in the book, 78 get named.

Two things about that data are worth knowing. Roughly one piece in twenty is registered
without coordinates, and a further handful carry `0.0, 0.0` -- including entries called
"Test Art Title" and "testarooney" -- so `fetch_art.py` keeps only what falls inside the
Black Rock Desert. And the camps file, which has far more rows, carries no coordinates at
all: only a street address like `D & 5:15`, of which about half resolve against the KML's
intersections and then only to a corner rather than to the camp. Art was worth using and
camps were not.

* **Distance and speed** are computed between consecutive fixes. The ceiling is the
  car's, not the receiver's: Beverly tops out around 10 mph on open playa, so anything
  implying more than 12 mph is something the vehicle cannot do, however confident the fix
  looks, and it is dropped and counted in the tiles. This used to be 45 mph, which was
  only ever a guard against gross jumps -- it let a 43 mph sample stand on the night the
  licence was pulled, on a log belonging to a car that cannot reach half of that. Bringing
  it down costs 2022, 2023 and 2024 about a tenth of a mile between them; it takes 4.8
  miles off 2025-08-25 and 6.0 off 2025-08-28, which is where that season's receiver spent
  whole minutes reporting 20 mph and more.
* **2022's latitude was made up by the monitor, and is rebuilt from its anchors.** The
  2022 monitor logged the GPS latitude only on the first row after it started or rolled
  to a new hourly file; every row after that it logged the previous row's latitude plus
  exactly 0.00001 degrees, whatever the receiver said (removed from the monitor in
  `256057d`). It compared the next fix against that invented value, so once the two were
  180 ft apart every fix was logged, twice a second, each one 3.6 ft further north: a
  straight run north at 5 mph until the hour turned. That is the "receiver" that used to
  be blamed for setting off across the playa. 99% of 2022's rows were logged that way.
  Longitude and altitude were real. The true latitude survives only at each file's first
  row, so those are the anchors. Between them the north-south movement is reckoned from
  the compass: each leg's real east-west step and the compass's course give its north
  step, and every hour is bent to land on the next anchor. The van's compass is poor --
  its steel and engine swamp the earth's field, so a full turn moves it only about 75
  degrees, and it cannot tell north-east from south-east -- so it is read through a table
  of what it says for each true course, measured on 2023 where the GPS was honest, and
  shifted 20 degrees for the 2022 sensor. Scored on 2023 with all but one fix an hour
  hidden, it put the typical point 535 ft from the truth against 581 for a straight line
  between anchors, and the worst tenth 2,398 ft against 3,097. Snapping to streets was
  tried as well and did worse than either, since so much of the driving is open playa.
  `STEPPED_LATITUDE_RECKONING = False` goes back to straight lines. A file is recognised
  by its steps rather than its year: all 140 of 2022's do it and none of the later
  seasons'.
* **Nothing outside the trash fence was the car.** On a night out on the playa a fix
  beyond the edge of the map is dropped. It was written for the 2022 runs north, which
  ended two and three times further out than the fence; with those rebuilt it is a guard
  that should not fire.
* **0.5 mph is the line between moving and not**, and distance, rolling time and
  stops all hang off it. A parked receiver wanders a few metres a minute, which
  reads as a tenth of a mile an hour; counting that as travel had a night in the
  yard reporting 1.3 miles the car never drove.
* **Stops** are runs of at least five minutes below that line. Two stops separated
  by less than five minutes that end up within 300 ft of each other are folded
  together, so nudging forward in a crowd stays one stop. Because positions are
  only logged when they change, a long silence that did not move is a stop, while
  one that covered ground is reported as a gap in the position log.
* **Poofs** are read out of the accumulator pressure trace, which the monitor samples
  at 10Hz around every burst: a poof is a fall of at least 5 psi inside three seconds
  followed by a recharge. The on-car counter is not persisted, so this is a
  reconstruction rather than a readback. The fall is measured from the highest reading
  of the three seconds before it. It used to be measured from the highest since the
  last poof, which was never beaten again once a tank started to run down and every
  recharge topped out lower: 2026-09-05 stopped counting at 23:24 with ninety minutes
  of poofing still to come. Fixing it took the book from 7,656 poofs to 9,559, and
  nearly every night gained some.
* **The pressure trace is calibrated where the monitor logged it raw.** Until midway
  through 2023 the accumulator went into the log as raw ADS1115 counts and was only
  converted for the display; after that the monitor logged psi. The 2022 season is all
  counts, and reading them as psi turned sensor noise into 97,595 poofs on one night.
  A trace that goes negative or leaves the gauge's range is still in counts and gets the
  monitor's own conversion, `raw / 200 + 10` clamped at zero -- which puts the idle
  readings around -2,000 counts at exactly 0 psi, as they should be.
* **A chattering sensor reports nothing rather than a number.** On the drive up in 2022
  and the night after, the sensor sat flipping between two readings about five psi apart
  ten times a second, which is electrics and not gas: no accumulator moves that fast, and
  the accumulator was never charged past 14 psi either. Read literally it made 39,064
  poofs on a night the poofer was off. When a full poof's worth of step falls between
  more than one sample pair in fifty, the night is left without a poof count and the page
  says why. A real night runs well under one in a hundred.
* **Propane** is inferred, not measured. Every poof empties part of a fixed-volume
  accumulator, so by the gas law the pressure it draws is proportional to the mass
  released; adding the drops up gives the usage curve. Turning that into pounds needs
  the accumulator's volume, which nothing in the logs records, so pass
  `--accumulator-gallons` to get a mass and treat it as only as good as that number.
* **The gauge is supply pressure, not tank level.** Nothing on the car measures how
  much propane is left. What it does show is the pressure the accumulator recovers to
  between poofs, which sags as the tank empties or goes cold under heavy draw. Rising
  recharge times through the night corroborate it -- on 2024-08-26 the supply fell
  43 to 30 psi while recharge went 19s to 34s.
* **Poof positions** are interpolated from the fixes either side of each poof. Positions
  are only logged when the car moves, so a long silence between two fixes in the same
  place is the car parked, and a poof in it is put where the car stood -- without that,
  2026-08-30 lost 303 of its poofs off the map, most of them fired standing still. Poofs
  that fired inside a silence that covered ground are left off the density map, and the
  legend says how many.
* **Tub water** comes from the `temp` stream. When the sensor was silent the report says
  so instead of drawing an empty chart -- the 2024 season has no `temp` rows at all. The
  stream also carries the monitor's own CPU temperature, which the report no longer draws:
  it says something about the Pi, nothing about the night.

Options
-------

    --night YYYY-MM-DD      the evening the excursion started (default: most recent)
    --data PATH             sensor monitor log directory
    --map PATH              map layers for every night, instead of each year's own
    --output PATH           where to write the report (a directory, with --all)
    --all                   report on every night, and write an index over them
    --playa-only            with --all, skip the shakedowns
    --links FILE            JSON of YYYY-MM-DD to URL, to index published copies
    --accumulator-gallons N report the propane draw as pounds
    --fragment              emit the body only, for embedding elsewhere
    --list                  list the nights that have data and exit

No third party packages are needed; it runs on a stock Python 3.

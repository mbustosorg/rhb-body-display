Red Hot Beverly Main Display
============================

A [Processing 3](https://processing.org/) sketch that drives the dashboard display for *Red Hot Beverly*, a Burning Man art car. Mounts on a monitor installed upside-down on the vehicle; the sketch rotates the canvas 180° to compensate.

The display shows a live Black Rock City map with the car's position, vehicle telemetry (tire pressure, temperature, water heater status, poof count), speed-colored track history, and offline moon phase information. It also supports full replay of past Burning Man years from archived GPS logs.

---

## Features

- **Live BRC map** — streets, man ring, city boundary, first aid, toilets, and ranger stations, sourced from per-year KML data
- **Real-time position** — car location plotted as a dot on the map via OSC
- **Speed-colored track** — trail behind the car colored fast/medium/slow
- **Telemetry gauges** — rotary dial for tire pressure and cabin temperature, with sparkline history
- **Water heater & poof counter** — status indicators with flashing alert when heater is on
- **Auto day/night mode** — switches map color scheme at calculated local sunrise/sunset
- **Moon phase display** — offline astronomical calculation: phase disc graphic, illumination %, altitude, and rise/set time (no internet required)
- **GPS replay** — replay archived position logs from any past Burning Man year, navigating by noon-to-noon day sessions at adjustable speed

---

## Dependencies

Install these libraries via the Processing Library Manager (`Sketch → Import Library → Manage Libraries`):

| Library | Purpose |
|---------|---------|
| [oscP5](http://www.sojamo.de/libraries/oscP5/) | Receives live telemetry over OSC |
| [giCentreUtils](https://www.gicentre.net/utils/) | WebMercator projection (lat/lon → screen) |

---

## Project Structure

```
rhb-body-display/
├── rhbbodydisplay/
│   ├── rhbbodydisplay.pde   # Main Processing sketch
│   ├── data/                # Default map layer CSVs (fallback year)
│   └── positions/           # GPS and heading ZIP archives
│       ├── positions_YYYY.zip
│       └── heading_YYYY.zip
├── kml_parsing/
│   ├── YYYY/layers/         # Per-year map CSVs parsed from BRC KML
│   │   ├── lines.csv        # Street grid
│   │   ├── man_ring.csv     # The Man platform ring
│   │   ├── city_bounds.csv  # Outer city boundary
│   │   ├── 10_00.csv        # 10:00 avenue
│   │   ├── 2_00.csv         # 2:00 avenue
│   │   ├── kelter.csv       # Kelter street
│   │   ├── first_aid.csv
│   │   ├── toilets.csv
│   │   └── ranger.csv
│   └── read_xml.py          # Script to parse BRC KML into layer CSVs
└── osc/                     # TouchOSC layout and system diagram
```

---

## OSC Messages

The sketch listens on port **12000** for OSC messages from the vehicle's onboard computer:

| Path | Type | Description |
|------|------|-------------|
| `/position/lat` | float | GPS latitude |
| `/position/lon` | float | GPS longitude |
| `/heading` | float | Compass heading (degrees) |
| `/speed` | float | Speed |
| `/pressure` | float | Tire pressure (PSI) |
| `/temperature` | float | Cabin temperature (°F) |
| `/water_heater` | float | Heater state (0=off, >0=on) |
| `/poof_count` | float | Running poof counter |
| `/free_disk` | float | Free disk space on logger |
| `/engine` | float | Engine state |
| `/moving` | float | Moving state |

---

## GPS Replay

Position archives live in `rhbbodydisplay/positions/` as `positions_YYYY.zip` files containing 15-minute CSV chunks. Sessions are automatically grouped into **noon-to-noon day buckets** matching the natural Burning Man schedule.

### Keyboard Controls

| Key | Action |
|-----|--------|
| `r` | Start / stop replay |
| `↑` / `↓` | Next / previous day session |
| `+` / `=` | Double replay speed (up to 3600×) |
| `-` | Halve replay speed |

Replay automatically loads the correct year's map layer when a session starts.

---

## Map Data

Per-year map CSVs are generated from the official BRC KML files using `kml_parsing/read_xml.py`. The city shifts slightly each year (~600 yards between some years), so each year's map data is used when replaying that year's GPS logs.

To add a new year:
1. Obtain the BRC KML for that year
2. Run `read_xml.py` to produce `kml_parsing/YYYY/layers/*.csv`
3. Add a `positions_YYYY.zip` archive to `rhbbodydisplay/positions/`

---

## Moon Calculations

All moon data is computed offline using astronomical algorithms (Jean Meeus simplified method):

- **Phase disc** — bezier-drawn graphic showing the correct crescent/gibbous/full shape
- **Illumination** — percentage of disc lit
- **Altitude** — degrees above or below the horizon at BRC coordinates
- **Rise / set** — local time for the current day, found by scanning the day in 6-minute steps

No network connection required.

---

## License

GNU General Public License v3 — see [LICENSE](LICENSE).

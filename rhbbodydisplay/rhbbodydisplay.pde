/*
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
 */

import oscP5.*;
import org.gicentre.utils.spatial.*;
import java.util.Date;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.text.ParseException;
import java.util.concurrent.TimeUnit;

OscP5 oscP5;

WebMercator proj = new WebMercator();

ArrayList<PVector>coords;
ArrayList<PVector>firstAid;
ArrayList<PVector>toilets;
ArrayList<PVector>ranger;
// Our own two marks. z carries the glyph: 0 is the camp star, 1 the burn flame
ArrayList<PVector>places;
ArrayList<PVector>man_ring;
ArrayList<PVector>city_bounds;

ArrayList<PVector>track;
// The streets and the markers never move between map reloads, so they are built once and
// drawn as shapes. Rebuilding 1,700 street segments and 43 vented booths from scratch on
// every frame was the bulk of what a frame cost. All three carry disableStyle(), so the
// colour is still whatever the caller sets and a change of theme needs no rebuild.
PShape streetShape, boothShape, crossShape;
FloatList track_pressure;
FloatList track_temperature;

PVector tlCorner, brCorner;

float heading = 0.0;
float pressure = 14;
float temperature = 40.0;
float lon = 0.0;
float lat = 0.0;
float speed = 0.0;
float free_disk = 1.0;
float water_heater = 0.0;
float lower_temp = 70.0;
float upper_temp = 75.0;
float engine = 0.0;
float moving = 0.0;
float poof_count = 0.0;
float translate_lon = 0.0;
float translate_lat = 0.0;
float ORIGIN_LON =  -119.2175207;
float ORIGIN_LAT = 40.7851999;
float OAKLAND_LON = -122.2537901;
float OAKLAND_LAT = 37.8504158;

// Timezone offset for Burning Man (PDT = UTC-7)
float TIMEZONE = -7.0;

// Day/night tracking
boolean darkMode = true;

// A frame time readout, off by default and toggled with 'f'. The number that matters is
// the millisecond one: frameRate is capped at whatever frameRate() asks for, so a healthy
// sketch just reads 10 and tells you nothing. Milliseconds per frame keep falling as
// things get cheaper, and once they sit well under 100 there is room to ask for more
// frames than ten
boolean showFrameTime = false;
float frameMillis = 0;
// Where the frame actually goes. millis() only resolves to 1ms, which is too coarse when
// the pieces are a few ms each, so these are nanoTime and smoothed the same way
float msBase = 0, msMarkers = 0, msTrack = 0, msInstruments = 0;
long sectionBegan = 0;
void sectionStart() { sectionBegan = System.nanoTime(); }
float sectionEnd(float running) {
  return running + ((System.nanoTime() - sectionBegan) / 1000000.0 - running) * 0.1;
}
float sunriseHour = 6.0;
float sunsetHour = 20.0;
int lastDayNightCheck = -1;

// Moon tracking (updated once per minute, rise/set once per day)
float moonRiseHour  = -1;
float moonSetHour   = -1;
float moonAltCached = 0.0;
float moonAgeCached = 0.0;
int   lastMoonDay   = -1;

// Theme colors — set by setDarkMode() or setLightMode()
color cBg, cCityFill, cManFill, cStreet, cManRing;
color cToilet, cFirstAid, cRanger;
color cCamp, cBurn, cBurnCore;
// Radius of our two marks. The POI dots beside them are drawn 16 across, so this keeps
// the glyphs a shade larger than those without shouting over the city
float PLACE_GLYPH_R = 10;
// First aid is drawn as the cross everyone already knows rather than another coloured dot.
// A cross needs a shade more room than a disc before its arms read, so it runs slightly
// larger than the 8 the other POIs are drawn at
float FIRST_AID_R = 9;
// Half height of a porto. There are 43 of them against three of everything else, so the
// booth is drawn narrower than the dot it replaces -- it has to stay quiet at that many
float PORTO_R = 8;
// A ranger station is a small lowercase r. The size is the type size, and a lowercase
// letter stands about half of that, so this lands near the 16 the dots were drawn at
float RANGER_TYPE = 24;
// The Man ring against the streets, which are drawn at 3. Still the heaviest line on the
// map, but only about twice the streets rather than the four times it began at
float MAN_RING_WEIGHT = 6;
color cTrackFast, cTrackMed, cTrackSlow;
color cText, cPosition;
color cSparkBg, cSparkBorder, cSparkRange, cSparkData;
color cRotaryDisc, cRotaryArc, cRotaryText;
color cHeaterOn, cSpeedFast, cSpeedMed;

// Replay state
boolean replaying = false;
ArrayList<PVector> replayData;     // x=rawLon, y=rawLat, z=timeSeconds
int replayIndex = 0;
float replayStartMillis = 0;
float REPLAY_SPEED = 120.0;        // 120x real time
ArrayList<ArrayList<String>> replaySessions = new ArrayList<ArrayList<String>>();
int currentReplaySession = 0;

int lastSecond = 0;
boolean testing = false;

PImage backgroundMap;

PShape city;
PShape man;
int offset = 100;

String mapDataDir = "";   // set by reloadMapForYear(); used by setupGeo/setupPOI
String currentMapYear = "";

// ------------------------------------------------------------------- weirdness
// Every so often the map does something it has no business doing for a few seconds, and
// then behaves itself again. The effects wrap the map's transform only: the draw loop
// closes that transform after the track and opens a plain one for the instruments, so the
// sparklines, the readouts and the sliders hold still while the city misbehaves around
// them. 'w' turns the whole business off, 'e' fires one on demand.
boolean effectsOn = true;
int effectKind = -1;          // -1 is nothing happening
int effectBegan = 0;
int effectRuns = 0;
int effectDue = 0;
final int EFFECT_SWAY = 0, EFFECT_BREATHE = 1, EFFECT_DRIFT = 2, EFFECT_TUMBLE = 3;
final int EFFECT_NEON = 4;
final int EFFECT_FISHEYE = 5;
final int EFFECT_TWIST = 6;
final int EFFECT_COUNT = 7;
// These rates were slow because the sketch only drew ten frames a second and anything
// quick juddered. At thirty they are slow because slow suits them -- a map that lolls is
// funny, a map that twitches looks broken. There is room to speed them up now if that
// turns out to be wrong on the car
int EFFECT_GAP_MIN = 40000, EFFECT_GAP_MAX = 150000;
int EFFECT_RUN_MIN = 7000,  EFFECT_RUN_MAX = 15000;
// How hard the lens bends. The cycle is tied to the length of the run rather than to a
// rate of its own: on a fixed rate the phase drifted against the envelope, so whichever
// half happened to land on the envelope's peak won and the other was squashed flat --
// which is why it only ever appeared to come towards you.
float FISHEYE_MAX = 0.55;
// How far the Man end of a radial street is dragged round at the hardest part of the wind.
// The rings are unmoved by this whatever it is set to -- a turn about the Man by an amount
// that depends only on distance slides a circle along itself and leaves it where it was.
// What bends is the clock streets, which wind up into spirals, and the city bounds
float TWIST_MAX = radians(80);
// sin^2(pi u) * sin(2 pi u) tops out at 0.6495, a third and two thirds of the way through.
// Dividing by it makes the MAX constants mean the real strongest bend, either way round
final float CYCLE_PEAK = 0.6495;

// One whole cycle over the run, whatever its length, eased to nothing at both ends: away
// from flat, back through it at the midpoint, the same distance the other way, and home
float effectCycle() {
  return effectSwell() * sin(TWO_PI * effectProgress()) / CYCLE_PEAK;
}

void scheduleEffect() {
  effectKind = -1;
  effectDue = millis() + int(random(EFFECT_GAP_MIN, EFFECT_GAP_MAX));
}

// Set one going this instant, whatever the scheduler had in mind
void startEffect(int kind) {
  effectKind = constrain(kind, 0, EFFECT_COUNT - 1);
  effectBegan = millis();
  effectRuns = int(random(EFFECT_RUN_MIN, EFFECT_RUN_MAX));
}

String effectName(int kind) {
  if (kind == EFFECT_SWAY) return "sway";
  if (kind == EFFECT_BREATHE) return "breathe";
  if (kind == EFFECT_DRIFT) return "drift";
  if (kind == EFFECT_TUMBLE) return "tumble";
  if (kind == EFFECT_NEON) return "neon";
  if (kind == EFFECT_FISHEYE) return "fisheye";
  if (kind == EFFECT_TWIST) return "twist";
  return "none";
}

void updateEffects() {
  // However it was started, an effect is left to finish. Cutting one off part way would
  // drop the map wherever the swing had got to rather than back where it began
  if (effectKind >= 0) {
    if (millis() - effectBegan > effectRuns) scheduleEffect();
    return;
  }
  // With the weirdness switched off nothing starts on its own, but 'e' still works
  if (!effectsOn) return;
  if (millis() >= effectDue) startEffect(int(random(EFFECT_COUNT)));
}

// How far along the current effect is, 0 to 1
float effectProgress() {
  if (effectKind < 0) return 0;
  return constrain((millis() - effectBegan) / float(effectRuns), 0, 1);
}

// 0 at the start, 1 in the middle, 0 again at the end. An effect always arrives and leaves
// gently, and the map is exactly where it was by the time it finishes
float effectEnvelope() {
  if (effectKind < 0) return 0;
  return sin(PI * effectProgress());
}

// ---------------------------------------------------------------- the fisheye
// A bulge cannot be had from the transform matrix: a matrix moves everything the same way
// and this has to move the middle further than the edge. So the map is drawn a second way
// while it runs, every point moved about the Man: the lens pushes it out or in along its
// own radius, the twist turns it about the Man by an amount that dies away with distance.
// Both are zero when no effect is running, and the fast cached path is used then instead.
float bulgeK = 0;          // 0 is flat, positive bulges out, negative sucks in
float twistK = 0;          // 0 is straight, otherwise radians of turn at the Man itself
float warpR = 1;          // radius at which both warps stop bending anything
PVector warpAt;           // the Man, in the same space the map is drawn in

// Whether anything is bending the map this frame. The cached shapes are drawn flat and
// cannot follow a warp, so this is what picks between them and the slow path
boolean warping() { return bulgeK != 0 || twistK != 0; }

// Both warps in one pass, about the Man. The lens moves a point along its own radius; the
// twist turns it about the Man without changing that radius at all. They are independent
// and only one runs at a time, but nothing stops them being combined.
//
// The lens is r' = R * u^(1-k). One exponent covers both directions: k above zero pulls the exponent
// under 1 and magnifies the middle, k below zero pushes it over 1 and sucks the middle in.
// It is monotonic and lands on R at u = 1 either way, so the rim holds and nothing folds
// through itself. The obvious form, mixing u with sqrt(u), went negative for negative k
// and flipped points to the far side of the Man
PVector warp(float x, float y) {
  if (!warping() || warpAt == null) return new PVector(x, y);
  float dx = x - warpAt.x, dy = y - warpAt.y;
  float r = sqrt(dx * dx + dy * dy);
  if (r < 0.001) return new PVector(x, y);
  float u = min(r / warpR, 1);

  if (bulgeK != 0) {
    float scale = warpR * pow(u, 1 - bulgeK) / r;
    dx *= scale; dy *= scale;
  }
  if (twistK != 0) {
    // Turn about the Man by an amount that falls away with distance. Squared, so the turn
    // dies out with no gradient left at the rim and the edge of the map shows no seam.
    // Taken from the radius before the lens touched it, so the two do not fight over it.
    // Straight from the rotation matrix rather than atan2 then back again: the angle of
    // the point never has to be known, only how far it is being turned
    float a = twistK * (1 - u) * (1 - u);
    float c = cos(a), sn = sin(a);
    float rx = dx * c - dy * sn;
    dy = dx * sn + dy * c;
    dx = rx;
  }
  return new PVector(warpAt.x + dx, warpAt.y + dy);
}

// A straight line stays straight however its ends are moved, and seven of the streets are
// two point lines. So a segment is cut into pieces short enough to take the curve.
// The twist bends a line far harder than the lens does: eight pieces left 8px of faceting
// down a long radial, where sixteen leaves 2px. It is cheap to allow more only when the
// twist is running, because the cap is all that changes and the cap only bites on long
// segments -- 22 of the 1,713 streets are over half the longest, and the median is 1.4%
void warpLine(float x1, float y1, float x2, float y2) {
  int cap = (twistK != 0) ? 20 : 8;
  int pieces = min(1 + int(dist(x1, y1, x2, y2) / 45.0), cap);
  PVector from = warp(x1, y1);
  for (int i = 1; i <= pieces; i++) {
    float t = i / float(pieces);
    PVector to = warp(lerp(x1, x2, t), lerp(y1, y2, t));
    line(from.x, from.y, to.x, to.y);
    from = to;
  }
}

void warpRun(ArrayList<PVector> run, boolean closed) {
  beginShape();
  for (int i = 0; i < run.size(); i++) {
    PVector at = geoToScreen(run.get(i));
    PVector b = warp(at.x + offset, at.y);
    vertex(b.x, b.y);
  }
  endShape(closed ? CLOSE : OPEN);
}

// The whole map again, every point put through the warp. Only runs while the fisheye or
// the twist is going: the rest of the time the cached shapes above do the same job cheaper.
void drawMapWarped() {
  noStroke();
  fill(cCityFill);
  warpRun(city_bounds, true);
  fill(cManFill);
  warpRun(man_ring, true);

  noFill();
  stroke(cStreet);
  strokeWeight(3);
  for (int i = 0; i < coords.size() - 1; i++) {
    if (coords.get(i).x != 0 && coords.get(i + 1).x != 0) {
      PVector a = geoToScreen(coords.get(i));
      PVector b = geoToScreen(coords.get(i + 1));
      warpLine(a.x + offset, a.y, b.x + offset, b.y);
    }
  }
  strokeWeight(MAN_RING_WEIGHT);
  stroke(cManRing);
  for (int i = 0; i < man_ring.size() - 1; i++) {
    PVector a = geoToScreen(man_ring.get(i));
    PVector b = geoToScreen(man_ring.get(i + 1));
    warpLine(a.x + offset, a.y, b.x + offset, b.y);
  }

  // The markers keep their own size and are simply carried to where the lens puts them.
  // Bending a glyph a few pixels across would only smear it
  noStroke();
  for (int i = 0; i < toilets.size(); i++) {
    PVector at = geoToScreen(toilets.get(i));
    PVector b = warp(at.x + offset, at.y);
    fill(cToilet);
    rect(b.x - PORTO_R * 0.62, b.y - PORTO_R, PORTO_R * 1.24, PORTO_R * 2);
  }
  for (int i = 0; i < firstAid.size(); i++) {
    PVector at = geoToScreen(firstAid.get(i));
    PVector b = warp(at.x + offset, at.y);
    fill(cFirstAid);
    rect(b.x - FIRST_AID_R * 0.34, b.y - FIRST_AID_R, FIRST_AID_R * 0.68, FIRST_AID_R * 2);
    rect(b.x - FIRST_AID_R, b.y - FIRST_AID_R * 0.34, FIRST_AID_R * 2, FIRST_AID_R * 0.68);
  }
}

// Old neon: every letter is its own tube, and old tubes fail one at a time. A tube that is
// going runs dim and cold for a while before it drops out altogether, and comes back the
// same way, so the noise is sampled per letter and moves slowly rather than per frame.
// Costs nothing when the effect is not running -- it is a plain text() call then.
void neonText(String s, float x, float y) {
  if (effectKind != EFFECT_NEON) { text(s, x, y); return; }
  color base = g.fillColor;
  float bad = effectEnvelope();
  float cursor = x;
  for (int i = 0; i < s.length(); i++) {
    String ch = s.substring(i, i + 1);
    float w = textWidth(ch);
    float n = noise(i * 3.7, millis() * 0.004);
    if (n < 0.30 * bad) { cursor += w; continue; }
    float glow = 1.0 - bad * 0.55 * (1.0 - n);
    fill(red(base) * glow, green(base) * glow, blue(base) * glow);
    text(ch, cursor, y);
    cursor += w;
  }
  fill(base);
}

// The plain envelope reaches 1 and returns, but it is still moving at both ends: its slope
// at u = 0 is PI, so it starts with a shove. Squaring it flattens both ends to nothing,
// which is what the lens wants -- it should swell out of flat and settle back into it
float effectSwell() {
  float e = effectEnvelope();
  return e * e;
}

// Seconds since the effect started, for the ones that oscillate
float effectSeconds() {
  return (millis() - effectBegan) / 1000.0;
}


void setup() {
  coords = new ArrayList<PVector>();
  firstAid = new ArrayList<PVector>();
  toilets = new ArrayList<PVector>();
  ranger = new ArrayList<PVector>();
  places = new ArrayList<PVector>();
  track = new ArrayList<PVector>();
  man_ring = new ArrayList<PVector>();
  city_bounds = new ArrayList<PVector>();
  track_pressure = new FloatList();
  track_pressure.append(50.0);
  track_temperature = new FloatList();
  track_temperature.append(13.0);
  track.add(proj.transformCoords(new PVector(ORIGIN_LON, ORIGIN_LAT)));

  mapDataDir = sketchPath("data/");
  setupGeo();
  buildShapes();
  setupPOI("toilets", toilets);
  setupPOI("first_aid", firstAid);
  setupPOI("ranger", ranger);
  setupPlaces();
  buildMarkerShapes();

  fullScreen();
  oscP5 = new OscP5(this, 10002);
  // Was ten a second, on the grounds that a frame was expensive. Measured, a frame costs
  // about 8ms: 6.4 for the city and its streets, 0.4 for the markers, 1 for the
  // instruments, and a track that starts near nothing. Thirty leaves a 33ms budget, so
  // there is still four times the headroom -- and the effects want the frames. Press 'f'
  // to watch it; if the track ever eats the budget late in a night, cap the track rather
  // than lower this
  frameRate(30);

  colorMode(RGB, 255);
  scheduleEffect();
  setDarkMode();
  updateDayNight();
  setupReplay();
}

void draw() {

  if (testing) {
    if (lastSecond != second()) {
      lastSecond = second();
      println("rhbbodydisplay: tick: " + lastSecond);
      PVector sim_track = track.get(0);
      int elapsed = millis() / 1000;
      float lat = sim_track.x + sin(float(elapsed) / 60.0) * float(elapsed) / 10.0;
      float lon = sim_track.y - cos(float(elapsed) / 60.0) * float(elapsed) / 10.0;
      track.add(new PVector(lat, lon, 15.0));
    }
  }

  updateDayNight();
  updateReplay();

  int frameBegan = millis();
  boolean flashOn = millis() - (millis() / 1000) * 1000.0 > 500.0;

  background(cBg);

  updateEffects();
  float env = effectEnvelope();
  float swing = 0, zoom = 1, slideX = 0, slideY = 0;
  bulgeK = 0;
  twistK = 0;
  if (effectKind == EFFECT_SWAY) {
    swing = radians(7) * env * sin(TWO_PI * 0.30 * effectSeconds());
  } else if (effectKind == EFFECT_BREATHE) {
    zoom = 1 + 0.10 * env * sin(TWO_PI * 0.22 * effectSeconds());
  } else if (effectKind == EFFECT_DRIFT) {
    slideX = 0.045 * width  * env * cos(TWO_PI * 0.18 * effectSeconds());
    slideY = 0.045 * height * env * sin(TWO_PI * 0.18 * effectSeconds());
  } else if (effectKind == EFFECT_FISHEYE) {
    bulgeK = FISHEYE_MAX * effectCycle();
    warpR = max(width, height) * 0.55;
    warpAt = manMapPoint();
  } else if (effectKind == EFFECT_TWIST) {
    // Winds one way, unwinds through straight, winds the other, and settles back true
    twistK = TWIST_MAX * effectCycle();
    warpR = max(width, height) * 0.55;
    warpAt = manMapPoint();
  } else if (effectKind == EFFECT_TUMBLE) {
    // One whole turn, eased at both ends, finishing back where it started
    float u = effectProgress();
    swing = TWO_PI * (u * u * (3 - 2 * u));
  }

  pushMatrix();
  // The map's own transform turns it about the bottom right corner, which is fine when it
  // never moves. Anything added there would swing the city clean off the screen, so the
  // effects wrap it and pivot on the Man instead -- the city rocks about him, the way it
  // is laid out around him in the first place
  PVector pivot = manPivot();
  translate(pivot.x + slideX, pivot.y + slideY);
  rotate(swing);
  scale(zoom);
  translate(-pivot.x, -pivot.y);
  translate(width, height);
  rotate(PI);

  sectionStart();
  if (warping()) {
    drawMapWarped();
  } else {
  noStroke();
  fill(cCityFill);
  shape(city, 0, 0);

  noStroke();
  fill(cManFill);
  shape(man, 0, 0);

  stroke(cStreet);
  strokeWeight(3);
  textSize(32);
  fill(cText);
  if (streetShape != null) shape(streetShape, 0, 0);
  strokeWeight(MAN_RING_WEIGHT);
  stroke(cManRing);
  for (int i = 0; i < man_ring.size() - 1; i++) {
    if (man_ring.get(i).x != 0 && man_ring.get(i + 1).x != 0) {
      PVector startCoord = geoToScreen(man_ring.get(i));
      PVector endCoord = geoToScreen(man_ring.get(i + 1));
      line(startCoord.x + offset, startCoord.y, endCoord.x + offset, endCoord.y);
    }
  }
  }
  msBase = sectionEnd(msBase);

  sectionStart();
  strokeWeight(2);
  noStroke();
  if (!warping()) {
    fill(cToilet);
    if (boothShape != null) shape(boothShape, 0, 0);
    fill(cFirstAid);
    if (crossShape != null) shape(crossShape, 0, 0);
  } else {
    // Under the lens the baked shapes would sit still while the city moved out from under
    // them, so they are drawn the slow way for the few seconds an effect lasts
    fill(cToilet);
    for (int i = 0; i < toilets.size(); i++) {
      PVector at = geoToScreen(toilets.get(i));
      PVector b = warp(at.x + offset, at.y);
      drawBooth(b.x, b.y, PORTO_R);
    }
    fill(cFirstAid);
    for (int i = 0; i < firstAid.size(); i++) {
      PVector at = geoToScreen(firstAid.get(i));
      PVector b = warp(at.x + offset, at.y);
      drawCross(b.x, b.y, FIRST_AID_R);
    }
  }
  for (int i = 0; i < ranger.size(); i++) {
    PVector at = geoToScreen(ranger.get(i));
    PVector b = warp(at.x + offset, at.y);
    drawRanger(b.x, b.y, RANGER_TYPE);
  }
  for (int i = 0; i < places.size(); i++) {
    PVector at = geoToScreen(places.get(i));
    PVector b = warp(at.x + offset, at.y);
    if (places.get(i).z > 0.5) drawFlame(b.x, b.y, PLACE_GLYPH_R);
    else                       drawStar(b.x, b.y, PLACE_GLYPH_R);
  }
  msMarkers = sectionEnd(msMarkers);

  sectionStart();
  paintTrack();
  msTrack = sectionEnd(msTrack);
  // The map ends here. Everything below is instrumentation, and it is drawn on the plain
  // base transform so the effects cannot take it with them: a sparkline that sways is a
  // sparkline you cannot read, and its box and its trace would part company besides
  popMatrix();
  pushMatrix();
  translate(width, height);
  rotate(PI);

  sectionStart();
  sparkline(310, 150, 150, 50, 0, 100, 30, 80, track_pressure);
  sparkline(310, 350, 150, 50, 60, 85, lower_temp, upper_temp, track_temperature);
  noStroke();
  textSize(60);
  fill(cText);
  neonText("Poofs:", 30, 560);
  neonText(str(int(poof_count)), 250, 560);
  neonText("Heater:", 30, 620);
  if (water_heater > 0.0) {
    if (flashOn) fill(cHeaterOn);
    neonText("ON", 250, 620);
    fill(cText);
  } else {
    fill(cText);
    neonText("OFF", 250, 620);
  }
  fill(cText);
  rotarySlider(150, 150, 200, 10, 80, pressure);
  rotarySlider(150, 350, 200, 20, 120, temperature);
  // Moon info — graphic disc + illumination and rise/set text
  drawMoonPhase(48, 666, 20, moonAgeCached);
  textSize(30);
  fill(cText);
  String moonLine = int(moonIllumination(moonAgeCached)) + "%";
  float nowH = hour() + minute() / 60.0;
  if (moonAltCached > 0) {
    moonLine += "  up " + int(moonAltCached) + "°";
    if (moonSetHour >= 0 && moonSetHour > nowH) moonLine += "  sets " + formatMoonHour(moonSetHour);
  } else if (moonRiseHour >= 0 && moonRiseHour > nowH) {
    moonLine += "  rises " + formatMoonHour(moonRiseHour);
  }
  neonText(moonLine, 80, 680);
  if (replaying && replaySessions.size() > 0) {
    textSize(28);
    fill(cSpeedMed);
    float progress = (replayData != null && replayData.size() > 0)
      ? float(replayIndex) / replayData.size() : 0;
    neonText("REPLAY  " + sessionLabel(currentReplaySession) + "  " + int(progress * 100) + "%", 30, 740);
    neonText(int(REPLAY_SPEED) + "x   [r] stop  [↑/↓] day  [+/-] speed", 30, 775);
    fill(cText);
  } else if (replaySessions.size() > 0) {
    textSize(28);
    fill(cSparkData);
    neonText("[r] replay: " + sessionLabel(currentReplaySession) + "  [↑/↓] change day", 30, 740);
    fill(cText);
  }
  if (lon != 0.0 || lat != 0.0) {
    PVector rhb = geoToScreen(proj.transformCoords(new PVector(lon + translate_lon, lat + translate_lat)));
    if (rhb.x >= 0 && rhb.x <= width && rhb.y >= 0 && rhb.y <= height) {
      PVector b = warp(rhb.x + offset, rhb.y);
      noStroke();
      fill(cPosition);
      circle(b.x, b.y, 18);
    }
  }
  msInstruments = sectionEnd(msInstruments);
  if (showFrameTime) {
    // Averaged over about a second, because a single frame bounces around too much to read
    frameMillis += ((millis() - frameBegan) - frameMillis) * 0.1;
    pushStyle();
    fill(cText);
    textSize(30);
    text(nf(frameMillis, 0, 1) + " ms   " + nf(frameRate, 0, 1) + " fps   track " + track.size(),
         30, height - 100);
    textSize(24);
    text("base " + nf(msBase, 0, 1) + "   markers " + nf(msMarkers, 0, 1)
       + "   track " + nf(msTrack, 0, 1) + "   instruments " + nf(msInstruments, 0, 1),
         30, height - 60);
    popStyle();
  }
  popMatrix();
}

void setDarkMode() {
  darkMode = true;
  cBg          = color(8, 8, 20);
  cCityFill    = color(14, 14, 58);
  cManFill     = color(26, 0, 0);
  cStreet      = color(58, 72, 106);
  cManRing     = color(255, 51, 51);
  cToilet      = color(0, 221, 255);
  cFirstAid    = color(255, 40, 40);
  cRanger      = color(255, 136, 0);
  cCamp        = color(255, 215, 0);
  cBurn        = color(255, 90, 20);
  cBurnCore    = color(255, 210, 60);
  cTrackFast   = color(255, 34, 0);
  cTrackMed    = color(255, 238, 0);
  cTrackSlow   = color(0, 255, 136);
  cText        = color(230, 236, 255);
  cPosition    = color(255, 0, 255);
  cSparkBg     = color(5, 15, 5);
  cSparkBorder = color(34, 68, 34);
  cSparkRange  = color(255, 68, 255);
  cSparkData   = color(0, 170, 255);
  cRotaryDisc  = color(100, 0, 180);
  cRotaryArc   = color(8, 8, 20);
  cRotaryText  = color(230, 236, 255);
  cHeaterOn    = color(255, 0, 0);
  cSpeedFast   = color(255, 68, 0);
  cSpeedMed    = color(255, 238, 0);
  // The markers bake their fill, so they are rebuilt whenever the palette moves under
  // them. Harmless before the POI lists load: the groups just come out empty
  buildMarkerShapes();
}

void setLightMode() {
  darkMode = false;
  cBg          = color(245, 240, 220);
  cCityFill    = color(210, 220, 255);
  cManFill     = color(200, 170, 170);
  cStreet      = color(50, 40, 30);
  cManRing     = color(180, 0, 0);
  cToilet      = color(0, 80, 200);
  cFirstAid    = color(200, 0, 0);
  cRanger      = color(160, 80, 0);
  cCamp        = color(180, 140, 0);
  cBurn        = color(200, 60, 0);
  cBurnCore    = color(240, 165, 30);
  cTrackFast   = color(200, 0, 0);
  cTrackMed    = color(180, 160, 0);
  cTrackSlow   = color(0, 140, 60);
  cText        = color(20, 20, 20);
  cPosition    = color(220, 0, 0);
  cSparkBg     = color(240, 255, 240);
  cSparkBorder = color(100, 130, 100);
  cSparkRange  = color(200, 0, 200);
  cSparkData   = color(0, 0, 200);
  cRotaryDisc  = color(200, 0, 0);
  cRotaryArc   = color(245, 240, 220);
  cRotaryText  = color(20, 20, 20);
  cHeaterOn    = color(220, 0, 0);
  cSpeedFast   = color(180, 0, 0);
  cSpeedMed    = color(160, 140, 0);
  // The markers bake their fill, so they are rebuilt whenever the palette moves under
  // them. Harmless before the POI lists load: the groups just come out empty
  buildMarkerShapes();
}

// Recalculate sunrise/sunset once per minute and switch mode if needed
void updateDayNight() {
  int currentMinute = hour() * 60 + minute();
  if (currentMinute == lastDayNightCheck) return;
  lastDayNightCheck = currentMinute;

  float[] times = calcSunriseSunset(year(), month(), day(), ORIGIN_LAT, ORIGIN_LON, TIMEZONE);
  sunriseHour = times[0];
  sunsetHour  = times[1];

  float currentHour = hour() + minute() / 60.0;
  boolean shouldBeDark = currentHour < sunriseHour || currentHour > sunsetHour;
  if (shouldBeDark && !darkMode) setDarkMode();
  else if (!shouldBeDark && darkMode) setLightMode();

  // Moon: altitude every minute, rise/set once per day
  float utcH = currentHour - TIMEZONE;
  float JDnow = julianDate(year(), month(), day(), utcH);
  moonAgeCached = moonAgeFromJD(JDnow);
  moonAltCached = moonAltitudeDeg(JDnow, ORIGIN_LAT, ORIGIN_LON);
  if (day() != lastMoonDay) {
    float[] moonTimes = calcMoonRiseSet(year(), month(), day(), ORIGIN_LAT, ORIGIN_LON, TIMEZONE);
    moonRiseHour = moonTimes[0];
    moonSetHour  = moonTimes[1];
    lastMoonDay  = day();
  }
}

// NOAA simplified sunrise/sunset algorithm — returns {sunriseLocalHour, sunsetLocalHour}
float[] calcSunriseSunset(int yr, int mo, int d, float lat, float lon, float tz) {
  int doy = calcDayOfYear(yr, mo, d);
  float lngHour = lon / 15.0;
  float[] result = new float[2];
  for (int i = 0; i < 2; i++) {
    float t = (i == 0) ? doy + ((6.0 - lngHour) / 24.0)
                       : doy + ((18.0 - lngHour) / 24.0);
    float M = (0.9856 * t) - 3.289;
    float L = M + (1.916 * sin(radians(M))) + (0.020 * sin(2 * radians(M))) + 282.634;
    while (L < 0) L += 360;
    while (L >= 360) L -= 360;
    float RA = degrees(atan(0.91764 * tan(radians(L))));
    while (RA < 0) RA += 360;
    while (RA >= 360) RA -= 360;
    float Lq = floor(L / 90) * 90, RAq = floor(RA / 90) * 90;
    RA = (RA + (Lq - RAq)) / 15.0;
    float sinDec = 0.39782 * sin(radians(L));
    float cosDec = cos(asin(sinDec));
    float cosH = (cos(radians(90.833)) - (sinDec * sin(radians(lat)))) / (cosDec * cos(radians(lat)));
    if (cosH > 1 || cosH < -1) { result[i] = (i == 0) ? -1 : 25; continue; }
    float H = (i == 0) ? (360.0 - degrees(acos(cosH))) : degrees(acos(cosH));
    H /= 15.0;
    float T = H + RA - (0.06571 * t) - 6.622;
    float UT = T - lngHour;
    while (UT < 0) UT += 24;
    while (UT >= 24) UT -= 24;
    float local = UT + tz;
    while (local < 0) local += 24;
    while (local >= 24) local -= 24;
    result[i] = local;
  }
  return result;
}

int calcDayOfYear(int yr, int mo, int d) {
  int[] dim = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  if ((yr % 4 == 0 && yr % 100 != 0) || yr % 400 == 0) dim[1] = 29;
  int doy = d;
  for (int m = 0; m < mo - 1; m++) doy += dim[m];
  return doy;
}

// ─── Moon calculations ────────────────────────────────────────────────────────

// Julian Date from calendar date + UTC hour
float julianDate(int yr, int mo, int d, float utcHour) {
  if (mo <= 2) { yr--; mo += 12; }
  int A = yr / 100;
  int B = 2 - A + A / 4;
  return (int)(365.25 * (yr + 4716)) + (int)(30.6001 * (mo + 1)) + d + utcHour / 24.0 + B - 1524.5;
}

// Moon equatorial coordinates {RA in hours, Dec in degrees}
// Simplified Jean Meeus algorithm, accurate to ~1°
float[] moonEquatorial(float JD) {
  float d  = JD - 2451545.0;
  float L  = ((218.316 + 13.176396 * d) % 360 + 360) % 360;
  float M  = ((134.963 + 13.064993 * d) % 360 + 360) % 360;
  float F  = ((93.272  + 13.229350 * d) % 360 + 360) % 360;
  float lam = L + 6.289 * sin(radians(M));
  float bet = 5.128 * sin(radians(F));
  float eps = 23.439 - 0.0000004 * d;
  float RA  = degrees(atan2(
    sin(radians(lam)) * cos(radians(eps)) - tan(radians(bet)) * sin(radians(eps)),
    cos(radians(lam))));
  RA = ((RA % 360) + 360) % 360;
  float Dec = degrees(asin(
    sin(radians(bet)) * cos(radians(eps)) +
    cos(radians(bet)) * sin(radians(eps)) * sin(radians(lam))));
  return new float[]{ RA / 15.0, Dec };
}

// Moon altitude above horizon in degrees (negative = below horizon)
float moonAltitudeDeg(float JD, float latDeg, float lonDeg) {
  float[] eq  = moonEquatorial(JD);
  float RA  = eq[0];   // hours
  float Dec = eq[1];   // degrees
  float GST = ((280.46061837 + 360.98564736629 * (JD - 2451545.0)) % 360 + 360) % 360;
  float LST = (GST + lonDeg) / 15.0;
  float HA  = ((LST - RA) % 24 + 24) % 24;
  if (HA > 12) HA -= 24;
  float HA_deg = HA * 15.0;
  return degrees(asin(
    sin(radians(latDeg)) * sin(radians(Dec)) +
    cos(radians(latDeg)) * cos(radians(Dec)) * cos(radians(HA_deg))));
}

// Moon age in days since last new moon (0 = new, ~14.77 = full, 29.53 = new again)
float moonAgeFromJD(float JD) {
  float age = (JD - 2451549.5) % 29.530589;
  return age < 0 ? age + 29.530589 : age;
}

// Moon illumination percentage from age
float moonIllumination(float age) {
  return (1.0 - cos(TWO_PI * age / 29.530589)) / 2.0 * 100.0;
}

String moonPhaseName(float age) {
  if (age <  1.85) return "New Moon";
  if (age <  7.38) return "Waxing Crescent";
  if (age <  9.22) return "First Quarter";
  if (age < 14.77) return "Waxing Gibbous";
  if (age < 16.61) return "Full Moon";
  if (age < 22.15) return "Waning Gibbous";
  if (age < 23.99) return "Last Quarter";
  return "Waning Crescent";
}

// Scan the day in 6-minute steps to find moonrise and moonset local hours
// Returns {riseHour, setHour} — -1 if not found for this calendar day
float[] calcMoonRiseSet(int yr, int mo, int d, float latDeg, float lonDeg, float tz) {
  float rise = -1, set = -1;
  float prevAlt = -999;
  for (float utcH = 0.0; utcH <= 25.0; utcH += 0.1) {
    float alt = moonAltitudeDeg(julianDate(yr, mo, d, utcH), latDeg, lonDeg);
    if (prevAlt > -999) {
      if (prevAlt < 0 && alt >= 0 && rise < 0) {
        float localH = ((utcH + tz) % 24 + 24) % 24 - alt / (alt - prevAlt) * 0.1;
        if (localH < 0) localH += 24;
        rise = localH;
      }
      if (prevAlt >= 0 && alt < 0 && set < 0) {
        float localH = ((utcH + tz) % 24 + 24) % 24 - alt / (alt - prevAlt) * 0.1;
        if (localH < 0) localH += 24;
        set = localH;
      }
    }
    prevAlt = alt;
  }
  return new float[]{ rise, set };
}

String formatMoonHour(float h) {
  if (h < 0) return "--:--";
  int hr = int(h) % 24;
  int mn = int((h - int(h)) * 60);
  return nf(hr, 2) + ":" + nf(mn, 2);
}

// Draw the moon phase disc centered at (cx,cy) with radius r.
// Uses two bezier half-paths: the lit outer arc + the terminator ellipse arc.
// termX = r*cos(phase*2π) for waxing, -r*cos(phase*2π) for waning.
// At new moon both arcs coincide → zero area; at full moon they enclose the disc.
void drawMoonPhase(float cx, float cy, float r, float age) {
  float phase = ((age / 29.530589) % 1.0 + 1.0) % 1.0;
  pushMatrix();
  translate(cx, cy);
  noStroke();
  // Dark disc background
  fill(22, 22, 45);
  circle(0, 0, r * 2);
  // Lit portion (skip at exact new moon to avoid degenerate shapes)
  if (phase > 0.01 && phase < 0.99) {
    boolean waxing = phase < 0.5;
    float termX = waxing ? r * cos(phase * TWO_PI) : -r * cos(phase * TWO_PI);
    float k  = 0.5523 * r;     // bezier magic for circle semicircle
    float kt = 0.5523 * termX; // bezier magic for terminator semiaxis
    fill(230, 220, 182);
    beginShape();
    vertex(0, -r);
    if (waxing) {              // lit on right
      bezierVertex( k, -r,  r, -k,  r, 0);
      bezierVertex( r,  k,  k,  r,  0, r);
    } else {                   // lit on left
      bezierVertex(-k, -r, -r, -k, -r, 0);
      bezierVertex(-r,  k, -k,  r,  0, r);
    }
    // Terminator: bottom (0,r) → (termX,0) → top (0,-r)
    bezierVertex(kt,  r,  termX,  k, termX,  0);
    bezierVertex(termX, -k,  kt, -r,     0, -r);
    endShape(CLOSE);
  }
  // Thin border ring
  stroke(55, 55, 88);
  strokeWeight(1);
  noFill();
  circle(0, 0, r * 2);
  noStroke();
  popMatrix();
}

// ─────────────────────────────────────────────────────────────────────────────

//Cardinal direction from heading
String cardinalFromHeading(float heading) {
    if (heading >= 337.5 || heading < 22.5) return "N";
    if (22.5 <= heading && heading < 67.5) return "NE";
    if (67.5 <= heading && heading < 112.5) return "E";
    if (112.5 <= heading && heading < 157.5) return "SE";
    if (157.5 <= heading && heading < 202.5) return "S";
    if (202.5 <= heading && heading < 247.5) return "SW";
    if (247.5 <= heading && heading < 292.5) return "W";
    if (292.5 <= heading && heading < 337.5) return "NW";
    return "";
}

// Draw a sparkline for a dataset
void sparkline(int x, int y, int wide, int tall, float minimum, float maximum, float lower, float upper, FloatList data) {
  float vertical_range = maximum - minimum;
  fill(cSparkBg);
  stroke(cSparkBorder);
  strokeWeight(2);
  // The range lines and the trace below both run from x - wide/2 to x + wide/2, so the box
  // has to be centred on x too. Drawn from the corner it sat half its own width to the
  // right of everything it was meant to contain. Restored straight after: this is the only
  // rect() in the sketch, but the mode is global and the next caller should not inherit it
  rectMode(CENTER);
  rect(x, y, wide, tall);
  rectMode(CORNER);
  strokeWeight(2);
  stroke(cSparkRange);
  float screen_y = y + tall / 2.0 - (upper - minimum) / vertical_range * tall;
  line(x - wide / 2, screen_y, x + wide / 2, screen_y);
  screen_y = y + tall / 2.0 - (lower - minimum) / vertical_range * tall;
  line(x - wide / 2, screen_y, x + wide / 2, screen_y);
  fill(cSparkData);
  stroke(cSparkData);
  strokeWeight(1);
  for (int i = 0; i < data.size(); i++) {
    float value = data.get(i);
    screen_y = y + tall / 2.0 - (value - minimum) / vertical_range * tall;
    circle(x - wide/2.0 + i * wide / data.size(), screen_y, 2);
  }
}

// Draw a rotary slider
void rotarySlider(float x, float y, float diameter, float lower, float upper, float level) {
  float ratio = (level - lower) / (upper - lower);
  ratio = max(min(ratio, 1.0), 0.0);
  noStroke();
  fill(cRotaryDisc);
  ellipse(x, y, diameter, diameter);
  fill(cRotaryArc);
  arc(x, y, diameter + 10, diameter + 10, PI / 4 - (3 * PI / 2) * (1.0 - ratio), 3 * PI / 4);
  ellipse(x, y, diameter / 2, diameter / 2);
  fill(cRotaryText);
  String s = str(int(level));
  textSize(85);
  neonText(s, x - 38, y + 20);
}

// Setup coordinate boundaries of the displayed map
void setupPOI(String name, ArrayList<PVector> list) {
  String[] geoCoords = loadStrings(mapDataDir + name + ".csv");
  WebMercator proj = new WebMercator();
  for (String line : geoCoords)
  {
    if (line.length() > 0) {
      String[] geoCoord = split(line.trim(), ",");
      if (geoCoord.length > 1) {
        float lon = float(geoCoord[0]);
        float lat = float(geoCoord[1]);
        list.add(proj.transformCoords(new PVector(lon, lat)));
      }
    }
  }
}

// Our camp and the burn, written per season by kml_parsing/mark_places.py as
// name,glyph,lon,lat. A season without the file simply has no marks to draw.
void setupPlaces() {
  String path = mapDataDir + "places.csv";
  if (!new java.io.File(path).exists()) return;
  String[] rows = loadStrings(path);
  if (rows == null) return;
  WebMercator proj = new WebMercator();
  for (String row : rows) {
    if (row.trim().length() == 0) continue;
    String[] field = split(row.trim(), ",");
    if (field.length < 4) continue;
    float lon = float(field[2]);
    float lat = float(field[3]);
    if (Float.isNaN(lon) || Float.isNaN(lat)) continue;
    PVector point = proj.transformCoords(new PVector(lon, lat));
    point.z = field[1].trim().equals("flame") ? 1 : 0;
    places.add(point);
  }
}

// A ranger station, written as a small r. The sketch never sets textAlign and so relies on
// the default everywhere else, which is why the whole style is pushed and popped around
// this: centring the letter here would otherwise re-centre every label drawn after it.
void drawRanger(float x, float y, float size) {
  pushStyle();
  pushMatrix();
  translate(x, y);
  fill(cRanger);
  textAlign(CENTER, CENTER);
  textSize(size);
  text("r", 0, 0);
  popMatrix();
  popStyle();
}

// A porto: a door taller than it is wide, with the vent knocked out of it. The vent is a
// real hole rather than a slot painted in the background colour, because these sit on the
// city fill, on the open playa and on the Man's ground, and a painted slot is only ever
// right on one of them.
PShape boothOutline(float x, float y, float h) {
  float w = h * 0.62;
  float vw = h * 0.34, vt = h * 0.55, vb = h * 0.21;
  PShape booth = createShape();
  booth.beginShape();
  booth.vertex(x - w, y - h); booth.vertex(x + w, y - h);
  booth.vertex(x + w, y + h); booth.vertex(x - w, y + h);
  booth.beginContour();
  booth.vertex(x - vw, y - vt); booth.vertex(x - vw, y - vb);
  booth.vertex(x + vw, y - vb); booth.vertex(x + vw, y - vt);
  booth.endContour();
  booth.endShape(CLOSE);
  booth.disableStyle();
  booth.setFill(cToilet);
  booth.setStroke(false);
  return booth;
}

// The first aid cross: equal arms, so it reads the same way up whichever way the map is
// turned. Half the width across the arms is what makes it a cross rather than a plus sign
PShape crossOutline(float x, float y, float h) {
  float t = h * 0.34;
  PShape cross = createShape();
  cross.beginShape();
  cross.vertex(x - t, y - h); cross.vertex(x + t, y - h); cross.vertex(x + t, y - t);
  cross.vertex(x + h, y - t); cross.vertex(x + h, y + t); cross.vertex(x + t, y + t);
  cross.vertex(x + t, y + h); cross.vertex(x - t, y + h); cross.vertex(x - t, y + t);
  cross.vertex(x - h, y + t); cross.vertex(x - h, y - t); cross.vertex(x - t, y - t);
  cross.endShape(CLOSE);
  cross.disableStyle();
  cross.setFill(cFirstAid);
  cross.setStroke(false);
  return cross;
}

// The baked shapes above are fixed where they were built, so they cannot follow the lens.
// These draw the same two glyphs a point at a time instead, and are used only while an
// effect is bending the map. Like the rangers and the stars, only the centre is moved:
// at eight or nine pixels across there is nothing in the glyph itself worth distorting
void drawBooth(float x, float y, float h) {
  float w = h * 0.62;
  float vw = h * 0.34, vt = h * 0.55, vb = h * 0.21;
  beginShape();
  vertex(x - w, y - h); vertex(x + w, y - h);
  vertex(x + w, y + h); vertex(x - w, y + h);
  beginContour();
  vertex(x - vw, y - vt); vertex(x - vw, y - vb);
  vertex(x + vw, y - vb); vertex(x + vw, y - vt);
  endContour();
  endShape(CLOSE);
}

void drawCross(float x, float y, float h) {
  float t = h * 0.34;
  beginShape();
  vertex(x - t, y - h); vertex(x + t, y - h); vertex(x + t, y - t);
  vertex(x + h, y - t); vertex(x + h, y + t); vertex(x + t, y + t);
  vertex(x + t, y + h); vertex(x - t, y + h); vertex(x - t, y + t);
  vertex(x - h, y + t); vertex(x - h, y - t); vertex(x - t, y - t);
  endShape(CLOSE);
}

// Built after the POI lists are loaded, and again whenever the map reloads to another year
// and every one of these positions moves
void buildMarkerShapes() {
  boothShape = createShape(GROUP);
  for (int i = 0; i < toilets.size(); i++) {
    PVector at = geoToScreen(toilets.get(i));
    boothShape.addChild(boothOutline(at.x + offset, at.y, PORTO_R));
  }
  crossShape = createShape(GROUP);
  for (int i = 0; i < firstAid.size(); i++) {
    PVector at = geoToScreen(firstAid.get(i));
    crossShape.addChild(crossOutline(at.x + offset, at.y, FIRST_AID_R));
  }
  // The group keeps a style of its own, and it is the group that gets drawn. Disabling it
  // only on the children left the group painting them in whatever it had stored rather
  // than in the fill set at the call, which is how the portos and the cross lost their
  // colours. Belt and braces: they are also given the right fill outright, so the shapes
  // are correct whichever style ends up winning
  boothShape.disableStyle();
  crossShape.disableStyle();
}

// A five pointed star. It turns with the city rather than against it, so it sits the same
// way up as everything else the map draws
void drawStar(float x, float y, float r) {
  pushMatrix();
  translate(x, y);
  fill(cCamp);
  beginShape();
  for (int i = 0; i < 10; i++) {
    float a = radians(-90 + i * 36);
    float reach = (i % 2 == 0) ? r : r * 0.42;
    vertex(reach * cos(a), reach * sin(a));
  }
  endShape(CLOSE);
  popMatrix();
}

// Fire, not a droplet: a tall tip with a second lick beside it and the notch between them
// doing most of the work, over a hotter core. A plain teardrop read as water at any size.
void drawFlame(float x, float y, float r) {
  pushMatrix();
  translate(x, y);
  fill(cBurn);
  beginShape();
  vertex(0.10*r, -1.55*r);
  bezierVertex( 0.55*r,-0.95*r,  0.78*r,-0.40*r,  0.74*r, 0.18*r);
  bezierVertex( 0.72*r, 0.75*r,  0.38*r, 1.08*r,  0.00*r, 1.08*r);
  bezierVertex(-0.38*r, 1.08*r, -0.72*r, 0.75*r, -0.72*r, 0.18*r);
  bezierVertex(-0.72*r,-0.20*r, -0.52*r,-0.46*r, -0.44*r,-0.86*r);
  bezierVertex(-0.40*r,-1.05*r, -0.30*r,-0.98*r, -0.28*r,-0.80*r);
  bezierVertex(-0.24*r,-0.48*r, -0.06*r,-0.85*r,  0.10*r,-1.55*r);
  endShape(CLOSE);
  fill(cBurnCore);
  beginShape();
  vertex(0.06*r, -0.70*r);
  bezierVertex( 0.32*r,-0.30*r,  0.40*r, 0.08*r,  0.38*r, 0.34*r);
  bezierVertex( 0.36*r, 0.68*r,  0.18*r, 0.84*r,  0.00*r, 0.84*r);
  bezierVertex(-0.18*r, 0.84*r, -0.38*r, 0.68*r, -0.38*r, 0.34*r);
  bezierVertex(-0.38*r, 0.04*r, -0.14*r,-0.32*r,  0.06*r,-0.70*r);
  endShape(CLOSE);
  popMatrix();
}

void buildShapes() {
  city = createShape();
  city.beginShape();
  city.noStroke();
  for (int i = 0; i < city_bounds.size() - 1; i++) {
    if (city_bounds.get(i).x != 0 && city_bounds.get(i + 1).x != 0) {
      PVector s = geoToScreen(city_bounds.get(i));
      PVector e = geoToScreen(city_bounds.get(i + 1));
      city.vertex(s.x + offset, s.y);
      city.vertex(e.x + offset, e.y);
    }
  }
  city.endShape(CLOSE);
  city.disableStyle();

  man = createShape();
  man.beginShape();
  man.noStroke();
  for (int i = 0; i < man_ring.size() - 1; i++) {
    if (man_ring.get(i).x != 0 && man_ring.get(i + 1).x != 0) {
      PVector s = geoToScreen(man_ring.get(i));
      PVector e = geoToScreen(man_ring.get(i + 1));
      man.vertex(s.x + offset, s.y);
      man.vertex(e.x + offset, e.y);
    }
  }
  man.endShape(CLOSE);
  man.disableStyle();

  streetShape = createShape();
  streetShape.beginShape(LINES);
  for (int i = 0; i < coords.size() - 1; i++) {
    if (coords.get(i).x != 0 && coords.get(i + 1).x != 0) {
      PVector from = geoToScreen(coords.get(i));
      PVector to = geoToScreen(coords.get(i + 1));
      streetShape.vertex(from.x + offset, from.y);
      streetShape.vertex(to.x + offset, to.y);
    }
  }
  streetShape.endShape();
  streetShape.disableStyle();
}

void reloadMapForYear(String year) {
  if (year.equals(currentMapYear)) return;
  currentMapYear = year;

  String kmlDir = sketchPath("../kml_parsing/" + year + "/layers/");
  String dataDir = sketchPath("data/" + year + "/");
  if (new java.io.File(kmlDir).exists())       mapDataDir = kmlDir;
  else if (new java.io.File(dataDir).exists()) mapDataDir = dataDir;
  else                                          mapDataDir = sketchPath("data/");
  println("Map data dir for " + year + ": " + mapDataDir);

  coords.clear(); man_ring.clear(); city_bounds.clear();
  firstAid.clear(); toilets.clear(); ranger.clear(); places.clear();
  setupGeo();
  buildShapes();
  setupPOI("toilets", toilets);
  setupPOI("first_aid", firstAid);
  setupPOI("ranger", ranger);
  setupPlaces();
  buildMarkerShapes();
}

// Setup coordinate boundaries of the displayed map
void setupGeo() {
  drawGeo(loadStrings(mapDataDir + "lines.csv"), coords);
  drawGeo(loadStrings(mapDataDir + "man_ring.csv"), man_ring);
  drawGeo(loadStrings(mapDataDir + "10_00.csv"), city_bounds);
  drawGeo(loadStrings(mapDataDir + "city_bounds.csv"), city_bounds);
  drawGeo(reverse(loadStrings(mapDataDir + "2_00.csv")), city_bounds);
  drawGeo(reverse(loadStrings(mapDataDir + "kelter.csv")), city_bounds);
}

void drawGeo(String[] geoCoords, ArrayList<PVector> vector) {
  WebMercator proj = new WebMercator();
  float left = 0.0;
  float upper = 0.0;
  float right = -999.0;
  float lower = 999.0;
  for (String line : geoCoords)
  {
    if (line.length() > 0) {
      String[] geoCoord = split(line.trim(), ",");
      if (geoCoord.length > 1) {
        float lon = float(geoCoord[0]);
        float lat = float(geoCoord[1]);
        left = min(left, lon);
        upper = max(upper, lat);
        right = max(right, lon);
        lower = min(lower, lat);
        vector.add(proj.transformCoords(new PVector(lon, lat)));
      }
    } else vector.add(new PVector(0.0, 0.0));
  }
  if (vector == coords) {
    tlCorner = proj.transformCoords(new PVector(left - 0.015, upper + 0.003));
    brCorner = proj.transformCoords(new PVector(right + 0.015, lower - 0.003));
  }
}

// Handle the IM JSON document update
void handleImu(String imu) {
  JSONObject json = parseJSONObject(imu);
  if (json == null) {
    println("JSONObject could not be parsed");
  } else {
    heading = json.getJSONObject("heading").getFloat("heading") - 15.0;
  }
}

// Handle the new pressure value
void handlePressure(float new_pressure) {
  pressure = new_pressure;
  if (track_pressure.size() > 500) track_pressure.remove(0);
  track_pressure.append(pressure);
}

// Handle the new heading value
void handleHeading(float new_heading) {
  heading = new_heading;
}

// Handle the new pressure value
void handleTemperature(float new_temperature) {
  temperature = new_temperature;
  if (track_temperature.size() > 50) track_temperature.remove(0);
  track_temperature.append(temperature);
}

// Handle the position update
void handleLat(float new_lat) {
  lat = new_lat + (ORIGIN_LAT - OAKLAND_LAT);
  track.add(proj.transformCoords(new PVector(lon, lat, speed)));
}

// Handle the position update
void handleLon(float new_lon) {
  lon = new_lon + (ORIGIN_LON - OAKLAND_LON);
  track.add(proj.transformCoords(new PVector(lon, lat, speed)));
}

// Handle the speed update
void handleSpeed(float new_speed) {
  speed = new_speed;
  track.add(proj.transformCoords(new PVector(lon, lat, speed)));
}

// Handle the free disk update
void handleFreeDisk(float new_free) {
  free_disk = new_free;
}

// Handle the water heater update
void handleWaterHeater(float new_value) {
  water_heater = new_value;
}

// Handle the lower water temp update
void handleLowerTemp(float new_value) {
  lower_temp = new_value;
}

// Handle the lower water temp update
void handleUpperTemp(float new_value) {
  upper_temp = new_value;
}

// Handle the engine status update
void handleEngine(float new_value) {
  engine = new_value;
}

// Handle the moving status update
void handleMoving(float new_value) {
  moving = new_value;
}

// Handle a poof count update
void handlePoofCount(float new_value) {
  poof_count = new_value;
}

// Handle a new OSC message
void oscEvent(OscMessage theOscMessage) {
  try {
    String message = theOscMessage.addrPattern();
    if (message.equals("/imu")) handleImu(theOscMessage.get(0).stringValue());
    else if (message.equals("/heading")) handleHeading(theOscMessage.get(0).floatValue());
    else if (message.equals("/pressure")) handlePressure(theOscMessage.get(0).floatValue());
    else if (message.equals("/temperature")) handleTemperature(theOscMessage.get(0).floatValue());
    else if (message.equals("/position/lat")) handleLat(theOscMessage.get(0).floatValue());
    else if (message.equals("/position/lon")) handleLon(theOscMessage.get(0).floatValue());
    else if (message.equals("/position/inferred_speed")) handleSpeed(theOscMessage.get(0).floatValue());
    else if (message.equals("/free_disk")) handleFreeDisk(theOscMessage.get(0).floatValue());
    else if (message.equals("/water_heater")) handleWaterHeater(theOscMessage.get(0).floatValue());
    else if (message.equals("/lower_temp")) handleLowerTemp(theOscMessage.get(0).floatValue());
    else if (message.equals("/upper_temp")) handleUpperTemp(theOscMessage.get(0).floatValue());
    else if (message.equals("/engine")) handleEngine(theOscMessage.get(0).floatValue());
    else if (message.equals("/moving")) handleMoving(theOscMessage.get(0).floatValue());
    else if (message.equals("/poof_count")) handlePoofCount(theOscMessage.get(0).floatValue());
  }
  catch (Exception e) {
    println(e);
  }
}

// Path format for zip entries: "ZIP:/abs/path/to/file.zip|entryname.csv"
String[] readCsvLines(String path) {
  if (path.startsWith("ZIP:")) {
    String[] parts = path.substring(4).split("\\|", 2);
    try {
      java.util.zip.ZipFile zf = new java.util.zip.ZipFile(parts[0]);
      java.util.zip.ZipEntry ze = zf.getEntry(parts[1]);
      if (ze == null) { zf.close(); return null; }
      java.io.BufferedReader br = new java.io.BufferedReader(
        new java.io.InputStreamReader(zf.getInputStream(ze)));
      ArrayList<String> lines = new ArrayList<String>();
      String line;
      while ((line = br.readLine()) != null) lines.add(line);
      br.close(); zf.close();
      return lines.toArray(new String[0]);
    } catch (Exception e) { println("ZIP read error: " + e); return null; }
  }
  return loadStrings(path);
}

// Returns the noon-to-noon bucket date (YYYYMMDD) for a positions_ or heading_ filename
String noonToBucket(String filename) {
  int firstUnder = filename.indexOf('_');
  String inner = filename.substring(firstUnder + 1, filename.length() - 4); // "YYYYMMDD_HH" or "YYYYMMDD_HH_MM"
  String[] parts = inner.split("_");
  int yr = int(parts[0].substring(0, 4));
  int mo = int(parts[0].substring(4, 6));
  int dy = int(parts[0].substring(6, 8));
  int hr = (parts.length > 1) ? int(parts[1]) : 0;
  if (hr < 12) {
    java.util.Calendar cal = java.util.Calendar.getInstance();
    cal.set(yr, mo - 1, dy);
    cal.add(java.util.Calendar.DAY_OF_MONTH, -1);
    return String.format("%04d%02d%02d", cal.get(java.util.Calendar.YEAR),
      cal.get(java.util.Calendar.MONTH) + 1, cal.get(java.util.Calendar.DAY_OF_MONTH));
  }
  return parts[0];
}

String sessionLabel(int idx) {
  if (idx < 0 || idx >= replaySessions.size()) return "";
  ArrayList<String> session = replaySessions.get(idx);
  if (session.size() == 0) return "";
  String first = session.get(0);
  String name = first.contains("|") ? first.substring(first.lastIndexOf('|') + 1)
                                    : first.substring(first.lastIndexOf('/') + 1);
  String bucket = noonToBucket(name);
  return bucket.substring(0,4) + "-" + bucket.substring(4,6) + "-" + bucket.substring(6,8) + " noon";
}

// Scan positions/ for positions_*.zip and heading_*.zip, grouped into noon-to-noon sessions
void setupReplay() {
  java.io.File folder = new java.io.File(sketchPath("positions"));
  String[] all = folder.list();
  if (all == null) return;
  java.util.Arrays.sort(all);

  java.util.TreeMap<String, ArrayList<String>> posBuckets = new java.util.TreeMap<String, ArrayList<String>>();

  for (String f : all) {
    String fl = f.toLowerCase();
    if (f.endsWith("~") || !fl.endsWith(".zip")) continue;
    if (!f.startsWith("positions_")) continue;
    String zipPath = sketchPath("positions/" + f);
    try {
      java.util.zip.ZipFile zf = new java.util.zip.ZipFile(zipPath);
      java.util.Enumeration<? extends java.util.zip.ZipEntry> e = zf.entries();
      while (e.hasMoreElements()) {
        String name = e.nextElement().getName();
        if (name.startsWith("positions_") && name.endsWith(".csv")) {
          String bucket = noonToBucket(name);
          if (!posBuckets.containsKey(bucket)) posBuckets.put(bucket, new ArrayList<String>());
          posBuckets.get(bucket).add("ZIP:" + zipPath + "|" + name);
        }
      }
      zf.close();
    } catch (Exception e) { println("ZIP scan error: " + e); }
  }

  replaySessions = new ArrayList<ArrayList<String>>();
  ArrayList<String> keys = new ArrayList<String>(posBuckets.keySet());
  java.util.Collections.reverse(keys);
  for (String key : keys) {
    ArrayList<String> pos = posBuckets.get(key);
    java.util.Collections.sort(pos);
    replaySessions.add(pos);
    println("Session " + key + ": " + pos.size() + " files");
  }
  currentReplaySession = 0;
}

void loadReplaySession(ArrayList<String> posPaths) {
  replayData = new ArrayList<PVector>();
  DateFormat parser = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");
  long startMs = -1;
  long lastMs  = -1;

  for (String path : posPaths) {
    String[] lines = readCsvLines(path);
    if (lines == null || lines.length < 2) continue;
    for (int i = 1; i < lines.length; i++) {
      String row = lines[i].trim();
      if (row.length() == 0) continue;
      String[] cols = split(row, ",");
      if (cols.length < 3) continue;
      try {
        Date d = parser.parse(cols[0].substring(0, 19));
        long ms = d.getTime();
        if (startMs < 0) startMs = ms;
        if (ms <= lastMs) continue;
        lastMs = ms;
        replayData.add(new PVector(float(cols[2]), float(cols[1]), (ms - startMs) / 1000.0));
      } catch (Exception e) {}
    }
  }
  println("Loaded " + replayData.size() + " points across " + posPaths.size() + " files");
}

void startReplay() {
  if (replaySessions.size() == 0) return;
  ArrayList<String> session = replaySessions.get(currentReplaySession);
  if (session.size() == 0) return;
  String first = session.get(0);
  String entryName = first.contains("|") ? first.substring(first.lastIndexOf('|') + 1)
                                         : first.substring(first.lastIndexOf('/') + 1);
  if (entryName.startsWith("positions_") && entryName.length() >= 14)
    reloadMapForYear(entryName.substring(10, 14));
  loadReplaySession(session);
  track.clear();
  replayIndex = 0;
  replayStartMillis = millis();
  replaying = true;
}

void stopReplay() {
  replaying = false;
}

void updateReplay() {
  if (!replaying || replayData == null || replayData.size() == 0) return;
  float elapsed = (millis() - replayStartMillis) / 1000.0 * REPLAY_SPEED;

  // Advance position
  while (replayIndex < replayData.size() - 1 && replayData.get(replayIndex).z <= elapsed) {
    PVector p = replayData.get(replayIndex);
    PVector next = replayData.get(replayIndex + 1);
    lat = p.y;
    lon = p.x;
    float dt = next.z - p.z;
    float dlat = (next.y - p.y) * 111000.0;
    float dlon = (next.x - p.x) * 111000.0 * cos(radians(p.y));
    float spd = (dt > 0) ? sqrt(dlat*dlat + dlon*dlon) / dt : 0;
    track.add(proj.transformCoords(new PVector(lon, lat, spd)));
    replayIndex++;
  }

  if (replayIndex >= replayData.size() - 1) stopReplay();
}

void keyPressed() {
  if (key == 'r' || key == 'R') {
    if (replaying) stopReplay();
    else startReplay();
  } else if (key == CODED) {
    int n = max(replaySessions.size(), 1);
    if (keyCode == UP) {
      currentReplaySession = (currentReplaySession + 1) % n;
      if (replaying) startReplay();
    } else if (keyCode == DOWN) {
      currentReplaySession = (currentReplaySession - 1 + n) % n;
      if (replaying) startReplay();
    }
  } else if (key == 'f' || key == 'F') {
    showFrameTime = !showFrameTime;
    frameMillis = 0;
  } else if (key == 'e' || key == 'E') {
    startEffect(int(random(EFFECT_COUNT)));
    println("Effect: " + effectName(effectKind) + " for " + effectRuns + "ms");
  } else if (key == 'w' || key == 'W') {
    effectsOn = !effectsOn;
    if (!effectsOn) effectKind = -1;
    else scheduleEffect();
    println("Weirdness " + (effectsOn ? "on" : "off") + " ('e' fires one either way)");
  } else if (key == '+' || key == '=') {
    REPLAY_SPEED = min(REPLAY_SPEED * 2, 3600);
  } else if (key == '-') {
    REPLAY_SPEED = max(REPLAY_SPEED / 2, 1);
  }
}

// The track, drawn straight. This was tried as a cached layer that only took new points,
// on the theory that redrawing every point each frame was the expensive part. Measurement
// said otherwise: the full screen alpha blit that fetched the layer back cost 39.5ms of a
// 47ms frame with a single point in it, while these circles cost about a thousandth of a
// millisecond each. The layer only broke even around twenty thousand points and lost
// badly everywhere below that, so it is gone.
void paintTrack() {
  strokeWeight(2);
  for (int i = 0; i < track.size(); i++) {
    PVector at = geoToScreen(track.get(i));
    PVector point = warp(at.x + offset, at.y);
    float speed = track.get(i).z;
    color band = speed > 10 ? cTrackFast : (speed > 5 ? cTrackMed : cTrackSlow);
    fill(band);
    stroke(band);
    circle(point.x, point.y, 5);
  }
}

// The Man in the space the map is drawn in, before the base transform turns it. The lens
// works here so that it bends the city rather than the screen
PVector manMapPoint() {
  if (man_ring.size() == 0) return new PVector(width / 2.0, height / 2.0);
  float sx = 0, sy = 0;
  for (int i = 0; i < man_ring.size(); i++) {
    sx += man_ring.get(i).x;
    sy += man_ring.get(i).y;
  }
  PVector centre = geoToScreen(new PVector(sx / man_ring.size(), sy / man_ring.size()));
  return new PVector(centre.x + offset, centre.y);
}

// Where the Man actually sits on the screen. The effects turn the city about him rather
// than about the middle of the display, which is a different point entirely once the map
// has been offset. Forty nine vertices is cheap enough to work out every frame, and that
// way there is no cached pivot to go stale when the map reloads to another year.
PVector manPivot() {
  if (man_ring.size() == 0) return new PVector(width / 2.0, height / 2.0);
  float sx = 0, sy = 0;
  for (int i = 0; i < man_ring.size(); i++) {
    sx += man_ring.get(i).x;
    sy += man_ring.get(i).y;
  }
  PVector centre = geoToScreen(new PVector(sx / man_ring.size(), sy / man_ring.size()));
  // The base transform turns the map about the bottom right corner, so a thing drawn at
  // (px, py) comes to rest on the screen at (width - px, height - py)
  return new PVector(width - (centre.x + offset), height - centre.y);
}

// Map from a geographic position to the screen location
PVector geoToScreen(PVector geo) {
  return new PVector(map(geo.x, tlCorner.x, brCorner.x, 0, width),
    map(geo.y, tlCorner.y, brCorner.y, 0, height));
}

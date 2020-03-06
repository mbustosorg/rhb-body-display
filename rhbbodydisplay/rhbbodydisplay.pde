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

OscP5 oscP5;

WebMercator proj = new WebMercator();

ArrayList<PVector>coords;  
ArrayList<PVector>firstAid;
ArrayList<PVector>toilets;  
ArrayList<PVector>ranger;  

ArrayList<PVector>track;

PVector tlCorner, brCorner;

float heading = 0.0;
int pressure = 0;
float temperature = 0.0;
float lon = 0.0;
float lat = 0.0;
float ORIGIN_LON = -119.21;
float ORIGIN_LAT = 40.79;

PImage backgroundMap;

void setup() {
  coords = new ArrayList<PVector>();  
  firstAid = new ArrayList<PVector>();  
  toilets = new ArrayList<PVector>();  
  ranger = new ArrayList<PVector>();
  track = new ArrayList<PVector>();
  
  setupGeo();
  setupPOI("toilets", toilets);
  setupPOI("first_aid", firstAid);
  setupPOI("ranger", ranger);
  
  int wide = int(abs((tlCorner.x - brCorner.x) / abs(tlCorner.y - brCorner.y) * 1000));
  print(wide);
  size(820, 1000);
  frameRate(25);
  oscP5 = new OscP5(this, 10002);
}

void draw() {
  background(202, 226, 245);
  fill(206, 173, 146);
  stroke(40);
  textSize(32);  
  fill(0);
  for (int i = 0; i < coords.size() - 1; i++) {
    if (coords.get(i).x != 0 && coords.get(i + 1).x != 0) {
      PVector startCoord = geoToScreen(coords.get(i));
      PVector endCoord = geoToScreen(coords.get(i + 1));
      line(startCoord.x, startCoord.y, endCoord.x, endCoord.y);
    }
  }
  stroke(0);
  fill(0, 0, 255);
  for (int i = 0; i < toilets.size(); i++) {
    PVector coord = geoToScreen(toilets.get(i));
    circle(coord.x, coord.y, 10);
  }
  fill(0, 255, 0);
  for (int i = 0; i < firstAid.size(); i++) {
    PVector coord = geoToScreen(firstAid.get(i));
    circle(coord.x, coord.y, 10);
  }
  fill(150, 75, 0);
  for (int i = 0; i < ranger.size(); i++) {
    PVector coord = geoToScreen(ranger.get(i));
    circle(coord.x, coord.y, 10);
  }
  fill(150);
  noStroke();
  for (int i = 0; i < track.size(); i++) {
    PVector coord = geoToScreen(track.get(i));
    circle(coord.y, coord.x, 1);
  }
  stroke(40);
  textSize(32);  
  fill(0);
  text("Lat: " + str(int(lat * 100) / 100.0), 10, 30);
  text("Lon: " + str(int(lon * 100) / 100.0), 10, 60);
  text("Pressure: " + str(pressure), 10, 90);
  text("Heading: " + str(int(heading)), 10, 120);
  text("Bath: " + str(int(temperature)), 10, 150);
  PVector rhb = geoToScreen(proj.transformCoords(new PVector(lon, lat)));
  fill(#FF0000);
  rectMode(CENTER);
  translate(rhb.y, rhb.x);
  rotate(radians(heading)); 
  square(0, 0, 10);
}

// Setup coordinate boundaries of the displayed map
void setupPOI(String name, ArrayList<PVector> list) {
  String[] geoCoords = loadStrings(name + ".csv");
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

// Setup coordinate boundaries of the displayed map
void setupGeo() {
  String[] geoCoords = loadStrings("lines.csv");
  WebMercator proj = new WebMercator();
  // Convert the GPS coordinates from lat/long to WebMercator
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
        coords.add(proj.transformCoords(new PVector(lon, lat)));
      }
    } else coords.add(new PVector(0.0, 0.0));
  } 
  tlCorner = proj.transformCoords(new PVector(left - 0.01, upper + 0.01));
  brCorner = proj.transformCoords(new PVector(right + 0.01, lower - 0.01));
}

// Handle the IM JSON document update
void handleImu(String imu) {
  JSONObject json = parseJSONObject(imu);	
  if (json == null) {
    println("JSONObject could not be parsed");
  } else {
    heading = json.getJSONObject("heading").getFloat("heading");
  }
}

// Handle the new pressure value
void handlePressure(int new_pressure) {
  pressure = new_pressure;
}

// Handle the new pressure value
void handleTemperature(float new_temperature) {
  temperature = new_temperature;
}

// Handle the position update
void handlePosition(float new_lat, float new_lon) {
  if (lon == 0.0) {
    ORIGIN_LAT = ORIGIN_LAT - new_lat;
    ORIGIN_LON = ORIGIN_LON - new_lon;
  }
  lat = new_lat + ORIGIN_LAT;
  lon = new_lon + ORIGIN_LON;
  track.add(proj.transformCoords(new PVector(lon, lat)));
}

// Handle a new OSC message
void oscEvent(OscMessage theOscMessage) {
  try {
    String message = theOscMessage.addrPattern();
    if (message.equals("/imu")) handleImu(theOscMessage.get(0).stringValue());
    else if (message.equals("/pressure")) handlePressure(theOscMessage.get(0).intValue());
    else if (message.equals("/temperature")) handleTemperature(theOscMessage.get(0).floatValue());
    else if (message.equals("/position")) handlePosition(theOscMessage.get(0).floatValue(), theOscMessage.get(1).floatValue());
  } 
  catch (Exception e) {
    println(e);
  }
}

// Map from a geographic position to the screen location
PVector geoToScreen(PVector geo) {
  return new PVector(map(geo.x, tlCorner.x, brCorner.x, 0, width), 
    map(geo.y, tlCorner.y, brCorner.y, 0, height));
}

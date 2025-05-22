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
ArrayList<PVector>man_ring;  
ArrayList<PVector>city_bounds;  

ArrayList<PVector>track;
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
//float ORIGIN_LON =  -119.2175207;
//float ORIGIN_LAT = 40.7851999;
//float ORIGIN_LON = -119.2544;
//float ORIGIN_LAT = 40.7658;
// Testing at home
float ORIGIN_LON =  -119.2175207;
float ORIGIN_LAT = 40.7851999;
float OAKLAND_LON = -122.2537901;
float OAKLAND_LAT = 37.8504158;
// On playa
//float ORIGIN_LON = 0.0;
//float ORIGIN_LAT = 0.0;
//float OAKLAND_LON = 0.0;
//float OAKLAND_LAT = 0.0;

int lastSecond = 0;
boolean testing = false;

PImage backgroundMap;

PShape city;
PShape man;
int offset = 100;


void setup() {
  coords = new ArrayList<PVector>();  
  firstAid = new ArrayList<PVector>();  
  toilets = new ArrayList<PVector>();  
  ranger = new ArrayList<PVector>();
  track = new ArrayList<PVector>();
  man_ring = new ArrayList<PVector>();
  city_bounds = new ArrayList<PVector>();
  track_pressure = new FloatList();
  track_pressure.append(50.0);
  track_temperature = new FloatList();
  track_temperature.append(13.0);
  track.add(proj.transformCoords(new PVector(ORIGIN_LON, ORIGIN_LAT)));
  
  setupGeo();
  
  city = createShape();
  city.beginShape();
  city.fill(200, 200, 255);
  city.noStroke();
  PVector startCoord = null;
  PVector endCoord = null;
  for (int i = 0; i < city_bounds.size() - 1; i++) {
    if (city_bounds.get(i).x != 0 && city_bounds.get(i + 1).x != 0) {
      startCoord = geoToScreen(city_bounds.get(i));
      endCoord = geoToScreen(city_bounds.get(i + 1));
      city.vertex(startCoord.x + offset, startCoord.y);
      city.vertex(endCoord.x + offset, endCoord.y);
    }
  }
  city.endShape(CLOSE);
  
  man = createShape();
  man.beginShape();
  man.fill(150, 0, 0);
  man.noStroke();
  startCoord = null;
  endCoord = null;
  for (int i = 0; i < man_ring.size() - 1; i++) {
    if (man_ring.get(i).x != 0 && man_ring.get(i + 1).x != 0) {
      startCoord = geoToScreen(man_ring.get(i));
      endCoord = geoToScreen(man_ring.get(i + 1));
      man.vertex(startCoord.x + offset, startCoord.y);
      man.vertex(endCoord.x + offset, endCoord.y);
    }
  }
  man.endShape(CLOSE);

  setupPOI("toilets", toilets);
  setupPOI("first_aid", firstAid);
  setupPOI("ranger", ranger);
  
  int wide = int(abs((tlCorner.x - brCorner.x) / abs(tlCorner.y - brCorner.y) * 1000));
  fullScreen();
  //size(500, 1000);
  frameRate(25);
  oscP5 = new OscP5(this, 10002);
  frameRate(10);
  
  String home_directory = "/Users/mauricio/Documents/development/projects/rhb-sensor-monitor/data-0828";
  //String home_directory = "/home/pi/development/data";
  java.io.File folder = new java.io.File(home_directory);
  
  String[] filenames = folder.list();
  Date now = new Date();
  DateFormat parser = new SimpleDateFormat("'positions_circle_'yyyyMMdd_hh_mm'.csv'");
  DateFormat timestamp_parser = new SimpleDateFormat("yyyy-MM-dd'T'hh:mm:ss");  println(now);
  for (int i = 0; i < filenames.length; i++) {
    if (filenames[i].contains("positions_circle_20240829_04_05.csv")) {
      try{
        Date date = parser.parse(filenames[i]);
        long diffInMillies = Math.abs(now.getTime() - date.getTime());
        long diff = TimeUnit.DAYS.convert(diffInMillies, TimeUnit.MILLISECONDS);
        //if (diff < 3) {
          println(filenames[i]);
          Table table = loadTable(home_directory + "/" + filenames[i], "header");
          for (TableRow row : table.rows()) {
            //println(row.getString("timestamp").substring(0, 19));
            try{
              Date timestamp_date = timestamp_parser.parse(row.getString("timestamp").substring(0, 19));
              long timestamp_diff = Math.abs(now.getTime() - timestamp_date.getTime());
              long hours_diff = TimeUnit.SECONDS.convert(timestamp_diff, TimeUnit.MILLISECONDS);
              //if (hours_diff < 12) {
                float lat = row.getFloat("lat") + (ORIGIN_LAT - OAKLAND_LAT);
                float lon = row.getFloat("lon") + (ORIGIN_LON - OAKLAND_LON);
                PVector coord = proj.transformCoords(new PVector(lon, lat));
                track.add(new PVector(coord.x, coord.y, 7.0));
              //}
            } catch (Exception e) {
              e.printStackTrace();
            } 
          }
        //}
      } catch (Exception e) {
        e.printStackTrace();
      } 
    }
  }

  colorMode(RGB, 255);
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
  boolean flashOn = millis() - (millis() / 1000) * 1000.0 > 500.0;
  
  background(100, 150, 245);

  shape(city, 0, 0);
  shape(man, 0, 0);
  
  stroke(40);
  textSize(32);  
  fill(0);
  for (int i = 0; i < coords.size() - 1; i++) {
    if (coords.get(i).x != 0 && coords.get(i + 1).x != 0) {
      PVector startCoord = geoToScreen(coords.get(i));
      PVector endCoord = geoToScreen(coords.get(i + 1));
      line(startCoord.x + offset, startCoord.y, endCoord.x + offset, endCoord.y);
    }
  }
  strokeWeight(10);
  stroke(150, 0, 0);
  for (int i = 0; i < man_ring.size() - 1; i++) {
    if (man_ring.get(i).x != 0 && man_ring.get(i + 1).x != 0) {
      PVector startCoord = geoToScreen(man_ring.get(i));
      PVector endCoord = geoToScreen(man_ring.get(i + 1));
      line(startCoord.x + offset, startCoord.y, endCoord.x + offset, endCoord.y);
    }
  }
  strokeWeight(2);
  stroke(0);
  fill(0, 0, 255);
  for (int i = 0; i < toilets.size(); i++) {
    PVector coord = geoToScreen(toilets.get(i));
    circle(coord.x + offset, coord.y, 10);
  }
  fill(0, 255, 0);
  for (int i = 0; i < firstAid.size(); i++) {
    PVector coord = geoToScreen(firstAid.get(i));
    circle(coord.x + offset, coord.y, 10);
  }
  fill(150, 75, 0);
  for (int i = 0; i < ranger.size(); i++) {
    PVector coord = geoToScreen(ranger.get(i));
    circle(coord.x + offset, coord.y, 10);
  }
  fill(200, 0, 200);
  noStroke();
  PVector coord = null;
  for (int i = 0; i < track.size(); i++) {
    coord = geoToScreen(track.get(i));
    if (track.get(i).z > 10) stroke(200, 0, 0);
    else if (track.get(i).z > 5) stroke(200, 200, 0);
    else stroke(100, 200, 100);
    circle(coord.x + offset, coord.y, 2);
  }
  if (coord != null) {
    color now_point = get(int(coord.x) + int(offset), int(coord.y));
    if (red(now_point) == 150 & green(now_point) == 0 && blue(now_point) == 0) {
      flashOn = true;
    }
  }
  sparkline(310, 150, 150, 50, 0, 100, 30, 80, track_pressure);
  sparkline(310, 350, 150, 50, 60, 85, lower_temp, upper_temp, track_temperature);
  stroke(40);
  textSize(60);
  fill(0);
  //if (moving > 0.0) {
  //  if (flashOn) {
  //    fill(#FF0000);
  //  }
  //  text("MOVING", 70, 790);
  //  fill(#000000);
  //} else {
  //  text("STOPPED", 70, 790);
  //}
  text("Poofs:", 30, 560);
  text(str(int(poof_count)), 250, 560);  
  text("Heater:", 30, 620);
  //text("Engine:", 30, 660);
  if (water_heater > 0.0) {
    if (flashOn) {
      fill(#FF0000);
    }
    text("ON", 250, 620);
    fill(#000000);
  } else {
    fill(#000000);
    text("OFF", 250, 620);
  }
  //if (engine == 1.0) {
  // if (flashOn) {
  //    fill(#FF0000);
  //  }
  //  text("ON", 250, 910);
  //  fill(#000000);
  //} else {
  //  text("OFF", 250, 910);
  //}
  fill(#000000);
  //text(cardinalFromHeading(heading) + " @ " + str(int(lat * 10000) / 10000.0) + ", " + str(int(lon * 10000) / 10000.0), 30, 680);
  text("Speed:", 30, 680);
  int last_speed = int(speed);
  if (flashOn) {
    if (last_speed > 10) fill(#C80000);
    else if (last_speed > 5) fill(#C8C800);
  }
  text(str(last_speed), 250, 680);
  fill(#000000);
  //text("Pressure: " + str(pressure), 10, 98);
  rotarySlider(150, 150, 200, 10, 80, pressure);
  //text("Bath: " + str(int(temperature)), 10, 132);
  rotarySlider(150, 350, 200, 20, 120, temperature);
  //text("Free: " + str(i8t(free_disk)), 10, 166);
  //rotarySlider(150, 520, 200, 0, 100, free_disk);
  PVector rhb = geoToScreen(proj.transformCoords(new PVector(lon + translate_lon, lat + translate_lat)));
  fill(#FF0000);
  rectMode(CENTER);
  translate(rhb.x + offset, rhb.y);
  rotate(radians(heading)); 
  //rect(0, 0, 10, 30);
  circle(0, 0, 15); 
}

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
  fill(#EFFFEF);
  stroke(#777777);
  strokeWeight(2);
  rect(x, y, wide, tall);
  strokeWeight(2);
  stroke(#FF00FF);
  float screen_y = y + tall / 2.0 - (upper - minimum) / vertical_range * tall;
  line(x - wide / 2, screen_y, x + wide / 2, screen_y);
  screen_y = y + tall / 2.0 - (lower - minimum) / vertical_range * tall;
  line(x - wide / 2, screen_y, x + wide / 2, screen_y);
  fill(#0000FF);
  stroke(#0000FF);
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
  fill(255, 0, 0);
  ellipse(x, y, diameter, diameter);
  fill(100, 150, 245);
  //fill(202, 226, 245);
  arc(x, y, diameter + 10, diameter + 10, PI / 4 - (3 * PI / 2) * (1.0 - ratio), 3 * PI / 4);
  ellipse(x, y, diameter / 2, diameter / 2);
  fill(0);
  String s = str(int(level));;
  float sw = textWidth(s);
  textSize(85);
  //text(s, x - sw / 2, y + 20);
  text(s, x - 38, y + 20);
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
  drawGeo(loadStrings("lines.csv"), coords);
  drawGeo(loadStrings("man_ring.csv"), man_ring);
  drawGeo(loadStrings("10_00.csv"), city_bounds);
  drawGeo(loadStrings("city_bounds.csv"), city_bounds);
  drawGeo(reverse(loadStrings("2_00.csv")), city_bounds);
  drawGeo(reverse(loadStrings("kelter.csv")), city_bounds);
}
  
void drawGeo(String[] geoCoords, ArrayList<PVector> vector) {
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
  heading = new_heading - 25.0;
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

// Map from a geographic position to the screen location
PVector geoToScreen(PVector geo) {
  return new PVector(map(geo.x, tlCorner.x, brCorner.x, 0, width), 
    map(geo.y, tlCorner.y, brCorner.y, 0, height));
}

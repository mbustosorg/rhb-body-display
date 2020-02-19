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
import processing.pdf.*;

OscP5 oscP5;

WebMercator proj = new WebMercator();
PVector tlCorner, brCorner;

float heading = 0.0;
int pressure = 0;
float lat = 0.0;
float lon = 0.0;

PImage backgroundMap;

void setup() {
    size(1000, 749);
    frameRate(25);
    oscP5 = new OscP5(this, 10002);
    setupGeo();
    backgroundMap = loadImage("oakland.png");
}

void draw() {
    //background(0);
    image(backgroundMap, 0, 0, width, height);
    textSize(32);  
    fill(0);
    text("Lat: " + str(lat), 10, 30);
    text("Lon: " + str(lon), 10, 60);
    text("Pressure: " + str(pressure), 10, 90);
    text("Heading: " + str(heading), 10, 120);
    PVector rhb = geoToScreen(proj.transformCoords(new PVector(lon, lat)));
    fill(#FF0000);
    rectMode(CENTER);
    translate(rhb.x, rhb.y);
    rotate(radians(heading)); 
    square(0, 0, 10);  
}

// Setup coordinate boundaries of the displayed map
void setupGeo() {
    tlCorner = proj.transformCoords(new PVector(-123.0, 38.0));
    brCorner = proj.transformCoords(new PVector(-122.0, 37.0));
}

// Handle the IM JSON document update
void handleImu(String imu) {
    JSONObject json = parseJSONObject(imu);	
    if (json == null) {
     	println("JSONObject could not be parsed");
    } else {
	heading = json.getJSONObject("heading").getFloat("heading");
	//println(heading);
    }
}

// Handle the new pressure value
void handlePressure(int new_pressure) {
    pressure = new_pressure;
}

// Handle the position update
void handlePosition(float new_lat, float new_lon) {
    lat = new_lat;
    lon = new_lon;
}

// Handle a new OSC message
void oscEvent(OscMessage theOscMessage) {
    try {
	String message = theOscMessage.addrPattern();
	if (message.equals("/imu")) handleImu(theOscMessage.get(0).stringValue());
	else if (message.equals("/pressure")) handlePressure(theOscMessage.get(0).intValue());
	else if (message.equals("/position")) handlePosition(theOscMessage.get(0).floatValue(),
							     theOscMessage.get(1).floatValue());
    } catch (Exception e) {
	println(e);
    }
}

// Map from a geographic position to the screen location
PVector geoToScreen(PVector geo) {
    return new PVector(map(geo.x, tlCorner.x, brCorner.x, 0, width),
		       map(geo.y, tlCorner.y, brCorner.y, 0, height));                
}

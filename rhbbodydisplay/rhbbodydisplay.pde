/**
 * oscP5sendreceive by andreas schlegel
 * example shows how to send and receive osc messages.
 * oscP5 website at http://www.sojamo.de/oscP5
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

void setupGeo() {
  tlCorner = proj.transformCoords(new PVector(-123.0, 38.0));
  brCorner = proj.transformCoords(new PVector(-122.0, 37.0));
}

void handleImu(String imu) {
     JSONObject json = parseJSONObject(imu);
     if (json == null) {
     	println("JSONObject could not be parsed");
     } else {
       heading = json.getJSONObject("heading").getFloat("heading");
       //println(heading);
     }
}

void handlePressure(int new_pressure) {
     pressure = new_pressure;
}

void handlePosition(float new_lat, float new_lon) {
     lat = new_lat;
     lon = new_lon;
}

/* incoming osc message are forwarded to the oscEvent method. */
void oscEvent(OscMessage theOscMessage) {
   try {
    String message = theOscMessage.addrPattern();
    //print(message);
    //println(" typetag: " + theOscMessage.typetag());
    if (message.equals("/imu")) handleImu(theOscMessage.get(0).stringValue());
    else if (message.equals("/pressure")) handlePressure(theOscMessage.get(0).intValue());
    else if (message.equals("/position")) handlePosition(theOscMessage.get(0).floatValue(),
							 theOscMessage.get(1).floatValue());
    //print(" value: " + theOscMessage.get(0).floatValue());
    //print(" value: " + theOscMessage.get(1).floatValue());
    //print(" value: " + theOscMessage.get(2).floatValue());
    //alt = theOscMessage.get(0).floatValue();
    //lat = theOscMessage.get(1).floatValue();
    //lon = theOscMessage.get(2).floatValue();
  } catch (Exception e) {
    println(e);
  }
}

PVector geoToScreen(PVector geo) {
  return new PVector(map(geo.x, tlCorner.x, brCorner.x, 0, width),
                     map(geo.y, tlCorner.y, brCorner.y, 0, height));                
}

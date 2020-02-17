/**
 * oscP5sendreceive by andreas schlegel
 * example shows how to send and receive osc messages.
 * oscP5 website at http://www.sojamo.de/oscP5
 */
 
import oscP5.*;
  
OscP5 oscP5;

float heading = 0.0;
int pressure = 0;
float lat = 0.0;
float lon = 0.0;

void setup() {
  size(800, 800);
  frameRate(25);
  oscP5 = new OscP5(this, 10002);
}

void draw() {
  background(0);  
  textSize(32);
  text("Lat: " + str(lat), 10, 30);
  text("Lon: " + str(lon), 10, 60);
  text("Pressure: " + str(pressure), 10, 90);
  text("Heading: " + str(heading), 10, 120);
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

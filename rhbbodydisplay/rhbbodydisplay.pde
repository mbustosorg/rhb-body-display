/**
 * oscP5sendreceive by andreas schlegel
 * example shows how to send and receive osc messages.
 * oscP5 website at http://www.sojamo.de/oscP5
 */
 
import oscP5.*;
  
OscP5 oscP5;

float lat = 0.0;
float lon = 0.0;
float alt = 0.0;

void setup() {
  size(400,400);
  frameRate(25);
  oscP5 = new OscP5(this, 10002);
}

void draw() {
  background(0);  
}

void handleImu(String imu) {
     JSONObject json = parseJSONObject(imu);
     if (json == null) {
     	println("JSONObject could not be parsed");
     } else {
       float heading = json.getJSONObject("heading").getFloat("heading");
       println(heading);
     }
}

/* incoming osc message are forwarded to the oscEvent method. */
void oscEvent(OscMessage theOscMessage) {
   try {
    String message = theOscMessage.addrPattern();
    print(message);
    println(" typetag: " + theOscMessage.typetag());
    if (message.equals("/imu")) handleImu(theOscMessage.get(0).stringValue());
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

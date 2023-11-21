#include <Adafruit_DotStar.h>
#include <SPI.h>

#define NUMPIXELS 1
#define DATAPIN 7
#define CLOCKPIN 8

// Turn off the rgb led
Adafruit_DotStar strip = Adafruit_DotStar(NUMPIXELS, DATAPIN, CLOCKPIN, DOTSTAR_BGR);

#include <Encoder.h>

#define CAM_PIN 4

unsigned long previousMillis = 0; 
const int pulseDuration = 5;  // ms
unsigned long pulseStartTime;

bool isPulsing = false;
bool shouldPulse = false;

unsigned int freq = 50;  // Hz
unsigned long interval = (1000 / freq); // ms

Encoder myEncoder(2, 3);
int count=101;

void setup() {
  pinMode(CAM_PIN, OUTPUT);
  digitalWrite(CAM_PIN, LOW);

  Serial.begin(115200);  // Start serial communication at 9600 baud rate
  
  myEncoder.write(0);
}

void loop() {
  unsigned long currentMillis = millis();

  if (Serial.available() > 0) {
    char receivedChar = Serial.read();
    // Check if the received character is 'S'
    if (receivedChar == 'S') {
      shouldPulse = true;
    }
    else if (receivedChar == 'E') {
      shouldPulse = false;
    }
    else if (receivedChar == 'A') {
      freq = Serial.parseInt();  // Parse the following integer
      interval = 1000 / freq;  // Update the interval
    }
  }

    if (isPulsing && currentMillis - pulseStartTime >= pulseDuration) {
      digitalWrite(CAM_PIN, LOW);
      isPulsing = false;
    }


  if (shouldPulse && currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      pulseStartTime = currentMillis;
      isPulsing = true;

      digitalWrite(CAM_PIN, HIGH);
      count=count+1;
      long pos;
      byte *b,m;

      b = (byte *) &pos;  
      pos = myEncoder.read();
      Serial.println(pos+count);
      }

}

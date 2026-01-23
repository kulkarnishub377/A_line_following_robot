/*
 * Line Following Robot - Basic Version
 * 
 * This is a simplified version without LCD and LED indicators.
 * Use this if you don't have an LCD display or want to minimize components.
 * 
 * Hardware Required:
 * - Arduino (Uno or Mega)
 * - L293D Motor Driver
 * - 2x IR Sensors
 * - 2x DC Motors
 * - Battery Pack
 */

// Motor Driver Pins
#define enA 5
#define in1 6
#define in2 7
#define enB 8
#define in3 9
#define in4 10

// IR Sensor Pins
#define R_S 4
#define L_S 2

void setup() {
  // Initialize serial for debugging (optional)
  Serial.begin(9600);
  
  // Configure pins
  pinMode(R_S, INPUT);
  pinMode(L_S, INPUT);
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  
  Serial.println("Line Following Robot - Basic Version");
  delay(1000);
}

void loop() {
  int rightSensor = digitalRead(R_S);
  int leftSensor = digitalRead(L_S);
  
  // Debug output
  Serial.print("L: ");
  Serial.print(leftSensor);
  Serial.print(" R: ");
  Serial.println(rightSensor);
  
  // Line following logic
  if (rightSensor == 0 && leftSensor == 0) {
    forward();
  }
  else if (rightSensor == 1 && leftSensor == 0) {
    turnRight();
  }
  else if (rightSensor == 0 && leftSensor == 1) {
    turnLeft();
  }
  else {
    stop();
  }
}

void forward() {
  analogWrite(enA, 150);
  analogWrite(enB, 150);
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
}

void turnRight() {
  analogWrite(enA, 100);
  analogWrite(enB, 100);
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
}

void turnLeft() {
  analogWrite(enA, 100);
  analogWrite(enB, 100);
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
}

void stop() {
  analogWrite(enA, 0);
  analogWrite(enB, 0);
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
}

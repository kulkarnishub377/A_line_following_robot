#include <Wire.h>
#include <LiquidCrystal_I2C.h> // Include the library for I2C LCD



#define enA 5  // Enable1 L293 Pin enA
#define in1 6  // Motor1 L293 Pin in1
#define in2 7  // Motor1 L293 Pin in2
#define in3 9  // Motor2 L293 Pin in3
#define in4 10 // Motor2 L293 Pin in4
#define enB 8  // Enable2 L293 Pin enB
#define R_S 4  // IR sensor Right
#define L_S 2  // IR sensor Left
#define LED1 A0 // Analog pin for LED1
#define LED2 A1 // Analog pin for LED2
#define LED3 A2 // Analog pin for LED3
#define LED4 A3 // Analog pin for LED3
#define LED5 A4 // Analog pin for LED3

LiquidCrystal_I2C lcd(0x27, 16, 2); // Address 0x27 for a 16 chars and 2 line display

void setup() {
  pinMode(R_S, INPUT);
  pinMode(L_S, INPUT);
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  pinMode(LED4, OUTPUT);
  pinMode(LED5, OUTPUT);


  
  lcd.init(); // Initialize the LCD
  lcd.backlight(); // Turn on the backlight
  digitalWrite(LED3, HIGH);
  digitalWrite(LED4, HIGH);
  digitalWrite(LED5, HIGH);

  lcd.print("LINE FOLLOWING ROBOT");
  // digitalWrite(enA, HIGH);
  // digitalWrite(enB, HIGH);
  delay(1000);
}

void loop() {
  if ((digitalRead(R_S) == 0) && (digitalRead(L_S) == 0)) {
    forward();
    lcd.setCursor(0, 0);
    lcd.print("Moving Forward");
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    
  } // if Right Sensor and Left Sensor are at White color then it will call forward function

  if ((digitalRead(R_S) == 1) && (digitalRead(L_S) == 0)) {
    turnRight();
    lcd.setCursor(0, 0);
    lcd.print("Turnning Right");
    digitalWrite(LED1, HIGH);
    digitalWrite(LED2, LOW);
  } // if Right Sensor is Black and Left Sensor is White then it will call turn Right function

  if ((digitalRead(R_S) == 0) && (digitalRead(L_S) == 1)) {
    turnLeft();
    lcd.setCursor(0, 0);
    lcd.print("Turnning Left");
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, HIGH);
  } // if Right Sensor is White and Left Sensor is Black then it will call turn Left function

  if ((digitalRead(R_S) == 1) && (digitalRead(L_S) == 1)) {
    Stop();
    lcd.setCursor(0, 0);
    lcd.print("Stopped");
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
  } // if Right Sensor and Left Sensor are at Black color then it will call Stop function
}

void forward() { // forward
  analogWrite(enA, 150); // Right Motor Speed
  analogWrite(enB, 150); // Left Motor Speed
  digitalWrite(in1, HIGH); // Right Motor forward Pin
  digitalWrite(in2, LOW);  // Right Motor backward Pin
  digitalWrite(in3, LOW);  // Left Motor backward Pin
  digitalWrite(in4, HIGH); // Left Motor forward Pin
}

void turnRight() { // turnRight
  analogWrite(enA, 100); // Right Motor Speed
  analogWrite(enB, 100); // Left Motor Speed
  digitalWrite(in1, LOW);  // Right Motor forward Pin
  digitalWrite(in2, HIGH); // Right Motor backward Pin
  digitalWrite(in3, LOW);  // Left Motor backward Pin
  digitalWrite(in4, HIGH); // Left Motor forward Pin
}

void turnLeft() { // turnLeft
  analogWrite(enA, 100); // Right Motor Speed
  analogWrite(enB, 100); // Left Motor Speed
  digitalWrite(in1, HIGH); // Right Motor forward Pin
  digitalWrite(in2, LOW);  // Right Motor backward Pin
  digitalWrite(in3, HIGH); // Left Motor backward Pin
  digitalWrite(in4, LOW);  // Left Motor forward Pin
}

void Stop() { // stop
  analogWrite(enA, 0); // Right Motor Speed
  analogWrite(enB, 0); // Left Motor Speed
  digitalWrite(in1, LOW); // Right Motor forward Pin
  digitalWrite(in2, LOW); // Right Motor backward Pin
  digitalWrite(in3, LOW); // Left Motor backward Pin
  digitalWrite(in4, LOW); // Left Motor forward Pin
}

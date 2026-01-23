/*
 * Line Following Robot
 * 
 * Description:
 *   An autonomous robot that follows a black line on a white surface using
 *   IR sensors. The robot displays its current state on an LCD and uses LEDs
 *   to provide visual feedback.
 * 
 * Hardware:
 *   - Arduino Mega (or Uno)
 *   - L293D Motor Driver IC
 *   - 2x IR Sensors (Digital output)
 *   - 16x2 I2C LCD Display
 *   - 2x DC Motors
 *   - 5x LEDs with 220Ω resistors
 *   - Battery pack (7.4V - 9V)
 * 
 * Author: E&TC Students
 * License: MIT
 */

#include <Wire.h>                    // I2C communication library
#include <LiquidCrystal_I2C.h>       // I2C LCD library

// ========================
// PIN DEFINITIONS
// ========================

// Motor Driver Pins (L293D)
#define enA 5   // Enable pin for Motor A (PWM for speed control)
#define in1 6   // Motor A input 1 (direction control)
#define in2 7   // Motor A input 2 (direction control)
#define enB 8   // Enable pin for Motor B (PWM for speed control)
#define in3 9   // Motor B input 3 (direction control)
#define in4 10  // Motor B input 4 (direction control)

// IR Sensor Pins
#define R_S 4   // Right IR sensor (Digital input: 0=white, 1=black)
#define L_S 2   // Left IR sensor (Digital input: 0=white, 1=black)

// LED Indicator Pins
#define LED1 A0 // Direction indicator LED 1 (shows right turn)
#define LED2 A1 // Direction indicator LED 2 (shows left turn)
#define LED3 A2 // Status LED 3 (always on during operation)
#define LED4 A3 // Status LED 4 (always on during operation)
#define LED5 A4 // Status LED 5 (always on during operation)

// ========================
// LCD CONFIGURATION
// ========================
// I2C address 0x27 for 16x2 LCD (try 0x3F if 0x27 doesn't work)
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ========================
// SETUP FUNCTION
// ========================
void setup() {
  // Configure IR sensor pins as inputs
  pinMode(R_S, INPUT);
  pinMode(L_S, INPUT);
  
  // Configure motor driver pins as outputs
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  
  // Configure LED pins as outputs
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  pinMode(LED4, OUTPUT);
  pinMode(LED5, OUTPUT);
  
  // Initialize LCD display
  lcd.init();
  lcd.backlight();
  
  // Turn on status LEDs (indicates robot is powered and ready)
  digitalWrite(LED3, HIGH);
  digitalWrite(LED4, HIGH);
  digitalWrite(LED5, HIGH);
  
  // Display startup message
  lcd.print("LINE FOLLOWING");
  lcd.setCursor(0, 1);
  lcd.print("ROBOT v1.0");
  
  // Wait 1 second before starting main loop
  delay(1000);
  
  // Clear LCD for status messages
  lcd.clear();
}

// ========================
// MAIN LOOP
// ========================
void loop() {
  // Read sensor values
  // 0 = Sensor over white surface
  // 1 = Sensor over black line
  int rightSensor = digitalRead(R_S);
  int leftSensor = digitalRead(L_S);
  
  // CASE 1: Both sensors on white (robot on track) - Move forward
  if ((rightSensor == 0) && (leftSensor == 0)) {
    forward();
    lcd.setCursor(0, 0);
    lcd.print("Moving Forward  ");  // Extra spaces to clear previous text
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
  }
  
  // CASE 2: Right sensor on black, left on white - Turn right to correct
  else if ((rightSensor == 1) && (leftSensor == 0)) {
    turnRight();
    lcd.setCursor(0, 0);
    lcd.print("Turning Right   ");  // Fixed typo: "Turnning" -> "Turning"
    digitalWrite(LED1, HIGH);         // LED1 indicates right turn
    digitalWrite(LED2, LOW);
  }
  
  // CASE 3: Left sensor on black, right on white - Turn left to correct
  else if ((rightSensor == 0) && (leftSensor == 1)) {
    turnLeft();
    lcd.setCursor(0, 0);
    lcd.print("Turning Left    ");  // Fixed typo: "Turnning" -> "Turning"
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, HIGH);          // LED2 indicates left turn
  }
  
  // CASE 4: Both sensors on black - Stop (end of line or intersection)
  else if ((rightSensor == 1) && (leftSensor == 1)) {
    Stop();
    lcd.setCursor(0, 0);
    lcd.print("Stopped         ");
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
  }
}

// ========================
// MOTOR CONTROL FUNCTIONS
// ========================

/**
 * Move robot forward
 * Both motors rotate in the same direction at the same speed
 */
void forward() {
  analogWrite(enA, 150);    // Right motor speed (0-255)
  analogWrite(enB, 150);    // Left motor speed (0-255)
  
  // Right motor forward
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  
  // Left motor forward
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
}

/**
 * Turn robot right
 * Right motor reverses while left motor moves forward
 * Creates a pivot turn to the right
 */
void turnRight() {
  analogWrite(enA, 100);    // Right motor speed (slower for turning)
  analogWrite(enB, 100);    // Left motor speed
  
  // Right motor backward (reverse)
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  
  // Left motor forward
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
}

/**
 * Turn robot left
 * Left motor reverses while right motor moves forward
 * Creates a pivot turn to the left
 */
void turnLeft() {
  analogWrite(enA, 100);    // Right motor speed
  analogWrite(enB, 100);    // Left motor speed (slower for turning)
  
  // Right motor forward
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  
  // Left motor backward (reverse)
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
}

/**
 * Stop the robot
 * Both motors stop by setting speed to 0
 */
void Stop() {
  analogWrite(enA, 0);      // Right motor speed = 0
  analogWrite(enB, 0);      // Left motor speed = 0
  
  // Set all motor pins to LOW for safety
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
}

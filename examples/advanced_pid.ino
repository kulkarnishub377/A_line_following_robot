/*
 * Line Following Robot - Advanced Version with PID Control
 * 
 * This version uses PID (Proportional-Integral-Derivative) control
 * for smoother line following with 3 or more IR sensors.
 * 
 * Hardware Required:
 * - Arduino Mega
 * - L293D Motor Driver
 * - 3x IR Sensors (Left, Center, Right)
 * - 2x DC Motors
 * - Battery Pack
 * - Optional: LCD Display
 * 
 * Note: This is an advanced example for learning purposes.
 * Requires tuning of PID constants for your specific setup.
 */

// Motor Driver Pins
#define enA 5
#define in1 6
#define in2 7
#define enB 8
#define in3 9
#define in4 10

// IR Sensor Pins (3 sensors for better line tracking)
#define L_S 2    // Left sensor
#define C_S 3    // Center sensor
#define R_S 4    // Right sensor

// PID Constants (tune these for your robot)
float Kp = 25;   // Proportional constant
float Ki = 0;    // Integral constant  
float Kd = 15;   // Derivative constant

// PID Variables
int lastError = 0;
int integral = 0;

// Motor base speed
int baseSpeed = 150;
int maxSpeed = 255;

void setup() {
  Serial.begin(9600);
  
  pinMode(L_S, INPUT);
  pinMode(C_S, INPUT);
  pinMode(R_S, INPUT);
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  
  Serial.println("Advanced PID Line Follower");
  delay(2000);
}

void loop() {
  // Read all sensors
  int left = digitalRead(L_S);
  int center = digitalRead(C_S);
  int right = digitalRead(R_S);
  
  // Calculate position error
  // -2: far left, -1: left, 0: center, 1: right, 2: far right
  int error = 0;
  
  if (left == 0 && center == 0 && right == 0) {
    error = 0;  // On line
  }
  else if (left == 1 && center == 0 && right == 0) {
    error = -2;  // Far left
  }
  else if (left == 1 && center == 1 && right == 0) {
    error = -1;  // Left
  }
  else if (left == 0 && center == 1 && right == 0) {
    error = 0;   // Center
  }
  else if (left == 0 && center == 1 && right == 1) {
    error = 1;   // Right
  }
  else if (left == 0 && center == 0 && right == 1) {
    error = 2;   // Far right
  }
  else {
    // All sensors on black - stop or continue with last error
    motorStop();
    return;
  }
  
  // PID Calculation
  int P = error;
  integral += error;
  int I = integral;
  int D = error - lastError;
  lastError = error;
  
  // Calculate correction
  int correction = (Kp * P) + (Ki * I) + (Kd * D);
  
  // Calculate motor speeds
  int leftSpeed = baseSpeed + correction;
  int rightSpeed = baseSpeed - correction;
  
  // Constrain speeds
  leftSpeed = constrain(leftSpeed, 0, maxSpeed);
  rightSpeed = constrain(rightSpeed, 0, maxSpeed);
  
  // Apply motor speeds
  moveMotors(leftSpeed, rightSpeed);
  
  // Debug output
  Serial.print("Error: ");
  Serial.print(error);
  Serial.print(" | Correction: ");
  Serial.print(correction);
  Serial.print(" | L: ");
  Serial.print(leftSpeed);
  Serial.print(" R: ");
  Serial.println(rightSpeed);
}

void moveMotors(int leftSpeed, int rightSpeed) {
  // Left motor
  analogWrite(enB, abs(leftSpeed));
  if (leftSpeed >= 0) {
    digitalWrite(in3, LOW);
    digitalWrite(in4, HIGH);
  } else {
    digitalWrite(in3, HIGH);
    digitalWrite(in4, LOW);
  }
  
  // Right motor
  analogWrite(enA, abs(rightSpeed));
  if (rightSpeed >= 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  }
}

void motorStop() {
  analogWrite(enA, 0);
  analogWrite(enB, 0);
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
}

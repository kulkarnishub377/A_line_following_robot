/*
 * Bluetooth Controlled Line Following Robot
 * 
 * This version adds Bluetooth control to start/stop the robot remotely.
 * Commands:
 * - 'S': Start line following
 * - 'X': Stop robot
 * - 'M': Manual mode (control via app)
 * - 'A': Auto mode (line following)
 * 
 * Hardware Required:
 * - Arduino Mega
 * - L293D Motor Driver
 * - 2x IR Sensors
 * - 2x DC Motors
 * - HC-05 Bluetooth Module
 * - Battery Pack
 * 
 * Bluetooth Connections:
 * - HC-05 TX → Arduino RX (Pin 19)
 * - HC-05 RX → Arduino TX (Pin 18) via voltage divider
 * - HC-05 VCC → 5V
 * - HC-05 GND → GND
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

// Robot states
bool autoMode = true;
bool robotRunning = true;

void setup() {
  // Serial for Bluetooth (use Serial1 on Mega)
  Serial1.begin(9600);
  Serial.begin(9600);  // Debug serial
  
  pinMode(R_S, INPUT);
  pinMode(L_S, INPUT);
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  
  Serial.println("Bluetooth Line Follower Ready");
  Serial1.println("Robot Ready. Send commands:");
  Serial1.println("S=Start, X=Stop, A=Auto, M=Manual");
}

void loop() {
  // Check for Bluetooth commands
  if (Serial1.available()) {
    char command = Serial1.read();
    handleCommand(command);
  }
  
  // Auto line following mode
  if (autoMode && robotRunning) {
    lineFollowing();
  }
}

void handleCommand(char cmd) {
  Serial.print("Command: ");
  Serial.println(cmd);
  
  switch(cmd) {
    case 'S':
    case 's':
      robotRunning = true;
      Serial1.println("Robot Started");
      break;
      
    case 'X':
    case 'x':
      robotRunning = false;
      motorStop();
      Serial1.println("Robot Stopped");
      break;
      
    case 'A':
    case 'a':
      autoMode = true;
      Serial1.println("Auto Mode ON");
      break;
      
    case 'M':
    case 'm':
      autoMode = false;
      motorStop();
      Serial1.println("Manual Mode ON");
      break;
      
    case 'F':  // Manual forward
      if (!autoMode) forward();
      break;
      
    case 'B':  // Manual backward
      if (!autoMode) backward();
      break;
      
    case 'L':  // Manual left
      if (!autoMode) turnLeft();
      break;
      
    case 'R':  // Manual right
      if (!autoMode) turnRight();
      break;
      
    case 'P':  // Manual stop
      motorStop();
      break;
  }
}

void lineFollowing() {
  int rightSensor = digitalRead(R_S);
  int leftSensor = digitalRead(L_S);
  
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
    motorStop();
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

void backward() {
  analogWrite(enA, 150);
  analogWrite(enB, 150);
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
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

void motorStop() {
  analogWrite(enA, 0);
  analogWrite(enB, 0);
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
}

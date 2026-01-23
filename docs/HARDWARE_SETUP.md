# Hardware Setup Guide

## Circuit Assembly Instructions

### Step 1: Prepare the Chassis
1. Assemble the robot chassis according to the manufacturer's instructions
2. Mount the two DC motors on either side of the chassis
3. Attach wheels to the motor shafts
4. Install the castor wheel at the front or back for balance

### Step 2: Mount the Arduino
1. Secure the Arduino Mega to the chassis using standoffs or double-sided tape
2. Ensure the Arduino is positioned for easy access to USB port
3. Leave space for the battery pack and other components

### Step 3: Wire the L293D Motor Driver
Connect the L293D IC to Arduino according to this pinout:

**Power Connections:**
- Pin 16 (Vcc1): Connect to Arduino 5V
- Pin 8 (Vcc2): Connect to battery positive (7-12V)
- Pins 4, 5, 12, 13 (GND): Connect all to common ground

**Motor Connections:**
- Pins 3, 6: Connect to Motor A
- Pins 11, 14: Connect to Motor B

**Control Connections:**
- Pin 1 (Enable A): Arduino Pin 5
- Pin 2 (Input 1): Arduino Pin 6
- Pin 7 (Input 2): Arduino Pin 7
- Pin 9 (Enable B): Arduino Pin 8
- Pin 10 (Input 3): Arduino Pin 9
- Pin 15 (Input 4): Arduino Pin 10

### Step 4: Install IR Sensors
1. Mount IR sensors at the front of the chassis
2. Position them about 1-2 cm apart
3. Adjust height to 1-2 cm above the ground
4. Connect sensor outputs:
   - Left sensor → Arduino Pin 2
   - Right sensor → Arduino Pin 4
5. Connect VCC to 5V and GND to ground

### Step 5: Connect the LCD Display
1. Connect the I2C LCD to Arduino:
   - VCC → 5V
   - GND → Ground
   - SDA → SDA pin (Pin 20 on Mega)
   - SCL → SCL pin (Pin 21 on Mega)

### Step 6: Add LED Indicators
1. Connect 5 LEDs with 220Ω resistors:
   - LED1 → Pin A0
   - LED2 → Pin A1
   - LED3 → Pin A2
   - LED4 → Pin A3
   - LED5 → Pin A4
2. Connect all LED cathodes (short leg) to ground
3. Connect anodes through resistors to Arduino pins

### Step 7: Power Setup
1. Connect battery pack to the motor driver (Vcc2)
2. Ensure common ground between Arduino and motor driver
3. Add a power switch for easy on/off control
4. Optional: Add a voltage regulator if using high voltage battery

## Testing Procedure

### Pre-flight Checks
1. ✅ Verify all connections are secure
2. ✅ Check polarity of battery connections
3. ✅ Ensure no short circuits
4. ✅ Test motors individually before full assembly

### Motor Test
```cpp
// Upload this test sketch to verify motor connections
void setup() {
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
}

void loop() {
  digitalWrite(5, HIGH);  // Enable motor
  digitalWrite(6, HIGH);  // Forward
  digitalWrite(7, LOW);
  delay(2000);
  
  digitalWrite(6, LOW);   // Reverse
  digitalWrite(7, HIGH);
  delay(2000);
}
```

### Sensor Test
```cpp
// Test IR sensors
void setup() {
  Serial.begin(9600);
  pinMode(2, INPUT);
  pinMode(4, INPUT);
}

void loop() {
  Serial.print("Left: ");
  Serial.print(digitalRead(2));
  Serial.print(" | Right: ");
  Serial.println(digitalRead(4));
  delay(500);
}
```

### LCD Test
```cpp
// Test LCD display
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  lcd.init();
  lcd.backlight();
  lcd.print("LCD Test OK!");
}

void loop() {}
```

## Calibration Guide

### IR Sensor Calibration
1. **Height Adjustment**: Position sensors 1-2 cm above the surface
2. **Sensitivity Tuning**: 
   - Use the potentiometer on each sensor module
   - Turn clockwise to decrease sensitivity
   - Turn counter-clockwise to increase sensitivity
3. **Testing**:
   - Place sensor over white surface - LED should be OFF
   - Place sensor over black line - LED should be ON
   - Adjust potentiometer until detection is reliable

### Motor Speed Calibration
1. Test the robot on a straight line
2. If robot drifts left: Increase right motor speed or decrease left motor speed
3. If robot drifts right: Increase left motor speed or decrease right motor speed
4. Adjust values in the code:
   ```cpp
   analogWrite(enA, 150); // Adjust this value for right motor
   analogWrite(enB, 150); // Adjust this value for left motor
   ```

### Track Requirements
- **Line Width**: 2-3 cm (0.75-1.2 inches)
- **Line Color**: Black on white surface
- **Surface**: Flat, non-reflective
- **Lighting**: Consistent, avoid direct sunlight
- **Contrast**: High contrast between line and surface

## Safety Notes

⚠️ **Important Safety Guidelines:**
- Never connect motor power directly to Arduino pins
- Use the motor driver IC for all motor connections
- Check battery polarity before connecting
- Add a fuse to protect against short circuits
- Don't exceed 12V on motor driver Vcc2
- Keep electronics away from metal chassis to prevent shorts
- Disconnect battery when uploading new code

## Common Issues

| Problem | Solution |
|---------|----------|
| Motors not running | Check enable pins, verify motor driver connections |
| Robot moving backward | Swap motor wires or change motor direction in code |
| One motor not working | Test motor separately, check driver IC connections |
| Sensors not detecting | Adjust sensor height and sensitivity potentiometer |
| LCD blank | Check I2C address, verify connections, adjust contrast |

## Tools Required

- Soldering iron and solder
- Wire strippers
- Screwdrivers (Phillips and flat)
- Multimeter for testing
- Hot glue gun (for securing components)
- Zip ties or cable organizers
- Double-sided tape

## Recommended Suppliers

Components can be sourced from:
- Arduino official store
- Adafruit
- SparkFun
- Amazon
- Local electronics stores
- AliExpress (for budget options)

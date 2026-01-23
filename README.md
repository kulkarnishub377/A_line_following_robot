# 🤖 Line Following Robot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-blue.svg)](https://www.arduino.cc/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> An autonomous Arduino-based robot that follows a black line on a white surface using IR sensors and visual feedback via LCD display and LEDs.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Circuit Diagram](#circuit-diagram)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## 🎯 Overview

This project is an autonomous line-following robot designed as a college mini-project for the E&TC branch. The robot uses infrared (IR) sensors to detect and follow a black line on a white surface, making it perfect for understanding robotics, sensor integration, and control systems.

**Key Highlights:**
- Real-time LCD feedback showing robot state
- Visual LED indicators for direction
- Smooth motor control with adjustable speeds
- Simple yet effective line-following algorithm

## ✨ Features

- **Autonomous Navigation**: Follows black lines without human intervention
- **Real-time Display**: 16x2 LCD shows current robot status
- **Visual Indicators**: 5 LEDs provide additional status feedback
- **Dual IR Sensors**: Left and right sensors for accurate line detection
- **Motor Control**: PWM-based speed control for smooth movements
- **Multiple States**: Forward, Left Turn, Right Turn, and Stop
- **Compact Design**: Optimized for small to medium-sized tracks

## 🔧 Hardware Requirements

### Essential Components

| Component | Specification | Quantity | Purpose |
|-----------|--------------|----------|---------|
| **Microcontroller** | Arduino Mega (or Uno) | 1 | Main control board |
| **Motor Driver** | L293D IC | 1 | Controls DC motors |
| **IR Sensors** | Digital IR sensor modules | 2 | Line detection |
| **DC Motors** | 3-12V DC geared motors | 2 | Robot movement |
| **LCD Display** | 16x2 I2C LCD | 1 | Status display |
| **LEDs** | 5mm LEDs (any color) | 5 | Visual indicators |
| **Battery** | 7.4V Li-ion or 9V battery | 1 | Power source |
| **Chassis** | Robot chassis kit | 1 | Physical structure |
| **Wheels** | Compatible with motors | 2 | Movement |
| **Castor Wheel** | Small ball caster | 1 | Support |
| **Resistors** | 220Ω resistors | 5 | LED current limiting |
| **Jumper Wires** | Male-to-Male, Male-to-Female | - | Connections |

### Optional Components
- Breadboard for prototyping
- Switch for power control
- Additional LEDs for decoration

## 📐 Circuit Diagram

### Pin Configuration

#### Motor Driver (L293D) Connections
```
Arduino Pin  →  L293D Pin    →  Function
    5        →  Enable A     →  Right motor speed (PWM)
    6        →  Input 1      →  Right motor direction
    7        →  Input 2      →  Right motor direction
    8        →  Enable B     →  Left motor speed (PWM)
    9        →  Input 3      →  Left motor direction
    10       →  Input 4      →  Left motor direction
```

#### Sensor Connections
```
Arduino Pin  →  Component
    2        →  Left IR Sensor (Digital Output)
    4        →  Right IR Sensor (Digital Output)
```

#### Display and LED Connections
```
Arduino Pin  →  Component
   SDA       →  LCD SDA (I2C Data)
   SCL       →  LCD SCL (I2C Clock)
   A0        →  LED 1 (via 220Ω resistor)
   A1        →  LED 2 (via 220Ω resistor)
   A2        →  LED 3 (via 220Ω resistor)
   A3        →  LED 4 (via 220Ω resistor)
   A4        →  LED 5 (via 220Ω resistor)
```

### Wiring Diagram
```
                    Arduino Mega
                   ┌─────────────┐
    Left Sensor ───┤ 2           │
    Right Sensor ──┤ 4           │
                   │             │
    Motor Driver ──┤ 5,6,7,8,9,10│
                   │             │
    LCD (I2C) ─────┤ SDA, SCL    │
    LEDs ──────────┤ A0-A4       │
                   └─────────────┘
```

> **Note**: Detailed circuit diagrams can be found in the `/docs` folder.

## 💻 Software Requirements

- **Arduino IDE** (v1.8.x or higher) - [Download here](https://www.arduino.cc/en/software)
- **Required Libraries**:
  - `Wire.h` (built-in with Arduino IDE)
  - `LiquidCrystal_I2C.h` - [Installation guide](#installing-libraries)

### Installing Libraries

1. Open Arduino IDE
2. Go to **Sketch** → **Include Library** → **Manage Libraries**
3. Search for "LiquidCrystal I2C"
4. Install the library by Frank de Brabander

**Alternative method (Manual Installation):**
```bash
# Navigate to Arduino libraries folder
cd ~/Documents/Arduino/libraries

# Download the library
git clone https://github.com/johnrickman/LiquidCrystal_I2C.git
```

## 🚀 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/kulkarnishub377/A_line_following_robot.git
cd A_line_following_robot
```

### Step 2: Open the Project
1. Launch Arduino IDE
2. Open `src/line_following_robot.ino`
3. Select your Arduino board: **Tools** → **Board** → **Arduino Mega** (or your board)
4. Select the correct port: **Tools** → **Port** → (your Arduino port)

### Step 3: Upload the Code
1. Click the **Upload** button (→) or press `Ctrl+U`
2. Wait for the upload to complete
3. You should see "Done uploading" message

## 📖 Usage

### Initial Setup

1. **Power On**: Connect the battery to the Arduino
2. **LCD Display**: Should show "LINE FOLLOWING ROBOT" on startup
3. **LED Indicators**: Three status LEDs (3, 4, 5) will light up
4. **Calibration**: Place the robot on a test track

### Operating the Robot

1. **Prepare the Track**: 
   - Use a white surface with a black line (2-3 cm wide)
   - Ensure good contrast between line and surface
   - Start with simple curves before complex paths

2. **Position the Robot**:
   - Place robot so the line is between both sensors
   - Ensure sensors are 1-2 cm above the surface

3. **Power On and Go**:
   - The robot will automatically start following the line
   - Watch the LCD for status updates
   - LED indicators show turning direction

### Understanding Robot States

| LCD Display | LED Status | Robot Action |
|-------------|-----------|--------------|
| "Moving Forward" | LED 1 & 2 OFF | Going straight on the line |
| "Turning Right" | LED 1 ON, LED 2 OFF | Turning right to follow line |
| "Turning Left" | LED 1 OFF, LED 2 ON | Turning left to follow line |
| "Stopped" | LED 1 & 2 OFF | Both sensors on black (end of line) |

## ⚙️ How It Works

### Algorithm Overview

The robot uses a simple but effective line-following algorithm:

```
┌─────────────────────────────────────────┐
│  Read IR Sensor Values                  │
│  (0 = White surface, 1 = Black line)    │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │  Sensor Logic   │
        └────────┬────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
   Both       Left=1      Right=1     Both=1
  Sensors=0   Right=0     Left=0      (Stop)
     │           │           │           │
  Forward    Turn Right  Turn Left     Stop
```

### Code Logic Explained

1. **Sensor Reading**: 
   - Continuously reads left and right IR sensors
   - `0` = sensor over white surface
   - `1` = sensor over black line

2. **Decision Making**:
   ```cpp
   if (Left=0 && Right=0)  → Both on white → Move Forward
   if (Left=0 && Right=1)  → Right on line → Turn Right
   if (Left=1 && Right=0)  → Left on line  → Turn Left
   if (Left=1 && Right=1)  → Both on line  → Stop
   ```

3. **Motor Control**:
   - Forward: Both motors at 150 PWM (speed)
   - Turning: Motors at 100 PWM with opposite directions
   - Stop: Both motors at 0 PWM

4. **Feedback**:
   - LCD updates with current state
   - LEDs indicate turning direction
   - Status LEDs remain lit during operation

## 🔧 Configuration

### Adjusting Motor Speed

In the code, you can modify these values for different speeds:

```cpp
// In forward() function
analogWrite(enA, 150); // Right Motor Speed (0-255)
analogWrite(enB, 150); // Left Motor Speed (0-255)

// In turnRight() and turnLeft() functions
analogWrite(enA, 100); // Turning Speed (0-255)
analogWrite(enB, 100);
```

**Speed Guidelines:**
- Lower values (80-120): Better control, slower movement
- Medium values (120-180): Balanced speed and control
- Higher values (180-255): Faster but less stable

### Sensor Sensitivity

- Adjust sensor height: 1-2 cm above surface is optimal
- Use sensor potentiometer to adjust detection threshold
- Test on your specific track surface

### LCD I2C Address

If your LCD doesn't work, try changing the address:
```cpp
LiquidCrystal_I2C lcd(0x27, 16, 2); // Try 0x3F if 0x27 doesn't work
```

To find your LCD address, use an I2C scanner sketch.

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Robot Doesn't Move
- **Check**: Battery voltage (should be 7-12V)
- **Check**: Motor driver connections
- **Check**: Enable pins are receiving PWM signals
- **Solution**: Verify all connections match the pin configuration

#### LCD Shows Nothing
- **Check**: I2C address (try 0x3F instead of 0x27)
- **Check**: I2C connections (SDA and SCL)
- **Check**: Contrast potentiometer on LCD
- **Solution**: Run I2C scanner to find correct address

#### Robot Doesn't Follow Line
- **Check**: Sensor height (1-2 cm optimal)
- **Check**: Line contrast (black on white)
- **Check**: Sensor orientation (pointing downward)
- **Solution**: Calibrate sensors using potentiometer

#### Erratic Movement
- **Check**: Loose connections
- **Check**: Insufficient power supply
- **Check**: Motor speed values (might be too high)
- **Solution**: Lower motor speeds, secure all connections

#### One Motor Not Working
- **Check**: Motor driver connections for that motor
- **Check**: Motor itself (swap motors to test)
- **Check**: Enable pin PWM signal
- **Solution**: Replace faulty motor or check driver IC

### Debug Mode

Add serial debugging to troubleshoot:
```cpp
void setup() {
  Serial.begin(9600);
  // ... rest of setup
}

void loop() {
  Serial.print("Left: ");
  Serial.print(digitalRead(L_S));
  Serial.print(" Right: ");
  Serial.println(digitalRead(R_S));
  // ... rest of loop
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Ways to Contribute
- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit code improvements
- 🎨 Add circuit diagrams or images

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Team Members
This project was developed as a collaborative effort by E&TC students. Special thanks to all team members who contributed their time, skills, and dedication.

### Learning Outcomes
- ✅ Sensor integration and calibration
- ✅ Motor control systems
- ✅ Embedded programming with Arduino
- ✅ Control algorithms and logic
- ✅ Hardware-software integration
- ✅ Team collaboration and project management

### Resources
- Arduino Community Forums
- L293D Motor Driver Documentation
- IR Sensor Tutorials
- Robotics Community

### Inspiration
This project showcases the practical application of robotics and automation in real-world scenarios, making it perfect for:
- Educational purposes
- STEM demonstrations
- Robotics competitions
- Learning embedded systems

## 📞 Support

If you have questions or need help:
- Open an [Issue](https://github.com/kulkarnishub377/A_line_following_robot/issues)
- Check the [Troubleshooting](#troubleshooting) section
- Review existing issues for solutions

---

**Made with ❤️ by robotics enthusiasts**

#Robotics #Arduino #Engineering #STEM #IoT #Automation

# Example Sketches

This directory contains alternative versions and enhancements of the line-following robot.

## Available Examples

### 1. Basic Version (`basic_version.ino`)
**Simplest implementation** - Perfect for beginners or minimalist builds.

**Features:**
- No LCD display required
- No LED indicators
- Serial debugging output
- Core line-following functionality only

**Use Case:**
- Learning the basics
- Limited components
- Budget builds
- Prototyping

**Hardware Needed:**
- Arduino (Uno or Mega)
- L293D Motor Driver
- 2x IR Sensors
- 2x DC Motors
- Battery

---

### 2. Advanced PID Version (`advanced_pid.ino`)
**Smooth and precise control** using PID algorithm.

**Features:**
- PID (Proportional-Integral-Derivative) control
- Support for 3 IR sensors (better accuracy)
- Adjustable speed control
- Smoother turns and transitions
- Serial debugging with detailed metrics

**Use Case:**
- Competitive robotics
- High-speed line following
- Complex track patterns
- Learning control theory

**Hardware Needed:**
- Arduino Mega (recommended)
- L293D Motor Driver
- 3x IR Sensors (Left, Center, Right)
- 2x DC Motors
- Battery

**Tuning Guide:**
The PID constants need to be tuned for your specific robot:
- `Kp` (Proportional): Start with 20-30, affects response to current error
- `Ki` (Integral): Start with 0, slowly increase if needed
- `Kd` (Derivative): Start with 10-20, helps prevent overshooting

**Tuning Process:**
1. Set Ki and Kd to 0
2. Increase Kp until robot oscillates around line
3. Add Kd to reduce oscillations
4. Add Ki only if robot drifts over time (usually not needed)

---

### 3. Bluetooth Control Version (`bluetooth_control.ino`)
**Wireless control** via smartphone or Bluetooth terminal.

**Features:**
- Bluetooth connectivity (HC-05/HC-06)
- Remote start/stop control
- Auto mode (line following)
- Manual mode (remote control)
- Status updates via Bluetooth

**Use Case:**
- Demonstrations
- Remote operation
- Testing and debugging
- Adding wireless features

**Hardware Needed:**
- Arduino Mega
- L293D Motor Driver
- 2x IR Sensors
- 2x DC Motors
- HC-05 or HC-06 Bluetooth module
- Battery

**Commands:**
- `S` - Start robot
- `X` - Stop robot
- `A` - Auto mode (line following)
- `M` - Manual mode
- `F` - Forward (manual mode)
- `B` - Backward (manual mode)
- `L` - Left turn (manual mode)
- `R` - Right turn (manual mode)
- `P` - Stop motors (manual mode)

**Setup:**
1. Connect HC-05 TX to Arduino RX (Pin 19)
2. Connect HC-05 RX to Arduino TX (Pin 18) through voltage divider
3. Pair with device (default PIN: 1234 or 0000)
4. Use Serial Bluetooth Terminal app

---

## How to Use Examples

### Method 1: Arduino IDE
1. Open the `.ino` file in Arduino IDE
2. Select your board and port
3. Upload to Arduino

### Method 2: Copy to Main Project
1. Copy the code from desired example
2. Paste into `src/line_following_robot.ino`
3. Upload to Arduino

## Comparison Table

| Feature | Basic | Main (src) | PID | Bluetooth |
|---------|-------|-----------|-----|-----------|
| Difficulty | Easy | Easy | Medium | Medium |
| Components | Minimal | Standard | More sensors | + BT module |
| LCD Display | ❌ | ✅ | Optional | Optional |
| LED Indicators | ❌ | ✅ | Optional | Optional |
| IR Sensors | 2 | 2 | 3+ | 2 |
| Control | Simple | Simple | PID | Simple + Remote |
| Speed | Medium | Medium | High | Medium |
| Accuracy | Good | Good | Excellent | Good |
| Wireless | ❌ | ❌ | ❌ | ✅ |

## Contributing

Have an interesting variation? Submit a pull request with:
- Well-commented code
- Description of new features
- Hardware requirements
- Usage instructions

## Ideas for More Examples

Want to contribute? Here are some ideas:

- **Obstacle Avoidance**: Add ultrasonic sensor to avoid obstacles
- **Speed Tracking**: Count encoder pulses for speed control
- **Multi-mode**: Switch between different line-following algorithms
- **WiFi Control**: Use ESP8266/ESP32 for web interface
- **OLED Display**: Use OLED instead of LCD for better visibility
- **Battery Monitor**: Monitor and display battery voltage
- **Data Logger**: Log sensor data to SD card
- **Voice Control**: Add voice commands via Bluetooth
- **Gesture Control**: Control with hand gestures using accelerometer

## Support

Questions about examples?
- Check the main [README](../README.md)
- Open an [issue](https://github.com/kulkarnishub377/A_line_following_robot/issues)
- Review [troubleshooting guide](../README.md#troubleshooting)

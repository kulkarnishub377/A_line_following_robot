# Circuit Diagram

## Schematic Overview

```
                                    Line Following Robot Circuit
                                          
         ┌─────────────────────────────────────────────────────────┐
         │                      Arduino Mega                       │
         │                                                          │
         │  Digital Pins:                    Analog Pins:          │
         │  2  ──────────────── Left IR      A0 ──── LED1          │
         │  4  ──────────────── Right IR     A1 ──── LED2          │
         │  5  ──────────────── Enable A     A2 ──── LED3          │
         │  6  ──────────────── Input 1      A3 ──── LED4          │
         │  7  ──────────────── Input 2      A4 ──── LED5          │
         │  8  ──────────────── Enable B                           │
         │  9  ──────────────── Input 3      I2C Pins:             │
         │  10 ──────────────── Input 4      SDA (20) ── LCD SDA   │
         │                                   SCL (21) ── LCD SCL   │
         │  5V ──────┬──────── Sensors                             │
         │  GND ─────┴──────── Common Ground                       │
         └───────────────────────────────────────────────────────┘
                     │
                     │
         ┌───────────┴──────────────────────────────────┐
         │         L293D Motor Driver IC                │
         │                                               │
         │  Pin 1  (Enable A) ─── Arduino Pin 5         │
         │  Pin 2  (Input 1)  ─── Arduino Pin 6         │
         │  Pin 3  (Output 1) ─── Motor A Wire 1        │
         │  Pin 4  (GND)      ─── Ground                │
         │  Pin 5  (GND)      ─── Ground                │
         │  Pin 6  (Output 2) ─── Motor A Wire 2        │
         │  Pin 7  (Input 2)  ─── Arduino Pin 7         │
         │  Pin 8  (Vcc2)     ─── Battery + (7-12V)     │
         │  Pin 9  (Enable B) ─── Arduino Pin 8         │
         │  Pin 10 (Input 3)  ─── Arduino Pin 9         │
         │  Pin 11 (Output 3) ─── Motor B Wire 1        │
         │  Pin 12 (GND)      ─── Ground                │
         │  Pin 13 (GND)      ─── Ground                │
         │  Pin 14 (Output 4) ─── Motor B Wire 2        │
         │  Pin 15 (Input 4)  ─── Arduino Pin 10        │
         │  Pin 16 (Vcc1)     ─── Arduino 5V            │
         └──────────────────────────────────────────────┘
                     │
                     │
              ┌──────┴──────┐
              │             │
         ┌────▼────┐   ┌────▼────┐
         │ Motor A │   │ Motor B │
         │ (Right) │   │ (Left)  │
         └─────────┘   └─────────┘
```

## IR Sensor Connections

```
    Left IR Sensor              Right IR Sensor
    ┌────────────┐             ┌────────────┐
    │  VCC  ─────┼──── 5V      │  VCC  ─────┼──── 5V
    │  GND  ─────┼──── GND     │  GND  ─────┼──── GND
    │  OUT  ─────┼──── Pin 2   │  OUT  ─────┼──── Pin 4
    └────────────┘             └────────────┘
```

## LCD Display Connection (I2C)

```
    16x2 LCD with I2C Module
    ┌────────────────────┐
    │  VCC  ────────── 5V     │
    │  GND  ────────── GND    │
    │  SDA  ────────── Pin 20 │
    │  SCL  ────────── Pin 21 │
    └────────────────────┘
```

## LED Connections

```
    Each LED connected with 220Ω resistor in series:
    
    Arduino Pin → 220Ω Resistor → LED Anode (+)
                                     │
                                     ▼
                              LED Cathode (-) → GND
    
    LED1: Pin A0 → Resistor → LED → GND
    LED2: Pin A1 → Resistor → LED → GND
    LED3: Pin A2 → Resistor → LED → GND
    LED4: Pin A3 → Resistor → LED → GND
    LED5: Pin A4 → Resistor → LED → GND
```

## Power Distribution

```
                    Battery Pack (7.4V - 9V)
                           │
                    ┌──────┴──────┐
                    │             │
                    │   Switch    │
                    │             │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
        L293D Pin 8 (Vcc2)        Arduino Vin
        (Motor Power)             (Logic Power)
              │                         │
              │                         │
              └────────┬────────────────┘
                       │
                    Ground
```

## Complete Wiring Table

| Component | Component Pin | Arduino Pin | Notes |
|-----------|---------------|-------------|-------|
| **L293D Motor Driver** | | | |
| | Pin 1 (Enable A) | 5 (PWM) | Right motor speed control |
| | Pin 2 (Input 1) | 6 | Right motor direction |
| | Pin 7 (Input 2) | 7 | Right motor direction |
| | Pin 9 (Enable B) | 8 (PWM) | Left motor speed control |
| | Pin 10 (Input 3) | 9 | Left motor direction |
| | Pin 15 (Input 4) | 10 | Left motor direction |
| | Pin 3, 6 (Output 1,2) | Motor A | Right motor |
| | Pin 11, 14 (Output 3,4) | Motor B | Left motor |
| | Pin 16 (Vcc1) | 5V | Logic power |
| | Pin 8 (Vcc2) | Battery+ | Motor power (7-12V) |
| | Pin 4,5,12,13 (GND) | GND | Common ground |
| **IR Sensors** | | | |
| Left Sensor | OUT | 2 | Line detection |
| Right Sensor | OUT | 4 | Line detection |
| Both Sensors | VCC | 5V | Power |
| Both Sensors | GND | GND | Ground |
| **LCD Display** | | | |
| | VCC | 5V | Power |
| | GND | GND | Ground |
| | SDA | 20 (SDA) | I2C data |
| | SCL | 21 (SCL) | I2C clock |
| **LEDs** | | | |
| LED 1 | Anode (via 220Ω) | A0 | Right turn indicator |
| LED 2 | Anode (via 220Ω) | A1 | Left turn indicator |
| LED 3 | Anode (via 220Ω) | A2 | Status indicator |
| LED 4 | Anode (via 220Ω) | A3 | Status indicator |
| LED 5 | Anode (via 220Ω) | A4 | Status indicator |
| All LEDs | Cathode | GND | Common ground |

## Notes

- Always connect grounds together (Arduino GND, Motor Driver GND, Battery GND)
- Use separate power for motors (through L293D) and Arduino to prevent voltage drops
- Add a decoupling capacitor (100µF) across motor driver power pins
- Use heat sinks on L293D if motors draw high current
- Keep wire lengths as short as possible to reduce noise
- Use color-coded wires for easier debugging (Red=Power, Black=Ground, etc.)

## Testing Points

Use a multimeter to verify:
1. Battery voltage: 7-12V
2. Arduino 5V pin: 4.5-5.5V
3. Sensor output: 0V (white) or 5V (black)
4. Motor driver inputs: 0V or 5V from Arduino
5. No continuity between power and ground

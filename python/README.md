# Python Modules – Line Following Robot

This folder contains a comprehensive Python implementation that complements
the Arduino C++ firmware in `src/` and `examples/`.

## Contents

| File | Description |
|------|-------------|
| `pid_controller.py` | Full PID controller class with anti-windup, derivative filter, performance metrics (IAE/ISE/ITAE), and Ziegler-Nichols auto-tuner |
| `sensor_simulation.py` | IR sensor model, configurable sensor array, parametric track geometry (oval, figure-8, S-curve), and a TrackSampler |
| `robot_simulation.py` | 2-D differential-drive kinematics, full robot simulation loop, telemetry recording, matplotlib visualiser dashboard |
| `data_logger.py` | In-memory telemetry logger, CSV export/import, statistical analyser, performance reports, and batch benchmarking |
| `serial_monitor.py` | Arduino serial interface (real hardware + mock simulator), command set, telemetry parser, live plotter, avrdude wrapper |
| `requirements.txt` | Python package dependencies |

## Quick Start

### 1 – Install dependencies

```bash
pip install -r requirements.txt
```

### 2 – Run the simulation

```bash
# Oval track with balanced PID (default)
python robot_simulation.py

# Figure-8 track with aggressive PID, save dashboard PNG
python robot_simulation.py --track figure8 --pid aggressive --save /tmp/result.png

# S-curve track, custom duration
python robot_simulation.py --track scurve --duration 40 --dt 0.005
```

### 3 – Use the serial monitor (real hardware or mock)

```bash
# Mock serial port (no hardware needed)
python serial_monitor.py

# Real hardware on Linux
# Edit serial_monitor.py and change port="MOCK" to port="/dev/ttyUSB0"
```

### 4 – Run the data logger benchmarks

```bash
python data_logger.py
```

### 5 – Explore the PID controller

```bash
python pid_controller.py
```

## Architecture

```
robot_simulation.py
    ├── LineFollowingRobot
    │       ├── DifferentialDrive   (kinematics)
    │       ├── SensorArray         (sensor_simulation.py)
    │       │       └── IRSensor    (×2 / ×3 / ×5)
    │       ├── TrackSampler        (sensor_simulation.py)
    │       │       └── Track       (oval / figure-8 / S-curve)
    │       └── LineFollowingPID    (pid_controller.py)
    │               └── PIDController
    └── Simulation                  (orchestrates a run)
            └── SimulationPlotter   (matplotlib dashboard)

data_logger.py
    ├── TelemetryLogger
    ├── CSVExporter
    ├── LogAnalyser
    ├── PerformanceReport
    └── BatchBenchmark

serial_monitor.py
    ├── ArduinoSerial   ──► real hardware via pyserial
    │       └── MockSerial  (built-in simulator)
    ├── TelemetryParser
    ├── SerialMonitor
    ├── LivePlotter
    └── FirmwareUploader
```

## How it relates to the Arduino code

| Arduino sketch | Python equivalent |
|----------------|-------------------|
| `src/line_following_robot.ino` – basic IR + motor logic | `robot_simulation.py` – full kinematic simulation |
| `examples/advanced_pid.ino` – PID control | `pid_controller.py` – `LineFollowingPID` class |
| `examples/basic_version.ino` – sensor read + motor | `sensor_simulation.py` – `SensorArray` + `Track` |
| `examples/bluetooth_control.ino` – serial commands | `serial_monitor.py` – `RobotCommandSet` + `ArduinoSerial` |

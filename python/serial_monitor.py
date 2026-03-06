"""
serial_monitor.py
=================
Serial communication interface between Python and the Line Following Robot
Arduino firmware.

This module provides:
  - ``ArduinoSerial``      – low-level send/receive over UART/USB.
  - ``RobotCommandSet``    – typed command constants (mirrors bluetooth_control.ino).
  - ``SerialMonitor``      – interactive text UI for monitoring the robot.
  - ``TelemetryParser``    – converts raw serial text into structured records.
  - ``LivePlotter``        – real-time matplotlib plot of incoming sensor data.
  - ``FirmwareUploader``   – thin wrapper around ``avrdude`` for flashing.

Dependencies: pyserial, numpy, matplotlib (optional for LivePlotter)

NOTE: When the physical hardware is not connected you can use the built-in
``MockSerial`` class to simulate a serial port for testing and development.
"""

from __future__ import annotations

import re
import sys
import time
import threading
import queue
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterator, List, Optional, Tuple

import numpy as np

# Optional matplotlib import – required only for LivePlotter.plot()
try:
    import matplotlib
    import os
    if not matplotlib.is_interactive() and os.environ.get("MPLBACKEND") is None:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import pyserial; fall back gracefully for mock-only use
# ---------------------------------------------------------------------------
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logger.warning(
        "pyserial is not installed.  Only MockSerial will be available.  "
        "Install with: pip install pyserial"
    )


# ---------------------------------------------------------------------------
# Command set (mirrors bluetooth_control.ino)
# ---------------------------------------------------------------------------

class RobotCommandSet(str, Enum):
    """All commands recognised by the Bluetooth-enabled Arduino firmware."""
    START         = "S"   # Start autonomous line following
    STOP          = "X"   # Stop all motors
    AUTO_MODE     = "A"   # Switch to autonomous mode
    MANUAL_MODE   = "M"   # Switch to manual control
    FORWARD       = "F"   # Manual forward
    BACKWARD      = "B"   # Manual backward
    TURN_LEFT     = "L"   # Manual left
    TURN_RIGHT    = "R"   # Manual right
    MOTOR_STOP    = "P"   # Manual motor stop
    STATUS_REQ    = "?"   # Request a status dump (extension)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParsedMessage:
    """A single decoded message from the Arduino."""
    raw:       str
    timestamp: float = field(default_factory=time.monotonic)
    msg_type:  str  = "unknown"   # "sensor", "status", "debug", "error"
    fields:    dict = field(default_factory=dict)


@dataclass
class SensorReading:
    """Decoded IR sensor reading from the serial stream."""
    timestamp: float
    left:      int    # 0 or 1
    right:     int    # 0 or 1
    center:    Optional[int] = None   # present only in 3-sensor mode


@dataclass
class MotorStatus:
    """Decoded motor status from the serial stream."""
    timestamp:  float
    left_speed: int   # PWM value 0-255
    right_speed: int
    correction: int


# ---------------------------------------------------------------------------
# Mock serial port (for testing without hardware)
# ---------------------------------------------------------------------------

class MockSerial:
    """
    Simulates an Arduino serial port for development and testing.

    Emits realistic sensor and PID debug lines at ~100 Hz and echoes
    any commands sent to it.
    """

    _SENSOR_TEMPLATE = "L: {l} R: {r}\r\n"
    _PID_TEMPLATE    = "Error: {e} | Correction: {c} | L: {ls} R: {rs}\r\n"

    def __init__(
        self,
        port: str = "MOCK",
        baudrate: int = 9600,
        scenario: str = "straight",
    ) -> None:
        self.port     = port
        self.baudrate = baudrate
        self.scenario = scenario
        self.is_open  = False
        self._buf     = b""
        self._rx_q: queue.Queue[bytes] = queue.Queue()
        self._tx_q: queue.Queue[bytes] = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def open(self) -> None:
        self.is_open = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._generator, daemon=True, name="MockSerial-gen"
        )
        self._thread.start()
        logger.debug("MockSerial opened on %s", self.port)

    def close(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.is_open = False

    def write(self, data: bytes) -> int:
        self._tx_q.put(data)
        return len(data)

    def readline(self) -> bytes:
        try:
            return self._rx_q.get(timeout=0.5)
        except queue.Empty:
            return b""

    def read_until(self, expected: bytes = b"\n", size: Optional[int] = None) -> bytes:
        return self.readline()

    @property
    def in_waiting(self) -> int:
        return self._rx_q.qsize()

    def __enter__(self) -> "MockSerial":
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Background generator thread
    # ------------------------------------------------------------------

    def _generator(self) -> None:
        t = 0.0
        while not self._stop_event.is_set():
            l, r, e, c, ls, rs = self._next_frame(t)
            line = self._PID_TEMPLATE.format(e=e, c=c, ls=ls, rs=rs).encode()
            self._rx_q.put(line)
            t += 0.01
            time.sleep(0.01)

    def _next_frame(self, t: float) -> Tuple:
        """Generate one frame of simulated sensor data."""
        if self.scenario == "straight":
            error      = int(round(0.3 * np.sin(2 * np.pi * t / 5.0)))
        elif self.scenario == "zigzag":
            error      = int(round(1.5 * np.sin(2 * np.pi * t / 2.0)))
        else:
            error      = 0

        correction = error * 25
        left_speed  = max(0, min(255, 150 + correction))
        right_speed = max(0, min(255, 150 - correction))
        return (0, 0, error, correction, left_speed, right_speed)


# ---------------------------------------------------------------------------
# Arduino serial interface
# ---------------------------------------------------------------------------

class ArduinoSerial:
    """
    Low-level serial interface for communicating with the Arduino.

    Wraps either ``serial.Serial`` (real hardware) or ``MockSerial``
    (simulation/testing).

    Parameters
    ----------
    port : str
        Serial port name (e.g. ``"COM3"`` on Windows, ``"/dev/ttyUSB0"`` on Linux).
        Pass ``"MOCK"`` to use the built-in simulator.
    baudrate : int
        Baud rate (must match Arduino sketch – default 9600).
    timeout : float
        Read timeout in seconds.
    mock_scenario : str
        Only used when port is ``"MOCK"``.
    """

    def __init__(
        self,
        port: str = "MOCK",
        baudrate: int = 9600,
        timeout: float = 1.0,
        mock_scenario: str = "straight",
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._mock_scenario = mock_scenario
        self._conn = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the serial connection."""
        if self.port.upper() == "MOCK":
            self._conn = MockSerial(
                port=self.port, baudrate=self.baudrate, scenario=self._mock_scenario
            )
            self._conn.open()
        elif not SERIAL_AVAILABLE:
            raise RuntimeError(
                "pyserial is not installed. Cannot open a real serial port. "
                "Use port='MOCK' for simulation."
            )
        else:
            self._conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
        logger.info("Connected to %s @ %d baud", self.port, self.baudrate)

    def disconnect(self) -> None:
        """Close the serial connection gracefully."""
        if self._conn and self._conn.is_open:
            self._conn.close()
            logger.info("Disconnected from %s", self.port)

    def __enter__(self) -> "ArduinoSerial":
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.disconnect()

    # ------------------------------------------------------------------
    # Read / Write
    # ------------------------------------------------------------------

    def send_command(self, cmd: RobotCommandSet) -> None:
        """Send a single-character command to the robot."""
        if self._conn is None or not self._conn.is_open:
            raise RuntimeError("Not connected.")
        self._conn.write(cmd.value.encode())
        logger.debug("Sent command: %s", cmd.name)

    def readline(self) -> str:
        """Read one line from the Arduino and decode it."""
        if self._conn is None:
            raise RuntimeError("Not connected.")
        raw = self._conn.readline()
        return raw.decode("utf-8", errors="replace").strip()

    def lines(self, count: Optional[int] = None) -> Iterator[str]:
        """Iterate over incoming lines, optionally stopping after ``count`` lines."""
        i = 0
        while count is None or i < count:
            line = self.readline()
            if line:
                yield line
                i += 1

    @property
    def is_connected(self) -> bool:
        return self._conn is not None and self._conn.is_open

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def list_ports() -> List[str]:
        """Return a list of available serial port names."""
        if not SERIAL_AVAILABLE:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]


# ---------------------------------------------------------------------------
# Telemetry parser
# ---------------------------------------------------------------------------

class TelemetryParser:
    """
    Parses raw serial text from the Arduino into structured objects.

    Supports the output formats from all three example sketches:
    - basic_version.ino:     ``L: 0 R: 1``
    - advanced_pid.ino:      ``Error: -1 | Correction: -25 | L: 125 R: 175``
    - bluetooth_control.ino: status strings like ``"Robot Started"``
    """

    # Regex patterns
    _RE_BASIC  = re.compile(r"L:\s*(\d)\s+R:\s*(\d)")
    _RE_PID    = re.compile(
        r"Error:\s*(-?\d+)\s*\|\s*Correction:\s*(-?\d+)"
        r"\s*\|\s*L:\s*(\d+)\s+R:\s*(\d+)"
    )
    _RE_STATUS = re.compile(r"(Robot|Auto|Manual|Started|Stopped|Ready)", re.I)

    def parse(self, line: str) -> ParsedMessage:
        """
        Parse a single serial line into a ``ParsedMessage``.

        Parameters
        ----------
        line : str
            One decoded line from the serial port.

        Returns
        -------
        ParsedMessage
        """
        now = time.monotonic()
        msg = ParsedMessage(raw=line, timestamp=now)

        m_pid = self._RE_PID.search(line)
        if m_pid:
            msg.msg_type = "pid"
            msg.fields = {
                "error":       int(m_pid.group(1)),
                "correction":  int(m_pid.group(2)),
                "left_speed":  int(m_pid.group(3)),
                "right_speed": int(m_pid.group(4)),
            }
            return msg

        m_basic = self._RE_BASIC.search(line)
        if m_basic:
            msg.msg_type = "sensor"
            msg.fields = {
                "left":  int(m_basic.group(1)),
                "right": int(m_basic.group(2)),
            }
            return msg

        m_status = self._RE_STATUS.search(line)
        if m_status:
            msg.msg_type = "status"
            msg.fields   = {"text": line}
            return msg

        msg.msg_type = "debug"
        msg.fields   = {"text": line}
        return msg

    def parse_pid_message(self, line: str) -> Optional[MotorStatus]:
        """Parse a PID line into a ``MotorStatus`` or return None."""
        m = self._RE_PID.search(line)
        if not m:
            return None
        return MotorStatus(
            timestamp=time.monotonic(),
            left_speed=int(m.group(3)),
            right_speed=int(m.group(4)),
            correction=int(m.group(2)),
        )

    def parse_sensor_message(self, line: str) -> Optional[SensorReading]:
        """Parse a basic sensor line into a ``SensorReading`` or return None."""
        m = self._RE_BASIC.search(line)
        if not m:
            return None
        return SensorReading(
            timestamp=time.monotonic(),
            left=int(m.group(1)),
            right=int(m.group(2)),
        )


# ---------------------------------------------------------------------------
# Interactive serial monitor
# ---------------------------------------------------------------------------

class SerialMonitor:
    """
    Text-based interactive monitor for the Arduino serial output.

    Start it, and it will print incoming lines with timestamps and
    colour-coded type labels.  You can also send commands interactively.

    Parameters
    ----------
    arduino : ArduinoSerial
        An already-connected ``ArduinoSerial`` instance.
    max_lines : int | None
        Stop after this many lines (None = run forever until interrupted).
    """

    COLOUR = {
        "pid":    "\033[36m",   # cyan
        "sensor": "\033[32m",   # green
        "status": "\033[33m",   # yellow
        "error":  "\033[31m",   # red
        "debug":  "\033[37m",   # white
        "reset":  "\033[0m",
    }

    def __init__(
        self,
        arduino: ArduinoSerial,
        max_lines: Optional[int] = None,
    ) -> None:
        self.arduino   = arduino
        self.max_lines = max_lines
        self.parser    = TelemetryParser()
        self._running  = False

    def run(self) -> None:
        """Start the blocking monitor loop."""
        self._running = True
        print("Serial Monitor started – Ctrl+C to stop\n")
        count = 0
        try:
            for line in self.arduino.lines(count=self.max_lines):
                if not self._running:
                    break
                msg = self.parser.parse(line)
                self._print_message(msg)
                count += 1
        except KeyboardInterrupt:
            pass
        print("\nSerial Monitor stopped.")

    def stop(self) -> None:
        self._running = False

    def _print_message(self, msg: ParsedMessage) -> None:
        colour = self.COLOUR.get(msg.msg_type, self.COLOUR["debug"])
        reset  = self.COLOUR["reset"]
        t_str  = f"{msg.timestamp:10.3f}"
        print(f"[{t_str}] {colour}[{msg.msg_type:6s}]{reset} {msg.raw}")


# ---------------------------------------------------------------------------
# Live plotter
# ---------------------------------------------------------------------------

class LivePlotter:
    """
    Accumulates motor-speed and error data from the serial stream and
    produces a matplotlib snapshot when ``plot()`` is called.

    Useful for offline analysis after capturing a serial session, or in
    environments where live animation isn't possible.

    Parameters
    ----------
    capacity : int
        Rolling-window size (number of records to keep).
    """

    def __init__(self, capacity: int = 500) -> None:
        self.capacity = capacity
        self._times:  list[float] = []
        self._left:   list[int]   = []
        self._right:  list[int]   = []
        self._errors: list[int]   = []

    def ingest(self, msg: ParsedMessage) -> None:
        """Append a parsed PID message to the internal buffers."""
        if msg.msg_type != "pid":
            return
        f = msg.fields
        self._times.append(msg.timestamp)
        self._left.append(f.get("left_speed", 0))
        self._right.append(f.get("right_speed", 0))
        self._errors.append(f.get("error", 0))
        # Trim to capacity
        if len(self._times) > self.capacity:
            self._times.pop(0)
            self._left.pop(0)
            self._right.pop(0)
            self._errors.pop(0)

    def ingest_many(self, messages: List[ParsedMessage]) -> None:
        for m in messages:
            self.ingest(m)

    def plot(self, save_path: Optional[str] = None):
        """
        Draw a two-panel chart (motor speeds and error) using matplotlib.

        Parameters
        ----------
        save_path : str | None
            If given, the figure is saved to this path instead of shown.
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "matplotlib is required for plotting. "
                "Install with: pip install matplotlib"
            )

        if not self._times:
            print("No data to plot.")
            return None

        t0 = self._times[0]
        t  = [ts - t0 for ts in self._times]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        fig.suptitle("Live Serial Monitor – Robot Telemetry")

        ax1.plot(t, self._left,  label="Left PWM",  color="royalblue")
        ax1.plot(t, self._right, label="Right PWM", color="tomato")
        ax1.set_ylabel("Motor PWM")
        ax1.legend()
        ax1.grid(True, linestyle=":", alpha=0.5)

        ax2.plot(t, self._errors, color="darkorange", label="Sensor error")
        ax2.axhline(0, color="black", linewidth=0.8)
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Error")
        ax2.legend()
        ax2.grid(True, linestyle=":", alpha=0.5)

        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Live plot saved to {save_path}")
        return fig


# ---------------------------------------------------------------------------
# Firmware uploader (thin avrdude wrapper)
# ---------------------------------------------------------------------------

class FirmwareUploader:
    """
    Upload compiled Arduino firmware (.hex) to the board using avrdude.

    Parameters
    ----------
    port : str
        Serial port connected to the Arduino.
    board : str
        Arduino board type for avrdude (e.g. ``"atmega2560"`` for Mega,
        ``"atmega328p"`` for Uno).
    baudrate : int
        Upload baud rate (57600 for Uno, 115200 for Mega).
    avrdude_path : str
        Path to the avrdude executable.
    """

    BOARD_CONFIG = {
        "atmega2560": {"programmer": "wiring",    "baudrate": 115200},
        "atmega328p": {"programmer": "arduino",   "baudrate": 57600},
        "atmega32u4": {"programmer": "avr109",    "baudrate": 57600},
    }

    def __init__(
        self,
        port: str,
        board: str = "atmega2560",
        baudrate: Optional[int] = None,
        avrdude_path: str = "avrdude",
    ) -> None:
        self.port         = port
        self.board        = board
        self.avrdude_path = avrdude_path
        cfg = self.BOARD_CONFIG.get(board, {})
        self.programmer   = cfg.get("programmer", "arduino")
        self.baudrate     = baudrate or cfg.get("baudrate", 115200)

    def upload(self, hex_path: str, dry_run: bool = False) -> str:
        """
        Build and optionally execute the avrdude command.

        Parameters
        ----------
        hex_path : str
            Path to the compiled ``*.hex`` file.
        dry_run : bool
            If True, return the command string without executing it.

        Returns
        -------
        str
            The avrdude command that was (or would be) run.
        """
        cmd = (
            f"{self.avrdude_path} "
            f"-p {self.board} "
            f"-c {self.programmer} "
            f"-P {self.port} "
            f"-b {self.baudrate} "
            f'-U flash:w:"{hex_path}":i'
        )
        if dry_run:
            return cmd

        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"avrdude failed (exit {result.returncode}):\n{result.stderr}"
            )
        return result.stdout


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Serial Monitor Self-Test ===\n")

    parser = TelemetryParser()
    plotter = LivePlotter(capacity=200)

    # Connect to mock Arduino
    with ArduinoSerial(port="MOCK", mock_scenario="zigzag") as ard:
        print("Reading 50 lines from mock Arduino…\n")
        messages = []
        for line in ard.lines(count=50):
            msg = parser.parse(line)
            plotter.ingest(msg)
            messages.append(msg)
            t_str = f"{msg.timestamp:.3f}"
            print(f"  [{t_str}] [{msg.msg_type:6s}] {msg.raw}")

    # Save live plot
    save_path = "/tmp/serial_monitor_plot.png"
    plotter.plot(save_path=save_path)

    # Firmware uploader dry-run
    uploader = FirmwareUploader(port="/dev/ttyUSB0", board="atmega2560")
    cmd = uploader.upload("/tmp/firmware.hex", dry_run=True)
    print(f"\navrdude dry-run command:\n  {cmd}")

    print("\nSelf-test complete.")

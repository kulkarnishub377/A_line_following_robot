"""
pid_controller.py
=================
A comprehensive PID (Proportional-Integral-Derivative) controller
implementation for the Line Following Robot.

This module provides:
  - A generic PID controller class with anti-windup and derivative filtering.
  - A specialised LineFollowingPID subclass pre-tuned for the robot.
  - Auto-tuning utilities (Ziegler-Nichols method).
  - Performance metrics (IAE, ISE, ITAE).

Dependencies: numpy
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PIDGains:
    """Container for PID tuning parameters."""
    kp: float = 1.0
    ki: float = 0.0
    kd: float = 0.0

    def __str__(self) -> str:
        return f"PIDGains(Kp={self.kp:.4f}, Ki={self.ki:.4f}, Kd={self.kd:.4f})"


@dataclass
class PIDState:
    """Internal runtime state of the PID controller."""
    integral: float = 0.0
    prev_error: float = 0.0
    prev_derivative: float = 0.0
    last_time: float = field(default_factory=time.monotonic)
    output_history: list = field(default_factory=list)
    error_history: list = field(default_factory=list)
    time_history: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core PID controller
# ---------------------------------------------------------------------------

class PIDController:
    """
    Generic discrete-time PID controller.

    Features
    --------
    * Anti-windup clamping on the integral term.
    * Optional derivative low-pass filter to reduce noise amplification.
    * Configurable output saturation limits.
    * Bumpless parameter switching.
    * Complete history logging for post-run analysis.

    Parameters
    ----------
    gains : PIDGains
        Initial Kp, Ki, Kd values.
    output_limits : tuple[float, float]
        (min, max) bounds for the controller output.
    integral_limits : tuple[float, float]
        (min, max) anti-windup bounds for the integral accumulator.
    derivative_filter : float
        Low-pass filter coefficient for the derivative term (0 = no filter,
        1 = maximum smoothing). Must be in [0, 1).
    setpoint : float
        Desired process value.
    sample_time : float | None
        Fixed sample time in seconds.  If None the controller uses the
        wall-clock elapsed time between calls.
    """

    def __init__(
        self,
        gains: PIDGains,
        output_limits: tuple[float, float] = (-255.0, 255.0),
        integral_limits: tuple[float, float] = (-100.0, 100.0),
        derivative_filter: float = 0.1,
        setpoint: float = 0.0,
        sample_time: Optional[float] = None,
    ) -> None:
        self.gains = gains
        self.output_limits = output_limits
        self.integral_limits = integral_limits
        self.derivative_filter = np.clip(derivative_filter, 0.0, 0.999)
        self.setpoint = setpoint
        self.sample_time = sample_time

        self._state = PIDState()
        self._start_time = time.monotonic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(self, measurement: float) -> float:
        """
        Compute the next control output.

        Parameters
        ----------
        measurement : float
            Current process measurement.

        Returns
        -------
        float
            Control output clamped to output_limits.
        """
        now = time.monotonic()
        dt = self._get_dt(now)

        error = self.setpoint - measurement
        self._state.integral = self._update_integral(error, dt)
        derivative = self._update_derivative(error, dt)

        output = (
            self.gains.kp * error
            + self.gains.ki * self._state.integral
            + self.gains.kd * derivative
        )
        output = np.clip(output, *self.output_limits)

        # Record history
        elapsed = now - self._start_time
        self._state.error_history.append(error)
        self._state.output_history.append(output)
        self._state.time_history.append(elapsed)

        self._state.prev_error = error
        self._state.last_time = now
        return float(output)

    def reset(self) -> None:
        """Reset integrator and derivative memory without clearing history."""
        self._state.integral = 0.0
        self._state.prev_error = 0.0
        self._state.prev_derivative = 0.0
        self._state.last_time = time.monotonic()

    def clear_history(self) -> None:
        """Erase all logged history."""
        self._state.output_history.clear()
        self._state.error_history.clear()
        self._state.time_history.clear()

    def set_gains(self, gains: PIDGains) -> None:
        """Bumpless parameter update – recalculate integral to avoid step."""
        if self.gains.ki != 0 and gains.ki != 0:
            self._state.integral *= self.gains.ki / gains.ki
        self.gains = gains

    # ------------------------------------------------------------------
    # Performance metrics
    # ------------------------------------------------------------------

    @property
    def iae(self) -> float:
        """Integral Absolute Error (lower is better)."""
        errors = np.array(self._state.error_history)
        times = np.array(self._state.time_history)
        if len(errors) < 2:
            return float("nan")
        return float(np.trapezoid(np.abs(errors), times))

    @property
    def ise(self) -> float:
        """Integral Squared Error."""
        errors = np.array(self._state.error_history)
        times = np.array(self._state.time_history)
        if len(errors) < 2:
            return float("nan")
        return float(np.trapezoid(errors ** 2, times))

    @property
    def itae(self) -> float:
        """Integral Time-weighted Absolute Error."""
        errors = np.array(self._state.error_history)
        times = np.array(self._state.time_history)
        if len(errors) < 2:
            return float("nan")
        return float(np.trapezoid(times * np.abs(errors), times))

    def summary(self) -> str:
        """Return a formatted performance summary string."""
        return (
            f"PID Performance Summary\n"
            f"  Gains  : {self.gains}\n"
            f"  Samples: {len(self._state.error_history)}\n"
            f"  IAE    : {self.iae:.4f}\n"
            f"  ISE    : {self.ise:.4f}\n"
            f"  ITAE   : {self.itae:.4f}\n"
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_dt(self, now: float) -> float:
        if self.sample_time is not None:
            return self.sample_time
        dt = now - self._state.last_time
        return dt if dt > 1e-9 else 1e-3

    def _update_integral(self, error: float, dt: float) -> float:
        integral = self._state.integral + error * dt
        return float(np.clip(integral, *self.integral_limits))

    def _update_derivative(self, error: float, dt: float) -> float:
        raw = (error - self._state.prev_error) / dt
        filtered = (
            self.derivative_filter * self._state.prev_derivative
            + (1.0 - self.derivative_filter) * raw
        )
        self._state.prev_derivative = filtered
        return filtered


# ---------------------------------------------------------------------------
# Specialised subclass
# ---------------------------------------------------------------------------

class LineFollowingPID(PIDController):
    """
    PID controller pre-configured for line following.

    The default gains replicate the values used in the Arduino
    ``advanced_pid.ino`` example (Kp=25, Ki=0, Kd=15) but expressed
    as a proper PID object so they can be compared and tuned in Python.

    The sensor error convention:
      -2 : far left of line
      -1 : slightly left
       0 : centred on line
      +1 : slightly right
      +2 : far right
    """

    # Preset gain sets named after tuning strategies
    PRESET_AGGRESSIVE = PIDGains(kp=40.0, ki=0.5, kd=20.0)
    PRESET_BALANCED   = PIDGains(kp=25.0, ki=0.0, kd=15.0)
    PRESET_CONSERVATIVE = PIDGains(kp=15.0, ki=0.0, kd=8.0)

    def __init__(
        self,
        preset: str = "balanced",
        base_speed: int = 150,
        max_speed: int = 255,
    ) -> None:
        presets = {
            "aggressive": self.PRESET_AGGRESSIVE,
            "balanced": self.PRESET_BALANCED,
            "conservative": self.PRESET_CONSERVATIVE,
        }
        gains = presets.get(preset.lower(), self.PRESET_BALANCED)
        super().__init__(
            gains=gains,
            output_limits=(-float(max_speed), float(max_speed)),
            integral_limits=(-50.0, 50.0),
            derivative_filter=0.05,
            setpoint=0.0,
            sample_time=0.01,
        )
        self.base_speed = base_speed
        self.max_speed = max_speed

    def motor_speeds(self, sensor_error: float) -> tuple[int, int]:
        """
        Translate a sensor error value into (left_speed, right_speed).

        Parameters
        ----------
        sensor_error : float
            Deviation of the robot from the line centre (-2 … +2).

        Returns
        -------
        tuple[int, int]
            Left and right motor PWM values in [0, max_speed].
        """
        correction = int(self.compute(sensor_error))
        left  = int(np.clip(self.base_speed + correction, 0, self.max_speed))
        right = int(np.clip(self.base_speed - correction, 0, self.max_speed))
        return left, right


# ---------------------------------------------------------------------------
# Ziegler-Nichols auto-tuner
# ---------------------------------------------------------------------------

class ZieglerNicholsTuner:
    """
    Estimate PID gains using the Ziegler-Nichols ultimate-gain method.

    The caller is responsible for running the plant with a P-only controller
    and recording the sustained oscillation period (Tu) and the gain at
    which oscillation occurs (Ku).

    Parameters
    ----------
    ku : float
        Ultimate (critical) gain.
    tu : float
        Oscillation period in seconds.
    """

    def __init__(self, ku: float, tu: float) -> None:
        if ku <= 0 or tu <= 0:
            raise ValueError("ku and tu must be positive.")
        self.ku = ku
        self.tu = tu

    def classic_pid(self) -> PIDGains:
        """Classic Ziegler-Nichols PID tuning rule."""
        return PIDGains(
            kp=0.6 * self.ku,
            ki=(1.2 * self.ku) / self.tu,
            kd=0.075 * self.ku * self.tu,
        )

    def no_overshoot_pid(self) -> PIDGains:
        """Modified rule targeting zero overshoot."""
        return PIDGains(
            kp=0.2 * self.ku,
            ki=(0.4 * self.ku) / self.tu,
            kd=0.066 * self.ku * self.tu,
        )

    def pi_only(self) -> PIDGains:
        """Ziegler-Nichols PI tuning."""
        return PIDGains(
            kp=0.45 * self.ku,
            ki=(0.54 * self.ku) / self.tu,
            kd=0.0,
        )

    def compare_all(self) -> dict[str, PIDGains]:
        """Return all tuning variants as a dict."""
        return {
            "classic_pid":     self.classic_pid(),
            "no_overshoot_pid": self.no_overshoot_pid(),
            "pi_only":         self.pi_only(),
        }


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== PID Controller Self-Test ===\n")

    # Basic P-only controller
    ctrl = PIDController(
        gains=PIDGains(kp=1.0, ki=0.1, kd=0.05),
        output_limits=(-100.0, 100.0),
        sample_time=0.01,
        setpoint=0.0,
    )

    # Simulate step response: measurement starts at -2 and drifts toward 0
    errors_sim = np.linspace(-2.0, 0.05, 200)
    for e in errors_sim:
        ctrl.compute(e)

    print(ctrl.summary())

    # Line-following PID
    lfpid = LineFollowingPID(preset="balanced")
    print("Motor speeds for error -2:", lfpid.motor_speeds(-2))
    print("Motor speeds for error  0:", lfpid.motor_speeds(0))
    print("Motor speeds for error +2:", lfpid.motor_speeds(2))

    # Ziegler-Nichols
    tuner = ZieglerNicholsTuner(ku=50.0, tu=0.8)
    for name, gains in tuner.compare_all().items():
        print(f"  {name:20s}: {gains}")

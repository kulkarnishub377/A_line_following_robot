"""
robot_simulation.py
===================
Full 2-D kinematic simulation of the Line Following Robot.

This module provides:
  - ``RobotState``         – immutable snapshot of the robot pose and speeds.
  - ``DifferentialDrive``  – unicycle/differential-drive kinematics.
  - ``LineFollowingRobot`` – high-level robot that ties together sensors,
                             PID controller, drive model, and a track.
  - ``Simulation``         – orchestrates a complete run and records telemetry.
  - ``SimulationPlotter``  – produces publication-quality matplotlib figures.

Dependencies: numpy, matplotlib
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import matplotlib
# Use the non-interactive Agg back-end unless the caller has already set
# a different back-end (e.g. TkAgg for interactive use).
import os
if not matplotlib.is_interactive() and os.environ.get("MPLBACKEND") is None:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

from pid_controller import LineFollowingPID, PIDGains, PIDController
from sensor_simulation import (
    SensorArray,
    SensorState,
    Track,
    TrackSampler,
    make_oval_track,
    make_figure8_track,
    make_s_curve_track,
)


# ---------------------------------------------------------------------------
# Robot state
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RobotState:
    """Immutable snapshot of robot kinematics."""
    x: float = 0.0         # World x-position (metres)
    y: float = 0.0         # World y-position (metres)
    heading: float = 0.0   # Heading in radians (0 = +x direction)
    left_speed: float = 0.0  # Left motor PWM [0, 255]
    right_speed: float = 0.0  # Right motor PWM [0, 255]
    timestamp: float = 0.0


# ---------------------------------------------------------------------------
# Differential-drive kinematics
# ---------------------------------------------------------------------------

class DifferentialDrive:
    """
    Kinematic model of a differential-drive (skid-steer) robot.

    Parameters
    ----------
    wheel_radius : float
        Radius of each driven wheel in metres.
    wheel_base : float
        Distance between the two driven wheels in metres.
    max_pwm : int
        Maximum PWM value (maps to ``max_linear_speed``).
    max_linear_speed : float
        Maximum linear wheel speed in m/s at full PWM.
    """

    def __init__(
        self,
        wheel_radius: float = 0.03,
        wheel_base: float = 0.12,
        max_pwm: int = 255,
        max_linear_speed: float = 0.5,
    ) -> None:
        self.wheel_radius = wheel_radius
        self.wheel_base = wheel_base
        self.max_pwm = max_pwm
        self.max_linear_speed = max_linear_speed

    def pwm_to_speed(self, pwm: float) -> float:
        """Convert a PWM duty cycle [0, max_pwm] to wheel speed (m/s)."""
        return (pwm / self.max_pwm) * self.max_linear_speed

    def step(
        self,
        state: RobotState,
        left_pwm: float,
        right_pwm: float,
        dt: float,
    ) -> RobotState:
        """
        Integrate the robot state forward by dt seconds.

        Uses the exact unicycle integration (arc-based) to avoid heading
        drift at large time steps.

        Parameters
        ----------
        state : RobotState
            Current robot state.
        left_pwm, right_pwm : float
            Motor commands in PWM units.
        dt : float
            Time step in seconds.

        Returns
        -------
        RobotState
            Updated robot state after dt seconds.
        """
        vl = self.pwm_to_speed(np.clip(left_pwm,  0, self.max_pwm))
        vr = self.pwm_to_speed(np.clip(right_pwm, 0, self.max_pwm))

        v = (vr + vl) / 2.0          # linear velocity
        omega = (vr - vl) / self.wheel_base  # angular velocity

        if abs(omega) < 1e-9:
            # Straight-line motion
            new_x = state.x + v * math.cos(state.heading) * dt
            new_y = state.y + v * math.sin(state.heading) * dt
            new_heading = state.heading
        else:
            # Arc motion
            r_curve = v / omega
            new_x = state.x + r_curve * (
                math.sin(state.heading + omega * dt) - math.sin(state.heading)
            )
            new_y = state.y - r_curve * (
                math.cos(state.heading + omega * dt) - math.cos(state.heading)
            )
            new_heading = state.heading + omega * dt

        # Normalise heading to [-π, π]
        new_heading = math.atan2(math.sin(new_heading), math.cos(new_heading))

        return RobotState(
            x=new_x,
            y=new_y,
            heading=new_heading,
            left_speed=left_pwm,
            right_speed=right_pwm,
            timestamp=state.timestamp + dt,
        )


# ---------------------------------------------------------------------------
# High-level robot
# ---------------------------------------------------------------------------

class LineFollowingRobot:
    """
    Autonomous line-following robot that combines sensors, PID, and kinematics.

    Parameters
    ----------
    track : Track
        The track to follow.
    n_sensors : int
        Number of IR sensors (2 or 3 recommended).
    pid_preset : str
        One of ``"aggressive"``, ``"balanced"``, or ``"conservative"``.
    base_speed : int
        Base motor PWM used when on-line.
    initial_state : RobotState
        Starting pose.
    """

    def __init__(
        self,
        track: Track,
        n_sensors: int = 3,
        pid_preset: str = "balanced",
        base_speed: int = 150,
        initial_state: Optional[RobotState] = None,
    ) -> None:
        self.track = track
        self.drive = DifferentialDrive()
        self.sensor_array = SensorArray(n_sensors=n_sensors, noise_probability=0.02)
        self.sampler = TrackSampler(self.sensor_array, track)
        self.pid = LineFollowingPID(preset=pid_preset, base_speed=base_speed)

        if initial_state is None:
            # Place robot at the first track waypoint facing the tangent
            wp = track.waypoints[0]
            wp2 = track.waypoints[1]
            heading = math.atan2(wp2[1] - wp[1], wp2[0] - wp[0])
            initial_state = RobotState(x=float(wp[0]), y=float(wp[1]),
                                       heading=heading)
        self.state = initial_state
        self._log: list[dict] = []

    # ------------------------------------------------------------------
    # Single step
    # ------------------------------------------------------------------

    def step(self, dt: float = 0.01) -> dict:
        """
        Advance the robot by one time step.

        Returns
        -------
        dict
            Telemetry snapshot for this step.
        """
        sample = self.sampler.sample(self.state.x, self.state.y, self.state.heading)
        error = sample["weighted_error"] * 2.0  # scale to Arduino's ±2 range

        left_pwm, right_pwm = self.pid.motor_speeds(error)

        # Stop if both sensors see black (end-of-line / intersection)
        all_black = all(r == SensorState.BLACK for r in sample["readings"])
        if all_black:
            left_pwm = right_pwm = 0

        self.state = self.drive.step(self.state, left_pwm, right_pwm, dt)

        telemetry = {
            "t":               self.state.timestamp,
            "x":               self.state.x,
            "y":               self.state.y,
            "heading":         self.state.heading,
            "left_pwm":        left_pwm,
            "right_pwm":       right_pwm,
            "weighted_error":  error,
            "discrete_error":  sample["discrete_error"],
            "cte":             sample["cross_track_error"],
            "stopped":         all_black,
        }
        self._log.append(telemetry)
        return telemetry

    # ------------------------------------------------------------------
    # Batch run
    # ------------------------------------------------------------------

    def run(self, duration: float = 20.0, dt: float = 0.01) -> list[dict]:
        """
        Run the simulation for ``duration`` seconds with step size ``dt``.

        Returns
        -------
        list[dict]
            Full telemetry log.
        """
        steps = int(duration / dt)
        for _ in range(steps):
            tel = self.step(dt)
            if tel["stopped"]:
                break
        return self._log

    @property
    def log(self) -> list[dict]:
        return self._log

    def log_as_arrays(self) -> dict[str, np.ndarray]:
        """Return the telemetry log as a dict of numpy arrays."""
        if not self._log:
            return {}
        keys = list(self._log[0].keys())
        return {k: np.array([row[k] for row in self._log]) for k in keys}


# ---------------------------------------------------------------------------
# Simulation orchestrator
# ---------------------------------------------------------------------------

class Simulation:
    """
    Top-level simulation runner that:
    * Creates and configures a ``LineFollowingRobot``.
    * Runs the simulation loop.
    * Captures wall-clock timing for real-time factor reporting.
    * Computes aggregate statistics.

    Parameters
    ----------
    track_type : str
        One of ``"oval"``, ``"figure8"``, or ``"scurve"``.
    duration : float
        Simulation time in seconds.
    dt : float
        Integration step size in seconds.
    pid_preset : str
        PID tuning preset forwarded to the robot.
    """

    def __init__(
        self,
        track_type: str = "oval",
        duration: float = 30.0,
        dt: float = 0.01,
        pid_preset: str = "balanced",
    ) -> None:
        self.track_type = track_type.lower()
        self.duration = duration
        self.dt = dt
        self.pid_preset = pid_preset

        self.track = self._build_track()
        self.robot = LineFollowingRobot(
            track=self.track,
            n_sensors=3,
            pid_preset=pid_preset,
        )

        self.wall_time_start: float = 0.0
        self.wall_time_end: float = 0.0

    def _build_track(self) -> Track:
        builders = {
            "oval":    lambda: make_oval_track(semi_major=1.0, semi_minor=0.6),
            "figure8": lambda: make_figure8_track(radius=0.6),
            "scurve":  lambda: make_s_curve_track(length=2.0, amplitude=0.35),
        }
        if self.track_type not in builders:
            raise ValueError(
                f"Unknown track type '{self.track_type}'. "
                f"Choose from: {list(builders)}"
            )
        return builders[self.track_type]()

    def run(self) -> dict[str, np.ndarray]:
        """Run the simulation and return telemetry arrays."""
        self.wall_time_start = time.monotonic()
        self.robot.run(duration=self.duration, dt=self.dt)
        self.wall_time_end = time.monotonic()
        return self.robot.log_as_arrays()

    @property
    def real_time_factor(self) -> float:
        """Ratio of simulated time to real elapsed time."""
        wall = self.wall_time_end - self.wall_time_start
        if wall < 1e-9:
            return float("inf")
        return self.duration / wall

    def statistics(self) -> dict:
        """Compute aggregate statistics from the completed run."""
        data = self.robot.log_as_arrays()
        if not data:
            return {}
        cte = data["cte"]
        return {
            "steps":          len(data["t"]),
            "sim_duration_s": float(data["t"][-1]),
            "mean_abs_cte_m": float(np.mean(np.abs(cte))),
            "max_abs_cte_m":  float(np.max(np.abs(cte))),
            "rms_cte_m":      float(np.sqrt(np.mean(cte ** 2))),
            "pid_iae":        self.robot.pid.iae,
            "pid_ise":        self.robot.pid.ise,
            "rtf":            self.real_time_factor,
        }

    def print_report(self) -> None:
        """Print a formatted simulation report to stdout."""
        stats = self.statistics()
        print(f"\n{'=' * 50}")
        print(f"  Line-Following Robot – Simulation Report")
        print(f"  Track   : {self.track_type}")
        print(f"  PID     : {self.pid_preset}")
        print(f"{'=' * 50}")
        for key, val in stats.items():
            if isinstance(val, float):
                print(f"  {key:25s}: {val:.4f}")
            else:
                print(f"  {key:25s}: {val}")
        print(f"{'=' * 50}\n")


# ---------------------------------------------------------------------------
# Visualiser
# ---------------------------------------------------------------------------

class SimulationPlotter:
    """
    Creates matplotlib figures visualising the simulation results.

    Parameters
    ----------
    simulation : Simulation
        A completed (post-``run()``) Simulation instance.
    """

    def __init__(self, simulation: Simulation) -> None:
        self.sim = simulation
        self.data = simulation.robot.log_as_arrays()

    # ------------------------------------------------------------------
    # Individual plots
    # ------------------------------------------------------------------

    def plot_trajectory(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """Plot robot trajectory overlaid on the track."""
        if ax is None:
            _, ax = plt.subplots(figsize=(8, 6))

        # Draw track
        wp = self.sim.track.waypoints
        ax.plot(wp[:, 0], wp[:, 1], "k--", linewidth=2, label="Track centre",
                alpha=0.6)

        # Draw robot path coloured by cross-track error magnitude
        x = self.data["x"]
        y = self.data["y"]
        cte = np.abs(self.data["cte"])

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        norm = plt.Normalize(cte.min(), cte.max())
        lc = LineCollection(segments, cmap="RdYlGn_r", norm=norm)
        lc.set_array(cte[:-1])
        lc.set_linewidth(2)
        ax.add_collection(lc)
        plt.colorbar(lc, ax=ax, label="Cross-track error (m)")

        # Start / end markers
        ax.plot(x[0], y[0], "go", markersize=10, label="Start", zorder=5)
        ax.plot(x[-1], y[-1], "rs", markersize=10, label="End",  zorder=5)

        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_title(f"Robot Trajectory – {self.sim.track_type.capitalize()} Track")
        ax.legend()
        ax.set_aspect("equal")
        ax.grid(True, linestyle=":", alpha=0.5)
        return ax

    def plot_cte_over_time(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """Plot cross-track error vs. simulation time."""
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 3))

        t   = self.data["t"]
        cte = self.data["cte"]
        ax.plot(t, cte, color="steelblue", linewidth=1, label="CTE")
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.fill_between(t, cte, alpha=0.15, color="steelblue")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Cross-track error (m)")
        ax.set_title("Cross-Track Error Over Time")
        ax.legend()
        ax.grid(True, linestyle=":", alpha=0.5)
        return ax

    def plot_motor_speeds(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """Plot left and right motor PWM signals over time."""
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 3))

        t = self.data["t"]
        ax.plot(t, self.data["left_pwm"],  label="Left PWM",  color="royalblue")
        ax.plot(t, self.data["right_pwm"], label="Right PWM", color="tomato")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("PWM")
        ax.set_title("Motor PWM Signals")
        ax.legend()
        ax.grid(True, linestyle=":", alpha=0.5)
        return ax

    def plot_heading(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """Plot robot heading angle over time."""
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 3))

        t = self.data["t"]
        ax.plot(t, np.degrees(self.data["heading"]), color="darkorange")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Heading (°)")
        ax.set_title("Robot Heading Over Time")
        ax.grid(True, linestyle=":", alpha=0.5)
        return ax

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def plot_dashboard(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Produce a 2×2 dashboard figure containing all four plots.

        Parameters
        ----------
        save_path : str | None
            If provided the figure is saved to this path (PNG format).
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            f"Line Following Robot Simulation\n"
            f"Track: {self.sim.track_type.capitalize()}  |  "
            f"PID: {self.sim.pid_preset.capitalize()}",
            fontsize=14,
        )

        self.plot_trajectory(ax=axes[0, 0])
        self.plot_cte_over_time(ax=axes[0, 1])
        self.plot_motor_speeds(ax=axes[1, 0])
        self.plot_heading(ax=axes[1, 1])

        plt.tight_layout(rect=[0, 0, 1, 0.93])

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Dashboard saved to: {save_path}")

        return fig


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Line Following Robot Simulation")
    parser.add_argument("--track",    default="oval",
                        choices=["oval", "figure8", "scurve"],
                        help="Track shape to simulate")
    parser.add_argument("--pid",      default="balanced",
                        choices=["aggressive", "balanced", "conservative"],
                        help="PID tuning preset")
    parser.add_argument("--duration", type=float, default=30.0,
                        help="Simulation duration in seconds")
    parser.add_argument("--dt",       type=float, default=0.01,
                        help="Integration time step in seconds")
    parser.add_argument("--save",     default=None,
                        help="Path to save dashboard PNG (optional)")
    args = parser.parse_args()

    sim = Simulation(
        track_type=args.track,
        duration=args.duration,
        dt=args.dt,
        pid_preset=args.pid,
    )

    print(f"Running {args.track} track simulation ({args.duration}s @ {args.dt}s step)…")
    sim.run()
    sim.print_report()

    plotter = SimulationPlotter(sim)
    save_path = args.save or f"/tmp/robot_sim_{args.track}_{args.pid}.png"
    plotter.plot_dashboard(save_path=save_path)
    print("Done.")

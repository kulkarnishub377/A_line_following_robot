"""
sensor_simulation.py
====================
Simulation of the IR sensors and track geometry used in the Line Following Robot.

This module provides:
  - ``IRSensor``       – models a single digital IR proximity sensor.
  - ``SensorArray``    – a configurable array of IRSensors (2, 3, 5, or 8).
  - ``Track``          – generates parametric track shapes (oval, figure-8,
                         S-curve, custom waypoints).
  - ``TrackSampler``   – queries track geometry to produce simulated sensor readings.

All geometry uses a right-handed 2-D coordinate system (x to the right,
y upward).  Angles are in radians unless documented otherwise.

Dependencies: numpy
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Iterator, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Sensor model
# ---------------------------------------------------------------------------

class SensorState(Enum):
    WHITE = 0   # surface is white / sensor sees reflective surface
    BLACK = 1   # surface is black  / sensor sees dark line


@dataclass
class IRSensor:
    """
    Model of a single digital IR proximity sensor.

    Attributes
    ----------
    name : str
        Human-readable label (e.g. ``"LEFT"``).
    x_offset : float
        Lateral offset from robot centre-line in metres (negative = left).
    noise_probability : float
        Probability of a spurious reading flip (0 = perfect sensor).
    """

    name: str
    x_offset: float = 0.0
    noise_probability: float = 0.02
    _rng: np.random.Generator = field(
        default_factory=lambda: np.random.default_rng(seed=42),
        repr=False,
        compare=False,
    )

    def read(self, over_line: bool) -> SensorState:
        """
        Return a (potentially noisy) sensor reading.

        Parameters
        ----------
        over_line : bool
            Ground-truth: is the sensor physically over the black line?

        Returns
        -------
        SensorState
        """
        state = SensorState.BLACK if over_line else SensorState.WHITE
        if self._rng.random() < self.noise_probability:
            # Flip due to noise
            state = SensorState.WHITE if state == SensorState.BLACK else SensorState.BLACK
        return state

    def read_digital(self, over_line: bool) -> int:
        """Return 0 (white) or 1 (black) as used by the Arduino code."""
        return self.read(over_line).value


# ---------------------------------------------------------------------------
# Sensor array
# ---------------------------------------------------------------------------

class SensorArray:
    """
    An array of equally-spaced IR sensors mounted below the robot.

    Parameters
    ----------
    n_sensors : int
        Number of sensors (2, 3, 5, or 8 are typical).
    spacing : float
        Centre-to-centre distance between adjacent sensors in metres.
    noise_probability : float
        Per-sensor noise probability forwarded to each ``IRSensor``.
    """

    SENSOR_NAMES = {
        2: ["LEFT", "RIGHT"],
        3: ["LEFT", "CENTER", "RIGHT"],
        5: ["FAR_LEFT", "LEFT", "CENTER", "RIGHT", "FAR_RIGHT"],
        8: [f"S{i}" for i in range(8)],
    }

    def __init__(
        self,
        n_sensors: int = 2,
        spacing: float = 0.015,
        noise_probability: float = 0.02,
    ) -> None:
        if n_sensors < 1:
            raise ValueError("At least one sensor is required.")
        self.n_sensors = n_sensors
        self.spacing = spacing

        names = self.SENSOR_NAMES.get(n_sensors, [f"S{i}" for i in range(n_sensors)])
        total_width = (n_sensors - 1) * spacing
        offsets = np.linspace(-total_width / 2, total_width / 2, n_sensors)

        self.sensors: list[IRSensor] = [
            IRSensor(name=names[i], x_offset=float(offsets[i]),
                     noise_probability=noise_probability)
            for i in range(n_sensors)
        ]

    def read_all(self, robot_x: float, robot_y: float, robot_heading: float,
                 track: "Track") -> list[SensorState]:
        """
        Read all sensors given the robot's current pose.

        Parameters
        ----------
        robot_x, robot_y : float
            Robot centre position in world coordinates (metres).
        robot_heading : float
            Robot heading in radians (0 = pointing in +x direction).
        track : Track
            The track object to query for line presence.

        Returns
        -------
        list[SensorState]
            One state per sensor.
        """
        readings = []
        cos_h = math.cos(robot_heading)
        sin_h = math.sin(robot_heading)
        # Perpendicular direction (90° to heading)
        perp_x = -sin_h
        perp_y =  cos_h

        for sensor in self.sensors:
            sx = robot_x + sensor.x_offset * perp_x
            sy = robot_y + sensor.x_offset * perp_y
            over = track.is_on_line(sx, sy)
            readings.append(sensor.read(over))

        return readings

    def weighted_error(self, readings: list[SensorState]) -> float:
        """
        Compute a weighted position error from sensor readings.

        Returns a value in [-1, 1] where:
          0    = robot centred on line
          < 0  = robot to the left of the line
          > 0  = robot to the right of the line
        """
        weights = np.linspace(-1.0, 1.0, self.n_sensors)
        values  = np.array([r.value for r in readings], dtype=float)
        total   = values.sum()
        if total == 0:
            return 0.0
        return float(np.dot(weights, values) / total)

    def discrete_error(self, readings: list[SensorState]) -> int:
        """
        Discrete error compatible with the Arduino advanced_pid.ino convention.

        Returns an integer error in {-2, -1, 0, 1, 2} for a 3-sensor array,
        or a generalised integer for other array sizes.
        """
        mid = self.n_sensors // 2
        indices = [i for i, r in enumerate(readings) if r == SensorState.BLACK]
        if not indices:
            return 0
        centroid = sum(indices) / len(indices)
        return int(round(centroid - mid))

    def __iter__(self) -> Iterator[IRSensor]:
        return iter(self.sensors)

    def __len__(self) -> int:
        return self.n_sensors

    def __repr__(self) -> str:
        names = [s.name for s in self.sensors]
        return f"SensorArray(n={self.n_sensors}, sensors={names})"


# ---------------------------------------------------------------------------
# Track geometry
# ---------------------------------------------------------------------------

class TrackShape(Enum):
    OVAL       = auto()
    FIGURE_8   = auto()
    S_CURVE    = auto()
    CUSTOM     = auto()


@dataclass
class Track:
    """
    Parametric 2-D track definition.

    The track is represented as a dense polyline of (x, y) waypoints.
    A robot sensor point is considered to be "on the line" if its
    distance to the nearest waypoint is less than ``line_width / 2``.

    Parameters
    ----------
    waypoints : np.ndarray, shape (N, 2)
        Ordered (x, y) track centreline points in metres.
    line_width : float
        Width of the black line in metres (default 0.025 m = 25 mm).
    closed : bool
        Whether the track forms a closed loop.
    """

    waypoints: np.ndarray
    line_width: float = 0.025
    closed: bool = True

    # Pre-built kdtree-like structure (built lazily)
    _tree: object = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.waypoints = np.asarray(self.waypoints, dtype=float)

    def is_on_line(self, x: float, y: float) -> bool:
        """Return True if point (x, y) lies within the line's width."""
        point = np.array([x, y])
        deltas = self.waypoints - point
        dists = np.hypot(deltas[:, 0], deltas[:, 1])
        return float(dists.min()) < (self.line_width / 2.0)

    def nearest_point_and_tangent(
        self, x: float, y: float
    ) -> tuple[np.ndarray, float]:
        """
        Find the nearest track point and the track tangent angle there.

        Returns
        -------
        nearest : np.ndarray, shape (2,)
            Nearest waypoint.
        tangent : float
            Track tangent angle in radians at the nearest waypoint.
        """
        point = np.array([x, y])
        deltas = self.waypoints - point
        dists = np.hypot(deltas[:, 0], deltas[:, 1])
        idx = int(np.argmin(dists))

        # Compute tangent using finite differences
        n = len(self.waypoints)
        if self.closed:
            prev_pt = self.waypoints[(idx - 1) % n]
            next_pt = self.waypoints[(idx + 1) % n]
        else:
            prev_pt = self.waypoints[max(idx - 1, 0)]
            next_pt = self.waypoints[min(idx + 1, n - 1)]

        dx = next_pt[0] - prev_pt[0]
        dy = next_pt[1] - prev_pt[1]
        tangent = math.atan2(dy, dx)
        return self.waypoints[idx], tangent

    def cross_track_error(self, x: float, y: float) -> float:
        """
        Signed lateral deviation from the track centre.

        Sign convention (right-handed 2-D frame):
          positive → robot is to the right of the line (when facing the
                     direction of travel along the track tangent).
          negative → robot is to the left of the line.
        """
        nearest, tangent = self.nearest_point_and_tangent(x, y)
        dx = x - nearest[0]
        dy = y - nearest[1]
        # The right-hand normal is obtained by rotating the tangent vector
        # clockwise by 90°, i.e. subtracting π/2 from the tangent angle.
        # Projecting (dx, dy) onto this normal gives positive values when the
        # robot is to the right of the line direction.
        normal_angle = tangent - math.pi / 2
        return dx * math.cos(normal_angle) + dy * math.sin(normal_angle)

    @property
    def total_length(self) -> float:
        """Approximate arc length of the track in metres."""
        segments = np.diff(self.waypoints, axis=0)
        lengths = np.hypot(segments[:, 0], segments[:, 1])
        if self.closed:
            closing = self.waypoints[0] - self.waypoints[-1]
            lengths = np.append(lengths, np.hypot(*closing))
        return float(lengths.sum())


# ---------------------------------------------------------------------------
# Track factory functions
# ---------------------------------------------------------------------------

def make_oval_track(
    semi_major: float = 1.0,
    semi_minor: float = 0.5,
    n_points: int = 500,
) -> Track:
    """Create a simple oval (ellipse) track."""
    t = np.linspace(0, 2 * math.pi, n_points, endpoint=False)
    x = semi_major * np.cos(t)
    y = semi_minor * np.sin(t)
    return Track(waypoints=np.column_stack([x, y]), closed=True)


def make_figure8_track(
    radius: float = 0.5,
    n_points: int = 600,
) -> Track:
    """Create a figure-8 track using a Lissajous curve."""
    t = np.linspace(0, 2 * math.pi, n_points, endpoint=False)
    x = radius * np.sin(t)
    y = radius * np.sin(2 * t) / 2
    return Track(waypoints=np.column_stack([x, y]), closed=True)


def make_s_curve_track(
    length: float = 2.0,
    amplitude: float = 0.4,
    n_points: int = 400,
) -> Track:
    """Create an S-shaped (sinusoidal) straight track."""
    x = np.linspace(0, length, n_points)
    y = amplitude * np.sin(2 * math.pi * x / length)
    return Track(waypoints=np.column_stack([x, y]), closed=False)


def make_custom_track(waypoints: Sequence[tuple[float, float]]) -> Track:
    """Build a track from a list of (x, y) waypoints."""
    pts = np.array(waypoints, dtype=float)
    return Track(waypoints=pts, closed=False)


# ---------------------------------------------------------------------------
# Track sampler – ties sensors to a track during simulation
# ---------------------------------------------------------------------------

class TrackSampler:
    """
    Helper that moves a ``SensorArray`` along a ``Track`` and produces
    readings that a controller can consume.

    Parameters
    ----------
    sensor_array : SensorArray
    track : Track
    """

    def __init__(self, sensor_array: SensorArray, track: Track) -> None:
        self.sensor_array = sensor_array
        self.track = track

    def sample(
        self, robot_x: float, robot_y: float, robot_heading: float
    ) -> dict:
        """
        Sample all sensors and return a result dict containing:
          readings         – list[SensorState]
          weighted_error   – float in [-1, 1]
          discrete_error   – int
          cross_track_error – float (metres)
          nearest_point    – np.ndarray(2,)
          track_tangent    – float (radians)
        """
        readings = self.sensor_array.read_all(
            robot_x, robot_y, robot_heading, self.track
        )
        nearest, tangent = self.track.nearest_point_and_tangent(robot_x, robot_y)
        return {
            "readings":           readings,
            "weighted_error":     self.sensor_array.weighted_error(readings),
            "discrete_error":     self.sensor_array.discrete_error(readings),
            "cross_track_error":  self.track.cross_track_error(robot_x, robot_y),
            "nearest_point":      nearest,
            "track_tangent":      tangent,
        }


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import pprint

    print("=== Sensor Simulation Self-Test ===\n")

    # Build a 3-sensor array
    array = SensorArray(n_sensors=3, spacing=0.02, noise_probability=0.0)
    print(f"Array: {array}\n")

    # Build an oval track
    track = make_oval_track(semi_major=1.0, semi_minor=0.5)
    print(f"Oval track length: {track.total_length:.3f} m")
    print(f"Is (0,0) on line? {track.is_on_line(0.0, 0.0)}")
    print(f"Is (1,0) on line? {track.is_on_line(1.0, 0.0)}\n")

    # Sample sensors with robot roughly on the line
    sampler = TrackSampler(array, track)
    pose = (1.0, 0.0, math.pi / 2)   # At right edge of oval, heading up
    result = sampler.sample(*pose)
    pprint.pprint({k: v for k, v in result.items() if k != "nearest_point"})

    # Try figure-8 track
    f8 = make_figure8_track(radius=0.5)
    print(f"\nFigure-8 track length: {f8.total_length:.3f} m")

    # Custom track
    pts = [(i * 0.1, math.sin(i * 0.3) * 0.2) for i in range(30)]
    custom = make_custom_track(pts)
    print(f"Custom track length: {custom.total_length:.3f} m")

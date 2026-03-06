"""
data_logger.py
==============
Data logging, CSV export, and analysis utilities for the Line Following Robot.

This module provides:
  - ``TelemetryLogger``   – in-memory log with time-stamped records.
  - ``CSVExporter``        – writes logs to CSV files.
  - ``LogAnalyser``        – statistical analysis of logged runs.
  - ``PerformanceReport``  – formats a human-readable or markdown report.
  - ``BatchBenchmark``     – runs multiple simulation variants and compares them.

Dependencies: numpy, csv (stdlib), pathlib (stdlib)
"""

from __future__ import annotations

import csv
import json
import math
import pathlib
import statistics
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RunStatus(Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"


# ---------------------------------------------------------------------------
# Telemetry record
# ---------------------------------------------------------------------------

@dataclass
class TelemetryRecord:
    """
    A single time-stamped snapshot of robot telemetry.

    All fields mirror the dict keys produced by
    ``LineFollowingRobot.step()`` in ``robot_simulation.py``.
    """
    t:              float = 0.0
    x:              float = 0.0
    y:              float = 0.0
    heading:        float = 0.0       # radians
    left_pwm:       int   = 0
    right_pwm:      int   = 0
    weighted_error: float = 0.0
    discrete_error: int   = 0
    cte:            float = 0.0       # cross-track error (metres)
    stopped:        bool  = False

    @classmethod
    def from_dict(cls, d: dict) -> "TelemetryRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# In-memory logger
# ---------------------------------------------------------------------------

class TelemetryLogger:
    """
    Append-only in-memory log of ``TelemetryRecord`` objects.

    Supports slicing, filtering, and iteration.

    Parameters
    ----------
    run_id : str
        Identifier for this logging session.
    max_records : int | None
        If set, older records are dropped when the limit is exceeded
        (circular buffer mode).
    """

    def __init__(
        self,
        run_id: str = "run_001",
        max_records: Optional[int] = None,
    ) -> None:
        self.run_id = run_id
        self.max_records = max_records
        self.status = RunStatus.PENDING
        self._records: List[TelemetryRecord] = []
        self._wall_start: Optional[float] = None
        self._wall_end:   Optional[float] = None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "TelemetryLogger":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.finish(success=(exc_type is None))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self.status = RunStatus.RUNNING
        self._wall_start = time.monotonic()

    def finish(self, success: bool = True) -> None:
        self._wall_end = time.monotonic()
        self.status = RunStatus.COMPLETED if success else RunStatus.FAILED

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def log(self, record: TelemetryRecord) -> None:
        """Append a record, enforcing max_records if configured."""
        self._records.append(record)
        if self.max_records and len(self._records) > self.max_records:
            self._records.pop(0)

    def log_dict(self, d: dict) -> None:
        """Convenience wrapper – convert a dict and append."""
        self.log(TelemetryRecord.from_dict(d))

    def log_many(self, records: Sequence[dict]) -> None:
        """Bulk-append a sequence of dicts."""
        for r in records:
            self.log_dict(r)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[TelemetryRecord]:
        return iter(self._records)

    def __getitem__(self, idx) -> TelemetryRecord:
        return self._records[idx]

    def as_arrays(self) -> Dict[str, np.ndarray]:
        """Return all fields as a dict of numpy arrays."""
        if not self._records:
            return {}
        keys = list(self._records[0].to_dict().keys())
        return {k: np.array([getattr(r, k) for r in self._records]) for k in keys}

    def filter(self, predicate) -> List[TelemetryRecord]:
        """Return records for which ``predicate(record)`` is True."""
        return [r for r in self._records if predicate(r)]

    @property
    def wall_duration(self) -> Optional[float]:
        if self._wall_start is None or self._wall_end is None:
            return None
        return self._wall_end - self._wall_start


# ---------------------------------------------------------------------------
# CSV export / import
# ---------------------------------------------------------------------------

class CSVExporter:
    """
    Export and import telemetry logs to/from CSV files.

    Parameters
    ----------
    directory : str | pathlib.Path
        Target directory for CSV files (created if it doesn't exist).
    """

    def __init__(self, directory: str = ".") -> None:
        self.directory = pathlib.Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        logger: TelemetryLogger,
        filename: Optional[str] = None,
    ) -> pathlib.Path:
        """
        Write the logger's records to a CSV file.

        Parameters
        ----------
        logger : TelemetryLogger
            Source log to export.
        filename : str | None
            File name.  Defaults to ``<run_id>_<timestamp>.csv``.

        Returns
        -------
        pathlib.Path
            Path to the written file.
        """
        if not logger:
            raise ValueError("Logger is empty – nothing to export.")

        ts = time.strftime("%Y%m%d_%H%M%S")
        fname = filename or f"{logger.run_id}_{ts}.csv"
        fpath = self.directory / fname

        fieldnames = list(TelemetryRecord.__dataclass_fields__.keys())
        with fpath.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for record in logger:
                writer.writerow(record.to_dict())

        return fpath

    @staticmethod
    def load(path: str) -> TelemetryLogger:
        """
        Load a CSV file back into a TelemetryLogger.

        Parameters
        ----------
        path : str
            Path to the CSV file.

        Returns
        -------
        TelemetryLogger
        """
        fpath = pathlib.Path(path)
        run_id = fpath.stem
        logger = TelemetryLogger(run_id=run_id)

        with fpath.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                d = {
                    "t":              float(row["t"]),
                    "x":              float(row["x"]),
                    "y":              float(row["y"]),
                    "heading":        float(row["heading"]),
                    "left_pwm":       int(row["left_pwm"]),
                    "right_pwm":      int(row["right_pwm"]),
                    "weighted_error": float(row["weighted_error"]),
                    "discrete_error": int(row["discrete_error"]),
                    "cte":            float(row["cte"]),
                    "stopped":        row["stopped"].lower() == "true",
                }
                logger.log_dict(d)

        logger.status = RunStatus.COMPLETED
        return logger


# ---------------------------------------------------------------------------
# Statistical analyser
# ---------------------------------------------------------------------------

class LogAnalyser:
    """
    Compute descriptive and control-quality statistics from a
    ``TelemetryLogger`` or a dict of arrays.

    Parameters
    ----------
    source : TelemetryLogger | dict
        Either a logger or the output of ``TelemetryLogger.as_arrays()``.
    """

    def __init__(self, source) -> None:
        if isinstance(source, TelemetryLogger):
            self._data = source.as_arrays()
        elif isinstance(source, dict):
            self._data = source
        else:
            raise TypeError("source must be TelemetryLogger or dict.")

    # ------------------------------------------------------------------
    # Basic stats
    # ------------------------------------------------------------------

    def describe(self, field: str) -> dict:
        """Return descriptive statistics for a named field."""
        arr = self._data[field].astype(float)
        return {
            "field":  field,
            "count":  len(arr),
            "mean":   float(np.mean(arr)),
            "std":    float(np.std(arr)),
            "min":    float(np.min(arr)),
            "p25":    float(np.percentile(arr, 25)),
            "median": float(np.median(arr)),
            "p75":    float(np.percentile(arr, 75)),
            "max":    float(np.max(arr)),
        }

    def describe_all(self) -> dict:
        """Describe every numeric field."""
        numeric_fields = [
            k for k, v in self._data.items()
            if v.dtype.kind in ("f", "i", "u")
        ]
        return {f: self.describe(f) for f in numeric_fields}

    # ------------------------------------------------------------------
    # Control quality metrics
    # ------------------------------------------------------------------

    def mean_absolute_cte(self) -> float:
        return float(np.mean(np.abs(self._data["cte"])))

    def rms_cte(self) -> float:
        return float(np.sqrt(np.mean(self._data["cte"] ** 2)))

    def max_cte(self) -> float:
        return float(np.max(np.abs(self._data["cte"])))

    def fraction_on_track(self, tolerance_m: float = 0.02) -> float:
        """
        Fraction of time steps where the robot was within ``tolerance_m``
        of the track centre.
        """
        on_track = np.abs(self._data["cte"]) <= tolerance_m
        return float(on_track.mean())

    def settling_time(self, threshold_m: float = 0.005) -> Optional[float]:
        """
        Estimate settling time: earliest time after which CTE stays
        within ±threshold_m continuously until the end.
        """
        cte = self._data["cte"]
        t   = self._data["t"]
        within = np.abs(cte) <= threshold_m
        # Find last time the robot was outside the threshold
        outside_indices = np.where(~within)[0]
        if len(outside_indices) == 0:
            return float(t[0])   # always within threshold
        last_outside = int(outside_indices[-1])
        if last_outside + 1 >= len(t):
            return None          # never settled
        return float(t[last_outside + 1])

    def oscillation_count(self, field: str = "cte") -> int:
        """Count the number of zero-crossings in a signal (oscillation proxy)."""
        arr = self._data[field].astype(float)
        signs = np.sign(arr)
        signs[signs == 0] = 1
        crossings = np.where(np.diff(signs))[0]
        return len(crossings)

    def average_speed_ratio(self) -> float:
        """
        Mean ratio of (left_pwm + right_pwm) / (2 * 255).
        Indicates average utilisation of motor capacity.
        """
        avg_pwm = (self._data["left_pwm"] + self._data["right_pwm"]) / 2.0
        return float(np.mean(avg_pwm / 255.0))

    def full_summary(self) -> dict:
        """Return all computed metrics in a single dict."""
        return {
            "mean_abs_cte_m":    self.mean_absolute_cte(),
            "rms_cte_m":         self.rms_cte(),
            "max_cte_m":         self.max_cte(),
            "fraction_on_track": self.fraction_on_track(),
            "settling_time_s":   self.settling_time(),
            "cte_oscillations":  self.oscillation_count("cte"),
            "avg_speed_ratio":   self.average_speed_ratio(),
        }


# ---------------------------------------------------------------------------
# Performance report
# ---------------------------------------------------------------------------

class PerformanceReport:
    """
    Formats a run summary as plain text or Markdown.

    Parameters
    ----------
    run_id : str
    track_type : str
    pid_preset : str
    analyser : LogAnalyser
    """

    def __init__(
        self,
        run_id: str,
        track_type: str,
        pid_preset: str,
        analyser: LogAnalyser,
    ) -> None:
        self.run_id    = run_id
        self.track     = track_type
        self.pid       = pid_preset
        self.analyser  = analyser

    def as_text(self) -> str:
        m = self.analyser.full_summary()
        lines = [
            f"Performance Report – {self.run_id}",
            f"  Track   : {self.track}",
            f"  PID     : {self.pid}",
            "-" * 40,
        ]
        for key, val in m.items():
            if val is None:
                lines.append(f"  {key:28s}: N/A")
            elif isinstance(val, float):
                lines.append(f"  {key:28s}: {val:.5f}")
            else:
                lines.append(f"  {key:28s}: {val}")
        return "\n".join(lines)

    def as_markdown(self) -> str:
        m = self.analyser.full_summary()
        rows = [
            "| Metric | Value |",
            "|--------|-------|",
        ]
        for key, val in m.items():
            if val is None:
                rows.append(f"| {key} | N/A |")
            elif isinstance(val, float):
                rows.append(f"| {key} | {val:.5f} |")
            else:
                rows.append(f"| {key} | {val} |")
        header = (
            f"## Performance Report: `{self.run_id}`\n"
            f"- **Track**: {self.track}\n"
            f"- **PID**  : {self.pid}\n\n"
        )
        return header + "\n".join(rows)

    def save(self, path: str, fmt: str = "text") -> None:
        """Write the report to a file (``fmt`` is ``"text"`` or ``"markdown"``)."""
        fpath = pathlib.Path(path)
        content = self.as_markdown() if fmt == "markdown" else self.as_text()
        fpath.write_text(content)
        print(f"Report saved to {fpath}")


# ---------------------------------------------------------------------------
# Batch benchmark
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    run_id:    str
    track:     str
    pid:       str
    metrics:   dict
    duration_s: float


class BatchBenchmark:
    """
    Run a matrix of (track × pid_preset) simulations and compare results.

    Parameters
    ----------
    tracks : list[str]
        Track type names.
    pid_presets : list[str]
        PID preset names.
    sim_duration : float
        Simulation duration for each run.
    dt : float
        Time step.
    """

    def __init__(
        self,
        tracks: Optional[List[str]] = None,
        pid_presets: Optional[List[str]] = None,
        sim_duration: float = 20.0,
        dt: float = 0.01,
    ) -> None:
        self.tracks      = tracks or ["oval", "scurve"]
        self.pid_presets = pid_presets or ["conservative", "balanced", "aggressive"]
        self.sim_duration = sim_duration
        self.dt          = dt
        self.results: List[BenchmarkResult] = []

    def run(self) -> List[BenchmarkResult]:
        """
        Execute all combinations, collect results.

        Returns
        -------
        list[BenchmarkResult]
        """
        # Import here to avoid circular import at module level
        from robot_simulation import Simulation

        total = len(self.tracks) * len(self.pid_presets)
        count = 0

        for track in self.tracks:
            for pid in self.pid_presets:
                count += 1
                run_id = f"{track}_{pid}"
                print(f"[{count}/{total}] Running: {run_id} …", end=" ", flush=True)

                t0 = time.monotonic()
                try:
                    sim = Simulation(
                        track_type=track,
                        duration=self.sim_duration,
                        dt=self.dt,
                        pid_preset=pid,
                    )
                    sim.run()
                    data = sim.robot.log_as_arrays()
                    analyser = LogAnalyser(data)
                    metrics = analyser.full_summary()
                    metrics["pid_iae"] = sim.robot.pid.iae
                    metrics["pid_ise"] = sim.robot.pid.ise
                    elapsed = time.monotonic() - t0
                    result = BenchmarkResult(
                        run_id=run_id, track=track, pid=pid,
                        metrics=metrics, duration_s=elapsed,
                    )
                    self.results.append(result)
                    print(f"done ({elapsed:.2f}s, mean_cte={metrics['mean_abs_cte_m']:.4f}m)")
                except Exception as exc:
                    elapsed = time.monotonic() - t0
                    print(f"FAILED: {exc}")

        return self.results

    def best_pid_for_track(self, track: str) -> Optional[str]:
        """Return the PID preset with lowest mean absolute CTE for a track."""
        candidates = [r for r in self.results if r.track == track]
        if not candidates:
            return None
        return min(candidates, key=lambda r: r.metrics["mean_abs_cte_m"]).pid

    def leaderboard(self) -> str:
        """Return a formatted leaderboard string."""
        if not self.results:
            return "(no results)"
        lines = [
            f"{'Run ID':25s}  {'Mean |CTE| (m)':>15}  {'Fraction on track':>18}  {'Wall time (s)':>13}",
            "-" * 75,
        ]
        sorted_results = sorted(
            self.results, key=lambda r: r.metrics["mean_abs_cte_m"]
        )
        for r in sorted_results:
            m = r.metrics
            lines.append(
                f"{r.run_id:25s}  {m['mean_abs_cte_m']:>15.5f}  "
                f"{m['fraction_on_track']:>18.3f}  {r.duration_s:>13.2f}"
            )
        return "\n".join(lines)

    def export_json(self, path: str) -> None:
        """Export all results to a JSON file."""
        data = [
            {
                "run_id":     r.run_id,
                "track":      r.track,
                "pid":        r.pid,
                "metrics":    r.metrics,
                "duration_s": r.duration_s,
            }
            for r in self.results
        ]
        pathlib.Path(path).write_text(json.dumps(data, indent=2))
        print(f"Results exported to {path}")


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Data Logger Self-Test ===\n")

    # Build a synthetic log
    logger = TelemetryLogger(run_id="test_run")
    logger.start()

    rng = np.random.default_rng(0)
    t = 0.0
    cte = 0.0
    for _ in range(500):
        cte = cte * 0.95 + rng.normal(0, 0.005)
        r = TelemetryRecord(
            t=t, x=t * 0.05, y=cte,
            heading=0.0,
            left_pwm=150, right_pwm=150,
            weighted_error=cte / 0.02,
            discrete_error=0,
            cte=cte,
            stopped=False,
        )
        logger.log(r)
        t += 0.01

    logger.finish()

    analyser = LogAnalyser(logger)
    report = PerformanceReport(
        run_id="test_run",
        track_type="oval",
        pid_preset="balanced",
        analyser=analyser,
    )
    print(report.as_text())

    # CSV round-trip
    exporter = CSVExporter(directory="/tmp")
    path = exporter.export(logger, filename="test_run.csv")
    print(f"\nExported to: {path}")
    loaded = CSVExporter.load(str(path))
    print(f"Loaded {len(loaded)} records back from CSV.")

    # Benchmark (small, fast)
    bench = BatchBenchmark(
        tracks=["oval"],
        pid_presets=["balanced", "conservative"],
        sim_duration=5.0,
        dt=0.02,
    )
    bench.run()
    print("\n" + bench.leaderboard())

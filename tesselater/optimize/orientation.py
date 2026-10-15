"""Discrete orientation search minimizing support cost + stability penalty."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv

from tesselater.analysis.toppling import analyze_toppling
from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.mesh_io import center_on_bed, place_on_bed
from tesselater.results import AnalysisResult, MeshActor
from tesselater.support.optimize import recommend_supports


@dataclass(frozen=True)
class OrientationPose:
    rx_deg: float
    ry_deg: float
    rz_deg: float

    def label(self) -> str:
        return f"rx={self.rx_deg:g}, ry={self.ry_deg:g}, rz={self.rz_deg:g}"


@dataclass
class OrientationTrial:
    pose: OrientationPose
    mesh: pv.PolyData
    support_cost: float
    support_kind: str
    support_volume_mm3: float
    tips: int
    toppling_ok: bool
    toppling_verdict: str
    fits_bed: bool
    total_cost: float


@dataclass
class OrientationResult:
    trials: list[OrientationTrial]
    best: OrientationTrial | None

    def to_analysis_result(self) -> AnalysisResult:
        if self.best is None:
            return AnalysisResult(
                name="orientation",
                verdict="No feasible orientation",
                message="No poses fit the bed.",
            )
        rows = []
        for t in self.trials[:12]:
            mark = "← best" if t is self.best else ""
            rows.append(
                f"{t.pose.label():28s}  J={t.total_cost:8.3f}  "
                f"sup={t.support_kind:14s} tips={t.tips:3d}  "
                f"topple={'OK' if t.toppling_ok else 'NO'} {mark}"
            )
        if len(self.trials) > 12:
            rows.append(f"… ({len(self.trials) - 12} more poses)")
        return AnalysisResult(
            name="orientation",
            verdict=f"Best pose {self.best.pose.label()} (J={self.best.total_cost:.3f})",
            metrics={
                "rx_deg": self.best.pose.rx_deg,
                "ry_deg": self.best.pose.ry_deg,
                "rz_deg": self.best.pose.rz_deg,
                "total_cost": self.best.total_cost,
                "support_kind": self.best.support_kind,
                "support_cost": self.best.support_cost,
                "tips": self.best.tips,
                "toppling_ok": self.best.toppling_ok,
                "n_trials": len(self.trials),
            },
            actors=[
                MeshActor(self.best.mesh, color="steelblue", opacity=0.85, label="best pose"),
            ],
            message="\n".join(rows),
        )


def _angle_grid(step: float) -> list[float]:
    step = max(float(step), 15.0)
    vals = list(np.arange(0.0, 360.0, step))
    # Always include 0
    if 0.0 not in vals:
        vals.insert(0, 0.0)
    return vals


def _apply_pose(mesh: pv.PolyData, pose: OrientationPose) -> pv.PolyData:
    m = mesh.copy(deep=True)
    if pose.rx_deg:
        m.rotate_x(pose.rx_deg, inplace=True)
    if pose.ry_deg:
        m.rotate_y(pose.ry_deg, inplace=True)
    if pose.rz_deg:
        m.rotate_z(pose.rz_deg, inplace=True)
    return place_on_bed(m, inplace=True)


def _fits_bed(mesh: pv.PolyData, config: AppConfig) -> bool:
    xmin, xmax, ymin, ymax, _, _ = mesh.bounds
    return (
        (xmax - xmin) <= config.printer.bed_width + 1e-6
        and (ymax - ymin) <= config.printer.bed_length + 1e-6
    )


def _toppling_ok(verdict: str) -> bool:
    v = verdict.lower()
    if "very likely" in v or "unstable" in v or "outside footprint" in v:
        return False
    if "no toppling" in v or "geometrically stable" in v:
        return True
    if "stable" in v:
        return True
    return "borderline" not in v



def search_orientations(
    mesh: pv.PolyData,
    config: AppConfig = DEFAULT_CONFIG,
) -> OrientationResult:
    """
    Brute-force yaw/pitch grid (optional Z spins).

    Score per pose:
        J = support_cost + unstable_penalty·[topple bad] + 0.05·tips
    """
    step = config.orientation.angle_step_deg
    rx_vals = _angle_grid(step)
    ry_vals = _angle_grid(step)
    rz_vals = _angle_grid(step) if config.orientation.include_z_spins else [0.0]

    # Cap explosion: if too many, thin the grid
    poses: list[OrientationPose] = []
    for rx in rx_vals:
        for ry in ry_vals:
            for rz in rz_vals:
                poses.append(OrientationPose(rx, ry, rz))
    max_n = config.orientation.max_candidates
    if len(poses) > max_n:
        # Keep identity + evenly subsampled poses
        idx = np.linspace(0, len(poses) - 1, max_n, dtype=int)
        poses = [poses[i] for i in sorted(set(idx))]

    base = mesh.copy(deep=True)
    trials: list[OrientationTrial] = []
    penalty = config.orientation.unstable_penalty

    for pose in poses:
        oriented = _apply_pose(base, pose)
        oriented = center_on_bed(
            oriented, config.printer.bed_width, config.printer.bed_length, inplace=True
        )
        fits = _fits_bed(oriented, config)
        if not fits:
            trials.append(
                OrientationTrial(
                    pose=pose,
                    mesh=oriented,
                    support_cost=float("inf"),
                    support_kind="—",
                    support_volume_mm3=0.0,
                    tips=0,
                    toppling_ok=False,
                    toppling_verdict="does not fit bed",
                    fits_bed=False,
                    total_cost=float("inf"),
                )
            )
            continue

        rec = recommend_supports(oriented, config)
        topple = analyze_toppling(oriented, config)
        ok = _toppling_ok(topple.verdict)
        if rec.best is None:
            scost, skind, svol, tips = 0.0, "none", 0.0, 0
        else:
            scost = rec.best.costs.cost
            skind = rec.best.candidate.kind
            svol = rec.best.costs.volume_mm3
            tips = rec.tip_map.count

        total = scost + (0.0 if ok else penalty) + 0.05 * tips
        trials.append(
            OrientationTrial(
                pose=pose,
                mesh=oriented,
                support_cost=scost,
                support_kind=skind,
                support_volume_mm3=svol,
                tips=tips,
                toppling_ok=ok,
                toppling_verdict=topple.verdict,
                fits_bed=True,
                total_cost=float(total),
            )
        )

    trials.sort(key=lambda t: t.total_cost)
    feasible = [t for t in trials if t.fits_bed and np.isfinite(t.total_cost)]
    best = feasible[0] if feasible else None
    return OrientationResult(trials=trials, best=best)

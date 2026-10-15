"""Export support candidates as printable solid meshes (STL)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyvista as pv

from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.support.candidates import SupportCandidate, SupportColumn


def _column_solid(col: SupportColumn, config: AppConfig, resolution: int = 16) -> pv.PolyData:
    """Cylinder shaft; point tips add a short cone under the part."""
    h = col.height
    if h <= 1e-6:
        return pv.PolyData()

    tip_len = 0.0
    shaft_h = h
    if col.tip_style == "point":
        tip_len = min(max(2.0 * col.radius, 0.8), 0.35 * h)
        shaft_h = max(h - tip_len, 1e-3)

    center_z = col.base_z + shaft_h / 2.0
    shaft = pv.Cylinder(
        center=(col.tip[0], col.tip[1], center_z),
        direction=(0, 0, 1),
        radius=col.radius,
        height=shaft_h,
        resolution=resolution,
        capping=True,
    ).triangulate()

    if tip_len <= 0:
        return shaft

    # Cone pointing up toward the part (apex at tip)
    cone = pv.Cone(
        center=(col.tip[0], col.tip[1], col.tip[2] - tip_len / 2.0),
        direction=(0, 0, 1),
        height=tip_len,
        radius=col.radius,
        resolution=resolution,
        capping=True,
    ).triangulate()
    return shaft.merge(cone)


def candidate_to_solid(
    candidate: SupportCandidate,
    config: AppConfig = DEFAULT_CONFIG,
    resolution: int = 16,
) -> pv.PolyData:
    """Boolean-ish merge of all column solids (watertight-enough for preview/print)."""
    solids: list[pv.PolyData] = []
    for col in candidate.columns:
        piece = _column_solid(col, config, resolution=resolution)
        if piece.n_points:
            solids.append(piece)
    if not solids:
        return pv.PolyData()
    merged = solids[0]
    for s in solids[1:]:
        merged = merged.merge(s)
    return merged


def export_supports_stl(
    candidate: SupportCandidate,
    path: str | Path,
    config: AppConfig = DEFAULT_CONFIG,
    *,
    resolution: int = 16,
) -> Path:
    """Write support solids to an STL file. Returns the path written."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    solid = candidate_to_solid(candidate, config, resolution=resolution)
    if solid.n_points == 0:
        # Write an empty placeholder mesh so pipelines don't crash
        solid = pv.Sphere(radius=0.01, center=(0, 0, 0))
    solid.save(str(out))
    return out


def export_oriented_part_stl(mesh: pv.PolyData, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.save(str(out))
    return out

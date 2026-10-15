"""First-layer warping visualization and tendency estimate."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv

from tesselater.config import AppConfig, DEFAULT_CONFIG, speed_limits
from tesselater.geometry import first_layer_footprint, mesh_height


@dataclass(frozen=True)
class WarpingResult:
    warping_tendency: float
    layer_height_ok: bool
    line_width_ok: bool
    recommended_line_width: float | None
    base: pv.PolyData
    warped_base: pv.PolyData
    message: str


def _extract_base(mesh: pv.PolyData, layer_height: float) -> pv.PolyData:
    """Clip a thin slab at the bottom of the mesh as the first-layer proxy."""
    z_min = float(mesh.bounds[4])
    # Keep points from z_min up through one layer (+ small epsilon).
    origin_z = z_min + max(layer_height, 0.05)
    base = mesh.clip(normal=[0, 0, 1], origin=[0, 0, origin_z], invert=True)
    if base.n_points == 0:
        # Fallback: use footprint vertices extruded as a point cloud polydata
        fp = first_layer_footprint(mesh, layer_height)
        if len(fp.hull_xy) == 0:
            return mesh.copy()
        pts = np.column_stack([fp.hull_xy, np.full(len(fp.hull_xy), z_min)])
        return pv.PolyData(pts)
    return base


def warping_tendency(config: AppConfig = DEFAULT_CONFIG) -> float:
    """Empirical |speed-driven width error| scaled by shrinkage fraction."""
    printer = config.printer
    line_width, ideal, _max_speed, quality_speed = speed_limits(printer)
    shrink = max(config.material.shrinkage_fraction, 1e-9)
    raw = abs(
        (printer.speed * printer.layer_height / max(line_width, 1e-9))
        - (quality_speed * printer.layer_height / max(ideal, 1e-9))
    )
    return float(raw / (shrink * 100.0))


def warped_first_layer_mesh(
    mesh: pv.PolyData,
    config: AppConfig = DEFAULT_CONFIG,
) -> tuple[pv.PolyData, pv.PolyData, float]:
    """
    Build a visually exaggerated warped first-layer mesh.

    Points are pulled toward a point above the base centroid with a factor
    that grows with distance from the centroid and with warping_tendency.
    """
    printer = config.printer
    material = config.material
    tendency = warping_tendency(config)
    base = _extract_base(mesh, printer.layer_height)
    if base.n_points == 0:
        return base, base, tendency

    height = mesh_height(mesh)
    scaled = base.copy()
    shrink = material.shrinkage_fraction
    scaled.points *= 1.0 - shrink

    centroid = np.mean(np.asarray(base.points), axis=0)
    above = centroid + np.array([0.0, 0.0, height * 0.2])
    directions = above - scaled.points
    distances = np.linalg.norm(scaled.points - centroid, axis=1)
    max_d = float(distances.max()) if len(distances) else 1.0
    normalized = distances / max(max_d, 1e-12)
    percent = shrink * 2.0
    factor = percent + (tendency / 1000.0) ** 1.1
    scaled.points = scaled.points + directions * normalized[:, None] * factor

    bed_ok = (
        material.recommended_bed_temp_range[0]
        <= printer.bed_temp
        <= material.recommended_bed_temp_range[1]
    )
    hot_ok = (
        material.recommended_hotend_temp_range[0]
        <= printer.hotend_temp
        <= material.recommended_hotend_temp_range[1]
    )
    if not (bed_ok and hot_ok):
        scaled.points = scaled.points + directions * normalized[:, None] * factor * 2.0

    return base, scaled, tendency


def analyze_warping(mesh: pv.PolyData, config: AppConfig = DEFAULT_CONFIG) -> WarpingResult:
    printer = config.printer
    line_width, ideal, _, _ = speed_limits(printer)
    minimum = printer.layer_height + printer.nozzle_size
    maximum = printer.layer_height + printer.nozzle_flat
    line_ok = minimum <= line_width <= maximum
    layer_ok = printer.layer_height <= printer.nozzle_size * 0.7

    base, warped, tendency = warped_first_layer_mesh(mesh, config)

    messages = []
    if not layer_ok:
        messages.append("Layer height is too high relative to nozzle size; lower it.")
    if not line_ok:
        messages.append(f"Recommended line width ≈ {ideal:.3f} mm.")
    if not messages:
        messages.append(f"Warping tendency index ≈ {tendency:.4f} (empirical).")

    return WarpingResult(
        warping_tendency=tendency,
        layer_height_ok=layer_ok,
        line_width_ok=line_ok,
        recommended_line_width=None if line_ok else ideal,
        base=base,
        warped_base=warped,
        message=" ".join(messages),
    )

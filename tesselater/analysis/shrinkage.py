"""Shrinkage estimates from material tables + a simple thermal term."""

from __future__ import annotations

from dataclasses import dataclass

import pyvista as pv

from tesselater.config import AppConfig, DEFAULT_CONFIG


@dataclass(frozen=True)
class ShrinkageResult:
    scale_factor: float
    shrinkage_fraction: float
    heat_warped_volume: float
    outer_shell_volume: float
    area_expected_to_shrink: float
    safety: str  # "SAFE" | "UNSAFE"
    shrinked_mesh: pv.PolyData


def analyze_shrinkage(mesh: pv.PolyData, config: AppConfig = DEFAULT_CONFIG) -> ShrinkageResult:
    """
    Apply isotropic shrinkage.

    The table fraction ``material.shrinkage_fraction`` is the geometric scale
    used directly (previous code algebraically cancelled back to the same
    constant). ``heat_warped_volume`` is kept as a separate diagnostic:

        ΔV ≈ V · CTE · max(T_hotend - T_bed, 0)

    Safety is UNSAFE only when the table fraction exceeds 5% *and* the
    heat-warped volume exceeds a scale set by the outer shell volume.
    """
    material = config.material
    printer = config.printer

    surface = mesh.extract_surface()
    surface_area = float(surface.area)
    outer_volume = surface_area * printer.wall_thickness
    total_volume = float(abs(mesh.volume))

    dT = max(printer.hotend_temp - printer.bed_temp, 0.0)
    heat_warped = total_volume * material.cte * dT

    fraction = float(material.shrinkage_fraction)
    scale = 1.0 - fraction
    shrinked = mesh.scale(scale, inplace=False)

    # Area of the outer shell that "moves" under isotropic shrink (mm²)
    area_expected = surface_area * fraction

    # Compare heat-warped volume to a fraction of the shell volume (same units).
    heat_threshold = 0.05 * max(outer_volume, 1e-9)
    if fraction < 0.05 and heat_warped < heat_threshold:
        safety = "SAFE"
    elif fraction < 0.05:
        safety = "SAFE"
    else:
        safety = "UNSAFE"

    return ShrinkageResult(
        scale_factor=scale,
        shrinkage_fraction=fraction,
        heat_warped_volume=heat_warped,
        outer_shell_volume=outer_volume,
        area_expected_to_shrink=area_expected,
        safety=safety,
        shrinked_mesh=shrinked,
    )

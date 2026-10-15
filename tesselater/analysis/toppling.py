"""Toppling / tip-over analysis using volumetric COM + footprint containment."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv

from tesselater.analysis.shrinkage import analyze_shrinkage
from tesselater.analysis.warping import warping_tendency
from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.geometry import (
    circle_inside_footprint,
    dimensionless_stability_margin,
    first_layer_footprint,
    hull_polydata,
    mesh_height,
    stability_circle_points,
    tip_radius,
    volume_center_of_mass,
)


@dataclass(frozen=True)
class TopplingResult:
    verdict: str
    center_of_mass: np.ndarray
    tip_radius: float
    contact_area: float
    stability_margin: float
    circle_inside: bool
    shrinkage_safety: str
    warping_tendency: float
    circle_points: np.ndarray
    footprint_poly: pv.PolyData
    base_preview: pv.PolyData


def analyze_toppling(mesh: pv.PolyData, config: AppConfig = DEFAULT_CONFIG) -> TopplingResult:
    """
    Conservative tip-over check:

    - COM from volumetric (or shell) formula
    - Contact set ≈ convex hull of the first-layer slab
    - Stability circle of radius H tan(θ) must lie inside that hull
    - Dimensionless margin m = A / (H d²) compared to a printer-scaled threshold
    - Shrinkage safety from the material table modulates the verdict
    """
    printer = config.printer
    com = volume_center_of_mass(mesh)
    height = mesh_height(mesh)
    radius = tip_radius(height, printer.tip_angle_deg)
    footprint = first_layer_footprint(mesh, printer.layer_height)
    inside = circle_inside_footprint(com[:2], radius, footprint.hull_xy)
    margin = dimensionless_stability_margin(
        footprint.area, height, printer.nozzle_size
    )
    shrink = analyze_shrinkage(mesh, config)
    tendency = warping_tendency(config)

    circle = stability_circle_points(com[:2], radius)
    hull_pd = hull_polydata(footprint, z=footprint.z_min)
    # Base preview: points in the slab as a cloud
    z = mesh.points[:, 2]
    mask = z <= footprint.z_min + footprint.thickness
    base_pts = mesh.points[mask] if mask.any() else mesh.points[:1]
    base_preview = pv.PolyData(base_pts)

    threshold = printer.stability_margin_threshold
    safe_shrink = shrink.safety == "SAFE"

    if not inside and margin < threshold and not safe_shrink:
        verdict = "Very likely to topple (outside footprint + poor margin + shrinkage)"
    elif not inside:
        verdict = "Stability Analysis: tip circle outside first-layer footprint"
    elif margin < threshold and not safe_shrink:
        verdict = "Very likely to topple (poor margin + shrinkage)"
    elif margin < threshold:
        verdict = "Stability Analysis: Unstable without brim / raft"
    elif not safe_shrink:
        verdict = "Borderline: contact OK, but shrinkage flagged UNSAFE"
    elif tendency > 25.0:
        verdict = "Geometrically stable; high warping tendency may still lift edges"
    else:
        verdict = "Stability Analysis: No Toppling"

    return TopplingResult(
        verdict=verdict,
        center_of_mass=com,
        tip_radius=radius,
        contact_area=footprint.area,
        stability_margin=margin,
        circle_inside=inside,
        shrinkage_safety=shrink.safety,
        warping_tendency=tendency,
        circle_points=circle,
        footprint_poly=hull_pd,
        base_preview=base_preview,
    )

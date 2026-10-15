"""Analysis actions: compute → AnalysisResult (UI only renders)."""

from __future__ import annotations

import numpy as np
import pyvista as pv

from tesselater.analysis.overhangs import find_overhang_cells
from tesselater.analysis.roughness import compute_surface_roughness
from tesselater.analysis.shrinkage import analyze_shrinkage
from tesselater.analysis.small_details import find_thin_cells
from tesselater.analysis.toppling import analyze_toppling
from tesselater.analysis.warping import analyze_warping
from tesselater.config import AppConfig
from tesselater.geometry import volume_center_of_mass
from tesselater.results import AnalysisResult, MeshActor
from tesselater.optimize.orientation import search_orientations
from tesselater.support.optimize import recommend_supports



def action_warping(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    result = analyze_warping(mesh, config)
    return AnalysisResult(
        name="warping",
        verdict=result.message,
        metrics={"warping_tendency": result.warping_tendency},
        message=result.message,
        secondary_title="First-layer warping",
        secondary_actors=[
            MeshActor(result.warped_base, color="red", opacity=0.55, label="Warped base"),
            MeshActor(mesh, color="blue", opacity=0.35, label="Original"),
        ],
    )


def action_small_details(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    result = find_thin_cells(mesh, config)
    actors = []
    if result.count:
        actors.append(MeshActor(result.thin_cells, color="red", label="thin"))
    return AnalysisResult(
        name="small_details",
        verdict=f"{result.count} thin cells",
        metrics={"count": result.count, "minimal_area": result.minimal_area},
        actors=actors,
        message=f"{result.count} thin cells (area < {result.minimal_area:.5f} mm²)",
    )


def action_toppling(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    warp = analyze_warping(mesh, config)
    result = analyze_toppling(mesh, config)
    actors = [
        MeshActor(result.base_preview, color="red", opacity=0.7, label="base"),
        MeshActor(
            pv.PolyData(result.circle_points),
            color="green",
            style="points",
            point_size=8.0,
            label="tip circle",
        ),
        MeshActor(
            pv.PolyData(result.center_of_mass.reshape(1, -1)),
            color="yellow",
            style="points",
            point_size=14.0,
            label="COM",
        ),
    ]
    if result.footprint_poly.n_points:
        actors.insert(
            1,
            MeshActor(
                result.footprint_poly,
                color="orange",
                style="wireframe",
                line_width=3.0,
                label="footprint",
            ),
        )
    detail = (
        f"{result.verdict}\n"
        f"margin m={result.stability_margin:.2f}, "
        f"A={result.contact_area:.1f} mm², "
        f"r={result.tip_radius:.2f} mm, "
        f"shrink={result.shrinkage_safety}"
    )
    return AnalysisResult(
        name="toppling",
        verdict=result.verdict,
        metrics={
            "stability_margin": result.stability_margin,
            "contact_area": result.contact_area,
            "circle_inside": result.circle_inside,
            "warping_tendency": result.warping_tendency,
        },
        actors=actors,
        message=detail,
        secondary_title="Warping (before toppling)",
        secondary_actors=[
            MeshActor(warp.warped_base, color="red", opacity=0.55),
            MeshActor(mesh, color="blue", opacity=0.35),
        ],
    )


def action_roughness(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    colored = compute_surface_roughness(mesh)
    rough_count = int(np.sum(colored.cell_data["RoughMask"]))
    return AnalysisResult(
        name="roughness",
        verdict=f"{rough_count} rough faces",
        metrics={"rough_faces": rough_count, "n_cells": colored.n_cells},
        actors=[
            MeshActor(
                colored,
                opacity=1.0,
                rgb_scalars="SurfaceRoughness",
                label="roughness",
            )
        ],
        message=f"Rough faces: {rough_count} / {colored.n_cells}",
    )


def action_shrinkage(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    result = analyze_shrinkage(mesh, config)
    msg = (
        f"Isotropic scale {result.scale_factor:.5f} "
        f"({result.shrinkage_fraction * 100:.2f}% table shrinkage)\n"
        f"Area expected to move: {result.area_expected_to_shrink:.2f} mm²\n"
        f"Heat-warped volume diagnostic: {result.heat_warped_volume:.4g} mm³\n"
        f"Safety: {result.safety}\n\n"
        "Green = original, red = shrunk."
    )
    return AnalysisResult(
        name="shrinkage",
        verdict=result.safety,
        metrics={
            "scale": result.scale_factor,
            "fraction": result.shrinkage_fraction,
            "safety": result.safety,
        },
        actors=[
            MeshActor(mesh, color="green", opacity=0.3, label="original"),
            MeshActor(result.shrinked_mesh, color="red", label="shrunk"),
        ],
        message=msg,
    )


def action_overhangs(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    overhangs = find_overhang_cells(mesh, config)
    limit = 180.0 - config.printer.overhang_angle_deg
    actors = []
    if overhangs.n_cells:
        actors.append(MeshActor(overhangs, color="red", label="overhangs"))
    return AnalysisResult(
        name="overhangs",
        verdict=f"{overhangs.n_cells} faces",
        metrics={"n_cells": overhangs.n_cells},
        actors=actors,
        message=(
            f"Overhang faces (normal >{limit:.0f}° from +Z, "
            f"{config.printer.overhang_angle_deg:.0f}° rule): {overhangs.n_cells}"
        ),
    )


def action_center_of_mass(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    com = volume_center_of_mass(mesh)
    return AnalysisResult(
        name="com",
        verdict="ok",
        metrics={"xyz": com.tolist()},
        actors=[
            MeshActor(
                pv.PolyData(com.reshape(1, -1)),
                color="red",
                style="points",
                point_size=16.0,
                label="COM",
            )
        ],
        message=f"COM ≈ ({com[0]:.2f}, {com[1]:.2f}, {com[2]:.2f}) mm",
    )


def action_supports(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    return recommend_supports(mesh, config).to_analysis_result()


def action_orientation(mesh: pv.PolyData, config: AppConfig) -> AnalysisResult:
    return search_orientations(mesh, config).to_analysis_result()

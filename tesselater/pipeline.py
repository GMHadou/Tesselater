"""Batch printability pipeline (headless-friendly)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pyvista as pv

from tesselater.analysis.overhangs import find_overhang_cells
from tesselater.analysis.roughness import compute_surface_roughness
from tesselater.analysis.shrinkage import analyze_shrinkage
from tesselater.analysis.small_details import find_thin_cells
from tesselater.analysis.toppling import analyze_toppling
from tesselater.analysis.warping import analyze_warping
from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.geometry import volume_center_of_mass
from tesselater.results import AnalysisResult
from tesselater.support.optimize import recommend_supports


@dataclass
class PrintabilityReport:
    results: dict[str, AnalysisResult] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    def verdicts(self) -> dict[str, str]:
        return {k: v.verdict for k, v in self.results.items()}


def run_pipeline(mesh: pv.PolyData, config: AppConfig = DEFAULT_CONFIG) -> PrintabilityReport:
    """Run core heuristics + support recommendation once."""
    warp = analyze_warping(mesh, config)
    topple = analyze_toppling(mesh, config)
    shrink = analyze_shrinkage(mesh, config)
    thin = find_thin_cells(mesh, config)
    overhangs = find_overhang_cells(mesh, config)
    rough = compute_surface_roughness(mesh)
    supports = recommend_supports(mesh, config).to_analysis_result()
    com = volume_center_of_mass(mesh)

    results = {
        "warping": AnalysisResult(
            name="warping",
            verdict=warp.message,
            metrics={"warping_tendency": warp.warping_tendency},
            message=warp.message,
        ),
        "toppling": AnalysisResult(
            name="toppling",
            verdict=topple.verdict,
            metrics={
                "stability_margin": topple.stability_margin,
                "contact_area": topple.contact_area,
                "circle_inside": topple.circle_inside,
            },
        ),
        "shrinkage": AnalysisResult(
            name="shrinkage",
            verdict=shrink.safety,
            metrics={
                "fraction": shrink.shrinkage_fraction,
                "scale": shrink.scale_factor,
            },
        ),
        "small_details": AnalysisResult(
            name="small_details",
            verdict=f"{thin.count} thin cells",
            metrics={"count": thin.count, "minimal_area": thin.minimal_area},
        ),
        "overhangs": AnalysisResult(
            name="overhangs",
            verdict=f"{overhangs.n_cells} faces",
            metrics={"n_cells": overhangs.n_cells},
        ),
        "roughness": AnalysisResult(
            name="roughness",
            verdict=f"{int(rough.cell_data['RoughMask'].sum())} rough faces",
            metrics={"rough_faces": int(rough.cell_data["RoughMask"].sum())},
        ),
        "supports": supports,
        "com": AnalysisResult(
            name="com",
            verdict="ok",
            metrics={"xyz": com.tolist()},
        ),
    }
    summary = {
        "warping_tendency": warp.warping_tendency,
        "toppling": topple.verdict,
        "shrinkage": shrink.safety,
        "thin_cells": thin.count,
        "overhang_faces": overhangs.n_cells,
        "best_support": supports.metrics.get("best_kind", "none"),
        "support_cost": supports.metrics.get("cost"),
        "support_volume_mm3": supports.metrics.get("volume_mm3"),
    }
    return PrintabilityReport(results=results, summary=summary)

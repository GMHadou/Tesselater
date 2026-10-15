"""Printability analysis routines (pure functions; no import-time plotting)."""

from tesselater.analysis.overhangs import find_overhang_cells
from tesselater.analysis.roughness import compute_surface_roughness
from tesselater.analysis.shrinkage import analyze_shrinkage
from tesselater.analysis.small_details import find_thin_cells
from tesselater.analysis.toppling import analyze_toppling
from tesselater.analysis.warping import analyze_warping, warped_first_layer_mesh

__all__ = [
    "analyze_shrinkage",
    "analyze_toppling",
    "analyze_warping",
    "compute_surface_roughness",
    "find_overhang_cells",
    "find_thin_cells",
    "warped_first_layer_mesh",
]

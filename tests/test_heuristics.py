"""Heuristic analyzers (warping, shrinkage, overhangs)."""

from __future__ import annotations

import pyvista as pv

from tesselater.analysis.overhangs import find_overhang_cells
from tesselater.analysis.shrinkage import analyze_shrinkage
from tesselater.analysis.warping import analyze_warping, warping_tendency
from tesselater.config import DEFAULT_CONFIG
from tesselater.mesh_io import center_on_bed, place_on_bed


def test_warping_tendency_positive():
    assert warping_tendency(DEFAULT_CONFIG) >= 0


def test_shrinkage_scale_matches_table():
    cube = center_on_bed(pv.Cube().triangulate(), 220, 220)
    result = analyze_shrinkage(cube, DEFAULT_CONFIG)
    expected = 1.0 - DEFAULT_CONFIG.material.shrinkage_fraction
    assert abs(result.scale_factor - expected) < 1e-12
    assert result.safety in {"SAFE", "UNSAFE"}


def test_overhang_ceiling_detected():
    # Downward-facing square above the bed
    ceiling = pv.Plane(center=(0, 0, 10), direction=(0, 0, -1), i_size=20, j_size=20)
    ceiling = ceiling.triangulate()
    ceiling = place_on_bed(ceiling)
    # After place_on_bed, plane sits at z=0 with normals possibly flipped — use explicit box shelf
    stem = pv.Cube(center=(0, 0, 5), x_length=2, y_length=2, z_length=10).triangulate()
    plate = pv.Cube(center=(0, 0, 11), x_length=20, y_length=20, z_length=2).triangulate()
    mesh = center_on_bed(stem.merge(plate), 220, 220)
    cells = find_overhang_cells(mesh, DEFAULT_CONFIG)
    assert cells.n_cells > 0


def test_analyze_warping_returns_meshes():
    mesh = center_on_bed(pv.Cube(x_length=10, y_length=10, z_length=10).triangulate(), 220, 220)
    result = analyze_warping(mesh, DEFAULT_CONFIG)
    assert result.warped_base.n_points >= 0
    assert isinstance(result.message, str)

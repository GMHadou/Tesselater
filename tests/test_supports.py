"""Support tip clustering, candidates, and scoring."""

from __future__ import annotations

import numpy as np
import pyvista as pv
import pytest

from tesselater.config import DEFAULT_CONFIG
from tesselater.mesh_io import center_on_bed, place_on_bed
from tesselater.pipeline import run_pipeline
from tesselater.support.candidates import generate_candidates
from tesselater.support.optimize import recommend_supports
from tesselater.support.score import score_candidate
from tesselater.support.tips import build_tip_map, cluster_tips_xy


def _table_with_overhang() -> pv.PolyData:
    """
    Horizontal top slab held by a thin stem — classic overhang needing support.

    Stem: 4×4×20 at origin; top plate: 30×30×2 sitting on the stem.
    """
    stem = pv.Cube(center=(0, 0, 10), x_length=4, y_length=4, z_length=20).triangulate()
    plate = pv.Cube(center=(0, 0, 21), x_length=30, y_length=30, z_length=2).triangulate()
    mesh = stem.merge(plate)
    return place_on_bed(mesh)


def test_cluster_tips_bins_points():
    centers = np.array(
        [
            [0.0, 0.0, 5.0],
            [0.5, 0.2, 5.0],
            [10.0, 10.0, 8.0],
        ]
    )
    areas = np.array([1.0, 1.0, 2.0])
    tips = cluster_tips_xy(centers, areas, pitch=3.0)
    assert len(tips) == 2


def test_overhang_mesh_produces_tips_and_candidates():
    mesh = center_on_bed(_table_with_overhang(), 220, 220)
    tip_map = build_tip_map(mesh, DEFAULT_CONFIG)
    assert tip_map.count >= 1
    assert tip_map.total_overhang_area > 0
    cands = generate_candidates(tip_map, DEFAULT_CONFIG)
    kinds = {c.kind for c in cands}
    assert {"dense_pillars", "sparse_pillars", "tree"} <= kinds
    for c in cands:
        costs = score_candidate(c, tip_map.count, DEFAULT_CONFIG)
        assert costs.feasible
        assert costs.volume_mm3 >= 0
        assert costs.contact_area_mm2 >= 0
        assert costs.scar_area_mm2 >= 0
        assert costs.peel_score >= 0


def test_recommend_picks_finite_cost():
    mesh = center_on_bed(_table_with_overhang(), 220, 220)
    rec = recommend_supports(mesh, DEFAULT_CONFIG)
    assert rec.best is not None
    assert np.isfinite(rec.best.costs.cost)
    # Sparse/tree should not use more columns than dense
    by_kind = {r.candidate.kind: r for r in rec.ranked}
    assert len(by_kind["tree"].candidate.columns) <= len(by_kind["dense_pillars"].candidate.columns)


def test_flat_cube_needs_no_supports():
    cube = center_on_bed(pv.Cube(x_length=20, y_length=20, z_length=10).triangulate(), 220, 220)
    rec = recommend_supports(cube, DEFAULT_CONFIG)
    result = rec.to_analysis_result()
    # Bed-contact underside faces are filtered out — a resting cube needs no pillars.
    assert result.name == "supports"
    assert rec.tip_map.count == 0
    assert result.verdict == "No supports needed"


def test_pipeline_summary_keys():
    mesh = center_on_bed(_table_with_overhang(), 220, 220)
    report = run_pipeline(mesh, DEFAULT_CONFIG)
    assert "best_support" in report.summary
    assert "toppling" in report.summary
    assert "supports" in report.results


@pytest.mark.parametrize("stl_name", ["Blade.stl"])
def test_sample_stl_pipeline(stl_name, request):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    path = root / "Files" / stl_name
    if not path.is_file():
        pytest.skip(f"missing {path}")
    from tesselater.mesh_io import load_mesh

    mesh = center_on_bed(load_mesh(path), 220, 220)
    report = run_pipeline(mesh)
    assert report.summary["overhang_faces"] >= 0
    assert report.results["supports"].name == "supports"

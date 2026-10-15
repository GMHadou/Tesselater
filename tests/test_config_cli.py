"""TOML config, materials, and CLI smoke."""

from __future__ import annotations

import json
from pathlib import Path

import pyvista as pv
import pytest

from tesselater.cli import main as cli_main
from tesselater.config import load_config, load_material, list_materials
from tesselater.mesh_io import center_on_bed, place_on_bed
from tesselater.optimize.orientation import search_orientations
from tesselater.support.export import export_supports_stl
from tesselater.support.optimize import recommend_supports


ROOT = Path(__file__).resolve().parents[1]


def test_list_and_load_materials():
    mats = list_materials()
    assert "pla" in mats
    assert "abs" in mats
    pla = load_material("pla")
    abs_ = load_material("abs")
    assert pla.shrinkage_fraction < abs_.shrinkage_fraction
    assert abs_.tip_bond > pla.tip_bond


def test_load_config_example():
    cfg = load_config(ROOT / "config.example.toml")
    assert cfg.printer.bed_width == 220.0
    assert cfg.support.weight_scar > 0


def test_material_override_sets_temps():
    cfg = load_config(material="abs")
    assert cfg.material.name == "ABS"
    assert cfg.printer.bed_temp >= 90.0


def _shelf() -> pv.PolyData:
    stem = pv.Cube(center=(0, 0, 10), x_length=4, y_length=4, z_length=20).triangulate()
    plate = pv.Cube(center=(0, 0, 21), x_length=30, y_length=30, z_length=2).triangulate()
    return place_on_bed(stem.merge(plate))


def test_export_supports_stl(tmp_path):
    mesh = center_on_bed(_shelf(), 220, 220)
    rec = recommend_supports(mesh)
    assert rec.best is not None
    out = tmp_path / "supports.stl"
    export_supports_stl(rec.best.candidate, out)
    assert out.is_file()
    assert out.stat().st_size > 100


def test_orientation_search_finds_pose():
    mesh = center_on_bed(_shelf(), 220, 220)
    result = search_orientations(mesh)
    assert result.best is not None
    assert result.best.fits_bed
    assert len(result.trials) >= 1


def test_cli_report(tmp_path):
    stl = ROOT / "Files" / "Blade.stl"
    if not stl.is_file():
        pytest.skip("no sample")
    out = tmp_path / "report.json"
    rc = cli_main(["report", str(stl), "-o", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert "summary" in data
    assert "best_support" in data["summary"]


def test_cli_materials():
    assert cli_main(["materials"]) == 0

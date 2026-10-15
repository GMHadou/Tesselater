"""Mesh loading helpers (no import-time I/O)."""

from __future__ import annotations

from pathlib import Path

import pyvista as pv


def load_mesh(file_path: str | Path) -> pv.PolyData:
    """Load an STL (or any PyVista-readable) mesh and return a PolyData copy."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Mesh file not found: {path}")
    mesh = pv.read(str(path))
    if not isinstance(mesh, pv.PolyData):
        mesh = mesh.extract_surface().cast_to_unstructured_grid().extract_surface()
        mesh = pv.PolyData(mesh)
    if mesh.n_points == 0:
        raise ValueError(f"Mesh has no points: {path}")
    return mesh


def place_on_bed(mesh: pv.PolyData, inplace: bool = False) -> pv.PolyData:
    """Translate mesh so its lowest Z sits on z=0."""
    target = mesh if inplace else mesh.copy(deep=True)
    min_z = float(target.bounds[4])
    target.points[:, 2] -= min_z
    return target


def center_on_bed(
    mesh: pv.PolyData,
    bed_width: float,
    bed_length: float,
    inplace: bool = False,
) -> pv.PolyData:
    """Center XY on the bed and rest the mesh on z=0."""
    target = place_on_bed(mesh, inplace=inplace)
    cx, cy, _ = target.center
    target.points[:, 0] -= cx - bed_width / 2.0
    target.points[:, 1] -= cy - bed_length / 2.0
    return target


def make_bed_plane(bed_width: float, bed_length: float) -> pv.PolyData:
    """Bed rectangle in the XY plane at z=0, centered on the bed origin."""
    plane = pv.Plane(
        center=(bed_width / 2.0, bed_length / 2.0, 0.0),
        direction=(0.0, 0.0, 1.0),
        i_size=bed_width,
        j_size=bed_length,
        i_resolution=10,
        j_resolution=10,
    )
    return plane


def rotate_mesh(mesh: pv.PolyData, axis: str, angle_degrees: float) -> pv.PolyData:
    """Rotate about axis, then re-seat on the bed (z=0)."""
    axis = axis.strip().lower()
    if axis == "x":
        mesh.rotate_x(angle_degrees, inplace=True)
    elif axis == "y":
        mesh.rotate_y(angle_degrees, inplace=True)
    elif axis == "z":
        mesh.rotate_z(angle_degrees, inplace=True)
    else:
        raise ValueError(f"Axis must be x, y, or z; got {axis!r}")
    return place_on_bed(mesh, inplace=True)


def is_likely_watertight(mesh: pv.PolyData) -> bool:
    """Cheap watertight heuristic: closed surface with positive volume."""
    try:
        return bool(mesh.n_open_edges == 0 and mesh.volume > 0)
    except Exception:
        return False

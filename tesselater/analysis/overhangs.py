"""Overhang detection from face normals vs build direction."""

from __future__ import annotations

import numpy as np
import pyvista as pv

from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.geometry import face_angles_to_build


def find_overhang_cells(
    mesh: pv.PolyData,
    config: AppConfig = DEFAULT_CONFIG,
    build_direction: np.ndarray | None = None,
) -> pv.UnstructuredGrid:
    """
    Faces that lean past the printable overhang angle from vertical.

    With build direction +Z, a vertical wall has normal angle 90° from +Z.
    A face tilted α past vertical (toward a ceiling) has normal angle ≈ 90°+α.
    The usual 45° rule therefore flags faces with

        angle(normal, +Z) > 180° − overhang_angle_deg
        (e.g. > 135° when overhang_angle_deg = 45).
    """
    angles = face_angles_to_build(mesh, build_direction)
    limit = 180.0 - config.printer.overhang_angle_deg
    overhang_ids = np.where(angles > limit)[0]
    if len(overhang_ids) == 0:
        return mesh.extract_cells([])
    return mesh.extract_cells(overhang_ids)

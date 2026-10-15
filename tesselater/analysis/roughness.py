"""Surface roughness coloring from local face angle to the build direction."""

from __future__ import annotations

import numpy as np
import pyvista as pv
from matplotlib.colors import to_rgb

from tesselater.geometry import face_angles_to_build


def compute_surface_roughness(
    mesh: pv.PolyData,
    build_direction: np.ndarray | None = None,
    smooth_color: str = "lightblue",
    rough_color: str = "purple",
    shallow_band: tuple[float, float] = (2.0, 45.0),
    steep_band: tuple[float, float] = (135.0, 178.0),
) -> pv.PolyData:
    """
    Mark faces in shallow stair-step and steep overhang bands as rough.

    Writes RGB ``cell_data['SurfaceRoughness']`` and a scalar mask
    ``cell_data['RoughMask']`` (1 = rough). Returns a copy.
    """
    work = mesh.copy()
    angles = face_angles_to_build(work, build_direction)
    rough = ((angles > shallow_band[0]) & (angles < shallow_band[1])) | (
        (angles > steep_band[0]) & (angles < steep_band[1])
    )

    colors = np.zeros((work.n_cells, 3), dtype=float)
    colors[rough] = to_rgb(rough_color)
    colors[~rough] = to_rgb(smooth_color)
    work.cell_data["SurfaceRoughness"] = colors
    work.cell_data["RoughMask"] = rough.astype(np.uint8)
    return work

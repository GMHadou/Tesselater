"""Geometry primitives."""

from __future__ import annotations

import numpy as np
import pyvista as pv

from tesselater.geometry import (
    circle_inside_footprint,
    first_layer_footprint,
    volume_center_of_mass,
)
from tesselater.mesh_io import center_on_bed


def test_cube_volume_com():
    cube = pv.Cube(x_length=10, y_length=10, z_length=20).triangulate()
    cube.points += np.array([5.0, 5.0, 10.0])
    com = volume_center_of_mass(cube)
    assert np.linalg.norm(com - np.array([5.0, 5.0, 10.0])) < 1e-3


def test_footprint_area_and_containment():
    box = pv.Cube(x_length=40, y_length=40, z_length=5).triangulate()
    box = center_on_bed(box, 220, 220)
    fp = first_layer_footprint(box, 0.2)
    com = volume_center_of_mass(box)
    assert fp.area > 100.0
    assert circle_inside_footprint(com[:2], 1.0, fp.hull_xy)

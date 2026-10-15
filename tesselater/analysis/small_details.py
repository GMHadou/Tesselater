"""Cells smaller than the printer's practical resolution."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv

from tesselater.config import AppConfig, DEFAULT_CONFIG


@dataclass(frozen=True)
class SmallDetailsResult:
    minimal_area: float
    thin_cells: pv.UnstructuredGrid
    count: int


def find_thin_cells(
    mesh: pv.PolyData,
    config: AppConfig = DEFAULT_CONFIG,
) -> SmallDetailsResult:
    """
    Flag cells whose area is below nozzle_size² · microstepping.

    Units: mm². This is a resolution heuristic, not a slicer guarantee.
    """
    printer = config.printer
    minimal_area = (printer.nozzle_size**2) * printer.microstepping
    sizes = mesh.compute_cell_sizes(length=False, area=True, volume=False)
    areas = np.asarray(sizes["Area"], dtype=float)
    ids = np.where(areas < minimal_area)[0]
    thin = mesh.extract_cells(ids)
    return SmallDetailsResult(minimal_area=minimal_area, thin_cells=thin, count=int(len(ids)))

"""Extract and cluster overhang tip points that need support."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv

from tesselater.analysis.overhangs import find_overhang_cells
from tesselater.config import AppConfig, DEFAULT_CONFIG


@dataclass(frozen=True)
class OverhangTip:
    """A representative point on an overhang that should be supported."""

    position: np.ndarray  # (3,) tip in world coords
    area: float  # mm² of clustered faces


@dataclass(frozen=True)
class TipMap:
    tips: tuple[OverhangTip, ...]
    overhang_cells: pv.UnstructuredGrid
    total_overhang_area: float

    @property
    def count(self) -> int:
        return len(self.tips)


def _cell_centers_and_areas(cells: pv.UnstructuredGrid) -> tuple[np.ndarray, np.ndarray]:
    if cells.n_cells == 0:
        return np.zeros((0, 3)), np.zeros(0)
    centers = np.asarray(cells.cell_centers().points, dtype=float)
    sizes = cells.compute_cell_sizes(length=False, area=True, volume=False)
    areas = np.asarray(sizes["Area"], dtype=float)
    return centers, areas


def cluster_tips_xy(
    centers: np.ndarray,
    areas: np.ndarray,
    pitch: float,
) -> list[OverhangTip]:
    """
    Bin overhang face centers on an XY grid of spacing ``pitch``.

    Each occupied bin becomes one tip at the area-weighted mean position
    (Z kept so columns meet the part underside).
    """
    if len(centers) == 0:
        return []
    pitch = max(float(pitch), 1e-6)
    keys = np.floor(centers[:, :2] / pitch).astype(np.int64)
    # Pack keys for grouping
    uniq, inverse = np.unique(keys, axis=0, return_inverse=True)
    tips: list[OverhangTip] = []
    for i in range(len(uniq)):
        mask = inverse == i
        w = areas[mask]
        w_sum = float(w.sum())
        if w_sum <= 0:
            pos = centers[mask].mean(axis=0)
            area = 0.0
        else:
            pos = (centers[mask] * w[:, None]).sum(axis=0) / w_sum
            area = w_sum
        tips.append(OverhangTip(position=pos, area=area))
    # Prefer lower tips first (closer to bed) when equal — stable order
    tips.sort(key=lambda t: (t.position[2], t.position[0], t.position[1]))
    return tips


def build_tip_map(mesh: pv.PolyData, config: AppConfig = DEFAULT_CONFIG) -> TipMap:
    """Overhang faces → clustered tip points for support generation."""
    overhangs = find_overhang_cells(mesh, config)
    centers, areas = _cell_centers_and_areas(overhangs)
    # Faces already on the bed do not need supports (first-layer contact).
    z_min = float(mesh.bounds[4])
    clearance = max(2.0 * config.printer.layer_height, 0.4)
    if len(centers):
        elevated = centers[:, 2] > z_min + clearance
        centers = centers[elevated]
        areas = areas[elevated]
        if overhangs.n_cells and elevated.any() and elevated.sum() < overhangs.n_cells:
            # Keep only elevated overhang cells for visualization when possible
            try:
                ids = np.where(elevated)[0]
                # cell_centers align with overhang cell order
                overhangs = overhangs.extract_cells(ids)
            except Exception:
                pass
    pitch = max(config.support.cluster_pitch_mm, config.printer.nozzle_size * 4.0)
    tips = cluster_tips_xy(centers, areas, pitch=pitch)
    total_area = float(areas.sum()) if len(areas) else 0.0
    return TipMap(
        tips=tuple(tips),
        overhang_cells=overhangs,
        total_overhang_area=total_area,
    )

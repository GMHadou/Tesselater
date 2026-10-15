"""Generate discrete support structure candidates from overhang tips."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pyvista as pv

from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.support.tips import OverhangTip, TipMap

TipStyle = Literal["point", "flat"]


@dataclass(frozen=True)
class SupportColumn:
    tip: np.ndarray  # (3,) meets part
    radius: float  # mm shaft radius
    base_z: float = 0.0
    tip_style: TipStyle = "point"

    @property
    def height(self) -> float:
        return max(float(self.tip[2] - self.base_z), 0.0)

    @property
    def volume(self) -> float:
        return float(np.pi * self.radius**2 * self.height)

    def contact_radius(self, point_tip_scale: float = 0.35) -> float:
        if self.tip_style == "point":
            return float(self.radius * point_tip_scale)
        return float(self.radius)

    def contact_area(self, point_tip_scale: float = 0.35) -> float:
        r = self.contact_radius(point_tip_scale)
        return float(np.pi * r**2)

    def scar_area(self, point_tip_scale: float = 0.35) -> float:
        """Expected surface scar after removal (≈ contact disk)."""
        return self.contact_area(point_tip_scale)

    def peel_difficulty(self, tip_bond: float = 1.0, point_tip_scale: float = 0.35) -> float:
        """
        Higher ⇒ harder to detach.

        Flat tips bond over the full shaft; point tips reduce area and add a
        geometric release factor (easier snap-off).
        """
        area = self.contact_area(point_tip_scale)
        style_factor = 1.0 if self.tip_style == "flat" else 0.45
        return float(area * tip_bond * style_factor)


@dataclass
class SupportCandidate:
    kind: str
    columns: list[SupportColumn]
    covered_tip_indices: list[int]

    def volume_mm3(self) -> float:
        return float(sum(c.volume for c in self.columns))

    def contact_area_mm2(self, point_tip_scale: float = 0.35) -> float:
        return float(sum(c.contact_area(point_tip_scale) for c in self.columns))

    def scar_area_mm2(self, point_tip_scale: float = 0.35) -> float:
        return float(sum(c.scar_area(point_tip_scale) for c in self.columns))

    def peel_score(self, tip_bond: float = 1.0, point_tip_scale: float = 0.35) -> float:
        return float(sum(c.peel_difficulty(tip_bond, point_tip_scale) for c in self.columns))

    def total_height_mm(self) -> float:
        return float(sum(c.height for c in self.columns))

    def to_polydata(self) -> pv.PolyData:
        """Visual proxy: line segments tip→bed."""
        if not self.columns:
            return pv.PolyData()
        pts: list[list[float]] = []
        lines: list[int] = []
        for col in self.columns:
            i0 = len(pts)
            pts.append([col.tip[0], col.tip[1], col.base_z])
            pts.append([col.tip[0], col.tip[1], col.tip[2]])
            lines.extend([2, i0, i0 + 1])
        return pv.PolyData(np.asarray(pts, dtype=float), lines=np.asarray(lines, dtype=np.int64))


def _radius_for_tip(tip: OverhangTip, config: AppConfig) -> float:
    base = config.support.pillar_radius_mm
    if base is None:
        base = config.printer.nozzle_size * 1.5
    grow = min(np.sqrt(max(tip.area, 0.0)) * 0.05, base)
    return float(base + grow)


def _merge_tips(tips: list[OverhangTip], merge_radius: float) -> list[OverhangTip]:
    if not tips or merge_radius <= 0:
        return list(tips)
    remaining = list(tips)
    merged: list[OverhangTip] = []
    while remaining:
        seed = remaining.pop(0)
        group = [seed]
        kept: list[OverhangTip] = []
        for t in remaining:
            if np.linalg.norm(t.position[:2] - seed.position[:2]) <= merge_radius:
                group.append(t)
            else:
                kept.append(t)
        remaining = kept
        weights = np.array([g.area for g in group], dtype=float)
        wsum = float(weights.sum())
        positions = np.array([g.position for g in group], dtype=float)
        if wsum > 0:
            pos = (positions * weights[:, None]).sum(axis=0) / wsum
        else:
            pos = positions.mean(axis=0)
        pos[2] = min(g.position[2] for g in group)
        merged.append(OverhangTip(position=pos, area=wsum))
    return merged


def _columns_from_tips(
    tips: list[OverhangTip],
    config: AppConfig,
    *,
    radius_scale: float,
    tip_style: TipStyle,
) -> list[SupportColumn]:
    return [
        SupportColumn(
            tip=t.position.copy(),
            radius=_radius_for_tip(t, config) * radius_scale,
            tip_style=tip_style,
        )
        for t in tips
    ]


def candidate_dense_pillars(tip_map: TipMap, config: AppConfig) -> SupportCandidate:
    """One pillar per tip — flat tips for maximum local stability."""
    columns = _columns_from_tips(list(tip_map.tips), config, radius_scale=1.0, tip_style="flat")
    return SupportCandidate(
        kind="dense_pillars",
        columns=columns,
        covered_tip_indices=list(range(len(tip_map.tips))),
    )


def candidate_sparse_pillars(tip_map: TipMap, config: AppConfig) -> SupportCandidate:
    merged = _merge_tips(list(tip_map.tips), config.support.sparse_merge_radius_mm)
    style: TipStyle = "point" if config.support.default_tip_style == "point" else "flat"
    columns = _columns_from_tips(merged, config, radius_scale=1.15, tip_style=style)
    return SupportCandidate(
        kind="sparse_pillars",
        columns=columns,
        covered_tip_indices=list(range(len(tip_map.tips))),
    )


def candidate_tree(tip_map: TipMap, config: AppConfig) -> SupportCandidate:
    merged = _merge_tips(list(tip_map.tips), config.support.tree_merge_radius_mm)
    columns = _columns_from_tips(merged, config, radius_scale=1.35, tip_style="point")
    return SupportCandidate(
        kind="tree",
        columns=columns,
        covered_tip_indices=list(range(len(tip_map.tips))),
    )


def generate_candidates(tip_map: TipMap, config: AppConfig = DEFAULT_CONFIG) -> list[SupportCandidate]:
    if tip_map.count == 0:
        return [SupportCandidate(kind="none", columns=[], covered_tip_indices=[])]
    return [
        candidate_dense_pillars(tip_map, config),
        candidate_sparse_pillars(tip_map, config),
        candidate_tree(tip_map, config),
    ]

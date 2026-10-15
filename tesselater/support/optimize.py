"""Pick the lowest-cost feasible support candidate for a mesh."""

from __future__ import annotations

from dataclasses import dataclass

import pyvista as pv

from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.results import AnalysisResult, MeshActor
from tesselater.support.candidates import SupportCandidate, generate_candidates
from tesselater.support.score import SupportCosts, score_candidate
from tesselater.support.tips import TipMap, build_tip_map


@dataclass
class RankedCandidate:
    candidate: SupportCandidate
    costs: SupportCosts


@dataclass
class SupportRecommendation:
    tip_map: TipMap
    ranked: list[RankedCandidate]
    best: RankedCandidate | None

    def to_analysis_result(self) -> AnalysisResult:
        if self.best is None or self.tip_map.count == 0:
            return AnalysisResult(
                name="supports",
                verdict="No supports needed",
                metrics={"tips": 0, "overhang_area_mm2": self.tip_map.total_overhang_area},
                message="No overhang tips detected under the current angle rule.",
                actors=[
                    MeshActor(self.tip_map.overhang_cells, color="red", opacity=0.5, label="overhangs")
                ]
                if self.tip_map.overhang_cells.n_cells
                else [],
            )

        best = self.best
        rows = []
        for r in self.ranked:
            mark = "← best" if r is best else ""
            rows.append(
                f"{r.candidate.kind:16s}  V={r.costs.volume_mm3:8.1f} mm³  "
                f"A={r.costs.contact_area_mm2:6.2f} mm²  "
                f"scar={r.costs.scar_area_mm2:6.2f}  "
                f"t≈{r.costs.estimated_time_s:6.1f}s  "
                f"J={r.costs.cost:8.3f} {mark}"
            )
        table = "\n".join(rows)
        actors = [
            MeshActor(self.tip_map.overhang_cells, color="crimson", opacity=0.35, label="overhangs"),
            MeshActor(
                best.candidate.to_polydata(),
                color="lime",
                opacity=1.0,
                style="wireframe",
                line_width=3.0,
                label=best.candidate.kind,
            ),
        ]
        # Tip markers
        if self.tip_map.tips:
            import numpy as np

            tip_pts = np.array([t.position for t in self.tip_map.tips], dtype=float)
            actors.append(
                MeshActor(
                    pv.PolyData(tip_pts),
                    color="yellow",
                    style="points",
                    point_size=12.0,
                    label="tips",
                )
            )

        return AnalysisResult(
            name="supports",
            verdict=f"Best: {best.candidate.kind} (J={best.costs.cost:.3f})",
            metrics={
                "tips": self.tip_map.count,
                "overhang_area_mm2": self.tip_map.total_overhang_area,
                "best_kind": best.candidate.kind,
                "volume_mm3": best.costs.volume_mm3,
                "contact_area_mm2": best.costs.contact_area_mm2,
                "estimated_time_s": best.costs.estimated_time_s,
                "scar_area_mm2": best.costs.scar_area_mm2,
                "peel_score": best.costs.peel_score,
                "cost": best.costs.cost,
                "n_columns": len(best.candidate.columns),
            },
            actors=actors,
            message=table,
        )


def recommend_supports(
    mesh: pv.PolyData,
    config: AppConfig = DEFAULT_CONFIG,
) -> SupportRecommendation:
    """
    Geometry-only support optimizer (stage B):

    overhang map → tip clusters → candidate structures → score → pick min J.
    FEA can later reject / re-rank ``ranked`` without changing this API.
    """
    tip_map = build_tip_map(mesh, config)
    candidates = generate_candidates(tip_map, config)
    ranked = [
        RankedCandidate(c, score_candidate(c, tip_map.count, config)) for c in candidates
    ]
    feasible = [r for r in ranked if r.costs.feasible]
    pool = feasible or ranked
    best = min(pool, key=lambda r: r.costs.cost) if pool else None
    # Stable display order: by cost
    ranked_sorted = sorted(ranked, key=lambda r: r.costs.cost)
    return SupportRecommendation(tip_map=tip_map, ranked=ranked_sorted, best=best)

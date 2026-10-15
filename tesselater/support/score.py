"""Multi-objective cost for support candidates (incl. scar / peel)."""

from __future__ import annotations

from dataclasses import dataclass

from tesselater.config import AppConfig, DEFAULT_CONFIG, speed_limits
from tesselater.support.candidates import SupportCandidate


@dataclass(frozen=True)
class SupportCosts:
    volume_mm3: float
    contact_area_mm2: float
    scar_area_mm2: float
    peel_score: float
    estimated_time_s: float
    travel_mm: float
    cost: float
    feasible: bool
    notes: str = ""


def estimate_print_time_s(
    volume_mm3: float,
    travel_mm: float,
    config: AppConfig,
) -> float:
    printer = config.printer
    line_width, _, _, quality = speed_limits(printer)
    extrusion_rate = max(line_width * printer.layer_height * printer.speed, 1e-9)
    t_ext = volume_mm3 / extrusion_rate
    travel_speed = max(quality * 1.5, 1.0)
    t_travel = travel_mm / travel_speed
    return float(t_ext + t_travel)


def estimate_travel_mm(candidate: SupportCandidate) -> float:
    if len(candidate.columns) <= 1:
        return 0.0
    pts = [c.tip[:2] for c in candidate.columns]
    order = sorted(range(len(pts)), key=lambda i: (pts[i][0], pts[i][1]))
    dist = 0.0
    for a, b in zip(order, order[1:]):
        delta = pts[b] - pts[a]
        dist += float((delta[0] ** 2 + delta[1] ** 2) ** 0.5)
    return dist


def score_candidate(
    candidate: SupportCandidate,
    n_tips: int,
    config: AppConfig = DEFAULT_CONFIG,
) -> SupportCosts:
    """
    J = w_t·(T/60) + w_v·(V/1000) + w_c·A_contact + w_s·scar_score

    scar_score blends scar area and peel difficulty (material tip_bond).
    """
    scale = config.support.point_tip_scale
    bond = config.material.tip_bond
    vol = candidate.volume_mm3()
    contact = candidate.contact_area_mm2(scale)
    scar = candidate.scar_area_mm2(scale)
    peel = candidate.peel_score(bond, scale)
    travel = estimate_travel_mm(candidate)
    time_s = estimate_print_time_s(vol, travel, config)

    w = config.support
    scar_score = 0.6 * scar + 0.4 * peel
    cost = (
        w.weight_time * (time_s / 60.0)
        + w.weight_volume * (vol / 1000.0)
        + w.weight_contact * contact
        + w.weight_scar * scar_score
    )

    if n_tips == 0 and candidate.kind == "none":
        return SupportCosts(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, True, "No overhangs — no supports needed.")

    covered = len(candidate.covered_tip_indices)
    feasible = covered >= n_tips and (n_tips == 0 or len(candidate.columns) > 0)
    n_point = sum(1 for c in candidate.columns if c.tip_style == "point")
    n_flat = len(candidate.columns) - n_point
    notes = (
        f"{candidate.kind}: {len(candidate.columns)} cols "
        f"(point={n_point}, flat={n_flat}), cover {covered}/{n_tips}, "
        f"scar={scar:.2f} mm² peel={peel:.2f}"
    )
    if not feasible:
        notes += " [INFEASIBLE]"
        cost = float("inf")

    return SupportCosts(
        volume_mm3=vol,
        contact_area_mm2=contact,
        scar_area_mm2=scar,
        peel_score=peel,
        estimated_time_s=time_s,
        travel_mm=travel,
        cost=float(cost),
        feasible=feasible,
        notes=notes,
    )

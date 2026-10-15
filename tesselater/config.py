"""Single source of printer / material / support configuration."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:  # pragma: no cover
        tomllib = None  # type: ignore


@dataclass(frozen=True)
class MaterialConfig:
    """Material thermal / shrinkage parameters (defaults: PLA)."""

    name: str = "PLA"
    cte: float = 68e-6  # /°C
    shrinkage_fraction: float = 0.005
    recommended_bed_temp_range: tuple[float, float] = (45.0, 60.0)
    recommended_hotend_temp_range: tuple[float, float] = (195.0, 210.0)
    fluid_transition_temp: float = 135.0
    # Relative interfacial bond at support tips (scales peel / scar cost)
    tip_bond: float = 1.0


@dataclass(frozen=True)
class PrinterConfig:
    """Printer geometry and process settings (defaults: Ender-3 class)."""

    bed_width: float = 220.0
    bed_length: float = 220.0
    nozzle_size: float = 0.4
    nozzle_flat: float = 0.8
    layer_height: float = 0.2
    line_width: float | None = None
    wall_thickness: float = 0.8
    infill_density: float = 0.2
    microstepping: float = 1.0 / 16.0
    speed: float = 80.0
    hotend_temp: float = 210.0
    bed_temp: float = 60.0
    overhang_angle_deg: float = 45.0
    tip_angle_deg: float = 5.0
    stability_margin_threshold: float = 50.0

    def resolved_line_width(self) -> float:
        if self.line_width is not None:
            return self.line_width
        return self.nozzle_size * 1.25


@dataclass(frozen=True)
class SupportConfig:
    """
    Support generation + multi-objective weights.

    J = w_t·(T/60) + w_v·(V/1000) + w_c·A_contact + w_s·scar_score
    """

    cluster_pitch_mm: float = 3.0
    sparse_merge_radius_mm: float = 6.0
    tree_merge_radius_mm: float = 10.0
    pillar_radius_mm: float | None = None
    weight_time: float = 1.0
    weight_volume: float = 1.0
    weight_contact: float = 0.15
    weight_scar: float = 0.25
    # "point" (easier detach) or "flat" (more stable, worse scar)
    default_tip_style: str = "point"
    point_tip_scale: float = 0.35  # contact radius factor for point tips


@dataclass(frozen=True)
class OrientationConfig:
    """Discrete orientation search settings."""

    angle_step_deg: float = 90.0
    include_z_spins: bool = False
    unstable_penalty: float = 50.0
    max_candidates: int = 64


@dataclass(frozen=True)
class AppConfig:
    material: MaterialConfig = field(default_factory=MaterialConfig)
    printer: PrinterConfig = field(default_factory=PrinterConfig)
    support: SupportConfig = field(default_factory=SupportConfig)
    orientation: OrientationConfig = field(default_factory=OrientationConfig)


DEFAULT_CONFIG = AppConfig()

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
MATERIALS_DIR = _PACKAGE_ROOT / "materials"


def flow_rate_mm3_s(hotend_temp: float) -> float:
    if hotend_temp <= 210:
        return 10.0
    if hotend_temp < 250:
        return 12.5
    return 15.0


def speed_limits(printer: PrinterConfig) -> tuple[float, float, float, float]:
    line_width = printer.resolved_line_width()
    minimum = printer.layer_height + printer.nozzle_size
    maximum = printer.layer_height + printer.nozzle_flat
    ideal = 0.5 * (minimum + maximum)
    flow = flow_rate_mm3_s(printer.hotend_temp)
    max_speed = flow / max(line_width * printer.layer_height, 1e-9)
    quality_speed = max_speed * 0.7
    return line_width, ideal, max_speed, quality_speed


def _load_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:
        raise ImportError(
            "TOML support requires Python 3.11+ or the 'tomli' package. "
            "pip install tomli"
        )
    with path.open("rb") as fh:
        return tomllib.load(fh)


def material_from_mapping(data: dict[str, Any]) -> MaterialConfig:
    bed = (
        float(data.get("recommended_bed_temp_min", 45.0)),
        float(data.get("recommended_bed_temp_max", 60.0)),
    )
    hot = (
        float(data.get("recommended_hotend_temp_min", 195.0)),
        float(data.get("recommended_hotend_temp_max", 210.0)),
    )
    if "recommended_bed_temp_range" in data:
        bed = tuple(data["recommended_bed_temp_range"])  # type: ignore[assignment]
    if "recommended_hotend_temp_range" in data:
        hot = tuple(data["recommended_hotend_temp_range"])  # type: ignore[assignment]
    return MaterialConfig(
        name=str(data.get("name", "custom")),
        cte=float(data.get("cte", 68e-6)),
        shrinkage_fraction=float(data.get("shrinkage_fraction", 0.005)),
        recommended_bed_temp_range=(float(bed[0]), float(bed[1])),
        recommended_hotend_temp_range=(float(hot[0]), float(hot[1])),
        fluid_transition_temp=float(data.get("fluid_transition_temp", 135.0)),
        tip_bond=float(data.get("tip_bond", 1.0)),
    )


def load_material(name_or_path: str | Path) -> MaterialConfig:
    """Load a material by name (`pla`) or TOML path."""
    raw = Path(name_or_path)
    if raw.suffix.lower() == ".toml" and raw.is_file():
        return material_from_mapping(_load_toml(raw))
    name = str(name_or_path).lower().removesuffix(".toml")
    path = MATERIALS_DIR / f"{name}.toml"
    if not path.is_file():
        raise FileNotFoundError(f"Material not found: {name_or_path} (looked in {path})")
    return material_from_mapping(_load_toml(path))


def list_materials() -> list[str]:
    if not MATERIALS_DIR.is_dir():
        return []
    return sorted(p.stem for p in MATERIALS_DIR.glob("*.toml"))


def _merge_dataclass(dc_obj: Any, data: dict[str, Any]) -> Any:
    if not data:
        return dc_obj
    allowed = {f.name for f in fields(dc_obj)}
    updates = {}
    for key, value in data.items():
        if key in allowed:
            updates[key] = value
    # Printer / support may use nested range keys via material path only
    return replace(dc_obj, **updates) if updates else dc_obj


def load_config(
    path: str | Path | None = None,
    *,
    material: str | None = None,
) -> AppConfig:
    """
    Load AppConfig from optional TOML, then apply material override.

    Resolution order: defaults → config.toml sections → --material.
    """
    cfg = DEFAULT_CONFIG
    if path is not None:
        p = Path(path)
        data = _load_toml(p)
        mat_data = dict(data.get("material", {}))
        if "material_file" in mat_data:
            cfg = replace(cfg, material=load_material(mat_data.pop("material_file")))
        elif mat_data:
            cfg = replace(cfg, material=material_from_mapping(mat_data))
        if "printer" in data:
            cfg = replace(cfg, printer=_merge_dataclass(cfg.printer, data["printer"]))
        if "support" in data:
            cfg = replace(cfg, support=_merge_dataclass(cfg.support, data["support"]))
        if "orientation" in data:
            cfg = replace(
                cfg, orientation=_merge_dataclass(cfg.orientation, data["orientation"])
            )
    if material:
        cfg = replace(cfg, material=load_material(material))
        # Align process temps to material recommendations when still at PLA defaults
        bed = cfg.material.recommended_bed_temp_range
        hot = cfg.material.recommended_hotend_temp_range
        cfg = replace(
            cfg,
            printer=replace(
                cfg.printer,
                bed_temp=0.5 * (bed[0] + bed[1]),
                hotend_temp=0.5 * (hot[0] + hot[1]),
            ),
        )
    return cfg

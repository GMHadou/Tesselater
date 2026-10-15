"""Command-line interface for reports, orientation search, and export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tesselater import __version__
from tesselater.config import list_materials, load_config
from tesselater.mesh_io import center_on_bed, load_mesh
from tesselater.optimize.orientation import search_orientations
from tesselater.pipeline import run_pipeline
from tesselater.support.export import export_oriented_part_stl, export_supports_stl
from tesselater.support.optimize import recommend_supports

_SUBCOMMANDS = frozenset({"gui", "report", "optimize", "export-supports", "materials"})


def _prep_mesh(path: Path, config):
    mesh = load_mesh(path)
    return center_on_bed(mesh, config.printer.bed_width, config.printer.bed_length, inplace=True)


def cmd_report(args: argparse.Namespace) -> int:
    config = load_config(args.config, material=args.material)
    reports = []
    for path in args.meshes:
        p = Path(path)
        mesh = _prep_mesh(p, config)
        report = run_pipeline(mesh, config)
        entry = {"file": str(p), "summary": report.summary, "verdicts": report.verdicts()}
        reports.append(entry)
        print(f"== {p.name} ==")
        for k, v in report.summary.items():
            print(f"  {k}: {v}")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(reports if len(reports) > 1 else reports[0], indent=2))
        print(f"Wrote {out}")
    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    config = load_config(args.config, material=args.material)
    out_dir = Path(args.output or "tesselater_out")
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for path in args.meshes:
        p = Path(path)
        mesh = _prep_mesh(p, config)
        print(f"Searching orientations for {p.name} …")
        orient = search_orientations(mesh, config)
        if orient.best is None:
            print(f"  No feasible pose for {p.name}")
            results.append({"file": str(p), "error": "no feasible pose"})
            continue

        best = orient.best
        stem = p.stem
        part_path = out_dir / f"{stem}_oriented.stl"
        export_oriented_part_stl(best.mesh, part_path)

        rec = recommend_supports(best.mesh, config)
        supports_path = None
        if rec.best is not None and rec.best.candidate.columns:
            supports_path = out_dir / f"{stem}_supports.stl"
            export_supports_stl(rec.best.candidate, supports_path, config)

        entry = {
            "file": str(p),
            "pose": {
                "rx_deg": best.pose.rx_deg,
                "ry_deg": best.pose.ry_deg,
                "rz_deg": best.pose.rz_deg,
            },
            "total_cost": best.total_cost,
            "support_kind": best.support_kind,
            "support_cost": best.support_cost,
            "tips": best.tips,
            "toppling": best.toppling_verdict,
            "oriented_stl": str(part_path),
            "supports_stl": str(supports_path) if supports_path else None,
            "n_trials": len(orient.trials),
        }
        results.append(entry)
        print(f"  best {best.pose.label()}  J={best.total_cost:.3f}  → {part_path}")
        if supports_path:
            print(f"  supports ({best.support_kind}) → {supports_path}")

    summary_path = out_dir / "optimize.json"
    summary_path.write_text(json.dumps(results if len(results) > 1 else results[0], indent=2))
    print(f"Wrote {summary_path}")
    return 0


def cmd_export_supports(args: argparse.Namespace) -> int:
    config = load_config(args.config, material=args.material)
    mesh = _prep_mesh(Path(args.mesh), config)
    rec = recommend_supports(mesh, config)
    if rec.best is None or not rec.best.candidate.columns:
        print("No supports to export.")
        return 1
    out = Path(args.output or "supports.stl")
    export_supports_stl(rec.best.candidate, out, config)
    print(f"Exported {rec.best.candidate.kind} → {out}")
    print(rec.to_analysis_result().message)
    return 0


def cmd_materials(_: argparse.Namespace) -> int:
    mats = list_materials()
    if not mats:
        print("No materials found.")
        return 1
    for m in mats:
        print(m)
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    from tesselater.ui.main_window import run_app

    config = load_config(args.config, material=args.material)
    return run_app(config)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tesselater",
        description="Geometric FDM printability checks and support optimization",
    )
    p.add_argument("--version", action="version", version=f"tesselater {__version__}")
    p.add_argument("--config", type=str, default=None, help="Path to config.toml")
    p.add_argument("--material", type=str, default=None, help="Material name or TOML path")

    sub = p.add_subparsers(dest="command")

    gui = sub.add_parser("gui", help="Open the Qt UI (default)")
    gui.set_defaults(func=cmd_gui)

    report = sub.add_parser("report", help="Batch printability JSON report")
    report.add_argument("meshes", nargs="+", help="STL files")
    report.add_argument("-o", "--output", help="Write JSON to this path")
    report.set_defaults(func=cmd_report)

    opt = sub.add_parser("optimize", help="Orientation search + export STLs")
    opt.add_argument("meshes", nargs="+", help="STL files")
    opt.add_argument("-o", "--output", default="tesselater_out", help="Output directory")
    opt.set_defaults(func=cmd_optimize)

    exp = sub.add_parser("export-supports", help="Export best supports as STL")
    exp.add_argument("mesh", help="STL file")
    exp.add_argument("-o", "--output", default="supports.stl")
    exp.set_defaults(func=cmd_export_supports)

    mats = sub.add_parser("materials", help="List bundled materials")
    mats.set_defaults(func=cmd_materials)

    return p


def _with_default_gui(argv: list[str]) -> list[str]:
    if not argv:
        return ["gui"]
    if any(a in _SUBCOMMANDS for a in argv):
        return argv
    # Global flags only → gui
    return ["gui", *argv]


def main(argv: list[str] | None = None) -> int:
    argv = _with_default_gui(list(sys.argv[1:] if argv is None else argv))
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        args = parser.parse_args(["gui"])
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

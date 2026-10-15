# Tesselater

Open-source geometric checks for FDM printability (warping, toppling, roughness,
shrinkage, overhangs, fine detail) plus **support scoring** and **orientation
search**. Inspired by
[Will-It-Print](https://link.springer.com/article/10.1007/s12008-021-00786-w).

Defaults target PLA on an Ender-3–class printer. Override via TOML / materials.

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt` / `pyproject.toml`

## Install & run (Arch / Linux)

```bash
git clone https://github.com/GMHadou/Tesselater.git
cd Tesselater
pyenv local 3.10.4   # or any 3.10+
python -m venv .venv-linux
source .venv-linux/bin/activate
pip install -r requirements.txt
pip install 'tomli>=2.0'   # only needed on Python < 3.11
pip install -e ".[dev]"    # optional: CLI entry + pytest

# GUI
PYTHONPATH=. python main.py
# or
PYTHONPATH=. python -m tesselater.cli gui
```

## CLI

```bash
# Batch report → JSON
PYTHONPATH=. python -m tesselater.cli report Files/Blade.stl -o report.json

# Orientation search + export oriented part + supports STL
PYTHONPATH=. python -m tesselater.cli optimize Files/Blade.stl -o tesselater_out

# Export supports only
PYTHONPATH=. python -m tesselater.cli export-supports Files/Blade.stl -o supports.stl

# Materials
PYTHONPATH=. python -m tesselater.cli materials
PYTHONPATH=. python -m tesselater.cli --material abs report Files/Blade.stl -o abs.json
```

Copy `config.example.toml` → `config.toml` and pass `--config config.toml`.

## Layout (v2.2)

| Path | Role |
|------|------|
| `main.py` / `tesselater/cli.py` | Entry + CLI |
| `tesselater/config.py` | Dataclasses + TOML loader |
| `materials/*.toml` | PLA / ABS (etc.) |
| `tesselater/geometry.py` | COM, footprint, tip circle |
| `tesselater/analysis/` | Heuristics |
| `tesselater/support/` | Tips → candidates → scar score → STL export |
| `tesselater/optimize/` | Orientation search |
| `tesselater/ui/` | Qt shell |
| `tests/` | pytest |

```bash
PYTHONPATH=. python -m pytest -q
```

## Analyses (UI)

- Warping, small details, toppling, roughness, shrinkage, overhangs
- **Supports (optimize)** — dense / sparse / tree; cost includes time, volume, contact, **scar/peel**
- **Orientation search** — discrete pose grid; replaces mesh with best pose
- COM / normals

## Configuration

- Code defaults: `tesselater/config.py`
- File overrides: `config.example.toml`
- Materials: `materials/pla.toml`, `materials/abs.toml`

Shrinkage reference:
https://filament2print.com/gb/blog/136_warping-contractions-3D-printing-parts.html

## Notes

Prefer watertight meshes. This is a geometry / heuristic optimizer, not full FEA.
`Curses.py` still launches the CLI/GUI for older docs.

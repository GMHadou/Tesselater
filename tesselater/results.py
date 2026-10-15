"""Shared analysis result types for UI / CLI / tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pyvista as pv


@dataclass(frozen=True)
class MeshActor:
    """Something the UI can draw without knowing analysis internals."""

    mesh: pv.DataSet
    color: str = "red"
    opacity: float = 1.0
    style: str = "surface"  # surface | points | wireframe
    point_size: float = 8.0
    line_width: float = 2.0
    rgb_scalars: str | None = None
    label: str | None = None


@dataclass
class AnalysisResult:
    """Uniform envelope returned by analyzers and the support optimizer."""

    name: str
    verdict: str
    metrics: dict[str, Any] = field(default_factory=dict)
    actors: list[MeshActor] = field(default_factory=list)
    message: str = ""
    # Optional secondary plotter content (title, actors) for pop-out windows
    secondary_title: str | None = None
    secondary_actors: list[MeshActor] = field(default_factory=list)

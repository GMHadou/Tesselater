"""Plotter helpers — keep MainWindow free of draw boilerplate."""

from __future__ import annotations

from typing import Protocol

import pyvista as pv

from tesselater.config import AppConfig
from tesselater.mesh_io import make_bed_plane
from tesselater.results import MeshActor


class PlotterLike(Protocol):
    def clear(self) -> None: ...
    def add_mesh(self, *args, **kwargs): ...
    def add_text(self, *args, **kwargs): ...
    def reset_camera(self) -> None: ...
    def update(self) -> None: ...


def bed_actor(config: AppConfig) -> MeshActor:
    p = config.printer
    return MeshActor(
        make_bed_plane(p.bed_width, p.bed_length),
        color="lightgrey",
        opacity=0.5,
        label="bed",
    )


def add_actor(plotter: PlotterLike, actor: MeshActor) -> None:
    kwargs: dict = {
        "color": actor.color,
        "opacity": actor.opacity,
    }
    if actor.rgb_scalars:
        kwargs["scalars"] = actor.rgb_scalars
        kwargs["rgb"] = True
        kwargs["show_scalar_bar"] = False
        kwargs.pop("color", None)
    if actor.style == "points":
        kwargs["point_size"] = actor.point_size
        kwargs["render_points_as_spheres"] = True
        kwargs["style"] = "points"
    elif actor.style == "wireframe":
        kwargs["style"] = "wireframe"
        kwargs["line_width"] = actor.line_width
    plotter.add_mesh(actor.mesh, **kwargs)


def reset_scene(
    plotter: PlotterLike,
    mesh: pv.PolyData | None,
    config: AppConfig,
    *,
    opacity: float = 1.0,
    color: str = "steelblue",
) -> None:
    plotter.clear()
    if mesh is not None:
        add_actor(plotter, MeshActor(mesh, color=color, opacity=opacity))
    add_actor(plotter, bed_actor(config))
    plotter.reset_camera()
    plotter.update()


def show_actors(
    plotter: PlotterLike,
    mesh: pv.PolyData | None,
    config: AppConfig,
    actors: list[MeshActor],
    *,
    mesh_color: str = "steelblue",
    mesh_opacity: float = 0.4,
    text: str = "",
) -> None:
    plotter.clear()
    if mesh is not None:
        add_actor(plotter, MeshActor(mesh, color=mesh_color, opacity=mesh_opacity))
    for actor in actors:
        if actor.mesh.n_points == 0:
            continue
        add_actor(plotter, actor)
    add_actor(plotter, bed_actor(config))
    if text:
        plotter.add_text(text, font_size=9)
    plotter.update()


def show_secondary_window(
    title: str,
    actors: list[MeshActor],
    config: AppConfig,
    text: str = "",
) -> None:
    plotter = pv.Plotter(title=title)
    plotter.set_background("white")
    for actor in actors:
        if actor.mesh.n_points == 0:
            continue
        add_actor(plotter, actor)
    add_actor(plotter, bed_actor(config))
    if text:
        plotter.add_text(text, font_size=10, color="black")
    plotter.show_grid()
    plotter.show()

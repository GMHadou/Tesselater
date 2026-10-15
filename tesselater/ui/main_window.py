"""PyQt5 + PyVistaQt main window (shell only)."""

from __future__ import annotations

import sys

import pyvista as pv
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from tesselater.config import AppConfig, DEFAULT_CONFIG
from tesselater.mesh_io import center_on_bed, is_likely_watertight, load_mesh, rotate_mesh
from tesselater.results import AnalysisResult
from tesselater.ui import actions
from tesselater.ui.viewers import reset_scene, show_actors, show_secondary_window



class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig = DEFAULT_CONFIG, *, ask_open: bool = True):
        super().__init__()
        self.config = config
        self.mesh = None
        self.mesh_file_path: str | None = None
        self._bounds_on = False
        self._grid_on = False

        self.setWindowTitle("Tesselater")
        self.setGeometry(100, 100, 960, 720)
        self._init_ui()
        if ask_open and not self._open_mesh_dialog():
            self.close()
            return
        if self.mesh is not None:
            reset_scene(self.plotter, self.mesh, self.config)

    def _init_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        self.plotter = QtInteractor(central)
        layout.addWidget(self.plotter.interactor)

        menu = self.menuBar()
        analysis_menu = menu.addMenu("Analysis")
        for name, slot in {
            "Warping analysis": self.on_warping_analysis,
            "Small Details": self.on_small_details,
            "Toppling": self.on_toppling,
            "Roughness": self.on_roughness,
            "Shrinkage": self.on_shrinkage,
            "Overhangs": self.on_overhangs,
            "Supports (optimize)": self.on_supports,
            "Orientation search": self.on_orientation,
            "Center of Mass": self.on_center_of_mass,
            "Vectors": self.on_vectors,
        }.items():
            act = QAction(name, self)
            act.triggered.connect(slot)
            analysis_menu.addAction(act)

        file_menu = menu.addMenu("File")
        open_act = QAction("Open Mesh…", self)
        open_act.triggered.connect(self.on_open_mesh)
        file_menu.addAction(open_act)
        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        view_menu = menu.addMenu("View")
        rotate_act = QAction("Rotate Mesh", self)
        rotate_act.triggered.connect(self.on_rotate_mesh)
        view_menu.addAction(rotate_act)

        self.bound_action = QAction("Toggle Bounds", self, checkable=True)
        self.bound_action.triggered.connect(self.on_toggle_bounds)
        view_menu.addAction(self.bound_action)

        self.grid_action = QAction("Toggle Grid", self, checkable=True)
        self.grid_action.triggered.connect(self.on_toggle_grid)
        view_menu.addAction(self.grid_action)

        help_menu = menu.addMenu("Help")
        about_act = QAction("About", self)
        about_act.triggered.connect(self.on_about)
        help_menu.addAction(about_act)

    def _require_mesh(self):
        if self.mesh is None:
            QMessageBox.warning(self, "No mesh", "Load an STL mesh first (File → Open Mesh).")
            return None
        return self.mesh

    def _run_action(self, result: AnalysisResult, *, mesh_opacity: float = 0.4) -> None:
        if result.message and result.name in {"warping", "shrinkage", "supports", "orientation"}:
            QMessageBox.information(self, result.name.replace("_", " ").title(), result.message)
        if result.secondary_title:
            show_secondary_window(
                result.secondary_title,
                result.secondary_actors,
                self.config,
                text=result.message if result.name == "warping" else "",
            )
        # Shrinkage draws its own green/red meshes; skip default mesh tint
        if result.name == "shrinkage":
            show_actors(
                self.plotter,
                None,
                self.config,
                result.actors,
                text=result.verdict,
            )
        elif result.name == "roughness":
            show_actors(
                self.plotter,
                None,
                self.config,
                result.actors,
                text=result.message,
            )
        else:
            show_actors(
                self.plotter,
                self.mesh,
                self.config,
                result.actors,
                mesh_opacity=mesh_opacity,
                mesh_color="white" if result.name == "toppling" else "steelblue",
                text=result.message,
            )

    def _open_mesh_dialog(self) -> bool:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open STL mesh",
            "",
            "STL Files (*.stl);;All Files (*)",
        )
        if not path:
            return False
        return self._load_path(path)

    def _load_path(self, path: str) -> bool:
        try:
            mesh = load_mesh(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Load error", str(exc))
            return False

        printer = self.config.printer
        mesh = center_on_bed(mesh, printer.bed_width, printer.bed_length, inplace=True)
        self.mesh = mesh
        self.mesh_file_path = path

        if not is_likely_watertight(mesh):
            QMessageBox.warning(
                self,
                "Mesh warning",
                "This mesh may not be watertight. Volume-based COM and shrinkage "
                "estimates can be unreliable. Prefer closed manifold STLs.",
            )
        return True

    def on_open_mesh(self) -> None:
        if self._open_mesh_dialog():
            reset_scene(self.plotter, self.mesh, self.config)

    def on_warping_analysis(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_warping(mesh, self.config), mesh_opacity=0.85)

    def on_small_details(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_small_details(mesh, self.config))

    def on_toppling(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_toppling(mesh, self.config), mesh_opacity=0.9)

    def on_roughness(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_roughness(mesh, self.config))

    def on_shrinkage(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_shrinkage(mesh, self.config))

    def on_overhangs(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_overhangs(mesh, self.config))

    def on_supports(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_supports(mesh, self.config), mesh_opacity=0.35)

    def on_orientation(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        QMessageBox.information(
            self,
            "Orientation search",
            "Searching discrete poses (may take a few seconds)…",
        )
        result = actions.action_orientation(mesh, self.config)
        if result.actors and isinstance(result.actors[0].mesh, pv.PolyData):
            self.mesh = result.actors[0].mesh
        self._run_action(result, mesh_opacity=0.85)

    def on_center_of_mass(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        self._run_action(actions.action_center_of_mass(mesh, self.config))

    def on_vectors(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        QMessageBox.information(
            self,
            "Normals",
            "Face normals open in a separate window. Close it to return.",
        )
        reset_scene(self.plotter, mesh, self.config, opacity=0.9)
        mesh.plot_normals(mag=max(self.config.printer.nozzle_size, 0.5), show_edges=True)

    def on_rotate_mesh(self) -> None:
        mesh = self._require_mesh()
        if mesh is None:
            return
        text, ok = QInputDialog.getText(
            self,
            "Rotate Mesh",
            "Axis and angle in degrees (e.g. x,30):",
        )
        if not ok or not text.strip():
            return
        try:
            axis, angle_s = text.split(",")
            angle = float(angle_s.strip())
            rotate_mesh(mesh, axis.strip(), angle)
            reset_scene(self.plotter, mesh, self.config)
        except ValueError:
            QMessageBox.critical(
                self,
                "Error",
                "Invalid format. Use axis,angle — e.g. x,30",
            )

    def on_toggle_bounds(self, state: bool) -> None:
        self._bounds_on = bool(state)
        if self._bounds_on:
            self.plotter.show_bounds()
        else:
            self.plotter.remove_bounds_axes()
        self.plotter.update()

    def on_toggle_grid(self, state: bool) -> None:
        self._grid_on = bool(state)
        if self._grid_on:
            self.plotter.show_grid()
        else:
            try:
                self.plotter.remove_bounding_box()
            except Exception:
                pass
            self.plotter.update()

    def on_about(self) -> None:
        QMessageBox.information(
            self,
            "About Tesselater",
            "Tesselater 2.1 — geometric FDM printability + support scoring.\n"
            "Docs: README.md and Explanations.txt\n"
            "https://github.com/GMHadou/Tesselater",
        )


def run_app(config: AppConfig = DEFAULT_CONFIG) -> int:
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(config=config)
    if window.mesh is None:
        return 1
    window.show()
    return app.exec_()

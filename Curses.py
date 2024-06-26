import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMessageBox, QVBoxLayout, QWidget, QInputDialog, QFileDialog
import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np
import mesh_loader  # Import the mesh_loader module
from variables import Microstepping,bed_width,bed_length
p=pv.Plotter()

# Define rotation function
def rotate_mesh(mesh, axis, angle_degrees):
    if axis == 'x':
        mesh.rotate_x(angle_degrees, inplace=True)
    elif axis == 'y':
        mesh.rotate_y(angle_degrees, inplace=True)
    elif axis == 'z':
        mesh.rotate_z(angle_degrees, inplace=True)
    min_z = mesh.bounds[4]
    mesh.points[:, 2] -= min_z

# Define shifting function
def shift(mesh):
    mesh_center = mesh.center
    shift_x = mesh_center[0] - (bed_width / 2)
    shift_y = mesh_center[1] - (bed_length / 2)
    shift_z = -mesh.bounds[4]  # shift towards the lowest position of the mesh

    shift_p = [shift_x, shift_y, shift_z]

    shifted_plane = pv.Plane(i_size=bed_width, j_size=bed_length, i_resolution=10, j_resolution=10)
    shifted_plane.translate(shift_p)
    shifted_plane.translate([-bed_width/2, -bed_length/2, 0])

    min_z_mesh = mesh.points[:, 2].min()
    min_z_plane = shifted_plane.points[:, 2].min()
    z_increment = (min_z_plane - min_z_mesh)

    if z_increment > 0:
        mesh.points[:, 2] += z_increment

    return shifted_plane

# Define utility functions
def calculate_flow(Temperature):
    if Temperature <= 210:
        return 10
    elif 210 < Temperature < 250:
        return 12.5
    else:
        return 15

def calculate_center_of_mass(mesh):
    vertices = mesh.points
    total_mass = len(vertices)
    weighted_sum = np.sum(vertices, axis=0)
    center_of_mass = weighted_sum / total_mass
    return center_of_mass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tesselater")
        self.setGeometry(100, 100, 800, 600)
        self.mesh_file_path = None
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.plotter = QtInteractor(central_widget)
        layout.addWidget(self.plotter.interactor)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Plotting:")
        
        # Dictionary to hold actions and corresponding methods
        actions = {
            "Warping analysis": self.on_warping_analysis,
            "Small Details": self.on_small_details,
            "Toppling": self.on_toppling,
            "Roughness": self.on_roughness,
            "Shrinkage": self.on_shrinkage,
            "Overhangs": self.on_overhangs,
            "Center of Mass": self.on_center_of_mass,
            "Vectors": self.on_vectors,
            "Exit": self.on_exit
        }

        for action_name, method in actions.items():
            action = QAction(action_name, self)
            action.triggered.connect(method)
            file_menu.addAction(action)

        view_menu = menu_bar.addMenu("View")
        rotate_action = QAction("Rotate Mesh", self)
        rotate_action.triggered.connect(self.on_rotate_mesh)
        view_menu.addAction(rotate_action)

        bound_action = QAction("Toggle Bounds", self, checkable=True)
        bound_action.triggered.connect(self.on_toggle_bounds)
        view_menu.addAction(bound_action)

        grid_action = QAction("Toggle Grid", self, checkable=True)
        grid_action.triggered.connect(self.on_toggle_grid)
        view_menu.addAction(grid_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)


        # Call the method to open file dialog and load mesh
        self.open_file_dialog()
        
        # Load mesh from the file path if selected
        if self.mesh_file_path:
            mesh_loader.load_mesh(self.mesh_file_path)  # Use mesh_loader to load the mesh

        self.plotter.add_mesh(pv.Plane(), color='white')

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("STL Files (*.stl)")
        if file_dialog.exec_() == QFileDialog.Accepted:
            self.mesh_file_path = file_dialog.selectedFiles()[0]
        else:
            sys.exit()

    def on_warping_analysis(self):
        from variables import Layer_Height 
        QMessageBox.information(self, "Info", "The first layer and its difference will be shown in a different page,in the main will be show the original Base")
        self.plotter.clear()
        shifted_plane = shift(mesh_loader.get_mesh())
        self.plotter.add_mesh(shifted_plane, color='grey')

    # Read the content of warping.py
        with open('warping.py', 'r') as file:
                warping_code = file.read()
    
        exec_context = {
            'Layer_Height': Layer_Height,
        # Include other necessary variables and imports here
    }

    # Execute the content of warping.py with the context
        exec(warping_code, exec_context)

    def on_small_details(self):
        QMessageBox.information(self, "Info", "For in-depth analysis, the opacity is changed")
        self.plotter.clear()
        shifted_plane = shift(mesh_loader.get_mesh())
        sizes = mesh_loader.get_mesh().compute_cell_sizes()
        areas = sizes['Area']
        Minimal_area = 0.4 * Microstepping
        filtered_cells = np.where(areas < Minimal_area)
        thin_cells = mesh_loader.get_mesh().extract_cells(filtered_cells)
        self.plotter.add_mesh(mesh_loader.get_mesh(), color='blue', opacity=0.5)
        self.plotter.add_mesh(thin_cells, color='red')
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_toppling(self):
        from Toppling import text,result
        QMessageBox.information(self, "Will it Topple?", text)
        self.plotter.clear()
        shifted_plane = shift(mesh_loader.get_mesh())
        self.plotter.add_mesh(mesh_loader.get_mesh(), color='blue',opacity=0.5)
        with open('Toppling.py', 'r') as file:
                warping_code = file.read()

        exec_context = {
            'result': result,
        # Include other necessary variables and imports here
    }
    # Execute the content of warping.py with the context
        exec(warping_code,exec_context)
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_roughness(self):
        self.plotter.clear()
        shifted_plane = shift(mesh_loader.get_mesh())
        from Roughness import calculate_and_visualize_surface_roughness
        calculate_and_visualize_surface_roughness(mesh_loader.get_mesh(), build_direction=[0, 0, 1], smooth_color="lightblue", rough_color="purple")
        self.plotter.add_mesh(mesh_loader.get_mesh())
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_shrinkage(self):
        QMessageBox.information(self, "Info", "Expected maximum shrinkage of a piece, The original is the green mesh")
        self.plotter.clear()
        shifted_plane = shift(mesh_loader.get_mesh())
        from Shrinkage import shrinked_mesh
        self.plotter.add_mesh(mesh_loader.get_mesh(), color='green', opacity=0.3)
        self.plotter.add_mesh(shrinked_mesh, color='red')
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_overhangs(self):
        self.plotter.clear()
        from vx import overhang_cells
        shifted_plane = shift(mesh_loader.get_mesh())
        self.plotter.add_mesh(overhang_cells, color='red')
        self.plotter.add_mesh(mesh_loader.get_mesh(), color='blue',opacity=0.4)
        overhang_cells.translate(mesh_loader.get_mesh().center)
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_center_of_mass(self):
        self.plotter.clear()
        shifted_plane = shift(mesh_loader.get_mesh())
        com = calculate_center_of_mass(mesh_loader.get_mesh())
        com_point = pv.PolyData(com.reshape(1, -1))
        self.plotter.add_mesh(com_point, color="red", point_size=10)
        self.plotter.add_mesh(mesh_loader.get_mesh(), color='blue', opacity=0.5)
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_vectors(self):
        QMessageBox.information(self, "Info", "The vectors will be shown in another screen, to return simply close the new window")
        self.plotter.clear()
        shifted_plane = shift(mesh_loader.get_mesh())
        self.plotter.add_mesh(mesh_loader.get_mesh(), color='blue')
        self.plotter.add_mesh(shifted_plane, color='grey')
        mesh_loader.get_mesh().plot_normals(mag=1, show_edges=True)

    def on_rotate_mesh(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Rotate Mesh")
        dialog.setLabelText("Enter the axis and angle for rotation (e.g. x,30):")
        dialog.setOkButtonText("Rotate")
        dialog.setCancelButtonText("Cancel")
        dialog.setInputMode(QInputDialog.TextInput)
        if dialog.exec_() == QInputDialog.Accepted:
            text = dialog.textValue()
            try:
                axis, angle_degrees = text.split(",")
                angle_degrees = float(angle_degrees)
                rotate_mesh(mesh_loader.get_mesh(), axis, angle_degrees)
            except ValueError as e:
                QMessageBox.critical(self, "Error", "Invalid input format. Please enter the axis and angle in the correct format (e.g. x,30).")

    def on_toggle_bounds(self, state):
        if state:
            self.plotter.show_bounds()
        else:
            self.plotter.remove_bounds_axes()

    def on_toggle_grid(self, state):
        if state:
            self.plotter.show_grid()
        

    def on_exit(self):
        self.close()

    def on_about(self):
        QMessageBox.information(self, "Documentation", "Check the page on GitHub")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())


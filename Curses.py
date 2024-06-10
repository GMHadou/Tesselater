import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMessageBox, QVBoxLayout, QWidget
import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np

mesh = pv.read("Files\Blade.stl")


def shift():
    mesh_center = mesh.center
    bed_width = 300.0  # in millimeters
    bed_length = 300.0  # in millimeters

# Print bed plane departs from mesh center
# Bounds 0 to 1 is x,2 to 3 is y,4 to 5 is z

# Calculate the shift required to center the grid on the mesh
    shift_x = mesh_center[0] - (bed_width / 2)
    shift_y = mesh_center[1] - (bed_length / 2)
    shift_z = -mesh.bounds[4]  # shift towards the lowest position of the mesh
# You could also, instead of shifting, create the plane with reference from the center point of the mesh as the origin
    shift_p= [shift_x, shift_y, shift_z]  # No shift along z axis    
    # Create the plane
    shifted_plane = pv.Plane(i_size=bed_width, j_size=bed_length, i_resolution=10, j_resolution=10)
    shifted_plane.translate(shift_p)
    # Resize the plane to match the bed dimensions


    
    # Resize the plane to always be bigger than the mesh

           # Add the translated plane to the plotter

    min_z_mesh = mesh.points[:, 2].min()

# Find the lowest Z-coordinate of the plane
    min_z_plane = shifted_plane.points[:, 2].min()

# Calculate the z_increment to align the mesh with the plane and elevate it to the power of 15
    z_increment = (min_z_plane - min_z_mesh)

# If z_increment is positive, it means the mesh needs to be raised to align with the plane
    if z_increment > 0:
    # Translate the mesh along the Z-axis by z_increment
        mesh.points[:, 2] += z_increment

    return shifted_plane

 

# Create the structured grid


# Define the dimensions of the print bed


# Create the structured grid
Bed_Temp = 50
Temperature = 195
initial_temp = 210
Fluid_Fase = 135


def calculate_flow():
        if Temperature <= 210:
            return 10
        elif 210 < Temperature < 250:
            return 12.5
        else:
            return 15


# Hardware package

Microstepping = 1 / 16
Nozzle_Size = 0.4
Nozzle_Flat = 0.8
Line_Width =Nozzle_Size * 1.25
Layer_Height = 0.1
Minimum = Layer_Height + Nozzle_Size
Maximum = Layer_Height + Nozzle_Flat
Ideal = (Minimum + Maximum) / 2
Speed = 80  # mm/s

   
def calculate_speed_quality():
        flow = calculate_flow()
        Max_Speed = flow / (Line_Width * Layer_Height)
        return Max_Speed * 0.7

  
def calculate_heat_warped(total_volume, CTE, Base_temp):
        return total_volume * CTE * (Temperature - Base_temp)
def calculate_center_of_mass(mesh):
    # Assuming uniform mass for each point
    uniform_mass = 1.0  # Adjust as needed
    
    # Get the vertices of the mesh
    vertices = mesh.points
    
    # Calculate the total mass and the weighted sum of positions
    total_mass = uniform_mass * len(vertices)
    weighted_sum = np.sum(vertices, axis=0) * uniform_mass
    
    # Calculate the center of mass
    center_of_mass = weighted_sum / total_mass
    
    return center_of_mass




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tesselater")
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Add PyVista render window
        self.plotter = QtInteractor(central_widget)
        layout.addWidget(self.plotter.interactor)

        # Create menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("Plotting:")

        option1_action = QAction("Warping analysis", self)
        option1_action.triggered.connect(self.on_option1)
        file_menu.addAction(option1_action)

        option2_action = QAction("Small Details", self)
        option2_action.triggered.connect(self.on_option2)

        file_menu.addAction(option2_action)

        option3_action = QAction("Toppling", self)
        option3_action.triggered.connect(self.on_option3)
        file_menu.addAction(option3_action)

        option4_action = QAction("Roughness", self)
        option4_action.triggered.connect(self.on_option4)
        file_menu.addAction(option4_action)

        option5_action = QAction("Shrinkage", self)
        option5_action.triggered.connect(self.on_option5)
        file_menu.addAction(option5_action)

        option6_action = QAction("Overhangs", self)
        option6_action.triggered.connect(self.on_option6)
        file_menu.addAction(option6_action)

        option7_action = QAction("Center of Mass", self)
        option7_action.triggered.connect(self.on_option7)
        file_menu.addAction(option7_action)

        option8_action = QAction("Vectors", self)
        option8_action.triggered.connect(self.on_option8)
        file_menu.addAction(option8_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.on_exit)
        file_menu.addAction(exit_action)

        # View menu
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

        # Help menu
        help_menu = menu_bar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)


        # Initialize PyVista plotter with a default plane mesh
        self.plotter.add_mesh(pv.Plane(), color='white')


 
    def on_option1(self):
        QMessageBox.information(self, "Info", "You selected Option 1")
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        import warping
        self.plotter.add_mesh(shifted_plane, color='grey')
        self.plotter.add_mesh(mesh, color='red')

    def on_option2(self):
        QMessageBox.information(self, "Info", "For in depth analysis,the opacity is changed")
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        Microstepping=1/16
# Filter cells based on area
# Compute cell sizes
        sizes = mesh.compute_cell_sizes()

# Access cell areas
        areas = sizes['Area']
#Here we make a quick calculus to see the little areas that are more prone to have errors,depending on your micro-stepping and nozzle size
        Minimal_area =Nozzle_Size*Microstepping
        filtered_cells = np.where(areas < Minimal_area)


# Extract the cells with thin area
        thin_cells = mesh.extract_cells(filtered_cells)
        self.plotter.add_mesh(mesh,color='blue',opacity=0.5)
        self.plotter.add_mesh(thin_cells, color='red')
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_option3(self):
        from Toppling import text

        QMessageBox.information(self, "Will it Topple?", text)
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        self.plotter.add_mesh(mesh, color='blue')
        self.plotter.add_mesh(shifted_plane, color='grey')


    def on_option4(self):
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        from Roughness import calculate_and_visualize_surface_roughness
        calculate_and_visualize_surface_roughness(mesh, build_direction=[0, 0, 1], smooth_color="lightblue", rough_color="purple")
        self.plotter.add_mesh(mesh)
        self.plotter.add_mesh(shifted_plane, color='grey')

         # Apply shifting

        
        
    
    def on_option5(self):
        QMessageBox.information(self, "Info", "Expected maximum shrinkage of a piece,The original is the green mesh")
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        from Shrinkage import shrinked_mesh
        self.plotter.add_mesh(mesh, color='green',opacity=0.3)
        self.plotter.add_mesh(shrinked_mesh, color='red')
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_option6(self):
        # Example action: update PyVista plot
        self.plotter.clear()
        from vx import overhang_cells
        shifted_plane=shift()
        self.plotter.add_mesh(overhang_cells, color='red')
        self.plotter.add_mesh(mesh, color='blue')
        overhang_cells.translate(mesh.center)
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_option7(self):
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        com = calculate_center_of_mass(mesh)
        com_point = pv.PolyData(com.reshape(1, -1))
        self.plotter.add_mesh(com_point, color="red", point_size=10)  # Adjust point_size as needed
        
        self.plotter.add_mesh(mesh, color='blue',opacity=0.5)
        self.plotter.add_mesh(shifted_plane, color='grey')

    def on_option8(self):
        QMessageBox.information(self, "Info", "The vectors will be shown in another screen,to return simply close the new window")
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        self.plotter.add_mesh(mesh, color='blue')
        self.plotter.add_mesh(shifted_plane, color='grey')
        mesh.plot_normals(mag=1, show_edges=True)

    def on_option9(self):
        QMessageBox.information(self, "Info", "The vectors will be shown in another screen,to return simply close the new window")
        # Example action: update PyVista plot
        self.plotter.clear()
        shifted_plane=shift()
        self.plotter.add_mesh(mesh, color='blue')
        self.plotter.add_mesh(shifted_plane, color='grey') 

    def on_rotate_mesh(self):
        axis = input("Enter the rotation axis (x, y, or z): ")
        angle_degrees = float(input("Enter the rotation angle in degrees: "))
        rotate_mesh(mesh, axis, angle_degrees)
    def on_toggle_bounds(self, state):
        if state:
            self.plotter.show_bounds()
        else:
            self.plotter.remove_bounds_axes()

    def on_toggle_grid(self, state):
        if state:
            self.plotter.show_grid()
        else:
            self.plotter.clear()  # This removes all actors including grid, we will add plane again
            
            self.plotter.add_mesh(pv.Plane(), color='white')  # Re-add the default plane

    def on_exit(self):
        self.close()

    def on_about(self):
        QMessageBox.information(self, "Documentation", "Check the page on github")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())


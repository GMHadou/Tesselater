import pyvista as pv
import numpy as np
import pymeshfix as fix
import trimesh

# The stl file is chosen based on a previously generated stl file generated in the same folder
mesh = pv.read("blade.stl")

p = pv.Plotter()
#Show xyz axis
p.show_axes()
p.view_xy()

#Vizualize general bounds
p.show_bounds(location='all',
    all_edges=True,)
p.show_grid(color='black')

#It's important to check the level of degradation of your stl surface(If it's watertight or not)
# Meshfix is repaired and saved,in case something is ignored and excluded,you can choose to slice manually in the algorithm,or to change the repair parameters(see meshfix.repair documentation)
#You could also try the trimesh method for hole filling
#If nothing works,the option to check the surface before voxelizing can be deactivated writing in the parameter:(check_surface=False).If so,change the mesh1 to mesh
#Remeshing works are being searched,but ideally,the 3d printing part should be already imported as a watertight surface(Otherwise,details could be missed)
def fix(mesh):
    # Check if the mesh is watertight or manifold
    if not (mesh.is_watertight or mesh.is_manifold):
        meshfix = trimesh.repair.MeshFix(mesh)
        meshfix.repair(remove_smallest_components=True)
        # Save the repaired mesh
        meshfix.save("Part1.stl")
        mesh= pv.read("Part1.stl")
        return mesh
    else:
        # Mesh is already watertight and manifold, so no need for repairs
        return mesh

# Get the bounds of the mesh
#Bounds are the limits of the extreme points of the mesh

# Get the dimensions of the mesh
mesh_bounds = mesh.bounds
mesh_center = mesh.center

# Define the dimensions of the print bed
bed_width = 300.0  # in millimeters
bed_length = 300.0  # in millimeters
#Print bed plane departs from mesh center
#Bounds 0 to 1 is x,2 to 3 is y,4 to 5 is z

# Calculate the shift required to center the grid on the mesh
shift_x = mesh_center[0] - (bed_width / 2)
shift_y = mesh_center[1] - (bed_length / 2)
#You could also,instead of shifting,create the plane with reference from the center point of the mesh as the origin

# All the grid measurements are automatically given in milimeters
# Define the number of divisions in the X and Y directions to create uniform squares
nx = 20  # Number of divisions in X
ny = 20 # Number of divisions in Y

#Generate the array for points until extreme+1,both for x and y

#If you want to change the reference planes for the grid,change the shifting point to any you desire

#This code will have a function to rotate the axis very soon,as it's necessary for calculations
x, y = np.meshgrid(np.linspace(0,bed_width, nx + 1) + shift_x, np.linspace(0,bed_length, ny + 1) + shift_y)
#Z grid is nullified
z = np.zeros_like(x)  # Z-coordinate for the plane

# Create the structured grid
plane = pv.StructuredGrid(x, y, z)

p.add_text("X,Y or Z to rotate", font_size=24)

points = mesh.points

def rotate_mesh(mesh, axis, angle_degrees):
    if axis == 'x':
        mesh.rotate_x(angle_degrees, inplace=True)
    elif axis == 'y':
        mesh.rotate_y(angle_degrees, inplace=True)
    elif axis == 'z':
        mesh.rotate_z(angle_degrees, inplace=True)

axis = input("Enter the rotation axis (x, y, or z): ")
angle_degrees = float(input("Enter the rotation angle in degrees: "))

rotate_mesh(mesh, axis, angle_degrees)

# Find the lowest Z-coordinate of the mesh
# Find the lowest Z-coordinate of the mesh
min_z_mesh = mesh.points[:, 2].min()

# Find the lowest Z-coordinate of the plane
min_z_plane = plane.points[:, 2].min()

# Calculate the z_increment to align the mesh with the plane and elevate it to the power of 15
z_increment = (min_z_plane - min_z_mesh)

# If z_increment is positive, it means the mesh needs to be raised to align with the plane
if z_increment > 0:
    # Translate the mesh along the Z-axis by z_increment
    mesh.points[:, 2] += z_increment

      



#Wireframe allows for visualizing the grid squares
p.add_mesh(mesh)
p.add_mesh(plane, style="wireframe")

# Check if there are any points below the Z-axis

# Render and visualize the modified mesh
mesh.plot()

p.show(cpos="XZ")










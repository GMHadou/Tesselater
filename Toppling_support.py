import numpy as np
import scipy.spatial
import pyvista as pv
from warping import first_layer_faces
from vx import overhang_cells

mesh=pv.read("Blade.stl")

mesh.rotate_x(45, inplace=True)



def calculate_center_of_mass(mesh):
    # Get the vertices of the mesh
    vertices = mesh.points

    # Calculate the center of mass
    center_of_mass = np.average(vertices, axis=0)

    return center_of_mass


def check_stability(mesh: pv.PolyData) -> str:
    """
    Check the stability of a mesh.

    Args:
        mesh (pv.PolyData): The mesh to analyze.

    Returns:
        str: A stability analysis result.
    """
    points = mesh.points[:, :2]
    mesh_height = np.ptp(mesh.points[:, 2])
    center_of_mass = calculate_center_of_mass(mesh)
    radius = mesh_height * np.tan(np.radians(5))
    theta = np.linspace(0, 2 * np.pi, 100)
    circle = np.column_stack([center_of_mass[0] + radius * np.cos(theta),
                              center_of_mass[1] + radius * np.sin(theta),
                              np.zeros_like(theta)])
    circle_stable = pv.PolyData(circle)
    Support=calculate_overhang_area(overhang_cells, mesh)
    p.add_mesh(circle_stable, color="green", opacity=0.3, label="Stable Circle")

    # Compute the minimum Z-coordinate value
    # Slice the mesh to get cells within a height range of 0.01
    Base = mesh.clip(normal=[0, 0, 1], origin=[0, 0, 0.1])

    p.add_mesh(Base, color="red", opacity=1, label="Base")
    # Check if all points of the circle are inside the base
    # Calculate the range of x and y coordinates of the mesh
    x_range = np.ptp(Base.points[:, 0])
    y_range = np.ptp(Base.points[:, 1])

# Calculate the base area by multiplying the x and y ranges
    base_area = (x_range * y_range)+Support

    is_inside_base = np.all((Base.bounds[0] <= circle[:, 0]) & (circle[:, 0] <= Base.bounds[1]) &
                            (Base.bounds[2] <= circle[:, 1]) & (circle[:, 1] <= Base.bounds[3]))
    
    threshold = 9.67

    # Extract the overhang faces
   # Calculate the overhang based on face normals


# Extract the overhang cells
    
    # Calculate stability_margin2 by dividing base_area by mesh_height
    stability_margin2 = base_area / mesh_height

    

    if is_inside_base:
        return "Stability Analysis: No Toppling"
        # Check if there is a cell below each overhang face
    elif (stability_margin2 < threshold):
        if(Support==0):
            return "Stability Analysis: Stable without support"
        else:
            return "Stability Analysis: Stable with support"

    else:
        return "Very Likely to topple (if it's standing upright)"


# Plot the convex hull, mesh, and the circle
p = pv.Plotter()
text = check_stability(mesh)
p.add_mesh(mesh, color="white")
p.add_text(text, font_size=24, color='white')

# Show the plot
p.show()

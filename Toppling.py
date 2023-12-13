import numpy as np
import scipy.spatial
import pyvista as pv

mesh = pv.read("output_mesh.stl")


def calculate_center_of_mass(mesh):
    # Assuming uniform mass for each point
    uniform_mass = 1.0  # Adjust as needed
    
    # Get the vertices of the mesh
    vertices = mesh.points
    
    # Calculate the center of mass
    center_of_mass = np.average(vertices, axis=0)
    
    return center_of_mass

import numpy as np
import scipy.spatial
import pyvista as pv

import numpy as np
import scipy.spatial
import pyvista as pv

def check_stability(mesh: pv.PolyData) -> str:
    """
    Check the stability of a mesh.

    Args:
        mesh (pv.PolyData): The mesh to analyze.

    Returns:
        str: A stability analysis result.
    """
    # Extract the x and y coordinates of the mesh points
    points = mesh.points[:, :2]

    # Compute the convex hull of the points
    convex_hull = scipy.spatial.ConvexHull(points)

    # Compute the volume of the convex hull
    convex_hull_area = convex_hull.volume

    # Compute the height of the mesh
    mesh_height = np.ptp(mesh.points[:, 2])

    # Calculate the center of mass of the mesh
    center_of_mass = calculate_center_of_mass(mesh)

    # Calculate the radius of the circle that will be used to check if the center of mass is inside the convex hull
    radius = mesh_height * np.tan(np.radians(5))

    # Generate a circle with the center at the center of mass and the given radius
    theta = np.linspace(0, 2*np.pi, 100)
    circle = np.column_stack([center_of_mass[0] + radius * np.cos(theta),
                              center_of_mass[1] + radius * np.sin(theta),
                              np.zeros_like(theta)])
    circle_polydata = pv.PolyData(circle)

    # Get the equations of the planes that define the convex hull
    equations = convex_hull.equations[:, :-1]

    # Compute the barycentric coordinates of the circle points with respect to the convex hull
    bary_coords = np.dot(circle_polydata.points[:, :2] - convex_hull.points[0, :2], equations.T) + convex_hull.equations[:, -1]

    # Check if all the barycentric coordinates are less than or equal to 0, indicating that the center of mass is inside the convex hull
    is_inside = np.all(bary_coords <= 0, axis=1)

    # Compute the area of the base of the convex hull
    base_area = np.abs(np.dot(convex_hull.equations[0, :2], [center_of_mass[0], center_of_mass[1]]) + convex_hull.equations[0, -1])

    # Compute the stability margin by dividing the base area by the mesh height
    stability_margin = base_area / mesh_height

    # Set the stability threshold
    threshold = 1.75

    # Set the position of the stability analysis text
    text_position = (10, 10)  # Example: top-left corner of the window
    
    # Check if the mesh is stable with support
    if np.any(is_inside):
        text = "Stability Analysis: Stable with support"
        return text
    
    # Check if the mesh is unlikely to topple under standardized circumstances
    elif stability_margin < threshold:
        text="Toppling is unlikely (On standardized circumstances)"
        return text
    
    # Otherwise, the mesh is very likely to topple without support
    else:
        text="Very Likely to topple (no support)"
        return text


# Plot the convex hull, mesh, and the circle
p = pv.Plotter()

# Calculate cell faces
mesh.extract_surface()

# Calculate cell face normals
mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True,flip_normals=True)

# Set the threshold angle for overhang detection (in degrees)
overhang_threshold_angle = 45.0

# Calculate the overhang based on face normals
overhang_faces = np.where(mesh.cell_normals[:, 2] < np.cos(np.radians(overhang_threshold_angle)))[0]

# Extract the overhang cells
overhang_cells = mesh.extract_cells(overhang_faces)

text=check_stability(mesh)
text_position = (10, 10)  # Example: top-left corner of the window
p.add_text(text, position=text_position, font_size=12, color='white')

# Original mesh in blue
p.add_mesh(mesh, color="blue")

# Add overhang cells in red
p.add_mesh(overhang_cells, color="red")

# Show the plot
p.show()
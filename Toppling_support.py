import numpy as np
import scipy.spatial
import pyvista as pv

mesh = pv.read("output_mesh.stl")


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
    convex_hull = scipy.spatial.ConvexHull(points)
    mesh_height = np.ptp(mesh.points[:, 2])
    center_of_mass = calculate_center_of_mass(mesh)
    radius = mesh_height * np.tan(np.radians(5))
    theta = np.linspace(0, 2*np.pi, 100)
    circle = np.column_stack([center_of_mass[0] + radius * np.cos(theta),
                              center_of_mass[1] + radius * np.sin(theta),
                              np.zeros_like(theta)])
    circle_stable = pv.PolyData(circle)


    # Extract the Z-coordinate values
    z_coords = mesh.points[:, 2]

    # Compute the minimum Z-coordinate value
    min_z = np.min(z_coords)

    # Shift the mesh to start at Z=0
    mesh.points[:, 2] -= min_z

    # Find the indices of the cells at Z=0 (first layer)
    z0_cell_indices = np.where(mesh.cell_centers().points[:, 2] == 0)[0]

    # Extract the faces of the first layer
    first_layer_faces = mesh.extract_cells(z0_cell_indices)

    # Extract feature edges from the first layer faces
    edges = first_layer_faces.extract_feature_edges(90)

    # Create a polygon based on the base edges
    base_polygon = pv.PolyData()

    # Add points and cells to the base_polygon
    base_polygon.points = edges.points
    base_polygon.lines = edges.lines

    base_vertices = mesh.points[mesh.points[:, 2] == 0, :2]
    p.add_mesh(circle_stable, color="red", opacity=0.8, line_width=5)
    p.add_mesh(base_polygon, color="green", line_width=5, opacity=0.8)  # Add base polygon for visualization
    # Check if all points of the circle are inside the base polygon
    is_inside_base = np.all(scipy.spatial.ConvexHull(base_vertices).equations[:, :-1] @ circle_stable.points[:, :2].T <= 0, axis=0)

    base_area = np.abs(np.dot(convex_hull.equations[0, :2], [center_of_mass[0], center_of_mass[1]]) + convex_hull.equations[0, -1])
    stability_margin = base_area / mesh_height
    threshold = 9.67

    if np.any(is_inside_base):
        return "Stability Analysis: Stable with support"
    elif stability_margin < threshold:
        return "Toppling is unlikely (On standardized circumstances)"
    else:
        return "Very Likely to topple (if there's no support or it's standing upright)"


# Plot the convex hull, mesh, and the circle
p = pv.Plotter()
text = check_stability(mesh)

p.add_mesh(mesh, color="white")
p.add_text(text, font_size=24, color='white')

# Show the plot
p.show()

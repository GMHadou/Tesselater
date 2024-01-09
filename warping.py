import pyvista as pv
import numpy as np
import scipy.spatial 

# Load the mesh
mesh = pv.read("output_mesh.stl")
p=pv.Plotter()

# Extract the Z-coordinate values
z_coords = mesh.points[:, 2]

    # Compute the minimum Z-coordinate value
min_z = np.min(z_coords)

    # Shift the mesh to start at Z=0
mesh.points[:, 2] -= min_z

    # Extract the x and y coordinates of the mesh points
points = mesh.points[:, :2]

    # Compute the convex hull of the points
convex_hull = scipy.spatial.ConvexHull(points)

    # Add a zero Z-coordinate to the convex hull points
convex_hull_points = np.column_stack([convex_hull.points, np.zeros(convex_hull.points.shape[0])])

# Find the indices of the cells at Z=0 (first layer)
z0_cell_indices = np.where(mesh.cell_centers().points[:, 2] == 0)[0]

    # Extract the faces of the first layer
first_layer_faces = mesh.extract_cells(z0_cell_indices)

edges = first_layer_faces.extract_feature_edges(90)

def analyse_corners(mesh: pv.PolyData) -> bool:

    # Assuming you have the edges variable defined somewhere
    edges = mesh.extract_feature_edges()

    # Get the vertices of the edges
    edge_vertices = edges.points

    # Ensure the length is even
    if len(edge_vertices) % 2 != 0:
        edge_vertices = edge_vertices[:-1]

    # Create vectors for each edge
    edge_vectors = [edge_vertices[i + 1] - edge_vertices[i] for i in range(0, len(edge_vertices), 2)]

    # Normalize the vectors
    edge_vectors = [v / np.linalg.norm(v) for v in edge_vectors]

    # Calculate angles between adjacent vectors using cross product
    angles = []
    for i in range(len(edge_vectors) - 1):
        angle = np.degrees(np.arccos(np.dot(edge_vectors[i], edge_vectors[i + 1])))
        cross_product = np.cross(edge_vectors[i], edge_vectors[i + 1])
        if cross_product[2] < 0:
            angle = 360 - angle
        angles.append(angle)

    # Check if any angle is greater than a threshold
    spiked_count = sum(angle > 90 for angle in angles)

    if spiked_count >= 2:
        p.add_text(f"Brim Recommended(At least two vertices have spiked corners)", font_size=16, color='red',position='lower_edge')
    else:
        p.add_text("Geometrically Safe", font_size=24, color='green',position='lower_edge')



def check_mesh_stability(mesh):
    
    max_edge_length = np.max(edges.length)

    if len(first_layer_faces.points) == 0:
        p.add_text("Very Safe(First Layer is very small for warping)", font_size=24, color='blue',position='lower_edge')
    else:
        p.add_mesh(first_layer_faces,show_edges=True, color="blue", opacity=0.8, label="First Layer Faces")
        p.add_mesh(edges, color="red", opacity=0.8,line_width=5)
        if np.any(max_edge_length > 85):
            p.add_text("Possibly needs Brim(Max Edge Length > 85)",color='black',font_size=18,position='lower_edge')
    # Plot the faces of the first layer
    # Check if the first layer mesh exists
        else:
            analyse_corners(mesh)
        

    # Set up the plotter
    
    p.camera_position = "xy"
     
    p.add_text("Bottom Layer(Press 'c' to show Convex Hull)", font_size=24, color='black')


    p.set_background("white")
    p.show_grid()
    p.show_axes()
   # Add a trigger event to press 'c' for the convex hull to be shown
    p.add_key_event("c", lambda: p.add_mesh(pv.PolyData(convex_hull_points), color="yellow", opacity=0.3, label="Convex Hull"))

    # Show the plot
    p.show()

# Example usage:
# Replace "your_mesh_file.stl" with the actual path to your mesh file
check_mesh_stability(mesh)












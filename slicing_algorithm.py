import numpy as np
import pyvista as pv

# Example: assuming you have 'mesh' as your PolyData
mesh = pv.read("output_mesh.stl")

# Extract the Z-coordinate values
z_coords = mesh.points[:, 2]

    # Compute the minimum Z-coordinate value
min_z = np.min(z_coords)

    # Shift the mesh to start at Z=0
mesh.points[:, 2] -= min_z

    # Extract the x and y coordinates of the mesh points
points = mesh.points[:, :2]
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

# Plot the base polygon
p = pv.Plotter()
p.add_mesh(mesh, color="blue")
p.add_mesh(base_polygon, color="red", line_width=5)
p.show()

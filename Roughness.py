import pyvista as pv
import numpy as np

def calculate_layer_thickness(mesh: pv.PolyData) -> float:
    """
    Calculate the layer thickness of a mesh.

    Args:
        mesh (pv.PolyData): The input mesh for which to calculate layer thickness.

    Returns:
        float: The calculated layer thickness (h).
    """
    # Assuming that layer thickness is the distance between Z coordinates of consecutive layers
    z_coords = mesh.points[:, 2]
    unique_z = np.unique(z_coords)
    unique_z.sort()  # Sort the unique Z coordinates in ascending order
    if len(unique_z) > 1:
        # Calculate the differences between consecutive Z coordinates
        layer_differences = np.diff(unique_z)
        # Return the average layer thickness
        h = np.mean(layer_differences)
    else:
        # If there's only one layer, thickness cannot be calculated
        raise ValueError("Mesh does not have multiple layers to calculate thickness.")
    
    return h

def calculate_ra(h, theta, theta_sup=45):
    # Initialize an array for the result
    ra = np.zeros_like(theta)

    # Apply conditions array-wise
    ra[theta < 20] = h * (112.6 + 4.7 * theta[theta < 20])
    ra[(20 <= theta) & (theta < theta_sup)] = 70.8 * (h / np.sin(np.radians(theta[(20 <= theta) & (theta < theta_sup)])))
    ra[(theta_sup <= theta) & (theta <= 160)] = 85.0 * (h / np.sin(np.radians(theta[(theta_sup <= theta) & (theta <= 160)])))
    ra[theta > 160] = h * (248.5 - 5.7 * (theta[theta > 160] - 160))

    return ra

def calculate_surface_roughness(normals, thickness, O_sup):
    angles = np.degrees(np.arccos(normals[:, 2]))

    # Initialize roughness array
    surface_roughness = np.zeros_like(angles)

    # Calculate roughness based on angle ranges
    mask1 = angles < O_sup
    surface_roughness[mask1] = thickness[mask1] * (112.6 + 4.7 * angles[mask1])

    mask2 = (O_sup <= angles) & (angles < 20)
    surface_roughness[mask2] = 70.8 * thickness[mask2] / np.sin(np.radians(angles[mask2]))

    mask3 = (20 <= angles) & (angles <= 160)
    surface_roughness[mask3] = 85.0 * thickness[mask3] / np.sin(np.radians(angles[mask3]))

    mask4 = (160 < angles) & (angles <= 180)
    surface_roughness[mask4] = thickness[mask4] * (248.5 - 5.7 * (angles[mask4] - 160))

    return surface_roughness

def highlight_high_roughness(mesh, Ra_max, surface_roughness, preference="cell"):
    # Create a copy of the mesh
    Ra_max = 100

    mesh_high_roughness = mesh.copy()

    # Check if surface_roughness is associated with cells or points
    if preference == "cell":
        # Set the cell arrays to the surface roughness values
        import vtkmodules.util.numpy_support as numpy_support
        mesh_high_roughness.GetCellData().SetScalars(numpy_support.numpy_to_vtk(surface_roughness))

        # Threshold the surface roughness to get cells with high roughness
        high_roughness_mask = surface_roughness > Ra_max
        mesh_high_roughness = mesh_high_roughness.extract_cells(high_roughness_mask)
    else:
        # Set the point arrays to the surface roughness values
        mesh_high_roughness.point_arrays["SurfaceRoughness"] = surface_roughness

        # Threshold the surface roughness to get points with low roughness
        high_roughness_mask = surface_roughness > Ra_max
        mesh_high_roughness = mesh_high_roughness.threshold(Ra_max, scalars="SurfaceRoughness", invert=True, inplace=False)

    return mesh_high_roughness

mesh = pv.read("Soldering_Fingers.stl")
O_sup = 45  # The threshold for the support inclination

# Calculate the angle of each facet with respect to the z-axis
cell_normals = mesh.cell_normals
theta = np.arccos(cell_normals[:, 2])  # z component of the normals
theta = np.degrees(theta)  # Convert from radians to degrees

# Calculate layer thickness
h = calculate_layer_thickness(mesh)

# Calculate Ra values based on the provided formula
ra = calculate_ra(h, theta)

# Calculate cell normals and area (considering cells are planar facets)
mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True)
cell_normals = mesh.cell_normals
cell_area = mesh.compute_cell_sizes(length=False, area=True, volume=False)["Area"]

# Calculate surface roughness for each facet
surface_roughness = calculate_surface_roughness(cell_normals, cell_area, O_sup)

# Highlight facets with high surface roughness
mesh_high_roughness = highlight_high_roughness(mesh, ra, surface_roughness, preference="cell")

# Plot the original mesh in gray and the highlighted mesh in viridis colormap
p = pv.Plotter()
p.add_mesh(mesh, color="gray")
p.add_mesh(mesh_high_roughness, cmap="magma")
p.show()

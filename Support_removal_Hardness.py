import pyvista as pv
import numpy as np

def measure_overhang_density(mesh, obb_tree, threshold_angle):
    """Measure the density of overhang cells in the mesh using an OBB tree."""
    # Calculate overhang cells
    mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True, flip_normals=True)
    overhang_faces = np.where(mesh.cell_normals[:, 2] < np.cos(np.radians(threshold_angle)))[0]
    overhang_cells = mesh.extract_cells(overhang_faces)

    # Initialize an array to store the density of overhang cells in each OBB
    obb_density = np.zeros(obb_tree.n_blocks)

    # Iterate over each block in the OBB tree
    for i in range(obb_tree.n_blocks):
        block = obb_tree.GetBlock(i)
        obb = block.GetBounds()
        obb_overhang_cells = overhang_cells.select_enclosed_points(obb)
        obb_density[i] = obb_overhang_cells.n_cells / obb_overhang_cells.n_points if obb_overhang_cells.n_points > 0 else 0

    return obb_density

# Load the mesh
mesh = pv.read("Output_mesh.stl")

# Construct the OBB tree
obb_tree = pv.OBBTree(mesh)

# Parameters
threshold_angle = 45.0  # Adjust as needed

# Measure overhang density
overhang_density = measure_overhang_density(mesh, obb_tree, threshold_angle)

# Print or visualize the density distribution
print("Max overhang density:", np.max(overhang_density))
print("Min overhang density:", np.min(overhang_density))










import pyvista as pv
import numpy as np
from mesh_loader import get_mesh

mesh = get_mesh()

# Calculate cell faces
mesh.extract_surface()

# Calculate cell face normals
mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True, flip_normals=False)

# Set the threshold angle for overhang detection (in degrees), that depends on the printer in question (so mine, for instance, will be 59)
# If you're having problems with this, just see the recommended parameters in Cura Slicer
overhang_threshold_angle = 135.0

# Calculate the overhang based on face normals
overhang_faces = np.where(mesh.cell_normals[:, 2] < np.cos(np.radians(overhang_threshold_angle)))[0]

# Extract the overhang cells
overhang_cells = mesh.extract_cells(overhang_faces)

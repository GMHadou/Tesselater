import numpy as np
import pyvista as pv
from matplotlib.colors import to_rgb

def calculate_and_visualize_surface_roughness(mesh, build_direction=[0, 0, 1], smooth_color="lightblue", rough_color="purple"):
    # Calculate face normals
    mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True)
    face_normals = mesh.cell_normals

    # Initialize color array
    colors = np.zeros((mesh.n_cells, 3))

    # Loop through each face to perform the necessary calculations
    for j in range(mesh.n_cells):
        normal = face_normals[j, :]
        angle = np.degrees(np.arccos(np.dot(normal, build_direction) / (np.linalg.norm(normal) * np.linalg.norm(build_direction))))

        # Determine color based on the angle
        if (135 < angle < 178) or (2 < angle < 45):
            colors[j, :] = to_rgb(rough_color)
        else:
            colors[j, :] = to_rgb(smooth_color)

    # Add color array to mesh
    mesh.cell_data["SurfaceRoughness"] = colors

    # Plot the mesh with colored faces
    p = pv.Plotter()
    p.add_mesh(mesh, scalars="SurfaceRoughness", cmap="viridis")
    p.show()

# Example usage with a PyVista mesh
mesh = pv.read("Soldering_Fingers.stl")
calculate_and_visualize_surface_roughness(mesh)


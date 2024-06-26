import pyvista as pv
import numpy as np

def plot_3d_mesh(vertices, triangles, defects=[]):
    plotter = pv.Plotter()
    mesh = pv.PolyData(vertices, triangles)

    # Plot the mesh
    plotter.add_mesh(mesh, color='grey', opacity=0.5, edge_color='k')

    # Highlight defects in red
    if defects:
        defect_triangles = np.array(defects)
        defect_mesh = pv.PolyData(vertices, defect_triangles.flatten())
        plotter.add_mesh(defect_mesh, color='red', opacity=0.7, line_width=1, representation='wireframe')

    # Show the plot
    plotter.show()

def find_defects(stl_filename, threshold=1e-5):
    mesh = pv.read(stl_filename)
    vertices = mesh.points
    triangles = mesh.faces.reshape((-1, 4))[:, 1:]

    # Find defects (non-watertight triangles)
    defects = []
    for i, triangle in enumerate(triangles):
        normal = np.cross(vertices[triangle[1]] - vertices[triangle[0]], vertices[triangle[2]] - vertices[triangle[0]])
        area = np.linalg.norm(normal) / 2.0
        if area < threshold:
            defects.append(triangle)

    return vertices, triangles, defects

if __name__ == "__main__":
    stl_filename = "output_mesh.stl"
    vertices, triangles, defects = find_defects(stl_filename)
    plot_3d_mesh(vertices, triangles, defects)

import pyvista as pv

# Initialize the mesh variable
mesh = None

def load_mesh(file_path):
    global mesh
    mesh = pv.read(file_path)

def get_mesh():
    return mesh

import pyvista as pv
import numpy as np
from scipy.spatial import cKDTree
from vx import overhang_cells,mesh

# Load the mesh
p = pv.Plotter()
#This code is an example on how to use the main functions of events in pyvista
def show_largest_connected_overhang():
    # Find the largest connected overhang cell
    largest_connected_mesh = overhang_cells.connectivity('largest')

    # Plot the largest connected overhang cells
    p.add_mesh(mesh, color="blue")
    p.add_mesh(largest_connected_mesh, color="yellow")
    p.add_text("Largest Connected Support Area", font_size=24)

    # Show the plotter
    p.show()

# Bind the event trigger function to the plotter
p.add_key_event("l", show_largest_connected_overhang)

# Show the plotter
p.show()









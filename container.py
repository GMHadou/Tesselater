import pyvista as pv
from pyvista import examples

plotter = pv.Plotter()
plotter.add_mesh(pv.Sphere(), smooth_shading=True)
plotter.show_bounds(location='all')
plotter.show()
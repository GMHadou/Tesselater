import pyvista as pv
from pyvista import examples

mesh = examples.download_cow()
mesh.points /= 1.5  # scale the mesh

camera = pv.Camera()
camera.position = (30.0, 30.0, 30.0)
camera.focal_point = (5.0, 5.0, 5.0)

axes = pv.Axes(show_actor=True, actor_scale=2.0, line_width=5)
axes.origin = (3.0, 3.0, 3.0)

p = pv.Plotter()

p.add_text("X-Axis Rotation", font_size=24)
p.add_actor(axes.actor)
p.camera = camera

for i in range(6):
    rot = mesh.rotate_x(60 * i, point=axes.origin, inplace=False)
    p.add_mesh(rot)

p.show()


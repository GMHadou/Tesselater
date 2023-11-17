import numpy as np
import scipy.spatial
import pyvista as pv
from main import calculate_center_of_mass, mesh

# Extract x and y coordinates from mesh points
points = mesh.points[:, :2]

# Compute convex hull of the base points
convex_hull = scipy.spatial.ConvexHull(points)

# Calculate the height of the mesh
mesh_height = np.max(mesh.points[:, 2]) - np.min(mesh.points[:, 2])

# Calculate the center of mass of the mesh
center_of_mass = calculate_center_of_mass(mesh)

# Calculate the radius based on the height and tangent of 5 degrees
radius = mesh_height * np.tan(np.radians(5))

# Create a circle in the xy-plane at the center of mass with the calculated radius
theta = np.linspace(0, 2*np.pi, 100)
x = center_of_mass[0] + radius * np.cos(theta)
y = center_of_mass[1] + radius * np.sin(theta)
z = np.zeros_like(x)

circle = pv.PolyData(np.column_stack([x, y, z]))

# Check if the circle is inside the convex hull
equations = convex_hull.equations[:, :-1]
bary_coords = (circle.points[:, :2] - convex_hull.points[0, :2]).dot(equations.T) + convex_hull.equations[:, -1]

# Check if any points of the circle are inside the convex hull
is_inside = np.all(bary_coords <= 0, axis=1)

# Check if any points of the circle are inside the convex hull
if np.any(is_inside):
    print("Stable with support")
else:
    print("Likely to topple (no support)")

# Plot the convex hull, mesh, and the circle
p = pv.Plotter()
p.add_mesh(mesh, color="blue", opacity=0.5)
p.add_mesh(pv.PolyData(np.column_stack([convex_hull.points, np.zeros(convex_hull.points.shape[0])])), color="green", opacity=0.3)
p.add_mesh(circle, color="red", opacity=0.3)
p.show()

import pyvista as pv
import numpy as np
import scipy.spatial 


mesh=pv.read("Output_mesh.stl")
p=pv.Plotter()
#Some Data of your printer will help calculate increased chance of geometrical warping
Nozzle_Size = 0.4
Nozzle_Flat = 0.8
Line_Width = Nozzle_Size * 1.25
Layer_Height = 0.1
Minimum = Layer_Height + Nozzle_Size
Maximum = Layer_Height + Nozzle_Flat
Ideal = (Minimum + Maximum) / 2
Speed=80#mm/s

if Line_Width < Minimum or Line_Width > Maximum:
    text2 = f"Recommended to change Layer Width to {Ideal}"

Temperature = 195

#Flow is the speed of ejection of material,given in mm^3/s
if Temperature <= 210:
    Flow = 10
elif 210<Temperature<250:
    Flow = 12.5
else:
    Flow = 15

Max_Speed = Flow / (Line_Width * Layer_Height)
Speed_Quality = Max_Speed * 0.7

mesh_height = np.ptp(mesh.points[:, 2])

Base = mesh.clip(normal=[0, 0, 1], origin=[0, 0, 0.1])

x_range = np.ptp(Base.points[:, 0])
y_range = np.ptp(Base.points[:, 1])

# Calculate the base area by multiplying the x and y ranges
base_area = (x_range * y_range)

stability_margin2 = base_area / mesh_height

threshold = 9.67
#A Biased number that gives an empirical estimation of warping increased possibility based on these variables
Warping_Tendency= abs(((Speed)*Layer_Height/(Line_Width))-(Speed_Quality)*Layer_Height/(Ideal))

# Extract the Z-coordinate values
z_coords = mesh.points[:, 2]

    # Compute the minimum Z-coordinate value
min_z = np.min(z_coords)


    # Extract the x and y coordinates of the mesh points
points = mesh.points[:, :2]

    # Compute the convex hull of the points
convex_hull = scipy.spatial.ConvexHull(points)

    # Add a zero Z-coordinate to the convex hull points
convex_hull_points = np.column_stack([convex_hull.points, np.zeros(convex_hull.points.shape[0])])

# Find the indices of the cells at Z=0 (first layer)
z0_cell_indices = np.where(mesh.cell_centers().points[:, 2] == 0)[0]

    # Extract the faces of the first layer
first_layer_faces = mesh.clip(normal=[0, 0, 1], origin=[0, 0, 0.1])

edges = first_layer_faces.extract_feature_edges(90)

def analyse_corners(mesh: pv.PolyData) -> bool:

    # Assuming you have the edges variable defined somewhere
    edges = mesh.extract_feature_edges()

    # Get the vertices of the edges
    edge_vertices = edges.points

    # Ensure the length is even
    if len(edge_vertices) % 2 != 0:
        edge_vertices = edge_vertices[:-1]

    # Create vectors for each edge
    edge_vectors = [edge_vertices[i + 1] - edge_vertices[i] for i in range(0, len(edge_vertices), 2)]

    # Normalize the vectors
    edge_vectors = [v / np.linalg.norm(v) for v in edge_vectors]

    # Calculate angles between adjacent vectors using cross product
    angles = []
    for i in range(len(edge_vectors) - 1):
        angle = np.degrees(np.arccos(np.dot(edge_vectors[i], edge_vectors[i + 1])))
        cross_product = np.cross(edge_vectors[i], edge_vectors[i + 1])
        if cross_product[2] < 0:
            angle = 360 - angle
        angles.append(angle)

    # Check if any angle is greater than a threshold
    spiked_count = sum(angle > 90 for angle in angles)

    if spiked_count >= 3:
        p.add_text(f"Brim Recommended(At least 3 vertices have spiked corners)", font_size=16, color='red',position='lower_edge')
    else:
        p.add_text("Geometrically Safe", font_size=24, color='green',position='lower_edge')



def check_mesh_stability(mesh):
    
    max_edge_length = np.max(edges.length)
    if(Layer_Height > Nozzle_Size*0.7):
                p.add_text("Layer Height is too high,lower it", font_size=24, color='red',position='lower_edge')

    if np.any(max_edge_length <= 85):
        if(stability_margin2 < threshold):
            p.add_text("Very Safe(Low chance of First Layer warping)", font_size=24, color='blue',position='lower_edge')
        else:
            p.add_text("Problem:Too small for First Layer", font_size=24, color='green',position='lower_edge')
    else:
        p.add_mesh(first_layer_faces,show_edges=True, color="blue", opacity=0.8, label="First Layer Faces")
        p.add_mesh(edges, color="red", opacity=0.8,line_width=5)          
        analyse_corners(first_layer_faces)
        

    # Set up the plotter
    
    p.camera_position = "xy"
     
    p.add_text("Warping Tendency is :"+str(Warping_Tendency), font_size=24, color='blue',position='upper_edge')
    print("Percentage of warping tendency is :"+str(Warping_Tendency))

    p.set_background("white")
    p.show_grid()

    # Show the plot
    p.show()

# Example usage:
# Replace "your_mesh_file.stl" with the actual path to your mesh file
check_mesh_stability(mesh)












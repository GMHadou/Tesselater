import pyvista as pv
import numpy as np
import scipy.spatial 
from Shrinkage import mesh,Percentage_by_total
from main import plane,stability_margin2

p=pv.Plotter()
#Some Data of your printer will help calculate increased chance of geometrical warping

Bed_Temp =50
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
layer=1
while len(Base.points) == 0:
    Base = mesh.clip(normal=[0, 0, 1], origin=[0, 0, layer * Layer_Height])
    layer += 1
    if layer > 10:
        break

x_range = np.ptp(Base.points[:, 0])
y_range = np.ptp(Base.points[:, 1])


#A Biased number that gives an empirical estimation of warping increased possibility based on these variables
Warping_Tendency= abs((((Speed)*Layer_Height/(Line_Width))-(Speed_Quality)*Layer_Height/(Ideal))/(Percentage_by_total*100))
Base = mesh.clip(normal=[0, 0, 1], origin=[0, 0, 0.1])

edges = Base.extract_feature_edges()
# Add the shrinked and normal mesh with different colors


def analyse_corners(mesh: pv.PolyData) -> bool:
    scaled_mesh = mesh.copy()
    scaled_mesh.points *= (1 - Percentage_by_total)
    
    # Calculate the centroid of the base mesh
    centroid = np.mean(Base.points, axis=0)
    
    # Calculate a point proportionally above the centroid
    above_centroid = centroid + np.array([0, 0, mesh_height * 0.2])
    
    
    # Calculate direction vectors from all scaled points to above_centroid
    directions = above_centroid - scaled_mesh.points
    
    # Calculate distances of all points from the centroid
    distances_from_centroid = np.linalg.norm(scaled_mesh.points - centroid, axis=1)
    
    # Normalize distances
    normalized_distances = distances_from_centroid / np.max(distances_from_centroid)
    Percent_for_Warp=Percentage_by_total*2
    # Pull the points towards the above_centroid with distance-based factor
    scaled_mesh.points += directions * normalized_distances[:, np.newaxis] * (Percent_for_Warp + pow(Warping_Tendency / 1000, 1.1))
    if not (45 <= Bed_Temp <= 60) or not (195 <= Temperature <= 210):
        scaled_mesh.points += directions * normalized_distances[:, np.newaxis] * (Percent_for_Warp + pow(Warping_Tendency / 1000, 1.1)) * 2
        if len(edges.points) > 0:
            edge_angles = []
            for i in range(len(edges.points)):
                p1 = edges.points[i]
                p2 = edges.points[(i + 1) % len(edges.points)]
                p3 = edges.points[(i + 2) % len(edges.points)]
                v1 = p2 - p1
                v2 = p3 - p2
                angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
                edge_angles.append(angle)
            
            if any(angle < np.pi / 2 for angle in edge_angles):
                scaled_mesh.points += directions * normalized_distances[:, np.newaxis] * (Percent_for_Warp + pow(Warping_Tendency / 1000, 1.1)) * 3
                if(stability_margin2 < 9.67):
                    scaled_mesh.points += directions * normalized_distances[:, np.newaxis] * (Percent_for_Warp + pow(Warping_Tendency / 1000, 1.1)) * 4

    
    p.add_mesh(scaled_mesh, color='red', opacity=0.5)
    p.add_mesh(plane, color='gray', opacity=0.5)
    p.add_mesh(mesh,opacity=0.8, color='blue')
    p.show()




   



def check_mesh_stability(mesh):
    
    if(Layer_Height > Nozzle_Size*0.7):
                p.add_text("Layer Height is too high,lower it", font_size=24, color='red',position='lower_edge')

    else :          
        analyse_corners(Base)
        

    # Set up the plotter
    
    p.camera_position = "xy"
     
    p.add_text("Warping Tendency is :"+str(Warping_Tendency), font_size=24, color='blue',position='upper_edge')
    print("Percentage of warping tendency is :"+str(Warping_Tendency))

    p.set_background("white")
    p.show_grid()

   
  

# Example usage:
# Replace "your_mesh_file.stl" with the actual path to your mesh file
check_mesh_stability(mesh)












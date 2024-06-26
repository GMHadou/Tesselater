import pyvista as pv
from mesh_loader import get_mesh
from variables import CTE,Temperature,Base_temp,Percentage_by_total,Wall_thickness
mesh = get_mesh() # Assuming this imports your mesh


# Extract surface and calculate areas and volumes
surface = mesh.extract_surface()
Surface_Area = surface.area
Outer_volume = Surface_Area * Wall_thickness
total_volume = mesh.volume

# Calculate heat-warped volume and shrinkage
heat_warped = total_volume * CTE * (Temperature - Base_temp)
Shrinkage_volume_surface2 = Outer_volume * Percentage_by_total
Area_shrinkage = Shrinkage_volume_surface2 / Wall_thickness
Shrinkage_percentage = Shrinkage_volume_surface2 / Outer_volume

# Shrink the surface and create a new PolyData
scaling_factor = 1 - Shrinkage_percentage

# Scale the entire mesh
shrinked_mesh = mesh.scale(scaling_factor, inplace=False)

# Initialize plotter and add mesh
p = pv.Plotter()
p.add_mesh(shrinked_mesh, color="red")
p.add_mesh(mesh,color="green",opacity=0.2)

# Output shrinkage results
print("Percentage of Warping: ", Percentage_by_total, "Area Expected to Shrink: ", Area_shrinkage)

# Define and check volume safety
def volume_safety(Shrinkage_volume_surface2, Outer_volume, heat_warped):
    if Shrinkage_volume_surface2 / Outer_volume < 0.05 or heat_warped < 40:
        return "SAFE"
    else:
        return "UNSAFE"

result = volume_safety(Shrinkage_volume_surface2, Outer_volume, heat_warped)
print(result)




import pyvista as pv
import numpy as np

mesh=pv.read("Blade.stl")


#Shrinkage percentage is defined as the general shrinkage based on the total mesh volume
#For PLA,it varies from 0.2 to 0.5
Print_speed=80 #mm/s
Temperature=210
Base_temp=60
Percentage_by_total=0.005#We always suppose the worst shrinkage percentage,for pla it is 0,5 percent
Layer_Height=0.2
Wall_thickness=0.8
#The density is given in percentage,the higher the density,the higher the shrinkage
Infill_density=0.1
#The actual heat dispersion is influenced by the number of walls,gaps between the infill,density of the infill and type of infill
#Volume plays a massive role in shrinkage.THe internal structure of the mesh is defined by many variables,some of which are considered to make this calculus work
surface=mesh.extract_surface()

Surface_Area=surface.area

Outer_volume=Surface_Area*Wall_thickness

total_volume = mesh.volume

#Even though CTE and Fluid_Fase are not used,they are present to correspond to possible calculus that are closer to a
#theoretical value of shrinkage
CTE = 68e-6  # Coefficient of Thermal Expansion for PLA in /°C
initial_temp = 210  # Initial temperature in °C
Fluid_Fase = 135  # Temperature of the start of the Phase that Plastic is molded
#Supposing an equal time of deposition between layers,this is the resulting ammount of warped milimiters,it will be used to roughly calculate safe volume print
heat_warped= total_volume * CTE * (Temperature - Base_temp)
#Truer Shrinkage
Shrinkage_volume_surface2=Outer_volume*Percentage_by_total
Area_shrinkage=Shrinkage_volume_surface2/Wall_thickness
Shrinkage_percentage=Shrinkage_volume_surface2/Outer_volume


print(Shrinkage_volume_surface2/Outer_volume,Area_shrinkage)


#Volume Safety calculation for toppling analysis
def volume_safety(Shrinkage_volume_surface2, Outer_volume, heat_warped):
    if Shrinkage_volume_surface2/Outer_volume < 0.05 or heat_warped < 40:
        unstable = 1
        return "SAFE"
    else:
        unstable=0
        return "UNSAFE"

result = volume_safety(Shrinkage_volume_surface2, Outer_volume, heat_warped)
print(result)




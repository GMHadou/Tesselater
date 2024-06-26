import numpy as np
import pyvista as pv
from scipy.ndimage import distance_transform_edt

def analyze_small_features(mesh, min_feature_size=0.85, layer_thickness=0.2):
    # Get the bounding box of the mesh
    bounds = mesh.bounds

    # Calculate grid size based on bounding box and layer thickness
    grid_size = np.ceil((np.array(bounds[1::2]) - np.array(bounds[::2])) / layer_thickness).astype(int)

    # Create an empty image data with proper keyword arguments
    image_data = pv.UniformGrid(dimensions=grid_size + 1, origin=bounds[::2], spacing=[layer_thickness] * 3)

    # Sample the mesh onto the image data
    mesh.sample(image_data)

    # Print available arrays
    print("Available arrays:", image_data.array_names)

    # Find the correct array (it may have a different name)
    valid_point_mask_array = [array for array in image_data.array_names if "ValidPointMask" in array]
    if not valid_point_mask_array:
        raise KeyError("No valid point mask array found.")

    # Calculate distance field
    distances = distance_transform_edt(image_data[valid_point_mask_array[0]])

    # Threshold distance field based on minimum feature size
    thin_regions = distances <= min_feature_size

    # Create PyVista mesh for visualization
    thin_mesh = pv.UniformGrid(dimensions=thin_regions.shape, origin=bounds[::2], spacing=[layer_thickness] * 3)
    thin_mesh.point_arrays['ThinRegions'] = thin_regions.flatten(order='F').astype(int)

    # Visualize the results
    p = pv.Plotter()
    p.add_mesh(mesh, color='lightgray', opacity=0.5)
    p.add_mesh(thin_mesh, name='ThinRegions', cmap='coolwarm', opacity=0.6)
    p.show()

# Assuming you have a PyVista mesh object named 'mesh'
mesh = pv.read("Soldering_Fingers.stl")
analyze_small_features(mesh)











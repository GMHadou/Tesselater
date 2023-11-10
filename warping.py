import tkinter as tk
from tkinter import filedialog
import pyvista as pv

def import_and_save_mesh(file_path, output_file):
    """
    Import an STL or PLY mesh and save it to a common format like PLY or VTK.

    Parameters:
    - file_path (str): Path to the STL or PLY file.
    - output_file (str): Path to save the mesh in PLY or VTK format.
    """
    # Determine the file format (STL or PLY)
    if file_path.lower().endswith('.stl'):
        mesh = pv.read(file_path)
    elif file_path.lower().endswith('.ply'):
        mesh = pv.read(file_path)
    else:
        print("Unsupported file format. Please select an STL or PLY file.")
        return

    # Save the loaded mesh to a common format (PLY or VTK)
    mesh.save(output_file)

def choose_file_and_save():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("STL and PLY Files", "*.stl *.ply")])

    if file_path:
        output_file = "output_mesh.stl"  # Change to your desired output format
        import_and_save_mesh(file_path, output_file)

if __name__ == "__main__":
    # Open a file dialog to choose the STL or PLY file and save it
    choose_file_and_save()


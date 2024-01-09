import gcodeutils

def gcode_to_stl(gcode_file, stl_file):
    # Load the G-code file
    gcode = gcodeutils.Gcode.from_file(gcode_file)

    # Convert the G-code to an STL mesh
    mesh = gcode.to_stl()

    # Save the STL file
    mesh.save(stl_file)

# Usage example
gcode_file = "input.gcode"
stl_file = "output.stl"
gcode_to_stl(gcode_file, stl_file)

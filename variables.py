# Constants
CTE = 68e-6  # Coefficient of Thermal Expansion for PLA in /°C
Print_speed = 80  # mm/s
Temperature = 210
Base_temp = 60
Percentage_by_total = 0.005  # Worst-case shrinkage percentage for PLA
Layer_Height = 0.2
Wall_thickness = 0.8
Infill_density = 0.1



# Printer Configuration





bed_width = 300.0  # in millimeters
bed_length = 300.0  # in millimeters

# Bed temperature in degrees Celsius
Bed_Temp = 60

# Temperature of the printer's hotend in degrees Celsius
Temperature = 210

initial_temp = 210
Fluid_Fase = 135


# Function to calculate the flow rate based on the temperature
def calculate_flow():
    if Temperature <= 210:
        return 10
    elif 210 < Temperature < 250:
        return 12.5
    else:
        return 15

# Microstepping value for the printer's stepper motor
Microstepping = 1 / 16

# Diameter of the printer's nozzle in millimeters
Nozzle_Size = 0.4

# Flat width of the printer's nozzle in millimeters
Nozzle_Flat = 0.8

# Width of each printed line in millimeters
Line_Width = Nozzle_Size * 1.25

# Height of each printed layer in millimeters
Layer_Height = 0.1

# Minimum layer height for optimal printing
Minimum = Layer_Height + Nozzle_Size

# Maximum layer height for optimal printing
Maximum = Layer_Height + Nozzle_Flat

# Ideal layer height for optimal printing
Ideal = (Minimum + Maximum) / 2

# Printing speed in millimeters per second
Speed = 80

# Function to calculate the maximum printing speed based on flow rate, line width, and layer height

flow = calculate_flow()
Max_Speed = flow / (Line_Width * Ideal)
Speed_Quality = Ideal * flow /Layer_Height

# Function to calculate the amount of heat warped based on total volume, coefficient of thermal expansion (CTE), and base temperature
print("Your ideal Speed is: ",Speed_Quality,"mm/s")



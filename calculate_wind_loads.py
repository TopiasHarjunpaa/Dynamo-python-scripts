import math
import clr
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.UI import TaskDialog

WALL_PRESSURE = 0.8
WALL_SUCTION = -0.5
MONOPITCH_SUCTION_US = -0.6
MONOPITCH_SUCTION_DS = -0.9
TERRAIN_CATEGORY_ROME = ["0", "I", "II", "III", "IV"]

def calculate_propability_factor(return_period):
    pass

def calculate_peak_velocity_pressure(terrain_category, cprop, height):
    pass

def calculate_roof_pressure(angle_factor, width):
    if width <= 10:
        return -0.7 + angle_factor
    elif width < 25:
        return 0.01 * width - 0.8 * angle_factor
    return -0.55 + angle_factor

def calculate_pressure_coefficents(angle, width, monopitch):
    coefficients = {}
    angle_factor = min(max((angle - 10) / 100, 0), 0.1)
    coefficients["Wall pressure"] = WALL_PRESSURE
    coefficients["Wall suction"] = WALL_SUCTION
    coefficients["Roof pressure"] = calculate_roof_pressure(angle_factor, width)
    if monopitch:
        coefficients["Roof suction to up slope"] = MONOPITCH_SUCTION_US
        coefficients["Roof suction to down slope"] = MONOPITCH_SUCTION_DS
    else:
        coefficients["Roof suction"] = max(min(0.03 * angle - 0.25, 0), 0.7)
    return coefficients

def add_basic_information(tc, angle, bay_width, height, return_period, monopitch, roof_width):
    roof_type = "Roof type: "
    if monopitch:
        roof_type += "Monopitch roof "
    else:
        roof_type += "Double pitch roof "
    roof_type += f"{roof_width/1000} m with {angle}° angle"

    response_text = f"Basic information:\n{roof_type}\n"
    response_text += f"Terrain category: {TERRAIN_CATEGORY_ROME[tc]}\nBay width: {bay_width/1000} m\nRoof height: {height}\nReturn period: {return_period} years\n"
    return response_text

terrain_category = IN[0]
angle = IN[1]
bay_width = IN[2]
height = IN[3]
return_period = IN[4]
monopitch = IN[5]
roof_width = IN[6]

response_text = add_basic_information(terrain_category, angle, bay_width, height, return_period, monopitch, roof_width)
coefficients = calculate_pressure_coefficents(angle, roof_width, monopitch)

response_text += "\nPressure coefficients:\n"
for key, value in coefficients.items():
    response_text += f"{key}: {value:.2f}\n"

TaskDialog.Show("Dynamo Player", response_text)

OUT = "Success!"
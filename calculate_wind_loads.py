import math
import clr
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.UI import TaskDialog

WALL_PRESSURE = 0.8
WALL_SUCTION = -0.5
MONOPITCH_SUCTION_US = -0.6
MONOPITCH_SUCTION_DS = -0.9
TERRAIN_CATEGORY_ROME = ["0", "I", "II", "III", "IV"]
Z_ZERO = [0.003, 0.01, 0.05, 0.3, 1] # List of roughness lengths z0 depended from TC
Z_MIN = [1, 1, 2, 5, 10] # List of zmin's depended from TC
OROGRAPHY_FACTOR = 1.0 # c0(ze)
TURBULENCE_FACTOR = 1.0 # kI
AIR_DENSITY = 1.25 # p
TERRAIN_FACTOR_FIN = 0.18
SHAPE_PARAMETER = 0.2 # To determine propability factor. Recommend value K = 0.2.
CPROP_EXPONENT = 0.5 # To determine propability factor. Recommend value n = 0.5.
CDIR = 1.0 # Directional factor. Recommended value cdir = 1.0.

def calculate_propability_factor(return_period):
    divident = 1 - SHAPE_PARAMETER * math.log(-1 * math.log(1 - 1 / return_period))
    divider = 1 - SHAPE_PARAMETER * math.log(-1 * math.log(0.98))
    cprop = (divident / divider) ** CPROP_EXPONENT
    
    return cprop

def calculate_terrain_factor(fin: bool, terrain_category: int) -> float:
    """Terrain factor is calculated using formula kr = 0.19 ⋅ (z0 / z0,II) ^ 0.07
        where:

        z0      is roughness length depended on the terrain category
        z0,II   is roughness length on the terrain category II

        Exception:

        Terrain factor should be 0.18 in Finland at terrain category 0. Explanation in finnish NA:

        "Tuulen nopeudet merialueilla tulevat aliarvioiduiksi, jos lauseketta (4.5) sovelletaan 
        maastokertoimen arviointiin. Tämän takia maastokertoimelle sovelletaan merialueilla 
        arvoa kr =0,18, joka perustuu tilastoaineistoon.
    Args:
        fin (bool): Boolean determine whether finnish NA should be followed or not. 
        terrain_category (int): Terrain category used in a calculation. Integer between 0 - 4.

    Returns:
        float: Terrain factor used in further wind load calculations
    """

    if fin and terrain_category == 0:
        return TERRAIN_FACTOR_FIN
    return 0.19 * (Z_ZERO[terrain_category]/Z_ZERO[2]) ** 0.07

def calculate_peak_velocity_pressure(
    fin: bool, terrain_category: int,
    return_period: float,
    height: float,
    fundamental_basic_wind_velocity: float,
    seasonal_factor: float=1.0
):
    wind_height = max(min(200, height), Z_MIN[terrain_category])
    cprop = calculate_propability_factor(return_period)
    basic_wind_velocity = fundamental_basic_wind_velocity * cprop * seasonal_factor * CDIR
    terrain_factor = calculate_terrain_factor(fin, terrain_category)
    roughness_factor = terrain_factor * math.log(wind_height / Z_ZERO[terrain_category]) # cr(ze) = kr ⋅ ln(max{ze, zmin} / z0)
    mean_wind_velocity = roughness_factor * OROGRAPHY_FACTOR * basic_wind_velocity # vm(ze) = cr(ze) ⋅ c0(ze) ⋅ vb
    wind_turbulence = TURBULENCE_FACTOR / (OROGRAPHY_FACTOR * math.log(wind_height / Z_ZERO[terrain_category])) # Iv(ze) = kI / [ c0(ze) ⋅ ln(max{ze, zmin} / z0) ]
    peak_velocity_pressure = (1 + 7 * wind_turbulence) * 1/2000 * AIR_DENSITY * mean_wind_velocity ** 2  # qp(ze) = (1 + 7 ⋅ Iv(ze)) ⋅ (1/2) ⋅ ρ ⋅ vm(ze)2

    return (
        fundamental_basic_wind_velocity, 
        seasonal_factor,
        cprop,
        basic_wind_velocity,
        terrain_category,
        roughness_factor,
        mean_wind_velocity,
        wind_turbulence,
        peak_velocity_pressure
    )

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

def add_basic_information(angle, bay_length, monopitch, roof_width):
    roof_type = "Roof type: Double pitch roof"
    if monopitch:
        roof_type = "Roof type: Monopitch roof"
    basic_info_header = "Basic information:\n"
    basic_info_params = f"{roof_type}\nRoof width: {roof_width/1000:.2f} m\nRoof angle: {angle}°\nBay length: {bay_length/1000} m"
    return basic_info_header + basic_info_params

def add_wind_calculation_information(params):
    wind_calculation_info_header = "Wind calculation parameters\n"
    terrain_category = f"Terrain category: {TERRAIN_CATEGORY_ROME[params[4]]}\n"
    fundamental_basic_wind_velocity = f"Fundamental basic wind velocity: {params[0]:.1f} m/s\n"
    wind_modifiers = f"Wind modifiers: cdir = {CDIR} | cseason = {params[1]} | cprop = {params[2]:.2f} ({params[2] ** 2:.2f})\n"
    basic_wind_velocity = f"Basic wind velocity: {params[3]:.1f} m/s\n"
    terrain_factor = f"Terrain roughness factor: {params[5]:.2f}\n"
    mean_wind_velocity = f"Mean wind velocity: {params[6]:.1f} m/s\n"
    wind_turbulence =f"Wind turbulence intensity: {params[7]:.2f} (c0 = {OROGRAPHY_FACTOR} | kl = {TURBULENCE_FACTOR})\n"
    peak_velocity_pressure = f"Peak wind velocity pressure: {params[8]:.2f} kN/m2\n"
    wind_calculation_info_params = (
        terrain_category +
        wind_modifiers +
        fundamental_basic_wind_velocity +
        basic_wind_velocity +
        mean_wind_velocity +
        terrain_factor +
        wind_turbulence +
        peak_velocity_pressure

    )
    return wind_calculation_info_header + wind_calculation_info_params

def add_pressure_coefficient_information(pressure_coefficients, bay_length, peak_velocity_pressure):
    pressure_coefficient_info_header = "Pressure coefficients:\n"
    pressure_coefficient_info_params = ""
    line_load = (bay_length / 1000) * peak_velocity_pressure
    for key, value in pressure_coefficients.items():
        pressure_coefficient_info_params += f"{key}: {value:.2f} | {value * line_load:.2f} kN/m\n"
    return pressure_coefficient_info_header + pressure_coefficient_info_params

terrain_category = IN[0]
angle = IN[1]
bay_length = IN[2]
height = IN[3]
return_period = IN[4]
monopitch = IN[5]
roof_width = IN[6]

wind_calculation_params = calculate_peak_velocity_pressure(True, terrain_category, return_period, height, 21)
peak_velocity_pressure = wind_calculation_params[8]
pressure_coefficients = calculate_pressure_coefficents(angle, roof_width, monopitch)

response_text = add_basic_information(angle, bay_length, monopitch, roof_width)
response_text += "\n\n"
response_text += add_wind_calculation_information(wind_calculation_params)
response_text += "\n"
response_text += add_pressure_coefficient_information(pressure_coefficients, bay_length, peak_velocity_pressure)

TaskDialog.Show("Dynamo Player", response_text)

OUT = "Success"
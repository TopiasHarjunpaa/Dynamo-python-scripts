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
TERRAIN_FACTOR_FIN = 0.18

def calculate_propability_factor(return_period: int, shape_parameter: float=0.2, cprob_exponent: float=0.5) -> float:
    """Probability factor is used to modify fundamental basic wind velocity vb which has mean return period
        of 50 years. The 10 minutes mean wind velocity having the probability p for an annual exceedence is determined
        by multiplying the fundamental basic wind velocity vb by the probability factor, cprob.
        It is calculated using the following expression given at EN 1911-1-4 (expression 4.2):

        cprob = (1 - K ⋅ ln(-ln(1 - p)) / 1 - K ⋅ ln(-ln(0.98)))^n  where:

        K is the shape parameter
        n is exponent
        p is probability for an annual exceedence

        NOTE: Return period has been limited to min 2 years, due value 1 or less will lead into error -> ln(0)

    Args:
        return_period (int): Return period in years to calculate probability for an annual exceedence.
        shape_parameter (float, optional): Parameter depending on the coefficient of variation of the extreme-value distribution. Defaults to 0.2.
        cprob_exponent (float, optional): Exponent of the expression. Defaults to 0.5.

    Returns:
        float: Probability factor to modify fundamental basic wind velocity
    """

    divident = 1 - shape_parameter * math.log(-1 * math.log(1 - 1 / max(return_period, 2)))
    divider = 1 - shape_parameter * math.log(-1 * math.log(0.98))
    cprob = (divident / divider) ** cprob_exponent
    
    return cprob

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

def convert_pressure_to_speed(pressure: float, air_density: float) -> float:
    """Converts wind pressure to wind speed using the expression qp = 0.5 ⋅ p ⋅ (vb)^2 which
        is modified into form of:

        vb = sqrt(1000 * qp * 2 / p)

        Expression uses wind pressure in form of N/m2 and therefore pressure recieved in argument
        will be converted in same form by multiplying it with the value of 1000. (1 kN/m2 = 1000 N/m2).

    Args:
        pressure (float): Wind pressure in form of kN/m2
        air_density (float): Air density depends on the altitude, temperature and barometric pressure.

    Returns:
        float: _description_
    """

    return math.sqrt((1000 * pressure * 2) / air_density)

def calculate_peak_velocity_pressure(
    fin: bool, 
    terrain_category: int,
    return_period: float,
    height: float,
    fundamental_basic_wind_velocity: float,
    seasonal_factor: float=1.0,
    orography_factor: float=1.0,
    air_density: float=1.25,
    directional_factor: float=1.0,
    turbulence_factor: float=1.0
) -> list:
    """Calculate peak wind velocity pressure according to EN 1991-1-4.
        Process involves following steps:

        1. Calculate probability factor
        2. Modify fundamental basic wind velocity: vb = cdir · cseason · vb,0 · cprob
        3. Calculate terrain factor: kr = 0.19 ⋅ (z0 / z0,II)^0.07
        4. Calculate roughness factor: cr(ze) = kr ⋅ ln(max{ze, zmin} / z0)
        5. Calculate mean wind velocity: vm(ze) = cr(ze) ⋅ c0(ze) ⋅ vb
        6. Calculate turbulence intensity: Iv(ze) = kI / (c0(ze) ⋅ ln(max{ze, zmin} / z0))
        7. Calculate peak velocity pressure: qp(ze) = (1 + 7 ⋅ Iv(ze)) ⋅ (1/2) ⋅ p ⋅ vm(ze)2

    Args:
        fin (bool): To determine whether finnish NA needs to be used or not.
        terrain_category (int): Value between 0 - 4 to determine roughness and turbulence factors.
        return_period (float): Return period in years to calculate probability for an annual exceedence.
        height (float): Structure height from the ground in meters.
        fundamental_basic_wind_velocity (float): is the fundamental value of the basic wind velocity in m/s. 
        seasonal_factor (float, optional): The value of seasonal factor. May be given in the NA. Defaults to 1.0.
        orography_factor (float, optional): Orography factor, taken as 1,0 unless otherwise specified in 4.3.3. Defaults to 1.0.
        air_density (float, optional): Air density depends on the altitude, temperature and barometric pressure. Defaults to 1.25.
        directional_factor (float, optional): The value of directional factor. May be given in the NA. Defaults to 1.0.
        turbulence_factor (float, optional): The value of the turbulence factor. May be given in the NA. Defaults to 1.0.

    Returns:
        list: Returns bunch of parameters and calculation results from various expression.
    """

    wind_height = max(min(200, height), Z_MIN[terrain_category])
    cprob = calculate_propability_factor(return_period)
    basic_wind_velocity = fundamental_basic_wind_velocity * cprob * seasonal_factor * directional_factor
    terrain_factor = calculate_terrain_factor(fin, terrain_category)
    roughness_factor = terrain_factor * math.log(wind_height / Z_ZERO[terrain_category])
    mean_wind_velocity = roughness_factor * orography_factor * basic_wind_velocity
    wind_turbulence = turbulence_factor / (orography_factor * math.log(wind_height / Z_ZERO[terrain_category]))
    peak_velocity_pressure = (1 + 7 * wind_turbulence) * 1/2000 * air_density * mean_wind_velocity ** 2
    peak_wind_speed = convert_pressure_to_speed(peak_velocity_pressure, air_density)

    return [
        terrain_category,
        directional_factor,
        seasonal_factor,
        cprob,
        fundamental_basic_wind_velocity,
        basic_wind_velocity,
        mean_wind_velocity,
        roughness_factor,
        fin,
        wind_turbulence,
        orography_factor,
        turbulence_factor,
        air_density,
        peak_velocity_pressure,
        peak_wind_speed
    ]

def calculate_roof_suction(angle: int, width: int) -> float:
    """Calculate external roof suction pressure coefficient according to EN 16508
        using roof angle and roof width.

    Args:
        angle (int): Roof angle in degrees.
        width (int): Roof width in millimeters.

    Returns:
        float: Roof suction pressure coefficient.
    """

    angle_factor = min(max((angle - 10) / 100, 0), 0.1)
    if width <= 10000:
        return -0.7 + angle_factor
    elif width < 25000:
        return 0.01 * width / 1000 - 0.8 + angle_factor
    return -0.55 + angle_factor

def calculate_pressure_coefficents(angle: int, width: int) -> dict:
    """Calculate pressure coefficients for weather protection according to EN 16508
        using roof angle and roof width. Sets roof pressure coefficients to zero if roof width
        has set to zero.

    Args:
        angle (int): Roof angle in degrees.
        width (int): Roof width in millimeters.

    Returns:
        dict: Pressure coefficients in dictionary format. Key = name of the pressure surface. Value = coefficient.
    """

    coefficients = {}
    coefficients["Wall pressure"] = WALL_PRESSURE
    coefficients["Wall suction"] = WALL_SUCTION
    coefficients["Roof pressure"] = min(max(0.03 * angle - 0.25, 0), 0.7)
    coefficients["Double-pitch roof suction"] = calculate_roof_suction(angle, width)
    coefficients["Mono-pitch roof suction to up slope"] = MONOPITCH_SUCTION_US
    coefficients["Mono-pitch roof suction to down slope"] = MONOPITCH_SUCTION_DS
    if roof_width == 0:
        coefficients["Roof pressure"] = 0
        coefficients["Double-pitch roof suction"] = 0
        coefficients["Mono-pitch roof suction to up slope"] = 0
        coefficients["Mono-pitch roof suction to down slope"] = 0      
    return coefficients

def add_basic_information(angle: int, bay_length: int, monopitch: bool, roof_width: int) -> str:
    """Format arguments and create multiline string of the basic information.

    Args:
        angle (int): Roof angle in degrees.
        bay_length (int): Bay length in millimeters.
        monopitch (bool): Boolen value to determine whether roof type is monopitch (true) or duopitch (false).
        roof_width (int): Roof width in millimeters.

    Returns:
        str: Multiline string of the basic information.
    """

    roof_type = "Roof type: Double pitch roof"
    if monopitch:
        roof_type = "Roof type: Monopitch roof"
    basic_info_header = "Basic information:\n"
    basic_info_params = f"{roof_type}\nRoof width: {roof_width/1000:.2f} m\nRoof angle: {angle}°\nBay length: {bay_length/1000} m"
    return basic_info_header + basic_info_params

def add_wind_calculation_information(params: tuple) -> str:
    """Format arguments and create multiline string of the wind calculation information.

    Args:
        params (tuple): bunch of calculation parameters and results from various expression used in wind calculations

    Returns:
        str: Multiline string of the wind calculation information.
    """

    wind_calculation_info_header = "Wind calculation parameters\n"
    terrain_category = f"Terrain category: {TERRAIN_CATEGORY_ROME[params[0]]}\n"
    wind_modifiers = f"Basic wind velocity modifiers: cdir = {params[1]:.1f} | cseason = {params[2]:.1f} | cprob = {params[3]:.2f}\n"
    fundamental_basic_wind_velocity = f"Fundamental basic wind velocity: {params[4]:.1f} m/s\n"
    basic_wind_velocity = f"Basic wind velocity: {params[5]:.1f} m/s\n"
    mean_wind_velocity = f"Mean wind velocity: {params[6]:.1f} m/s\n"
    terrain_factor = f"Terrain roughness factor: {params[7]:.2f}\n"
    if(params[8] and params[0] == 0):
        terrain_factor += f"Note: Terrain factor {TERRAIN_FACTOR_FIN} used in accordance to Finnish NA in terrain category 0\n"
    wind_turbulence =f"Wind turbulence intensity: {params[9]:.2f} (c0 = {params[10]:.1f} | kl = {params[11]:.1f})\n"
    air_pressure = f"Air pressure: {params[12]:.2f} kg/m2\n"
    peak_velocity_pressure = f"Peak wind velocity pressure: {params[13]:.2f} kN/m2 ({params[14]:.1f} m/s peak wind speed)\n"
    wind_calculation_info_params = (
        terrain_category +
        wind_modifiers +
        fundamental_basic_wind_velocity +
        basic_wind_velocity +
        mean_wind_velocity +
        terrain_factor +
        wind_turbulence +
        air_pressure +
        peak_velocity_pressure

    )
    return wind_calculation_info_header + wind_calculation_info_params

def add_pressure_coefficient_information(pressure_coefficients: dict, bay_length: int, peak_velocity_pressure: float, monopitch: bool) -> str:
    """Format arguments and create multiline string of the pressure coefficient information.
        Pressure coefficients are in dictionary format. In text formating process, each surface type:

        - Gets surface type name
        - Pressure coefficient
        - Modified line load value p [kN/m] = cp ⋅ bay length [m] ⋅ peak velocity pressure [kN/m2]

    Args:
        pressure_coefficients (dict): Pressure coefficients in dictionary format. Key = name of the pressure surface. Value = coefficient.
        bay_length (int): Bay length in millimeters
        peak_velocity_pressure (float): _description_

    Returns:
        str: Multiline string of the pressure coefficient information.
    """

    pressure_coefficient_info_header = "Pressure coefficients:\n"
    pressure_coefficient_info_params = ""
    filtered_coefficients = pressure_coefficients.copy()
    if (monopitch):
        filtered_coefficients.pop("Double-pitch roof suction")
    else:
        filtered_coefficients.pop("Mono-pitch roof suction to up slope")
        filtered_coefficients.pop("Mono-pitch roof suction to down slope")

    line_load = (bay_length / 1000) * peak_velocity_pressure
    for key, value in filtered_coefficients.items():
        pressure_coefficient_info_params += f"{key}: {value:.2f} | {value * line_load:.2f} kN/m\n"
    return pressure_coefficient_info_header + pressure_coefficient_info_params

def add_nominal_duration_information(return_period: float) -> str:
    """Calculates probability factor using value of the return period and formats response with
        with additional information according to EN 1991-1-6 ie. what is the maximum nominal duration
        with certain return period.

    Args:
        return_period (float): Return period in years

    Returns:
        str: Multiline string of the nominal duration information.
    """

    nominal_duration_info_header = "Nominal length of the structure:\n"
    cprob = calculate_propability_factor(return_period)
    cprob2 = cprob ** 2
    return_period_info = f"Return period used in calculation: {return_period} years\n"
    cprob_info = f"Corresponds probability factor cprob = {cprob:.2f} and cprob2 = {cprob2:.2f}\n"
    if (cprob2 < 0.7):
        cprob_info += "Note: According to EN 12811-1 cprob2 shall be not less than 0.70\n"
    nominal_duration_info = "Corresponds nominal duration of "
    
    if (return_period < 2):
        nominal_duration_info += "0 days.\n"
    if (2 <= return_period < 5):
        nominal_duration_info += "less than 3 days (minimum period 2 years)\n"
    if (5 <= return_period < 10):
        nominal_duration_info += "less than 3 months (minimum period 5 years)\n"
    if (10 <= return_period < 50):
        nominal_duration_info += "less than 1 year (minimum period 10 years)\n"
    if (return_period >= 50):
        nominal_duration_info += "greater than 1 year (minimum period 50 year)\n"

    return nominal_duration_info_header + return_period_info + cprob_info + nominal_duration_info

def format_imposed_loads(imposed_load: float) -> dict:
    """Formats response according to imposed load value. Includes imposed load
        and combination factor based on EN 12811-1. Converts imposed load value from kilograms to kilonewtons.

    Args:
        imposed_load (float): Imposed load in kilograms.

    Returns:
        dict: Multiline string of the imposed load information.
    """
    combination_factor = "1,00"
    if imposed_load <= 75:
        combination_factor = "0,00"
    if 75 < imposed_load <= 200:
        combination_factor = "0,25"
    if 200 < imposed_load <= 600:
        combination_factor = "0,50"
    return {"Imposed loads": f"{imposed_load/100:.2f}".replace(".", ","), "Imposed load combination factor": combination_factor}

def format_consequence_class(consequence_class: int) -> dict:
    """Calculates K factor according to consequence class based on EN 1990 and creates response
        in dictionary format.

    Args:
        consequence_class (int): _description_

    Returns:
        dict: Dictionary where key is formatted consequence class and value is K factor.
    """

    k_factor = "1,00"
    if (consequence_class == 1):
        k_factor = "0,90"
    if (consequence_class == 3):
        k_factor = "1,10"
    return {"Consequence class": f"CC{consequence_class}", "K factor": k_factor}

def format_input(wind_calculation_params: list,
    pressure_coefficients: dict,
    angle: int,
    bay_length: int,
    roof_width: int,
    return_period: float,
    height: float,
    imposed_load: float,
    consequence_class: int,
    snow_load: float
) -> list:
    """Formats input with calculate parameters. These will be used as Revit parameters.

    Returns:
        list: List containing list with parameters names and other list with parameter values.
    """

    name_list = [
        "Terrain category",
        "Directional factor",
        "Seasonal factor",
        "Probability factor",
        "Fundamental basic wind velocity",
        "Basic wind velocity",
        "Mean wind velocity",
        "Roughness factor",
        "Wind turbulence intensity",
        "Orography factor",
        "Turbulence factor",
        "Air density",
        "Peak velocity pressure",
        "Peak wind speed",
        "Roof angle",
        "Bay length",
        "Roof width",
        "Return period",
        "Height above ground",
        "Snow load"
        ]
    value_list = [f"{value:.2f}".replace(".", ",") for value in wind_calculation_params[:8] + wind_calculation_params[9:]]
    value_list[0] = TERRAIN_CATEGORY_ROME[wind_calculation_params[0]]
    value_list += [
        f"{angle:.2f}".replace(".", ","),
        f"{bay_length / 1000:.2f}".replace(".", ","),
        f"{roof_width / 1000:.2f}".replace(".", ","),
        f"{return_period:.0f}",
        f"{height:.0f}".replace(".", ","),
        f"{snow_load/100:.2f}".replace(".", ",")
    ]
    peak_velocity_pressure = wind_calculation_params[13]
    line_load = peak_velocity_pressure * bay_length / 1000
    for key, value in pressure_coefficients.items():
        name_list.append(key)
        name_list.append(f"{key} load")
        value_list.append(f"{value:.2f}".replace(".", ","))
        value_list.append(f"{value * line_load:.2f}".replace(".", ","))
    for key, value in format_imposed_loads(imposed_load).items():
        name_list.append(key)
        value_list.append(value)
    for key, value in format_consequence_class(consequence_class).items():
        name_list.append(key)
        value_list.append(value)
    return [name_list, value_list]

# Input parameters recieved from the Revit / Dynamo user.
finnish_na = IN[0] # boolen
fundamental_basic_wind_velocity = IN[1] #in meters per second
terrain_category = IN[2] #int value 0-4
return_period = max(IN[3], 2) # in years. Min 2 years.
seasonal_factor = IN[4]
orography_factor = IN[5]
height = IN[6] # in meters
roof_width = IN[7] # in millimeters
bay_length = IN[8] # in millimeters
angle = IN[9] # in degrees
monopitch = IN[10] # boolean
imposed_load = IN[11] #in kilograms
snow_load = IN[12] #in kilograms
consequence_class = IN[13] #int value 1-3

if roof_width == 0:
    angle = 0

wind_calculation_params = calculate_peak_velocity_pressure(
    finnish_na,
    terrain_category,
    return_period, height,
    fundamental_basic_wind_velocity,
    seasonal_factor,
    orography_factor
)
peak_velocity_pressure = wind_calculation_params[13]
pressure_coefficients = calculate_pressure_coefficents(angle, roof_width)

response_text = add_basic_information(angle, bay_length, monopitch, roof_width)
response_text += "\n\n"
response_text += add_wind_calculation_information(wind_calculation_params)
response_text += "\n"
response_text += add_pressure_coefficient_information(pressure_coefficients, bay_length, peak_velocity_pressure, monopitch)
response_text += "\n"
response_text += add_nominal_duration_information(return_period)

TaskDialog.Show("Wind calculation results", response_text)

OUT = format_input(
    wind_calculation_params,
    pressure_coefficients,
    angle,
    bay_length,
    roof_width,
    return_period,
    height,
    imposed_load,
    consequence_class,
    snow_load
)
import math
import clr
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.UI import TaskDialog


terrain_category = IN[0]
terrain_category_rome = ["0", "I", "II", "III", "IV"]
angle = IN[1]
width = IN[2]
height = IN[3]
return_period = IN[4]

response_text = f"Windloads:\n\nTerrain category: {terrain_category_rome[terrain_category]}\nRoof angle: {angle} degrees\nBay width: {width/1000} m"

TaskDialog.Show("Dynamo Player", response_text)

OUT = "Success!"
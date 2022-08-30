from RevitServices.Persistence import DocumentManager 
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

doc = DocumentManager.Instance.CurrentDBDocument

projectInfoParams = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ProjectInformation).ToElements()[0].Parameters

result = []
for parameter in projectInfoParams:
    result.append([parameter.Definition.Name, parameter.AsString()])

author = result[6]
client_name = result[13]
address = result[14]
project_name = result[15]
supervisor = result[24]

OUT = [author, client_name, address, project_name, supervisor]
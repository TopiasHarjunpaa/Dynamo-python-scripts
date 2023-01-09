from datetime import date
from RevitServices.Persistence import DocumentManager as dm
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory


FIN = {"Author": "Suunnittelija",
        "Client Name": "Asiakkaan nimi",
        "Project Address": "Osoite",
        "Project Name": "Projektin nimi",
        "Supervisor name": "Työnjohtaja",
        "Date": "Päivämäärä",
        "Count": "Määrä",
        "Product number": "Tuotenumero",
        "Product names": {1: "Tuotenimi FIN", 2: "Tuotenimi ENG", 3: "Tuotenimi SWE"},
        "Weight": "Paino",
        "List price": "Listahinta",
        "Material list": "Kalustolista",
        "Total weight": "Kokonaispaino",
        "Total price": "Kokonaishinta"
        }

ENG = {"Author": "Designer",
        "Client Name": "Client name",
        "Project Address": "Project address",
        "Project Name": "Project name",
        "Supervisor name": "Supervisor name",
        "Date": "Date",
        "Count": "Count",
        "Product number": "Product number",
        "Product names": {1: "Product name FIN", 2: "Product name ENG", 3: "Product name SWE"},
        "Weight": "Weight",
        "List price": "List price",
        "Material list": "Material list",
        "Total weight": "Total weight",
        "Total price": "Total price"
        }

# Needs to be properly translated later
SWE = {"Author": "Designer",
        "Client Name": "Klient namn",
        "Project Address": "Projekt address",
        "Project Name": "Project namn",
        "Supervisor name": "Handledarens namn",
        "Date": "Datum",
        "Count": "Räkna",
        "Product number": "Produktnummer",
        "Product names": {1: "Productnamn FIN", 2: "Productnamn ENG", 3: "Productnamn SWE"},
        "Weight": "Vikt",
        "List price": "Listpris €",
        "Material list": "Produktlista",
        "Total weight": "Totalvikt",
        "Total price": "Totalpris"
        }

LANGUAGES =[FIN, ENG, SWE]

def get_main_language(input):
    index = input[3] - 1
    primary_language = LANGUAGES[index]
    product_names = []
    order = [input[3]]
    product_names.append(primary_language["Product names"][input[3]])
    for key, value in primary_language["Product names"].items():
        if input[key - 1] and key != input[3]:
            product_names.append(value)
            order.append(key)
    primary_language["Product names"] = product_names
    primary_language["Key order"] = order
    return primary_language

def convert_language(filtered_project_params, main_language):
    output = []
    for value in filtered_project_params:
        converted = [main_language[value[0]], value[1]]
        output.append(converted)
    output.append(["Total weight", main_language["Total weight"]])
    output.append(["Total price", main_language["Total price"]])
    output.append(["Material list", main_language["Material list"]])

    return output

def filter_project_info(project_params):
    result = []
    for param in project_params:
        result.append([param.Definition.Name, param.AsString()])
    
    author = result[6]
    client_name = result[13]
    address = result[14]
    project_name = result[15]
    supervisor = result[22]
    datetime = ["Date", date.today()]

    return [author, client_name, address, project_name, supervisor, datetime]

def get_headers(ml):
    names_length = len(ml["Product names"])
    count = ml["Count"]
    product_number = ml["Product number"]
    main_product_name = ml["Product names"][0]
    weight = ml["Weight"]
    list_price = ml["List price"]
    headers = [count, product_number, main_product_name, weight, list_price]
    if names_length > 1:
        for i in range(1, names_length):
            headers.append(ml["Product names"][i])
    
    return headers

main_language = get_main_language(IN[0])
project_params = FilteredElementCollector(dm.Instance.CurrentDBDocument).OfCategory(BuiltInCategory.OST_ProjectInformation).ToElements()[0].Parameters
filtered_project_params = filter_project_info(project_params)
project_info = convert_language(filtered_project_params, main_language)
headers = get_headers(main_language)
OUT = [project_info, headers, main_language["Key order"]]

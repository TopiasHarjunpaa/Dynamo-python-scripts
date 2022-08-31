default_path = IN[0]
project_info = IN[1]
list_name = project_info[8][1]
project_name = project_info[3][1]
date = project_info[5][1]

new_path = f"{default_path[:-13]}{list_name}  - {project_name} - {date}"
OUT = new_path

def create_project_info_and_headers(info, sums):
	info_list = []
	project_info = info[0]
	headers = info[1]
	for param in project_info[:-3]:
		info_list.append(f'{param[0]}: {param[1]}')
	
	info_list.append(f"{project_info[6][1]}: {sums[0]:.2f} kg")
	info_list.append(f"{project_info[7][1]}: {sums[1]:.2f} €")
	info_list.append('')
	info_list.append(headers)

	return info_list

def get_tarpaulin_parameters(length, width):
	tarpaulin_length = int(length)/1000
	tarpaulin_width = float(width)/1000
	tarpaulin_area = tarpaulin_length * tarpaulin_width
	return tarpaulin_length, tarpaulin_width, tarpaulin_area

def format_tarpaulin_product_number(product_number, length, width):
	if width != 2.572:
		return "KHTASAUS"
	return f"{product_number}{int(length)}"

def format_tarpaulin_names(fin, eng, swe, length, width):
	suffix = f" {width:.2f} x {length:.2f} m".replace(".", ",")
	if width == 0.154:
		suffix = f" {width:.3f} x {length:.2f} m".replace(".", ",")
	fin += suffix
	eng += suffix.replace("m", "M")
	swe += suffix
	return fin, eng, swe

def combine_lists(project_list, master_list, info):
	combined_list = []
	key_order = info[2]
	total_weight = 0
	total_price = 0
	roof_system = False

	for product in project_list[1:]:
		count = product[0]
		product_number = product[1]
		name_fin = product[2]
		name_eng = product[3]
		name_swe = product[4]
		weight = float(product[5])
		total_weight += weight * int(count)
		found = False

		if product_number == "KHKATT" and len(product) >= 8:
			roof_system = True
			tarpaulin_length, tarpaulin_width, tarpaulin_area = get_tarpaulin_parameters(product[6], product[7])
			edited_product_number = format_tarpaulin_product_number(product_number, tarpaulin_length, tarpaulin_width)
			edited_name_fin, edited_name_eng, edited_name_swe = format_tarpaulin_names(name_fin, name_eng, name_swe, tarpaulin_length, tarpaulin_width)
			
			weight = round(tarpaulin_area * 0.67, 1)
			price = round(tarpaulin_area * 12.7, 2)
			total_weight += weight * int(count)
			total_price += price * int(count)

			row = [count, edited_product_number, weight, price, edited_name_fin, edited_name_eng, edited_name_swe]
			sorted_row = sort_rows(key_order, row)
			combined_list.append(sorted_row)
			found = True
		else:
			for master_product in master_list[1:]:
				m_product_number = master_product[0]
				m_price = float(master_product[5])

				if product_number == m_product_number:
					row = [count, product_number, weight, m_price, name_fin, name_eng, name_swe]
					sorted_row = sort_rows(key_order, row)
					combined_list.append(sorted_row)
					total_price += m_price * int(count)
					found = True
					break

		if not found:
			row = [count, product_number, weight, '0', name_fin, name_eng, name_swe]
			sorted_row = sort_rows(key_order, row)
			combined_list.append(sorted_row)
		
	if roof_system:
		row = ["0", "KHPÄÄT", "0", "0", "Muista lisätä päätypeitteet", "REMEMBER GABLE TARPAULINS", "Komma ihåg gavelduk"]
		sorted_row = sort_rows(key_order, row)
		combined_list.append(sorted_row)

	return combined_list, (total_weight, total_price)

def sort_rows(key_order, row):
	"""Raw row order:
	0:	count
	1:	product number
	2:	weight
	3:	price
	4:	name FIN
	5:	name ENG
	6:	name SWE
	"""

	sorted_row = row[:2]
	names = row[4:]
	ordered_names = []

	for number in key_order:
		ordered_names.append(names[number - 1])
	
	sorted_row.append(ordered_names[0])
	sorted_row.append(row[2])
	sorted_row.append(row[3])

	for name in ordered_names[1:]:
		sorted_row.append(name)
	
	return sorted_row

combined_list, sums = combine_lists(IN[0], IN[1], IN[2])
project_info = create_project_info_and_headers(IN[2], sums)
OUT = project_info + combined_list

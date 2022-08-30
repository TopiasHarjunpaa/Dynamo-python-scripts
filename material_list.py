def CombineLists(first,second,headers, info):
	combinedList = []
	for param in info:
		combinedList.append(f'{param[0]}: {param[1]}')
	combinedList.append('')
	combinedList.append(headers)
	totalWeight = 0
	totalPrice = 0
	for a in first[1:]:
		newRow = []
		count = a[0]
		productNumber = a[2]
		found = False
		for b in second:
			if (productNumber == b[0]):
				productName = b[1]
				weight = b[4]
				price = b[5]
				combinedList.append([count,
									productNumber,
									productName,
									weight,
									price,
									b[2],
									b[3]
									])
				totalWeight += weight * int(count)
				totalPrice += price * int(count)
				found = True
				break
		if not found:
			combinedList.append([count,
								productNumber,
								a[1],
								'0',
								'0',
								'NA',
								'NA'
								])
	combinedList.append(['',
						'',
						'',
						totalWeight,
						totalPrice
						])

	return combinedList

OUT = CombineLists(IN[0], IN[1], IN[2], IN[3])
import math
import copy

class BaySetup:
    def __init__(self, count=0):
        self.bay_count = count
        self.bays = []

    def set_count(self, count):
        self.bay_count = count
    
    def get_count(self):
        return self.bay_count

    def get_bays(self):
        return self.bays

    def add_bay(self, bay):
        self.bays.append(bay)
        self.bay_count += 1
    
    def remove_bays(self):
        self.bays = []
    
    def check_sum(self):
        count = 0
        for bay in self.bays:
            count += bay
        return count
    
    def __str__(self):
        total_dist = self.check_sum()
        return f"count: {self.bay_count} - distance: {total_dist}"

def find_least_bays(distance, tolerance, bay_lengths):
    result = [BaySetup() for i in range(distance + tolerance + 1)]

    for i in range(1, distance + tolerance + 1):
        bay_setup = result[i]
        bay_setup.set_count(math.inf)
        result[i] = bay_setup

        for bay in bay_lengths:
            if bay <= i:
                new_bay_setup = result[i - bay]
                best_bay_setup = result[i]
                new_bay_setup_count = new_bay_setup.get_count()
                best_bay_setup_count = best_bay_setup.get_count()
    
                if new_bay_setup_count != math.inf and new_bay_setup_count + 1 < best_bay_setup_count:
                    bay_copy = copy.deepcopy(new_bay_setup)
                    bay_copy.add_bay(bay)
                    result[i] = bay_copy

    return sort_results(result, tolerance, distance)

def sort_results(result, tolerance, distance):
    best_results = []
    lowest_count = math.inf
    min_distance = max(0, distance - tolerance)
    for search_dist in range(min_distance, distance + tolerance + 1):
        bay_setup = result[search_dist]
        bay_setup_count = bay_setup.get_count()
        if bay_setup_count < lowest_count and bay_setup_count != 0:
            best_results = [bay_setup]
            lowest_count = bay_setup_count
        elif bay_setup_count == lowest_count and bay_setup_count != math.inf:
            best_results.append(bay_setup)
    
    return best_results

def compact_bays(list_of_bays, bay_lengths):
    compacted_list = []
    for bay in reversed(bay_lengths):
        count = list_of_bays.count(bay)
        if count > 0:
            info = f"{count} x {bay}"
            compacted_list.append(info)
    
    return compacted_list

bay_lengths = [154, 390, 450, 732, 1088, 1400, 1572, 2072, 2572]
tolerance = 125
distance = 100000


print(f"Targeted distance: {distance}")
results = find_least_bays(distance, tolerance, bay_lengths)
for result in results:
    info = ', '.join(compact_bays(result.get_bays(), bay_lengths))
    print(result)
    print(info)
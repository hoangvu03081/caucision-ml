from sortedcontainers import SortedList, SortedKeyList
import numpy as np
from paretoset import paretoset


def optimize_campaign(rows, capacity, costs):
    rows[:, 1::2] *= -1
    weight_columns = rows[:, 1::2]
    weighted_columns = weight_columns + costs
    rows[:, 1::2] = weighted_columns
    rows = rows.reshape((-1, rows.shape[1] // 2, 2))

    past_dominant_items = SortedList([], key=lambda x: -x[0])
    categories_count = rows.shape[1] / 2

    customer_count = len(rows)

    best_indices = []
    all_efficiency_angles = []  # this is an array of users' efficiency angles
    original_indices = []

    for customer_index, row in enumerate(rows):
        mask = paretoset(row, sense=["max", "min"], distinct=False)
        pareto_sorted = row[mask]
        original_row_indices = np.where(mask)[0]  # "original": before pareto sorted

        dominants = np.array(pareto_sorted)
        sorted_indices = np.argsort(dominants[:, 1])
        sorted_dominants = dominants[sorted_indices]

        original_indices.append(original_row_indices[sorted_indices])
        sorted_dominants = [sub_array[:2] for sub_array in sorted_dominants]

        differences = np.diff(sorted_dominants, axis=0)
        incremental_values = np.empty((len(sorted_dominants), 2))
        incremental_values[0] = sorted_dominants[0]
        incremental_values[1:] = differences

        efficiency_angles = []  # This is the array of **a** user's efficiency angles
        for idx, incremental_value in enumerate(incremental_values):
            incremental_value, incremental_weight = incremental_value

            if incremental_value == 0 and incremental_weight == 0:
                efficiency_angle = 3 * np.pi / 2
            elif incremental_value < 0 and incremental_weight <= 0:
                efficiency_angle = 2 * np.pi + np.arctan2(incremental_value, incremental_weight)
            else:
                efficiency_angle = np.arctan2(incremental_value, incremental_weight)

            item_weight = sorted_dominants[idx][1]

            past_dominant_items.add([efficiency_angle, item_weight])

            efficiency_angles.append(efficiency_angle)

        all_efficiency_angles.append(efficiency_angles)

    # efficiency_functions = calculate_efficiency_angle_functions(past_dominant_items)
    past_dominant_items_count = len(past_dominant_items)

    # The piece wise function is a list of pairs {𝜃𝑝, 𝑓(𝜃𝑝)}
    piece_wise_functions = SortedKeyList([], key=lambda x: x[1])
    piece_wise_functions.add([past_dominant_items[0][0], past_dominant_items[0][1] / past_dominant_items_count])

    previous_cumulative_weight = piece_wise_functions[0][1]

    # Note that index here starts from 0, but is actually 1 inside the algorithm
    for index, item in enumerate(past_dominant_items[1:]):
        efficiency_angle, item_weight = item
        efficiency_function = previous_cumulative_weight + past_dominant_items[index + 1][1] / past_dominant_items_count

        previous_cumulative_weight = efficiency_function
        piece_wise_functions.add([efficiency_angle, efficiency_function])

    minimum_angle = float('inf')
    minimum_angles = []
    for efficiency_angle, efficiency_function in piece_wise_functions:
        if efficiency_angle < minimum_angle:
            minimum_angle = efficiency_angle
        minimum_angles.append(minimum_angle)
    minimum_angles.append(minimum_angle)

    efficiency_functions = piece_wise_functions

    past_dominant_items_count = len(past_dominant_items)
    for user_index, efficiency_angles in enumerate(all_efficiency_angles):
        # Description: Calculate efficiency threshold
        current_customer_index = user_index + 1
        comparison_factor = capacity / (
                (past_dominant_items_count / customer_count) * (customer_count - current_customer_index + 1))

        valid_cumulative_weight_index = efficiency_functions.bisect_key_left(comparison_factor)
        efficiency_threshold = minimum_angles[valid_cumulative_weight_index]

        # Description: Pick the suitable angle
        min_angle = float('inf')
        min_index = -1

        promotion_count = len(costs)

        for index, angle in enumerate(efficiency_angles):
            if angle >= efficiency_threshold and angle < min_angle:
                min_angle = angle
                min_index = index

        if min_index == -1:
            best_indices.append(promotion_count)
            continue

        treatment_index = original_indices[user_index][min_index]
        best_indices.append(treatment_index)
        capacity -= rows[user_index][treatment_index][1]

    return np.array(best_indices)

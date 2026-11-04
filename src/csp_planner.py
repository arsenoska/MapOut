
from src.route_matrix import get_route_matrix


# Generate a multi-day itinerary using Constraint Satisfaction and backtracking
def generate_csp_itinerary(
    attractions,
    destination,
    interests,
    budget,
    days,
    minutes_per_day,
    transport_mode="walking",
    max_transfer_minutes=None
):
    # Check that the user's trip preferences are valid
    if days <= 0 or minutes_per_day <= 0 or budget < 0:
        raise ValueError("Invalid trip preferences")

    if transport_mode not in ("walking", "driving"):
        raise ValueError("Invalid transportation mode")

    # Set the maximum travel time allowed between attractions
    if max_transfer_minutes is None:
        max_transfer_minutes = (
            25 if transport_mode == "walking" else 20
        )

    if max_transfer_minutes <= 0:
        raise ValueError("Invalid maximum transfer time")

    # Prepare interests for matching, ignoring uppercase/lowercase differences
    selected_interests = {
        interest.strip().lower()
        for interest in interests
    }

    # Find attractions that match the destination, interests, and constraints
    suitable = []

    for attraction in attractions:
        # Skip attractions outside the selected city
        if attraction["city"].strip().lower() != destination.strip().lower():
            continue

        # An attraction can belong to multiple categories
        # Support categories stored as either a list or a string
        categories_value = attraction["categories"]

        if isinstance(categories_value, str):
            categories_value = categories_value.split("|")

        categories = {
            category.strip().lower()
            for category in categories_value
        }

        # Keep an attraction if at least one category matches an interest
        if not categories.intersection(selected_interests):
            continue

        # Read and check the attraction's cost, duration, and coordinates
        try:
            cost = float(attraction["estimated_cost_eur"])
            duration = int(attraction["visit_duration_min"])
            latitude = float(attraction["latitude"])
            longitude = float(attraction["longitude"])
        except (ValueError, TypeError):
            continue

        if cost < 0 or duration <= 0:
            continue

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue

        # Keep only attractions that can individually fit the trip limits
        if cost <= budget and duration <= minutes_per_day:
            suitable.append(attraction)

    # Limit the number of attractions to keep the prototype manageable
    if len(suitable) > 20:
        raise ValueError(
            "More than 20 matching attractions. "
            "Narrow the interests for this prototype."
        )

    # Get real travel times and distances before starting backtracking
    matrix = get_route_matrix(suitable, transport_mode)

    durations = matrix["durations"]
    distances = matrix["distances"]

    # Look up the travel time and distance between two attractions
    def route(first, second):
        # Attractions are identified by their positions in the suitable list
        if first == second:
            return 0.0, 0.0

        minutes = durations[first][second]
        kilometers = distances[first][second]

        # Return None when no valid route is available
        if minutes is None or kilometers is None:
            return None

        return minutes, kilometers

    # Check whether a new attraction is close enough to the others in a day
    def is_nearby(attraction_index, day):
        for existing_index in day:
            # Check travel time in both directions
            forward = route(existing_index, attraction_index)
            backward = route(attraction_index, existing_index)

            if forward is None or backward is None:
                return False

            # Reject attractions that exceed the maximum transfer time
            if max(forward[0], backward[0]) > max_transfer_minutes:
                return False

        return True

    # Arrange daily attractions using the nearest-neighbor approach
    def order_day(day):
        if len(day) <= 1:
            return day.copy()

        best_order = None
        best_time = float("inf")

        # Try each attraction as a possible starting point
        for start in day:
            remaining = [i for i in day if i != start]
            ordered = [start]
            total_time = 0.0

            while remaining:
                current = ordered[-1]

                # Find attractions reachable from the current location
                reachable = [
                    i for i in remaining
                    if route(current, i) is not None
                ]

                if not reachable:
                    break

                # Choose the nearest unvisited attraction by travel time
                nearest = min(
                    reachable,
                    key=lambda i: route(current, i)[0]
                )

                total_time += route(current, nearest)[0]
                ordered.append(nearest)
                remaining.remove(nearest)

            # Keep the visiting order with the shortest travel time found
            if not remaining and total_time < best_time:
                best_time = total_time
                best_order = ordered

        return best_order

    # Calculate the cost, visiting time, and travel time for one day
    def day_details(day):
        ordered = order_day(day)

        if ordered is None:
            return None

        # Sum the time spent visiting attractions
        visit_minutes = sum(
            int(suitable[i]["visit_duration_min"])
            for i in ordered
        )

        # Sum the estimated entrance costs
        cost = sum(
            float(suitable[i]["estimated_cost_eur"])
            for i in ordered
        )

        travel_minutes = 0.0
        distance_km = 0.0

        # Add travel time and distance between consecutive attractions
        for i in range(len(ordered) - 1):
            segment = route(ordered[i], ordered[i + 1])

            travel_minutes += segment[0]
            distance_km += segment[1]

        # Return the calculated daily itinerary
        return {
            "attractions": [
                suitable[i] for i in ordered
            ],
            "cost": round(cost, 2),
            "visit_minutes": visit_minutes,
            "travel_minutes": round(travel_minutes, 1),
            "minutes": round(
                visit_minutes + travel_minutes, 1
            ),
            "distance_km": round(distance_km, 2)
        }

    # Create empty days and store the best solution found
    itinerary = [[] for _ in range(days)]
    best_itinerary = [[] for _ in range(days)]

    best_score = None
    best_count = -1

    # Limit the number of search steps to avoid excessive computation
    search_nodes = 0
    max_search_nodes = 15000

    # Compare the current itinerary with the best solution found so far
    def evaluate_solution():
        nonlocal best_itinerary, best_score, best_count

        count = sum(len(day) for day in itinerary)
        used_days = sum(bool(day) for day in itinerary)

        total_travel = sum(
            day_details(day)["travel_minutes"]
            for day in itinerary
        )

        # Prefer more attractions, less travel time, and more used days
        score = (-count, total_travel, -used_days)

        if best_score is None or score < best_score:
            best_score = score
            best_count = count
            best_itinerary = [
                day.copy() for day in itinerary
            ]

    # Use backtracking to explore possible attraction assignments
    def backtrack(index, total_cost):
        nonlocal search_nodes

        # Stop searching when the maximum number of steps is reached
        if search_nodes >= max_search_nodes:
            return

        search_nodes += 1

        # Evaluate the itinerary when all attractions have been considered
        if index == len(suitable):
            evaluate_solution()
            return

        selected_count = sum(
            len(day) for day in itinerary
        )

        remaining = len(suitable) - index

        # Skip branches that cannot improve the number of attractions
        if selected_count + remaining < best_count:
            return

        attraction = suitable[index]
        cost = float(attraction["estimated_cost_eur"])

        # Only consider the attraction if it fits the remaining budget
        if total_cost + cost <= budget:

            # Try days with fewer attractions first
            day_order = sorted(
                range(days),
                key=lambda i: len(itinerary[i])
            )

            tried_empty_day = False

            for day_index in day_order:
                day = itinerary[day_index]

                # Avoid exploring equivalent empty-day assignments
                if not day:
                    if tried_empty_day:
                        continue
                    tried_empty_day = True

                # Check whether the attraction is close enough
                if not is_nearby(index, day):
                    continue

                candidate = day + [index]
                details = day_details(candidate)

                if details is None:
                    continue

                # Check the daily limit using visiting time and real travel time
                if details["minutes"] > minutes_per_day:
                    continue

                # Add the attraction and explore the next possibility
                day.append(index)
                backtrack(index + 1, total_cost + cost)

                # Remove the attraction to try a different assignment
                day.pop()

        # Also explore the possibility of skipping this attraction
        backtrack(index + 1, total_cost)

    # Start with an empty solution and search for a better itinerary
    evaluate_solution()
    backtrack(0, 0.0)

    # Calculate the final details for every day
    daily_results = [
        day_details(day)
        for day in best_itinerary
    ]

    # Return the complete itinerary and overall trip totals
    return {
        "days": daily_results,
        "transport_mode": transport_mode,
        "total_cost": round(
            sum(day["cost"] for day in daily_results), 2
        ),
        "total_attractions": sum(
            len(day["attractions"]) for day in daily_results
        ),
        "total_visit_minutes": sum(
            day["visit_minutes"] for day in daily_results
        ),
        "total_travel_minutes": round(
            sum(day["travel_minutes"] for day in daily_results), 1
        ),
        "total_distance_km": round(
            sum(day["distance_km"] for day in daily_results), 2
        ),
        "search_limit_reached": (
            search_nodes >= max_search_nodes
        )
    }

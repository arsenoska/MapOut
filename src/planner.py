def generate_itinerary(attractions, destination, interests, budget, available_minutes):

    # Store the attractions selected for the itinerary
    itinerary = []

    # Track the total cost and visit duration
    total_cost = 0
    total_duration = 0

    # Go through each attraction in the dataset
    for attraction in attractions:

        # Skip attractions that are not in the selected city
        if attraction["city"].lower() != destination.lower():
            continue



        # Skip attractions that do not match the user's interests
        if not any(
            interest.lower() in [category.lower() for category in attraction["categories"]]
            for interest in interests
        ):
            continue



        # Get the estimated visit duration of the attraction
        duration = attraction["visit_duration_min"]

        # Skip the attraction if it exceeds the available time
        if total_duration + duration > available_minutes:
            continue



        # Get the estimated cost of the attraction
        cost = attraction["estimated_cost_eur"]

        # Skip attractions with unknown costs
        if cost is None:
            continue

        # Skip attractions that exceed the remaining budget
        if total_cost + cost > budget:
            continue



        # Add the attraction to the itinerary
        itinerary.append(attraction)

        # Update the total cost and visit duration
        total_cost += cost
        total_duration += duration


    return itinerary, total_cost, total_duration


from src.data_loader import load_attractions
from src.csp_planner import generate_csp_itinerary


# Ask the user for a valid positive whole number
def ask_positive_int(prompt):
    while True:
        try:
            value = int(input(prompt))

            if value > 0:
                return value

            print("Please enter a number greater than zero.")

        except ValueError:
            print("Invalid input. Please enter a whole number.")


# Ask the user for a valid non-negative budget
def ask_budget():
    while True:
        try:
            budget = float(input("Total budget in EUR: "))

            if 0 <= budget < float("inf"):
                return budget

            print("Please enter a valid non-negative budget.")

        except ValueError:
            print("Invalid input. Please enter a number.")


# Ask the user to choose walking or driving
def ask_transport():
    while True:
        mode = input(
            "Transport mode (walking/driving): "
        ).strip().lower()

        if mode in ("walking", "driving"):
            return mode

        print("Please choose 'walking' or 'driving'.")


# Format an attraction's price for display
def format_attraction_price(attraction):
    raw_price = attraction.get("estimated_cost_eur")

    # Blank means unknown, not free
    if raw_price is None or str(raw_price).strip() == "":
        return "Price unknown"

    try:
        price = float(raw_price)

        if price == 0:
            return "Free"

        return f"Estimated €{price:.2f}"

    except (ValueError, TypeError):
        return "Price unknown"


# Collect trip preferences from the user
def get_user_preferences(attractions):
    destinations = sorted({
        attraction["city"].strip()
        for attraction in attractions
        if attraction.get("city", "").strip()
    })

    print("\n===== Welcome to MapOut =====")
    print("\nAvailable destinations:")
    print(", ".join(destinations))

    while True:
        destination_input = input(
            "\nChoose a destination: "
        ).strip()

        destination = next(
            (
                city for city in destinations
                if city.lower() == destination_input.lower()
            ),
            None
        )

        if destination is not None:
            break

        print(
            "Destination not found. "
            "Please choose from the list."
        )

    days = ask_positive_int("Number of days: ")
    budget = ask_budget()

    hours = ask_positive_int(
        "Available sightseeing hours per day: "
    )
    minutes_per_day = hours * 60

    # Show available interests for the destination
    categories = set()

    for attraction in attractions:
        if (
            attraction["city"].strip().lower()
            != destination.lower()
        ):
            continue

        value = attraction.get("categories", [])

        if isinstance(value, str):
            value = value.split("|")

        for category in value:
            if category.strip():
                categories.add(category.strip())

    available_interests = sorted(categories)

    print("\nAvailable interests:")
    print(", ".join(available_interests))

    while True:
        entered = input(
            "Choose interests (separated by commas): "
        )

        requested = [
            item.strip()
            for item in entered.split(",")
            if item.strip()
        ]

        interests = []

        for item in requested:
            match = next(
                (
                    category for category in available_interests
                    if category.lower() == item.lower()
                ),
                None
            )

            if match and match not in interests:
                interests.append(match)

        if interests:
            break

        print(
            "Please choose at least one valid interest."
        )

    transport_mode = ask_transport()

    max_transfer_minutes = (
        25 if transport_mode == "walking" else 20
    )

    return {
        "destination": destination,
        "interests": interests,
        "budget": budget,
        "days": days,
        "minutes_per_day": minutes_per_day,
        "transport_mode": transport_mode,
        "max_transfer_minutes": max_transfer_minutes,
    }


# Display the generated itinerary and trip summary
def display_itinerary(result, destination, days):
    print(
        f"\n===== MapOut - {days}-Day Trip "
        f"to {destination} ====="
    )

    print(
        "Transportation:",
        result["transport_mode"].capitalize()
    )

    # Explain candidate selection when a large dataset was filtered
    matching_count = result.get(
        "total_matching_attractions"
    )

    considered_count = result.get(
        "csp_candidates_considered"
    )

    candidate_limit_applied = result.get(
        "candidate_limit_applied",
        False
    )

    if candidate_limit_applied:
        print("\nAttraction selection:")
        print(
            f"  {matching_count} attractions matched "
            "your destination, interests, and basic constraints."
        )
        print(
            f"  MapOut selected {considered_count} candidates "
            "for detailed route planning."
        )
        print(
            "  Candidates were selected using interest relevance, "
            "proximity, visit duration, and recorded costs."
        )
        print(
            "  Note: Other matching attractions were not "
            "included in this search."
        )

    # Display each day
    for day_number, day in enumerate(
        result["days"],
        start=1
    ):
        print(f"\nDay {day_number}:")

        if not day["attractions"]:
            print(
                "No attractions planned for this day."
            )

        for attraction in day["attractions"]:
            print(f"  - {attraction['name']}")

            print(
                f"    Visit duration: "
                f"{attraction['visit_duration_min']} minutes"
            )

            print(
                f"    Price: "
                f"{format_attraction_price(attraction)}"
            )

        print(
            f"\n  Visit time: "
            f"{day['visit_minutes']} minutes"
        )

        print(
            f"  Travel time: "
            f"{day['travel_minutes']:.1f} minutes"
        )

        print(
            f"  Total time: "
            f"{day['minutes']:.1f} minutes"
        )

        print(
            f"  Route distance: "
            f"{day['distance_km']:.2f} km"
        )

        known_cost = day.get(
            "known_cost",
            day["cost"]
        )

        unknown_count = day.get(
            "unknown_price_count",
            0
        )

        print(
            f"  Known estimated cost: "
            f"€{known_cost:.2f}"
        )

        if unknown_count > 0:
            print(
                f"  Attractions with unknown prices: "
                f"{unknown_count}"
            )

            print(
                "  Note: Actual costs may be higher "
                "because some prices are unknown."
            )

    # Display trip totals
    print("\n===== Trip Summary =====")

    print(
        "Total attractions:",
        result["total_attractions"]
    )

    total_known_cost = result.get(
        "total_known_cost",
        result["total_cost"]
    )

    total_unknown_prices = result.get(
        "unknown_price_count",
        0
    )

    print(
        f"Known estimated trip cost: "
        f"€{total_known_cost:.2f}"
    )

    print(
        f"Attractions with unknown prices: "
        f"{total_unknown_prices}"
    )

    print(
        f"Total visit time: "
        f"{result['total_visit_minutes']} minutes"
    )

    print(
        f"Total travel time: "
        f"{result['total_travel_minutes']:.1f} minutes"
    )

    print(
        f"Total route distance: "
        f"{result['total_distance_km']:.2f} km"
    )

    # Explain unknown-price limitations
    if total_unknown_prices > 0:
        print("\nIMPORTANT:")
        print(
            "Some attractions have unconfirmed prices."
        )
        print(
            "The amount shown includes only "
            "recorded admission estimates."
        )
        print(
            "The actual trip cost may be higher "
            "than the displayed amount."
        )
        print(
            "Please confirm admission prices "
            "before your trip."
        )

    # Explain search limitations
    if result.get("search_limit_reached", False):
        print(
            "\nNote: The search limit was reached. "
            "A better itinerary may exist."
        )

    if candidate_limit_applied:
        print(
            "\nNote: This itinerary was generated "
            "from a selected subset of matching attractions."
        )
        print(
            "It is not guaranteed to be the optimal itinerary "
            "across the entire dataset."
        )

    print("========================")


# Main application entry point
def main():
    attractions = load_attractions()

    preferences = get_user_preferences(attractions)

    print(
        "\nGenerating your personalized itinerary..."
    )

    try:
        result = generate_csp_itinerary(
            attractions=attractions,
            **preferences
        )

        display_itinerary(
            result,
            preferences["destination"],
            preferences["days"]
        )

    except ValueError as error:
        print(
            f"\nUnable to generate itinerary: {error}"
        )


if __name__ == "__main__":
    main()

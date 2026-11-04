
from src.data_loader import load_attractions
from src.csp_planner import generate_csp_itinerary
from src.route_matrix import get_route_matrix


# Choose the test scenario
destination = "Ohrid"
interests = ["History", "Culture", "Nature", "Relaxation", "Adventure"]
budget = 50
days = 3
minutes_per_day = 360
transport_mode = "driving"
max_transfer_minutes = 20

attractions = load_attractions()

# Generate itinerary using real routing data
result = generate_csp_itinerary(
    attractions=attractions,
    destination=destination,
    interests=interests,
    budget=budget,
    days=days,
    minutes_per_day=minutes_per_day,
    transport_mode=transport_mode,
    max_transfer_minutes=max_transfer_minutes
)

print(
    f"\nMapOut - {days}-Day Trip to {destination}"
    f" ({transport_mode.capitalize()})"
)

selected_ids = []

for day_number, day in enumerate(result["days"], start=1):
    print(f"\nDay {day_number}:")

    for attraction in day["attractions"]:
        print(f"  - {attraction['name']}")
        print(
            f"    Visit duration: "
            f"{attraction['visit_duration_min']} minutes"
        )
        print(
            f"    Estimated cost: "
            f"€{float(attraction['estimated_cost_eur']):.2f}"
        )

        selected_ids.append(attraction["id"])

        assert attraction["city"].lower() == destination.lower()

        categories = {
            category.strip().lower()
            for category in attraction["categories"].split("|")
        }

        assert any(
            interest.lower() in categories
            for interest in interests
        )

    print(f"\n  Visit time: {day['visit_minutes']} minutes")
    print(f"  Travel time: {day['travel_minutes']:.1f} minutes")
    print(f"  Total time: {day['minutes']:.1f} minutes")
    print(f"  Daily cost: €{day['cost']:.2f}")
    print(f"  Route distance: {day['distance_km']:.2f} km")

    # Verify daily time constraint
    assert day["minutes"] <= minutes_per_day + 0.1

    # Verify daily cost
    calculated_cost = sum(
        float(a["estimated_cost_eur"])
        for a in day["attractions"]
    )
    assert abs(calculated_cost - day["cost"]) < 0.01

# Verify no attraction appears twice
assert len(selected_ids) == len(set(selected_ids))

# Verify overall constraints
assert len(result["days"]) == days
assert len(selected_ids) == result["total_attractions"]
assert result["total_cost"] <= budget + 0.01

# Verify geographic grouping with the cached matrix
selected = [
    attraction
    for day in result["days"]
    for attraction in day["attractions"]
]

if selected:
    matrix = get_route_matrix(selected, transport_mode)
    positions = {
        attraction["id"]: index
        for index, attraction in enumerate(selected)
    }

    for day in result["days"]:
        items = day["attractions"]

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a = positions[items[i]["id"]]
                b = positions[items[j]["id"]]

                forward = matrix["durations"][a][b]
                backward = matrix["durations"][b][a]

                assert forward is not None
                assert backward is not None
                assert max(forward, backward) <= max_transfer_minutes

print("\nTrip Summary")
print(f"Total attractions: {result['total_attractions']}")
print(f"Total cost: €{result['total_cost']:.2f}")
print(
    f"Total travel time: "
    f"{result['total_travel_minutes']:.1f} minutes"
)
print(
    f"Total route distance: "
    f"{result['total_distance_km']:.2f} km"
)

if result["search_limit_reached"]:
    print("\nNote: Search limit reached; solution may improve.")

print("\nAll CSP planner tests passed!")

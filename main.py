from src.data_loader import load_attractions
from src.csp_planner import generate_csp_itinerary


# Load attractions from the CSV file
attractions = load_attractions()


# Set the user's trip preferences
destination = "Ohrid"
interests = ["History", "Culture", "Nature", "Relaxation", "Adventure"]
budget = 50
days = 3
minutes_per_day = 360
transport_mode = "driving"
max_transfer_minutes = 20


# Generate a multi-day itinerary using the CSP planner
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


# Display the generated itinerary for each day
print(f"\n===== MapOut - {days}-Day Trip to {destination} =====")
print("Transportation:", transport_mode.capitalize())

for day_number, day in enumerate(result["days"], start=1):
    print(f"\nDay {day_number}:")

    if not day["attractions"]:
        print("No attractions planned for this day.")

    for attraction in day["attractions"]:
        print(f"  - {attraction['name']}")
        print(f"    Visit duration: {attraction['visit_duration_min']} minutes")
        print(f"    Estimated cost: €{float(attraction['estimated_cost_eur']):.2f}")

    # Display the daily cost, duration, and travel distance
    print(f"\n  Visit time: {day['visit_minutes']} minutes")
    print(f"  Travel time: {day['travel_minutes']:.1f} minutes")
    print(f"  Total time: {day['minutes']:.1f} minutes")
    print(f"  Daily cost: €{day['cost']:.2f}")
    print(f"  Route distance: {day['distance_km']:.2f} km")


# Display the overall trip summary
print("\n===== Trip Summary =====")
print("Total attractions:", result["total_attractions"])
print(f"Total cost: €{result['total_cost']:.2f}")
print(f"Total visit time: {result['total_visit_minutes']} minutes")
print(f"Total travel time: {result['total_travel_minutes']:.1f} minutes")
print(f"Total route distance: {result['total_distance_km']:.2f} km")

if result["search_limit_reached"]:
    print("Note: Search limit reached; a better solution may exist.")

print("========================")

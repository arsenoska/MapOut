from src.data_loader import load_attractions
from src.validator import validate_attractions
from src.planner import generate_itinerary


# Display the generated itinerary for testing
def display_itinerary(destination, itinerary, total_cost, total_duration):

    print("\n===== MapOut Baseline Itinerary =====")
    print("Destination:", destination)

    if not itinerary:
        print("No attractions found for the selected preferences.")

    for attraction in itinerary:
        print("-", attraction["name"])

    print("Total estimated cost:", total_cost, "EUR")
    print("Total visit duration:", total_duration, "minutes")
    print("===================================")


# Load and validate the dataset
attractions = load_attractions()
attractions_list, total, valid, warnings = validate_attractions(attractions)



# Test 1: Ohrid - History and Culture
itinerary, total_cost, total_duration = generate_itinerary(
    attractions_list,
    "Ohrid",
    ["History", "Culture"],
    10,
    180
)

# Check that the itinerary respects the limits
assert total_cost <= 10
assert total_duration <= 180
assert len(itinerary) > 0
assert all(attraction["city"] == "Ohrid" for attraction in itinerary)

# Check that the selected attractions match the user's interests
assert all(
    any(interest in attraction["categories"] for interest in ["History", "Culture"])
    for attraction in itinerary
)

print("Test 1 passed: Ohrid itinerary respects city, interests, budget, and time limits.")

# Display the Ohrid itinerary
display_itinerary("Ohrid", itinerary, total_cost, total_duration)



# Test 2: Gostivar - Nature and Relaxation
itinerary, total_cost, total_duration = generate_itinerary(
    attractions_list,
    "Gostivar",
    ["Nature", "Relaxation"],
    5,
    180
)

# Check that the itinerary respects the limits
assert total_cost <= 5
assert total_duration <= 180
assert len(itinerary) > 0
assert all(attraction["city"] == "Gostivar" for attraction in itinerary)

# Check that the selected attractions match the user's interests
assert all(
    any(interest in attraction["categories"] for interest in ["Nature", "Relaxation"])
    for attraction in itinerary
)

print("Test 2 passed: Gostivar itinerary respects city, interests, budget, and time limits.")

# Display the Gostivar itinerary
display_itinerary("Gostivar", itinerary, total_cost, total_duration)



# Test 3: Tetovo - History and Culture
itinerary, total_cost, total_duration = generate_itinerary(
    attractions_list,
    "Tetovo",
    ["History", "Culture"],
    5,
    180
)

# Check that the itinerary respects the limits
assert total_cost <= 5
assert total_duration <= 180
assert len(itinerary) > 0
assert all(attraction["city"] == "Tetovo" for attraction in itinerary)

# Check that the selected attractions match the user's interests
assert all(
    any(interest in attraction["categories"] for interest in ["History", "Culture"])
    for attraction in itinerary
)

print("Test 3 passed: Tetovo itinerary respects city, interests, budget, and time limits.")

# Display the Tetovo itinerary
display_itinerary("Tetovo", itinerary, total_cost, total_duration)
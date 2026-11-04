
from src.data_loader import load_attractions
from src.route_matrix import get_route_matrix


# Load MapOut attractions
attractions = load_attractions()


def find_attraction(name):
    for attraction in attractions:
        if attraction["name"] == name:
            return attraction

    raise ValueError(f"Attraction not found: {name}")


# Select two attractions
susica = find_attraction("Church of St. Nicholas, Sušica")
vrutok = find_attraction("Vardar River Source at Vrutok")

print("\nMapOut - Real Route Testing")
print(f"From: {susica['name']}")
print(f"To: {vrutok['name']}")


# Test walking and driving using the route matrix
for mode in ["walking", "driving"]:
    try:
        matrix = get_route_matrix([susica, vrutok], mode)

        # Get the route from the first attraction to the second
        distance = matrix["distances"][0][1]
        duration = matrix["durations"][0][1]

        # Check that a valid route was found
        assert distance is not None
        assert duration is not None

        print(f"\n{mode.capitalize()} route:")
        print(f"Distance: {distance:.2f} km")
        print(
            f"Estimated travel time: "
            f"{duration:.1f} minutes"
        )

        # Verify the routing results
        assert distance >= 0
        assert duration >= 0

        print(f"{mode.capitalize()} routing test passed!")

    except RuntimeError as error:
        print(f"\n{mode.capitalize()} route unavailable:")
        print(error)
        raise


print("\nAll routing tests passed!")


import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv


# Find the main project folder and load the API key from .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Folder used to save routing results for future use
CACHE_DIR = PROJECT_ROOT / ".cache"

# Match user transportation choices with OpenRouteService profiles
PROFILES = {
    "walking": "foot-walking",
    "driving": "driving-car"
}


# Get real travel times and distances between all selected attractions
def get_route_matrix(attractions, transport_mode):
    # Check that the transportation mode is supported
    if transport_mode not in PROFILES:
        raise ValueError("Use walking or driving")

    # Return empty results when there are no attractions
    if not attractions:
        return {"durations": [], "distances": []}

    # Prepare coordinates in longitude, latitude order for the API
    coordinates = [
        [
            float(a["longitude"]),
            float(a["latitude"])
        ]
        for a in attractions
    ]

    # Create a unique identifier for these locations and transport mode
    import hashlib

    cache_data = json.dumps(
        [transport_mode, coordinates]
    )

    cache_id = hashlib.sha256(
        cache_data.encode("utf-8")
    ).hexdigest()[:20]

    # Create the cache folder and determine where to save the matrix
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"matrix_{cache_id}.json"

    # Use previously saved results instead of requesting them again
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as file:
            return json.load(file)

    # Read the OpenRouteService API key from the environment
    api_key = os.getenv("ORS_API_KEY")

    if not api_key:
        raise ValueError("ORS_API_KEY is missing")

    # Select the correct API profile for walking or driving
    profile = PROFILES[transport_mode]

    url = (
        "https://api.openrouteservice.org"
        f"/v2/matrix/{profile}"
    )

    # Prepare the request with coordinates and required measurements
    request_data = json.dumps({
        "locations": coordinates,
        "metrics": ["distance", "duration"],
        "units": "km"
    }).encode("utf-8")

    # Create the HTTP POST request to OpenRouteService
    request = Request(
        url,
        data=request_data,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )

    # Send the request and read the routing results
    try:
        with urlopen(request, timeout=60) as response:
            result = json.load(response)

    # Handle API errors, including too many requests
    except HTTPError as error:
        if error.code == 429:
            raise RuntimeError(
                "OpenRouteService rate limit reached. "
                "Wait until the limit resets before trying again."
            ) from error

        details = error.read().decode(
            "utf-8", errors="replace"
        )

        raise RuntimeError(
            f"Matrix API error {error.code}: {details}"
        ) from error

    # Handle connection problems or request timeouts
    except (URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Matrix connection failed: {error}"
        ) from error

    # Check that the API returned a complete matrix
    n = len(attractions)

    durations = result.get("durations")
    distances = result.get("distances")

    if (
        not isinstance(durations, list)
        or not isinstance(distances, list)
        or len(durations) != n
        or len(distances) != n
        or any(len(row) != n for row in durations)
        or any(len(row) != n for row in distances)
    ):
        raise RuntimeError("Invalid routing matrix response")

    # Convert travel durations from seconds into minutes
    matrix = {
        "durations": [
            [
                None if value is None else value / 60
                for value in row
            ]
            for row in durations
        ],
        "distances": distances
    }

    # Save the successful matrix so future tests can reuse it
    with open(cache_file, "w", encoding="utf-8") as file:
        json.dump(matrix, file, indent=2)

    # Return the travel times and distances to the CSP planner
    return matrix

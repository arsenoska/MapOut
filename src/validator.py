
# Categories supported by MapOut
valid_categories = [
    "History",
    "Culture",
    "Nature",
    "Adventure",
    "Relaxation",
    "Food",
    "Entertainment",
    "Beach",
    "Shopping",
    "Museum",
    "Art",
    "Family",
    "Archaeology",
    "Literature",
    "Music"
]


def validate_attractions(attractions):

    # Count attractions and validation results
    total_attractions = 0
    valid_attractions = 0
    warning_count = 0


    # Store IDs to detect duplicates
    used_ids = set()


    # Store validated attractions for itinerary planning
    attractions_list = []


    for attraction in attractions:

        total_attractions += 1

        # Check for missing fields or extra values in the CSV row
        if None in attraction or any(
            attraction[column] is None for column in attraction
        ):
            print("Warning: Incomplete or malformed CSV row:", total_attractions)
            warning_count += 1
            continue

        # Track warnings for the current attraction
        has_warning = False



        # Check if attraction ID is missing or invalid
        try:
            attraction_id = int(attraction["id"])

            if attraction_id <= 0:
                print("Warning: Invalid ID for", attraction["name"])
                has_warning = True
                warning_count += 1
                continue

        except (ValueError, TypeError):
            print("Warning: Invalid ID for", attraction["name"])
            has_warning = True
            warning_count += 1
            continue

        # Check for duplicate IDs
        if attraction_id in used_ids:
            print("Warning: Duplicate ID for", attraction["name"])
            has_warning = True
            warning_count += 1
            continue



        # Check if the attraction name is missing
        if not attraction["name"].strip():
            print("Warning: Attraction name is missing!")
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue



        # Check if the attraction source is missing
        if not attraction["source"].strip():
            print("Warning: Missing source for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue


        
        # Check if availability information is missing
        if not attraction["availability"].strip():
            print("Warning: Missing availability for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue



        # Check if city or region is missing
        if not attraction["city"].strip():
            print("Warning: Missing city for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue

        if not attraction["region"].strip():
            print("Warning: Missing region for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue


        
        # Split attraction categories into a list
        categories = [
            category.strip()
            for category in attraction["categories"].split("|")
        ]

        # Check if categories are missing or invalid
        if not categories or any(
            category not in valid_categories for category in categories
        ):
            print("Warning: Invalid categories for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue



        # Check if geographical coordinates are missing
        if not attraction["latitude"] or not attraction["longitude"]:
            print("Warning: Missing coordinates for", attraction["name"])
            warning_count += 1
            continue

        # Check whether coordinates contain valid numbers
        try:
            latitude = float(attraction["latitude"])
            longitude = float(attraction["longitude"])

            # Check if coordinates are within valid geographical ranges
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                print("Warning: Coordinates out of range for", attraction["name"])
                warning_count += 1
                continue

        except ValueError:
            print("Warning: Invalid coordinates for", attraction["name"])
            warning_count += 1
            continue



        # Check if the attraction cost is unknown
        if attraction["estimated_cost_eur"] == "":
            cost = None
            print("Info: Unknown cost for", attraction["name"])
        else:
            # Convert the cost into a number
            try:
                cost = float(attraction["estimated_cost_eur"])
            except ValueError:
                print("Warning: Invalid cost for", attraction["name"])
                has_warning = True
                warning_count += 1
                continue

        # Check if the cost is negative
        if cost is not None and cost < 0:
            print("Warning: Negative cost for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue



        # Convert visit duration into an integer
        try:
            duration = int(attraction["visit_duration_min"])
        except ValueError:
            print("Warning: Invalid duration for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue

        # Check if the duration is zero or negative
        if duration <= 0:
            print("Warning: Invalid duration for", attraction["name"])
            print("------------------------------")
            has_warning = True
            warning_count += 1
            continue



        # Display the attraction information
        print("Name:", attraction["name"])
        print("City:", attraction["city"])
        print("Region:", attraction["region"])
        print("Categories:", ", ".join(categories))

        if cost is None:
            print("Estimated Cost: Unknown")
        else:
            print("Estimated Cost:", cost, "EUR")

        print("Visit Duration:", duration, "minutes")
        print("------------------------------")



        used_ids.add(attraction_id)

        # Store the validated attraction
        attractions_list.append({
            "id": attraction_id,
            "name": attraction["name"],
            "city": attraction["city"],
            "region": attraction["region"],
            "categories": categories,
            "latitude": latitude,
            "longitude": longitude,
            "estimated_cost_eur": cost,
            "visit_duration_min": duration,
            "availability": attraction["availability"],
            "source": attraction["source"]
        })



        # Count attractions without validation warnings
        if not has_warning:
            valid_attractions += 1


    # Return validated attractions and validation statistics
    return attractions_list, total_attractions, valid_attractions, warning_count

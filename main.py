import csv

# Categories supported by MapOut
valid_categories = [
    "History",
    "Adventure",
    "Relaxation",
    "Food",
    "Entertainment"
]

# Count data validation warnings
warning_count = 0

# Open the attractions dataset in read mode
with open("attractions.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file) # Read each row using the column names, storeas each attraction as a dictionary
    
    for attraction in reader:

        # Check if the attraction name is missing
        if not attraction["name"]:
            print("Warning: Attraction name is missing!")
            print("------------------------------")
            continue


        # Check if the attraction category is valid
        if attraction["category"] not in valid_categories:
            print("Warning: Invalid category for", attraction["name"])
            print("------------------------------")
            continue


        # Check if geographical coordinates are missing
        if not attraction["latitude"] or not attraction["longitude"]:
            print("Warning: Missing coordinates for", attraction["name"])
            warning_count += 1

        # Check whether coordinates contain valid numbers
        else:
            try:
                latitude = float(attraction["latitude"])
                longitude = float(attraction["longitude"])
                
                # Check if coordinates are within valid geographical ranges
                if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                    print("Warning: Coordinates out of range for", attraction["name"])
            
            except ValueError:
                print("Warning: Invalid coordinates for", attraction["name"])


        # Check if the attraction cost is unknown
        if attraction["estimated_cost_eur"] == "":
            cost = None
            print("Warning: Unknown cost for", attraction["name"])
        else:
            # Convert the cost into a number
            try:
                cost = float(attraction["estimated_cost_eur"])
            except ValueError:
                print("Warning: Invalid cost for", attraction["name"])
                continue

        # Check if the cost is negative
        if cost is not None and cost < 0:
            print("Warning: Negative cost for", attraction["name"])
            print("------------------------------")
            continue


        # Convert visit duration into an integer
        try:
            duration = int(attraction["visit_duration_min"])
        except ValueError:
            print("Warning: Invalid duration for", attraction["name"])
            print("------------------------------")
            continue

        # Check if the duration is zero or negative
        if duration <= 0:
            print("Warning: Invalid duration for", attraction["name"])
            print("------------------------------")
            continue


        # Display the attraction information
        print("Name:", attraction["name"])
        print("Category:", attraction["category"])
        if cost is None:
            print("Estimated Cost: Unknown")
        else:
            print("Estimated Cost:", cost, "EUR")
        print("Visit Duration:", duration, "minutes")
        print("------------------------------")



# Display the number of missing-coordinate warnings
print("Missing coordinate warnings:", warning_count)
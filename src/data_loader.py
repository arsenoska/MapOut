import csv
from pathlib import Path


# Find the attractions dataset inside the data folder
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "attractions.csv"


def load_attractions():
    # Open and read the CSV file
    with open(DATA_PATH, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        # Check that the CSV contains all required columns
        required_columns = [
            "id", "name", "city", "region", "categories",
            "latitude", "longitude", "estimated_cost_eur",
            "visit_duration_min", "availability", "source"
        ]

        if not reader.fieldnames or any(
            column not in reader.fieldnames for column in required_columns
        ):
            raise ValueError("CSV file is missing one or more required columns!")

        # Read all attractions and return them as dictionaries
        return list(reader)
from src.data_loader import load_attractions
from src.validator import validate_attractions


# Load attractions from the CSV file
attractions = load_attractions()

# Validate the dataset
attractions_list, total, valid, warnings = validate_attractions(attractions)

# Display validation summary
print("\n===== MapOut Validation Summary =====")
print("Total attractions:", total)
print("Valid attractions:", valid)
print("Attractions ready for planning:", len(attractions_list))
print("Total warnings:", warnings)
print("====================================")

# Check that the dataset contains valid attractions
assert total > 0
assert valid == len(attractions_list)

print("\nValidation test passed!")

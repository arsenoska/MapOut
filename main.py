from src.data_loader import load_attractions
from src.validator import validate_attractions

# Load attractions from the CSV file
attractions = load_attractions()

# Validate the attractions and get the results
attractions_list, total_attractions, valid_attractions, warning_count = validate_attractions(attractions)

# Display validation summary
print("\n===== MapOut Validation Summary =====")
print("Total attractions:", total_attractions)
print("Valid attractions:", valid_attractions)
print("Attractions ready for planning:", len(attractions_list))
print("Total warnings:", warning_count)
print("====================================")
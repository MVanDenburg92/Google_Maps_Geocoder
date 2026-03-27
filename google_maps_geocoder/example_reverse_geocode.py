"""
Example: Reverse Geocoding (Lat/Lon to Address)
Converts geographic coordinates to addresses
"""

# Import necessary function
from geocode_signed_url_enhanced import signed_url_geocode
import os

# Get API credentials from environment
private_key = os.getenv("GOOGLE_MAPS_PRIVATE_KEY")
if not private_key:
    raise ValueError("GOOGLE_MAPS_PRIVATE_KEY is not set in the environment.")

# Define parameters for REVERSE geocoding
input_file = r"Test_Reverse_Geocode.csv"  # Your CSV file with latitude and longitude columns
output_file = 'geocoded_results_reverse.csv'
base_url = "http://maps.googleapis.com/maps/api/geocode/json"
client = "gme-cushmanwakefield"
channel = "GBC"

# Run REVERSE geocoding (lat/lon -> address)
print("Starting Reverse Geocoding...")
results = signed_url_geocode(
    input_file=input_file,
    output_file=output_file,
    private_key=private_key,
    base_url=base_url,
    client=client,
    channel=channel,
    geocode_only=False,      # Generate new signed URLs
    limit=None,              # Process all rows (or set to a number like 100 for testing)
    reverse_geocode=True,    # REVERSE geocoding mode (lat/lon -> address)
    lat_col='latitude',      # Name of your latitude column
    lon_col='longitude'      # Name of your longitude column
)

print(f"\nReverse geocoding complete! Results shape: {results.shape}")
print(f"\nOutput columns: {results.columns.tolist()}")

# Display sample results
print("\nSample results (first 5 rows):")
print(results[['formatted_address', 'city', 'state', 'country', 'postcode']].head())

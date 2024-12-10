# Google Maps Geocoder

Google Maps Geocoder is a Python module for geocoding addresses using the Google Maps Geocoding API. It supports batch geocoding for DataFrame-based datasets and includes tools for cleaning, preprocessing, and enriching location data.

## Features

- Clean and preprocess location data for geocoding.
- Geocode individual or bulk addresses with Google Maps API.
- Append geocode results to DataFrames, including latitude, longitude, and other metadata.
- Automatic handling of API rate limits.

## Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/<username>/Google_Maps_Geocoder.git
cd Google_Maps_Geocoder
pip install -r requirements.txt
```

## Usage

Here is a quick example of how to use the `GoogleGeocoder` class:

```python
import pandas as pd
from google_geocoder import GoogleGeocoder

# Initialize the geocoder
api_key = "YOUR_GOOGLE_API_KEY"
geocoder = GoogleGeocoder(api_key)

# Load your dataset
data = pd.read_csv("example_addresses.csv")

# Clean and prepare the data for geocoding
data, needs_geocoding = geocoder.cleanup_pd(data)

# Perform geocoding if needed
if needs_geocoding:
    geocoded_data = geocoder.geocode_addresses(data, needs_geocoding)
    print(geocoded_data.head())
else:
    print("Data already contains geocoded coordinates.")
```

## Repository Structure
```
Google_Maps_Geocoder/
|— google_maps_geocoder/          # Source code
|   |— __init__.py
|   |— geocoder.py
|— tests/                        # Test cases
|   |— __init__.py
|   |— test_geocoder.py
|— examples/                     # Example scripts
|— README.md
|— LICENSE
|— setup.py
```


## Requirements

- Python 3.7+
- `pandas`
- `requests`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Testing the Connection

Before using the module, test your API key and internet connection:

```python
from google_geocoder import GoogleGeocoder

api_key = "YOUR_GOOGLE_API_KEY"
geocoder = GoogleGeocoder(api_key)
# The connection test runs during initialization.
```

## API Reference

### `GoogleGeocoder`

#### `__init__(api_key, return_full_results=False)`

- `api_key`: Your Google Maps API key.
- `return_full_results`: Whether to include the full API response in results (default: `False`).

#### `test_connection()`

Tests the API key and internet connection by geocoding a sample address.

#### `cleanup_pd(destinations)`

Cleans and preprocesses a DataFrame for geocoding.

- `destinations`: Input DataFrame.
- Returns: Tuple `(cleaned DataFrame, needs_geocoding)`.

#### `get_google_results(address)`

Fetches geocode results from the Google Maps API.

- `address`: String address to geocode.
- Returns: Dictionary containing geocode results.

#### `geocode_addresses(destinations, destinations_value)`

Geocodes a list of addresses and appends the results to the input DataFrame.

- `destinations`: DataFrame containing location data.
- `destinations_value`: Boolean indicating if geocoding is needed.
- Returns: Updated DataFrame with geocode results.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for feedback.

## Contact

For questions or support, reach out via the GitHub repository.


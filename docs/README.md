# Google Maps Geocoder Documentation

## Overview
The **Google Maps Geocoder** is a Python module for geocoding addresses using the Google Maps Geocoding API. This package simplifies address cleanup, geocoding, and integration of geospatial data with Google Maps services.

---

## Table of Contents
1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Usage Examples](#usage-examples)
4. [Classes and Methods](#classes-and-methods)
5. [Contributing](#contributing)
6. [License](#license)

---

## Installation

### Requirements
- Python 3.7+
- Dependencies:
  - `pandas`
  - `requests`

### Installation via pip
```bash
pip install google-maps-geocoder
```

---

## Getting Started

### Importing the Package
```python
from google_maps_geocoder import GoogleGeocoder
```

### Initialize the Geocoder
To use the module, initialize the `GoogleGeocoder` class with your Google Maps API key:
```python
geocoder = GoogleGeocoder(api_key="YOUR_API_KEY")
```

### Test the Connection
Before using the geocoder, verify the API key and internet connection:
```python
geocoder.test_connection()
```

---

## Usage Examples

### Geocoding a Single Address
```python
result = geocoder.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
print(result)
```
Output:
```json
{
    "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
    "latitude": 37.422309,
    "longitude": -122.084624,
    "accuracy": "ROOFTOP",
    "google_place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA",
    "type": "street_address",
    "postcode": "94043"
}
```

### Geocoding Multiple Addresses in a DataFrame
```python
import pandas as pd

# Sample DataFrame
addresses = pd.DataFrame({
    "Address": [
        "1600 Amphitheatre Parkway, Mountain View, CA",
        "1 Infinite Loop, Cupertino, CA"
    ]
})

# Clean up and geocode
geocoded_addresses = geocoder.batch_geocode(addresses, "Address")
print(geocoded_addresses)
```

---

## Classes and Methods

### `GoogleGeocoder`
The main class for interacting with the Google Maps Geocoding API.

#### Constructor
```python
GoogleGeocoder(api_key: str)
```
- **Parameters**:
  - `api_key` (str): Your Google Maps API key.

#### Methods

1. **`geocode`**
   ```python
   geocode(address: str, return_full_response: bool = False) -> dict
   ```
   - **Description**: Geocode a single address.
   - **Parameters**:
     - `address` (str): The address to geocode.
     - `return_full_response` (bool): Return the full API response if `True`. Default is `False`.
   - **Returns**: A dictionary with geocoding results.

2. **`batch_geocode`**
   ```python
   batch_geocode(df: pd.DataFrame, address_column: str) -> pd.DataFrame
   ```
   - **Description**: Geocode multiple addresses from a DataFrame.
   - **Parameters**:
     - `df` (pd.DataFrame): A DataFrame containing addresses.
     - `address_column` (str): The name of the column with addresses.
   - **Returns**: A DataFrame with geocoded results appended.

3. **`test_connection`**
   ```python
   test_connection() -> None
   ```
   - **Description**: Tests the API key and internet connectivity.
   - **Raises**: `ConnectionError` if the test fails.

---

## Contributing

### Reporting Issues
If you encounter any issues, please [open an issue on GitHub](https://github.com/yourusername/Google_Maps_Geocoder/issues).

### Contributing Code
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed explanation of your changes.

---

## License
This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
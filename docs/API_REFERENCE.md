# API Reference for Google Maps Geocoder

This document outlines the available classes, methods, and their usage in the **Google Maps Geocoder** Python module.

---

## `GoogleGeocoder`
The main class for interacting with the Google Maps Geocoding API.

### Initialization
```python
GoogleGeocoder(api_key: str)
```
- **Parameters:**
  - `api_key` (str): Your Google Maps API key.
- **Returns:**
  - An instance of the `GoogleGeocoder` class.

---

### Methods

#### `test_connection()`
Tests the connection to the Google Maps Geocoding API by attempting to geocode a known address.

- **Usage:**
```python
gmaps.test_connection()
```
- **Raises:**
  - `ConnectionError`: If the connection to the API fails or the API key is invalid.

---

#### `geocode(address: str) -> dict`
Geocodes a single address and returns the geocoding result.

- **Parameters:**
  - `address` (str): The address to geocode.
- **Returns:**
  - `dict`: A dictionary containing geocoding details such as latitude, longitude, formatted address, and more.

- **Usage:**
```python
result = gmaps.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
print(result)
```

- **Example Output:**
```json
{
    "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
    "latitude": 37.422309,
    "longitude": -122.084624,
    "accuracy": "ROOFTOP",
    "google_place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA",
    "type": "street_address",
    "postcode": "94043",
    "status": "OK"
}
```

---

#### `batch_geocode(dataframe: pandas.DataFrame, address_column: str) -> pandas.DataFrame`
Performs batch geocoding on a DataFrame of addresses.

- **Parameters:**
  - `dataframe` (pandas.DataFrame): The DataFrame containing addresses to geocode.
  - `address_column` (str): The column name in the DataFrame where addresses are stored.

- **Returns:**
  - `pandas.DataFrame`: The input DataFrame with additional columns for geocoding results, such as latitude, longitude, and formatted address.

- **Usage:**
```python
import pandas as pd

addresses = pd.DataFrame({
    "Address": ["1600 Amphitheatre Parkway, Mountain View, CA", "1 Infinite Loop, Cupertino, CA"]
})

geocoded_df = gmaps.batch_geocode(addresses, "Address")
print(geocoded_df)
```

- **Example Output:**
| Address                                      | formatted_address                              | latitude   | longitude    | accuracy  |
|----------------------------------------------|-----------------------------------------------|------------|--------------|-----------|
| 1600 Amphitheatre Parkway, Mountain View, CA | 1600 Amphitheatre Parkway, Mountain View, CA  | 37.422309  | -122.084624  | ROOFTOP   |
| 1 Infinite Loop, Cupertino, CA               | 1 Infinite Loop, Cupertino, CA               | 37.331741  | -122.030333  | ROOFTOP   |

---

## Exceptions

### `ConnectionError`
Raised when there is an issue connecting to the Google Maps Geocoding API.

### Example Handling
```python
try:
    gmaps.test_connection()
except ConnectionError as e:
    print("Connection test failed:", e)
```

---

## Notes
- Ensure that your API key has sufficient permissions for the Google Maps Geocoding API.
- For batch geocoding, API usage limits may apply. Consider optimizing your queries to avoid reaching the limit.

---

For more details or troubleshooting, visit the [documentation](../README.md) or check out the [Google Maps API documentation](https://developers.google
# Google Maps Geocoder

Google Maps Geocoder is a Python module that provides tools for geocoding addresses using the Google Maps Geocoding API. This library supports single and batch geocoding and includes utilities for cleaning and validating address data.  This module allows the user to batch geocode as many addresses as they please.  JUst simply prepare your addresses in a csv and use it as an input for the module. 

---

## Features
- Geocode single addresses or batches from a DataFrame.
- Address cleanup and validation before geocoding.
- Handles API connection testing and error handling.

---

## Installation

### Requirements
- Python 3.7+
- Dependencies:
  - `pandas`
  - `requests`

### Install via pip
```bash
pip install google-maps-geocoder
```

---

## Usage

### Initialize the Geocoder
```python
from google_maps_geocoder import GoogleGeocoder

gmaps = GoogleGeocoder(api_key="YOUR_API_KEY")
```

### Test the API Connection
```python
gmaps.test_connection()
```

### Geocode a Single Address
```python
result = gmaps.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
print(result)
```

### Geocode Multiple Addresses in a DataFrame
```python
import pandas as pd

# Example DataFrame
addresses = pd.DataFrame({
    "Address": [
        "1600 Amphitheatre Parkway, Mountain View, CA",
        "1 Infinite Loop, Cupertino, CA"
    ]
})

# Batch geocoding
geocoded_df = gmaps.batch_geocode(addresses, "Address")
print(geocoded_df)
```

---

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

---

## Contributing

We welcome contributions to improve this project. To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support
For issues or questions, please open an [issue on GitHub](https://github.com/yourusername/Google_Maps_Geocoder/issues).


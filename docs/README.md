# Google Maps Geocoder

Google Maps Geocoder is a Python module for working with the Google Maps Geocoding API. It provides tools for cleaning datasets, geocoding addresses, and appending geocode results to data.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Initialization](#initialization)
  - [Cleaning Data](#cleaning-data)
  - [Geocoding Addresses](#geocoding-addresses)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Google Maps Geocoder is designed to streamline geocoding operations with Google Maps Geocoding API. It is especially useful for processing large datasets of addresses and ensuring geocode results are correctly formatted and appended.

## Features

- Validate API key and test connection to Google Maps API.
- Clean and preprocess data for geocoding.
- Geocode addresses and append results to your dataset.
- Handle API query limits with automatic retry logic.

## Installation

Clone this repository and install the dependencies:

```bash
$ git clone https://github.com/yourusername/Google_Maps_Geocoder.git
$ cd Google_Maps_Geocoder
$ pip install -r requirements.txt
```

## Usage

### Initialization

To use the Google Maps Geocoder module, import it and initialize it with your API key:

```python
from google_geocoder import GoogleGeocoder

API_KEY = "your_api_key_here"
geocoder = GoogleGeocoder(api_key=API_KEY)
```

### Cleaning Data

Use the `cleanup_pd` method to clean and preprocess your dataset:

```python
import pandas as pd

data = pd.read_csv("your_dataset.csv")
cleaned_data, needs_geocoding = geocoder.cleanup_pd(data)
```

### Geocoding Addresses

Use the `geocode_addresses` method to geocode your cleaned data:

```python
if needs_geocoding:
    geocoded_data = geocoder.geocode_addresses(cleaned_data, needs_geocoding)
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve this project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


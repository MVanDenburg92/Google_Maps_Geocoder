# API Reference for Google Maps Geocoder

This document outlines the available classes, methods, and their usage in the **Google Maps Geocoder** Python module.

---

## `GoogleGeocoder`

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


# Google Maps Geocoder

Google Maps Geocoder is a comprehensive Python module for working with Google Maps APIs, including both the Geocoding API and the Address Validation API. It provides tools for cleaning datasets, geocoding addresses, validating address formats, and appending results to data with enterprise-grade signed URL support.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Address Validation](#address-validation)
  - [Geocoding](#geocoding)
  - [Signed URL Geocoding (Enterprise)](#signed-url-geocoding-enterprise)
  - [Command Line Interface](#command-line-interface)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Google Maps Geocoder is designed to streamline geocoding and address validation operations with Google Maps APIs. It supports both the traditional Geocoding API for converting addresses to coordinates and the newer Address Validation API for standardizing and validating address formats. The module is especially useful for processing large datasets of addresses with robust error handling, rate limiting, and batch processing capabilities.

## Features

- **Address Validation**: Validate and standardize addresses using Google's Address Validation API
- **Geocoding**: Convert addresses to coordinates using Google's Geocoding API
- **Signed URL Support**: Generate signed URLs for enterprise Google Maps API usage
- **Batch Processing**: Efficiently process large CSV files with configurable batch sizes
- **Rate Limiting**: Built-in rate limiting and retry logic to handle API quotas
- **Multi-Region Support**: Support for international addresses across 40+ countries
- **Flexible Configuration**: Environment variables, config objects, and CLI options
- **Comprehensive Error Handling**: Detailed error reporting and logging
- **CSV Integration**: Direct CSV file processing with customizable column mapping
- **Command Line Interface**: Easy-to-use CLI for common operations

## Repository Structure

```
Google_Maps_Geocoder/
├── google_maps_geocoder/      # Main package containing the module
│   ├── __init__.py            # Package initialization and main exports
│   ├── geocoder.py            # Core geocoding implementation
│   ├── geocode_signed_url.py  # Signed URL geocoding for enterprise usage
│   ├── address_validator.py   # Address validation using Google's Address Validation API
│   ├── utils.py               # Shared utility functions
│   ├── exceptions.py          # Custom exception classes
│   ├── config.py              # Configuration management
│   └── cli.py                 # Command line interface
├── tests/                     # Unit and integration tests
│   ├── __init__.py            # Test package initialization
│   ├── test_geocoder.py       # Test cases for the geocoder
│   ├── test_address_validator.py # Test cases for address validation
│   ├── test_utils.py          # Test cases for utility functions
│   └── test_integration.py    # Integration tests
├── examples/                  # Example scripts demonstrating module usage
│   ├── basic_geocoding.py     # Basic geocoding example
│   ├── address_validation.py  # Address validation example
│   ├── batch_processing.py    # Large dataset processing example
│   ├── signed_url_example.py  # Enterprise signed URL example
│   └── custom_config.py       # Custom configuration example
├── docs/                      # Documentation files
│   ├── README.md              # User guide
│   ├── API_REFERENCE.md       # Detailed API documentation
│   ├── CONFIGURATION.md       # Configuration options
│   └── EXAMPLES.md            # Additional examples
├── .gitignore                 # Files and directories to ignore in Git
├── LICENSE                    # Repository license
├── README.md                  # Project overview (this file)
├── setup.py                   # Script for packaging and installation
├── requirements.txt           # List of dependencies
└── pyproject.toml             # Build system configuration
```

## Installation

Clone this repository and install the dependencies:

```bash
$ git clone https://github.com/yourusername/Google_Maps_Geocoder.git
$ cd Google_Maps_Geocoder
$ pip install -r requirements.txt
```

For development installation:

```bash
$ pip install -e .
```

## Configuration

Set up your Google Maps API credentials using environment variables:

```bash
export GOOGLE_API_KEY="your_api_key_here"
export GOOGLE_CLIENT_ID="your_client_id"      # For signed URLs (enterprise)
export GOOGLE_PRIVATE_KEY="your_private_key"  # For signed URLs (enterprise)
```

Or create a configuration object in your code:

```python
from google_maps_geocoder import Config

config = Config(
    google_api_key="your_api_key_here",
    default_region="US",
    batch_size=100,
    delay_seconds=0.1
)
```

## Usage

### Address Validation

Validate and standardize addresses using Google's Address Validation API:

```python
from google_maps_geocoder import AddressValidator

# Initialize with API key
validator = AddressValidator()

# Validate a single address
result = validator.validate_single_address(
    "123 Main St, Boston, MA 02101", 
    region="US"
)
print(f"Valid: {result}")

# Validate addresses from CSV
results = validator.validate_csv_addresses(
    csv_file_path="addresses.csv",
    output_file="validated_addresses.csv"
)
```

### Geocoding

Convert addresses to coordinates using the traditional Geocoding API:

```python
from google_maps_geocoder import GoogleGeocoder

# Initialize geocoder
geocoder = GoogleGeocoder(api_key="your_api_key_here")

# Test connection
geocoder.test_connection()

# Geocode a single address
result = geocoder.get_google_results("123 Main St, Boston, MA")
print(f"Coordinates: {result['latitude']}, {result['longitude']}")

# Process DataFrame with addresses
import pandas as pd
data = pd.read_csv("addresses.csv")
cleaned_data, needs_geocoding = geocoder.cleanup_pd(data)

if needs_geocoding:
    geocoded_data = geocoder.geocode_addresses(cleaned_data, needs_geocoding)
```

### Signed URL Geocoding (Enterprise)

For enterprise usage with signed URLs and higher rate limits:

```python
from google_maps_geocoder import signed_url_geocode

result = signed_url_geocode(
    input_file="addresses.csv",
    output_file="geocoded_results.csv", 
    private_key="your_private_key",
    base_url="https://maps.googleapis.com/maps/api/geocode/json",
    client="your_client_id",
    channel="your_channel"
)
```

### Command Line Interface

The module includes a CLI for common operations:

```bash
# Validate addresses from CSV
geocode validate addresses.csv -o validated.csv --summary

# Geocode with signed URLs
geocode geocode addresses.csv results.csv --private-key="key" --client-id="id"

# Custom column names
geocode validate data.csv -o results.csv \
  --address-col="StreetAddress" \
  --city-col="CityName" \
  --state-col="StateCode" \
  --zip-col="PostalCode"
```

## API Reference

### Main Classes

- **`GoogleGeocoder`**: Traditional geocoding functionality
- **`AddressValidator`**: Address validation using Google's Address Validation API
- **`Config`**: Configuration management for API keys and processing options

### Key Functions

- **`validate_csv_addresses()`**: Convenience function for CSV address validation
- **`signed_url_geocode()`**: Enterprise geocoding with signed URLs
- **`concatenate_address_fields()`**: Utility for combining address components
- **`generate_validation_summary()`**: Generate statistics for validation results

### CSV Format

The module expects CSV files with these default column names (customizable):

```csv
Address,City,State,Zip
123 Main St,Boston,MA,02101
456 Oak Ave,New York,NY,10001
789 Pine Rd,Los Angeles,CA,90210
```

### Supported Regions

Address validation supports 40+ countries including:
- US (United States)
- CA (Canada)
- GB (United Kingdom)
- AU (Australia)
- DE (Germany)
- FR (France)
- And many more...

## Examples

### Basic Address Validation

```python
from google_maps_geocoder import validate_csv_addresses, generate_validation_summary

# Validate addresses with default settings
results = validate_csv_addresses(
    csv_file_path="addresses.csv",
    output_file="validated.csv"
)

# Get summary statistics
summary = generate_validation_summary(results)
print(f"Validation rate: {summary['validation_rate']}%")
```

### International Addresses

```python
# Validate UK addresses
results = validator.validate_csv_addresses(
    "uk_addresses.csv",
    default_region="GB",
    output_file="uk_validated.csv"
)
```

### Custom Configuration

```python
from google_maps_geocoder import Config, AddressValidator

config = Config(
    batch_size=50,
    delay_seconds=0.2,  # 200ms between requests
    max_retries=5,
    default_region="CA"
)

validator = AddressValidator(config)
results = validator.validate_csv_addresses("addresses.csv")
```

### Error Handling

```python
from google_maps_geocoder.exceptions import ValidationAPIError, CSVError

try:
    results = validator.validate_csv_addresses("addresses.csv")
except ValidationAPIError as e:
    print(f"API Error: {e}")
except CSVError as e:
    print(f"CSV Processing Error: {e}")
```

## Rate Limits and Costs

### API Quotas
- **Geocoding API**: 40,000 requests per month (free tier)
- **Address Validation API**: Pay-per-use
- **Enterprise**: Higher limits with signed URLs

### Pricing (as of 2024)
- **Address Validation**: $5.00 per 1,000 requests
- **Geocoding**: $5.00 per 1,000 requests
- Check [Google Maps Pricing](https://developers.google.com/maps/billing/gmp-billing) for current rates

### Rate Limiting Features
- Configurable delays between requests
- Automatic retry with exponential backoff
- Batch processing for large datasets
- Request progress tracking and logging

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup

1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install in development mode: `pip install -e .`
5. Install development dependencies: `pip install -e .[dev]`
6. Run tests: `pytest`

### Guidelines

- Add tests for new functionality
- Follow PEP 8 style guidelines
- Update documentation for API changes
- Ensure backward compatibility when possible

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See the `docs/` directory for detailed guides
- **Issues**: Report bugs or request features via GitHub Issues
- **API Keys**: Get your Google Maps API key at [Google Cloud Console](https://console.cloud.google.com/)
- **API Documentation**: 
  - [Geocoding API](https://developers.google.com/maps/documentation/geocoding)
  - [Address Validation API](https://developers.google.com/maps/documentation/address-validation)
# Google Maps Geocoding with Signed URLs

Enhanced geocoding script supporting both **forward geocoding** (address → lat/lon) and **reverse geocoding** (lat/lon → address) using Google Maps API with URL signing.

## Features

### Forward Geocoding (Original Functionality)
- Convert addresses to geographic coordinates (latitude/longitude)
- Returns formatted address, coordinates, accuracy, place ID, and postal code

### Reverse Geocoding (New Feature)
- Convert geographic coordinates to detailed addresses
- Returns comprehensive address components:
  - Full formatted address
  - Street number and name
  - City, county, state (with codes)
  - Country (with codes)
  - Postal code
  - Place ID and location type

### Performance Features
- Parallel processing with ThreadPoolExecutor
- Automatic retry logic for rate limiting (HTTP 429)
- Exponential backoff for failed requests
- Batch processing (100 URLs per batch)
- Progress tracking
- Periodic saves every 100 records

## Installation

```bash
pip install pandas requests google_maps_geocoder
```

## Setup

### 1. Set Environment Variable
```bash
# Windows
set GOOGLE_MAPS_PRIVATE_KEY=your_private_key_here

# Linux/Mac
export GOOGLE_MAPS_PRIVATE_KEY=your_private_key_here

# Python
import os
os.environ['GOOGLE_MAPS_PRIVATE_KEY'] = 'your_private_key_here'
```

### 2. Prepare Your Data

#### For Forward Geocoding:
Your CSV needs an address column that will be processed by `GoogleGeocoder().cleanup_pd()` to create an `ADDRESS_FULL` column.

#### For Reverse Geocoding:
Your CSV needs latitude and longitude columns. Default column names are:
- `latitude`
- `longitude`

You can specify custom column names using the `lat_col` and `lon_col` parameters.

## Usage

### Forward Geocoding (Address → Lat/Lon)

```python
from geocode_signed_url_enhanced import signed_url_geocode
import os

private_key = os.getenv("GOOGLE_MAPS_PRIVATE_KEY")

results = signed_url_geocode(
    input_file="addresses.csv",
    output_file="geocoded_forward.csv",
    private_key=private_key,
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=False,  # Forward geocoding mode
    limit=None  # Process all rows
)
```

**Output columns:**
- `formatted_address`
- `latitude`
- `longitude`
- `accuracy`
- `google_place_id`
- `type`
- `postcode`
- `number_of_results`
- `status`

### Reverse Geocoding (Lat/Lon → Address)

```python
from geocode_signed_url_enhanced import signed_url_geocode
import os

private_key = os.getenv("GOOGLE_MAPS_PRIVATE_KEY")

results = signed_url_geocode(
    input_file="locations.csv",
    output_file="geocoded_reverse.csv",
    private_key=private_key,
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=True,   # Reverse geocoding mode
    lat_col='latitude',     # Your latitude column name
    lon_col='longitude',    # Your longitude column name
    limit=None              # Process all rows
)
```

**Output columns:**
- `formatted_address` - Complete address string
- `street_number` - Building/house number
- `street_name` - Street/road name
- `city` - City/locality
- `county` - Administrative area level 2
- `state` - Administrative area level 1 (full name)
- `state_code` - State abbreviation (e.g., "CA", "NY")
- `country` - Country name
- `country_code` - Country code (e.g., "US", "CA")
- `postcode` - Postal/ZIP code
- `latitude` - Latitude from geocoding result
- `longitude` - Longitude from geocoding result
- `accuracy` - Location accuracy type
- `google_place_id` - Unique place identifier
- `type` - Place type(s)
- `number_of_results` - Number of results returned
- `status` - API response status

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_file` | str | Required | Path to input CSV file |
| `output_file` | str | Required | Name of output CSV file |
| `private_key` | str | Required | Google Maps API private key |
| `base_url` | str | Required | Google Maps API endpoint |
| `client` | str | Required | Google Maps client ID |
| `channel` | str | Required | Google Maps channel |
| `geocode_only` | bool | False | If True, read existing signed URLs |
| `dir` | str | 'results' | Directory name for results |
| `limit` | int | None | Limit rows to process (None = all) |
| `reverse_geocode` | bool | False | **True for reverse, False for forward** |
| `lat_col` | str | 'latitude' | Latitude column name (reverse only) |
| `lon_col` | str | 'longitude' | Longitude column name (reverse only) |

## Example: Test with Your Data

```python
from geocode_signed_url_enhanced import signed_url_geocode
import os

private_key = os.getenv("GOOGLE_MAPS_PRIVATE_KEY")

# Test with first 10 rows
results = signed_url_geocode(
    input_file="Test_Reverse_Geocode.csv",
    output_file="test_results.csv",
    private_key=private_key,
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=True,
    lat_col='latitude',
    lon_col='longitude',
    limit=10  # Test with 10 rows first
)

print(results[['name', 'formatted_address', 'city', 'state']].head())
```

## Output File Structure

The script creates a `results` directory (or custom `dir` parameter) containing:

1. **site_numbered_cleaned_data.csv** - Original data with Site_Number
2. **signed_urls.csv** - Generated signed URLs
3. **google_results_df.csv** - Raw geocoding results
4. **[output_file]** - Final merged results with all original columns plus geocoding data

## Performance Notes

- **Batch size**: 100 URLs per batch (configurable in code)
- **Max workers**: 10 parallel threads (configurable in code)
- **Rate limiting**: Automatic retry with exponential backoff
- **Minimum delay**: 0.11 seconds between URL generation
- **Progress saves**: Every 100 rows during processing

## Error Handling

The script handles:
- Missing or invalid lat/lon values (automatically skipped)
- HTTP 429 (Too Many Requests) with automatic retry
- Network timeouts
- Invalid API responses
- Missing columns

## Example Data

### Input for Reverse Geocoding:
```csv
id,name,latitude,longitude
1,Location A,40.7128,-74.0060
2,Location B,34.0522,-118.2437
```

### Output:
```csv
id,name,latitude,longitude,formatted_address,city,state,country
1,Location A,40.7128,-74.0060,"New York, NY, USA",New York,New York,United States
2,Location B,34.0522,-118.2437,"Los Angeles, CA, USA",Los Angeles,California,United States
```

## Troubleshooting

### "GOOGLE_MAPS_PRIVATE_KEY is not set"
Set the environment variable before running the script.

### "Column not found in the data"
For reverse geocoding, ensure your CSV has `latitude` and `longitude` columns (or specify custom names with `lat_col` and `lon_col`).

### Rate Limiting Issues
The script automatically handles rate limiting, but you can:
- Reduce `max_workers` in `process_in_batches()`
- Increase batch delays
- Contact Google about your API quota

### No Results / Empty Addresses
- Verify coordinates are valid (lat: -90 to 90, lon: -180 to 180)
- Check if coordinates are in remote/ocean locations
- Review the `status` column in output for API error messages

## API Costs

Google Maps Geocoding API pricing (as of 2025):
- $5 per 1,000 requests
- First $200 per month is free (40,000 free requests)

For 2,069 rows in your test file:
- Cost: ~$10.35 (without free tier)
- With free tier: $0 if under 40,000 requests/month

## License

This script is for use with valid Google Maps API credentials only. Ensure compliance with Google Maps Platform Terms of Service.

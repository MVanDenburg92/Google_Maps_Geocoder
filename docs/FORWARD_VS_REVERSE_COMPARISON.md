# Forward vs Reverse Geocoding Comparison

## Quick Reference

| Feature | Forward Geocoding | Reverse Geocoding |
|---------|------------------|-------------------|
| **Input** | Address text | Latitude & Longitude |
| **Output** | Coordinates | Address components |
| **Parameter** | `reverse_geocode=False` | `reverse_geocode=True` |
| **Input Column** | `ADDRESS_FULL` (auto-generated) | `latitude`, `longitude` |
| **Use Case** | "Where is this address?" | "What's at these coordinates?" |

## Detailed Comparison

### Forward Geocoding (Original Functionality)

**Purpose:** Convert text addresses to geographic coordinates

**Input Requirements:**
- CSV with address data
- Address column(s) processed by `GoogleGeocoder().cleanup_pd()`
- Creates `ADDRESS_FULL` column for geocoding

**API Call:**
```
?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&client=...
```

**Output Fields:**
- `formatted_address` - Cleaned address from Google
- `latitude` - Decimal degrees
- `longitude` - Decimal degrees  
- `accuracy` - ROOFTOP, RANGE_INTERPOLATED, etc.
- `google_place_id` - Unique identifier
- `type` - street_address, locality, etc.
- `postcode` - Postal code only

**Example:**
```python
# Input CSV
address, city, state
1600 Amphitheatre Parkway, Mountain View, CA

# Output
formatted_address: "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
latitude: 37.4224764
longitude: -122.0842499
```

### Reverse Geocoding (NEW Functionality)

**Purpose:** Convert coordinates to detailed address information

**Input Requirements:**
- CSV with latitude and longitude columns
- Default column names: `latitude`, `longitude`
- Can specify custom names via `lat_col` and `lon_col`

**API Call:**
```
?latlng=37.4224764,-122.0842499&client=...
```

**Output Fields (Enhanced):**
- `formatted_address` - Full address string
- `street_number` - Building number (e.g., "1600")
- `street_name` - Road name (e.g., "Amphitheatre Parkway")
- `city` - Locality (e.g., "Mountain View")
- `county` - Admin level 2 (e.g., "Santa Clara County")
- `state` - Admin level 1 full name (e.g., "California")
- `state_code` - State abbreviation (e.g., "CA")
- `country` - Country name (e.g., "United States")
- `country_code` - ISO code (e.g., "US")
- `postcode` - Postal code (e.g., "94043")
- `latitude` - Validated coordinate
- `longitude` - Validated coordinate
- `accuracy` - Location type
- `google_place_id` - Unique identifier
- `type` - Result types

**Example:**
```python
# Input CSV
id, latitude, longitude
1, 37.4224764, -122.0842499

# Output
formatted_address: "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
street_number: "1600"
street_name: "Amphitheatre Parkway"
city: "Mountain View"
county: "Santa Clara County"
state: "California"
state_code: "CA"
country: "United States"
country_code: "US"
postcode: "94043"
```

## Code Examples

### Forward Geocoding
```python
results = signed_url_geocode(
    input_file="addresses.csv",
    output_file="forward_results.csv",
    private_key=private_key,
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=False,  # ← FORWARD MODE
    limit=None
)
# Input needs: address data
# Output includes: lat/lon coordinates
```

### Reverse Geocoding
```python
results = signed_url_geocode(
    input_file="locations.csv",
    output_file="reverse_results.csv",
    private_key=private_key,
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=True,   # ← REVERSE MODE
    lat_col='latitude',     # Column names
    lon_col='longitude',
    limit=None
)
# Input needs: lat/lon coordinates
# Output includes: detailed address components
```

## Key Implementation Differences

### URL Generation

**Forward:**
```python
def generate_signed_urls(data, private_key, base_url, client, channel):
    query = urllib.parse.urlencode({
        "address": address,
        "client": client,
        "channel": channel
    })
```

**Reverse:**
```python
def generate_signed_urls_reverse(data, private_key, base_url, client, channel, 
                                 lat_col, lon_col):
    latlng = f"{lat},{lon}"
    query = urllib.parse.urlencode({
        "latlng": latlng,  # ← Key difference
        "client": client,
        "channel": channel
    })
```

### Response Processing

**Forward:** Uses `process_url()` with basic address parsing

**Reverse:** Uses `process_url_reverse()` with enhanced component extraction:
```python
for component in answer.get('address_components', []):
    types = component.get('types', [])
    if 'street_number' in types:
        components['street_number'] = component.get('long_name', '')
    elif 'route' in types:
        components['street_name'] = component.get('long_name', '')
    # ... extracts all address components
```

## When to Use Each

### Use Forward Geocoding When:
- You have address text/strings
- You need to plot locations on a map
- You want to standardize addresses
- You're building a location search feature
- Example: Store locator with address input

### Use Reverse Geocoding When:
- You have GPS coordinates
- You need human-readable addresses
- You're processing tracking/telemetry data
- You want to enrich coordinate data
- Example: Convert data center locations to addresses

## Combined Workflow Example

You can use both in sequence:

1. **Forward geocode** addresses to get accurate coordinates
2. **Reverse geocode** those coordinates to get standardized address components
3. Compare to validate data quality

```python
# Step 1: Forward geocode addresses
forward_results = signed_url_geocode(
    input_file="raw_addresses.csv",
    output_file="with_coordinates.csv",
    reverse_geocode=False,
    # ... other params
)

# Step 2: Reverse geocode the results to get standardized addresses
reverse_results = signed_url_geocode(
    input_file="results/with_coordinates.csv",
    output_file="fully_geocoded.csv",
    reverse_geocode=True,
    lat_col='latitude',
    lon_col='longitude',
    # ... other params
)
```

## Common Issues

### Forward Geocoding Issues:
- Ambiguous addresses → Multiple results
- Incomplete addresses → Low accuracy
- Typos → Wrong location or no results

### Reverse Geocoding Issues:
- Ocean/remote coordinates → No results
- Invalid coordinates → Error status
- Plus codes/areas → Less precise addresses

## Performance

Both modes have similar performance characteristics:
- **Parallel processing**: 10 workers
- **Batch size**: 100 URLs
- **Rate limiting**: Automatic retry
- **Speed**: ~10 requests/second with API limits

**Estimated time for 2,069 locations:**
- With free API: ~3-4 minutes
- With paid API (higher quota): ~2-3 minutes

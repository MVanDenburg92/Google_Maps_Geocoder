# Quick Start Guide: Reverse Geocoding

## What You Have

I've enhanced your Google Maps geocoding script to support **reverse geocoding** - converting latitude/longitude coordinates to detailed addresses.

## Files Provided

1. **geocode_signed_url_enhanced.py** - Main script with both forward and reverse geocoding
2. **example_forward_geocode.py** - Example for address → coordinates
3. **example_reverse_geocode.py** - Example for coordinates → address
4. **test_reverse_geocode.py** - Quick test script (10 rows)
5. **README_GEOCODING.md** - Complete documentation
6. **FORWARD_VS_REVERSE_COMPARISON.md** - Detailed comparison guide

## Fastest Way to Get Started

### Step 1: Set Your API Key
```python
import os
os.environ['GOOGLE_MAPS_PRIVATE_KEY'] = 'your_private_key_here'
```

### Step 2: Run Reverse Geocoding
```python
from geocode_signed_url_enhanced import signed_url_geocode

results = signed_url_geocode(
    input_file="Test_Reverse_Geocode.csv",
    output_file="results_with_addresses.csv",
    private_key=os.getenv("GOOGLE_MAPS_PRIVATE_KEY"),
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=True,  # ← THE KEY PARAMETER
    lat_col='latitude',
    lon_col='longitude',
    limit=None  # Process all rows
)
```

### Step 3: Check Results
Results will be in: `results/results_with_addresses.csv`

## What Changed from Original Code

### NEW PARAMETER: `reverse_geocode`
- **`reverse_geocode=False`** → Address to coordinates (original behavior)
- **`reverse_geocode=True`** → Coordinates to address (NEW!)

### NEW PARAMETERS: `lat_col` and `lon_col`
- Specify which columns contain your coordinates
- Defaults: `latitude` and `longitude`

### NEW OUTPUT COLUMNS (Reverse Geocoding)
When `reverse_geocode=True`, you get:
- `formatted_address` - Full address
- `street_number` - Building number
- `street_name` - Street name
- `city` - City name
- `county` - County name
- `state` - State full name
- `state_code` - State abbreviation (CA, TX, etc.)
- `country` - Country name
- `country_code` - Country code (US, CA, etc.)
- `postcode` - ZIP/postal code
- Plus: `google_place_id`, `accuracy`, `type`, etc.

## Test Before Full Run

```python
# Test with just 10 rows first
results = signed_url_geocode(
    input_file="Test_Reverse_Geocode.csv",
    output_file="test_results.csv",
    private_key=os.getenv("GOOGLE_MAPS_PRIVATE_KEY"),
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=True,
    limit=10  # ← Test with 10 rows
)
```

## For Your 2,069 Location File

```python
# Full run for all 2,069 locations
results = signed_url_geocode(
    input_file="Test_Reverse_Geocode.csv",
    output_file="datacenter_addresses.csv",
    private_key=os.getenv("GOOGLE_MAPS_PRIVATE_KEY"),
    base_url="http://maps.googleapis.com/maps/api/geocode/json",
    client="gme-cushmanwakefield",
    channel="GBC",
    reverse_geocode=True,
    lat_col='latitude',
    lon_col='longitude',
    limit=None  # Process all
)

# Estimated time: 3-4 minutes
# Estimated cost: ~$10 (or free with $200/month credit)
```

## Output Location

All results are saved in the `results/` directory:
- `site_numbered_cleaned_data.csv` - Your original data with ID numbers
- `signed_urls.csv` - Generated API URLs
- `google_results_df.csv` - Raw geocoding results
- `[your_output_file].csv` - Final combined results

## Backward Compatible

Your existing forward geocoding code still works exactly the same:
```python
# This still works as before
signed_url_geocode(
    input_file=input_file,
    output_file=output_file,
    private_key=private_key,
    base_url=base_url,
    client=client,
    channel=channel,
    geocode_only=False,
    limit=None
    # reverse_geocode defaults to False
)
```

## Key Features

✅ Parallel processing (10 workers)
✅ Automatic retry on rate limits
✅ Progress tracking
✅ Saves every 100 rows
✅ Handles missing/invalid coordinates
✅ Detailed error reporting
✅ Both forward and reverse geocoding

## Need Help?

See the full documentation in **README_GEOCODING.md** for:
- Detailed parameter explanations
- Error troubleshooting
- Performance tuning
- API cost calculations
- More examples

## Quick Comparison

| | Forward | Reverse |
|---|---|---|
| **Input** | Addresses | Lat/Lon |
| **Output** | Coordinates | Addresses |
| **Parameter** | `reverse_geocode=False` | `reverse_geocode=True` |

That's it! You're ready to reverse geocode your locations. 🚀

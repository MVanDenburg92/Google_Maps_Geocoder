"""
Quick Test Script for Reverse Geocoding
Tests the reverse geocoding functionality with a few sample locations
"""

import os
import sys

# Check if the google_maps_geocoder module is available
try:
    from google_maps_geocoder import GoogleGeocoder
    GEOCODER_AVAILABLE = True
except ImportError:
    print("WARNING: google_maps_geocoder not found. You'll need to install it:")
    print("pip install google_maps_geocoder")
    GEOCODER_AVAILABLE = False

# Import the enhanced geocoding function
try:
    from geocode_signed_url_enhanced import signed_url_geocode
except ImportError:
    print("ERROR: geocode_signed_url_enhanced.py not found in the current directory")
    sys.exit(1)

def main():
    """Run a quick test of reverse geocoding."""
    
    # Check for API key
    private_key = os.getenv("GOOGLE_MAPS_PRIVATE_KEY")
    if not private_key:
        print("\n" + "="*60)
        print("ERROR: GOOGLE_MAPS_PRIVATE_KEY not set!")
        print("="*60)
        print("\nPlease set your Google Maps API private key:")
        print("\nWindows:")
        print('  set GOOGLE_MAPS_PRIVATE_KEY=your_key_here')
        print("\nLinux/Mac:")
        print('  export GOOGLE_MAPS_PRIVATE_KEY=your_key_here')
        print("\nOr in Python:")
        print('  os.environ["GOOGLE_MAPS_PRIVATE_KEY"] = "your_key_here"')
        print("="*60)
        sys.exit(1)
    
    # Configuration
    input_file = "Test_Reverse_Geocode.csv"
    output_file = "test_reverse_geocoding_results.csv"
    base_url = "http://maps.googleapis.com/maps/api/geocode/json"
    client = "gme-cushmanwakefield"
    channel = "GBC"
    
    print("\n" + "="*60)
    print("REVERSE GEOCODING TEST")
    print("="*60)
    print(f"\nInput file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Processing: First 10 rows (test mode)")
    print(f"Mode: REVERSE GEOCODING (lat/lon → address)")
    print("="*60 + "\n")
    
    try:
        # Run reverse geocoding on first 10 rows
        results = signed_url_geocode(
            input_file=input_file,
            output_file=output_file,
            private_key=private_key,
            base_url=base_url,
            client=client,
            channel=channel,
            geocode_only=False,
            limit=10,  # Only process first 10 rows for testing
            reverse_geocode=True,  # REVERSE GEOCODING MODE
            lat_col='latitude',
            lon_col='longitude'
        )
        
        print("\n" + "="*60)
        print("TEST COMPLETE!")
        print("="*60)
        print(f"\nProcessed: {len(results)} locations")
        print(f"\nSample Results:")
        print("-"*60)
        
        # Display sample results
        display_cols = ['name', 'formatted_address', 'city', 'state', 'country']
        available_cols = [col for col in display_cols if col in results.columns]
        
        if available_cols:
            print(results[available_cols].head(5).to_string(index=False))
        else:
            print(results.head(5).to_string(index=False))
        
        print("\n" + "="*60)
        print(f"Full results saved to: results/{output_file}")
        print("="*60 + "\n")
        
    except FileNotFoundError:
        print(f"\nERROR: Could not find input file: {input_file}")
        print("Please make sure the file exists in the current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

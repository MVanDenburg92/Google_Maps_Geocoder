import hashlib
import hmac
import base64
import urllib.parse
import time
import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor
from google_maps_geocoder import GoogleGeocoder

geocoder = GoogleGeocoder()

def load_data(file_path, geocoder, nrows=None):
    data = pd.read_csv(file_path, nrows=nrows)
    print(data.describe)
    print("Original columns:", data.columns)
    
    data, needs_geocoding = geocoder.cleanup_pd(data)
    
    print("Post-cleanup columns:", data.columns)
    
    if 'ADDRESS_FULL' not in data.columns:
        raise ValueError("Error: 'ADDRESS_FULL' column is missing after cleanup. Check input format.")
    
    return data


def load_data_reverse(file_path, nrows=None, lat_col='latitude', lon_col='longitude'):
    """
    Load data for reverse geocoding (lat/lon to address).
    
    Args:
        file_path: Path to the CSV file
        nrows: Number of rows to load (None for all)
        lat_col: Name of the latitude column
        lon_col: Name of the longitude column
    
    Returns:
        DataFrame with validated lat/lon columns
    """
    data = pd.read_csv(file_path, nrows=nrows)
    print("Original columns:", data.columns.tolist())
    print(f"Loaded {len(data)} records from {file_path}")
    
    # Check for required columns
    if lat_col not in data.columns:
        raise ValueError(f"Error: '{lat_col}' column not found in the data")
    if lon_col not in data.columns:
        raise ValueError(f"Error: '{lon_col}' column not found in the data")
    
    # Remove rows with missing lat/lon
    original_len = len(data)
    data = data.dropna(subset=[lat_col, lon_col])
    removed = original_len - len(data)
    if removed > 0:
        print(f"Removed {removed} rows with missing lat/lon values")
    
    return data


def sign_url(url, private_key):
    parsed_url = urllib.parse.urlparse(url)
    url_to_sign = parsed_url.path + "?" + parsed_url.query
    decoded_key = base64.urlsafe_b64decode(private_key)
    signature = hmac.new(decoded_key, url_to_sign.encode(), hashlib.sha1)
    encoded_signature = base64.urlsafe_b64encode(signature.digest()).decode("utf-8")
    return f"{url}&signature={encoded_signature}"


def generate_signed_urls(data, private_key, base_url, client, channel):
    """Generate signed URLs for forward geocoding (address to lat/lon)."""
    master_df = pd.DataFrame([], columns=['Signed_URL'], dtype='str')
    for address in data['ADDRESS_FULL']:
        query = urllib.parse.urlencode({"address": address, "client": client, "channel": channel})
        url = f"{base_url}?{query}"
        start_time = time.time()
        signed_url = sign_url(url, private_key)
        master_df = pd.concat([master_df, pd.DataFrame([signed_url], columns=['Signed_URL'])])
        duration = time.time() - start_time
        if duration < 0.11:
            time.sleep(0.11 - duration)
    return master_df


def generate_signed_urls_reverse(data, private_key, base_url, client, channel, lat_col='latitude', lon_col='longitude'):
    """
    Generate signed URLs for reverse geocoding (lat/lon to address).
    
    Args:
        data: DataFrame with latitude and longitude columns
        private_key: Google Maps API private key
        base_url: Google Maps API base URL
        client: Google Maps client ID
        channel: Google Maps channel
        lat_col: Name of the latitude column
        lon_col: Name of the longitude column
    
    Returns:
        DataFrame with signed URLs
    """
    master_df = pd.DataFrame([], columns=['Signed_URL'], dtype='str')
    
    for idx, row in data.iterrows():
        lat = row[lat_col]
        lon = row[lon_col]
        
        # Create latlng parameter for reverse geocoding
        latlng = f"{lat},{lon}"
        query = urllib.parse.urlencode({"latlng": latlng, "client": client, "channel": channel})
        url = f"{base_url}?{query}"
        
        start_time = time.time()
        signed_url = sign_url(url, private_key)
        master_df = pd.concat([master_df, pd.DataFrame([signed_url], columns=['Signed_URL'])])
        
        duration = time.time() - start_time
        if duration < 0.11:
            time.sleep(0.11 - duration)
    
    return master_df


def process_url(url):
    try:
        results = requests.get(url)
        # Add retry logic for rate limiting
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries and results.status_code == 429:  # Too Many Requests
            retry_count += 1
            sleep_time = 2 ** retry_count  # Exponential backoff
            time.sleep(sleep_time)
            results = requests.get(url)
            
        # Handle potential issues
        if results.status_code != 200:
            return {
                "formatted_address": None,
                "latitude": None,
                "longitude": None,
                "accuracy": None,
                "google_place_id": None,
                "type": None,
                "postcode": None,
                "number_of_results": 0,
                "status": f"HTTP Error: {results.status_code}"
            }
            
        # Process successful results
        results = results.json()
        
        if len(results.get('results', [])) == 0:
            output = {
                "formatted_address": None,
                "latitude": None,
                "longitude": None,
                "accuracy": None,
                "google_place_id": None,
                "type": None,
                "postcode": None
            }
        else:
            answer = results['results'][0]
            output = {
                "formatted_address": answer.get('formatted_address'),
                "latitude": answer.get('geometry', {}).get('location', {}).get('lat'),
                "longitude": answer.get('geometry', {}).get('location', {}).get('lng'),
                "accuracy": answer.get('geometry', {}).get('location_type'),
                "google_place_id": answer.get("place_id"),
                "type": ",".join(answer.get('types', [])),
                "postcode": ",".join([x['long_name'] for x in answer.get('address_components', [])
                                    if 'postal_code' in x.get('types', [])])
            }
        
        output['number_of_results'] = len(results.get('results', []))
        output['status'] = results.get('status')
        return output
        
    except Exception as e:
        # Handle errors gracefully
        return {
            "formatted_address": None,
            "latitude": None,
            "longitude": None,
            "accuracy": None,
            "google_place_id": None,
            "type": None,
            "postcode": None,
            "number_of_results": 0,
            "status": f"Error: {str(e)}"
        }


def process_url_reverse(url):
    """
    Process reverse geocoding URL and extract detailed address components.
    
    Args:
        url: Signed Google Maps API URL for reverse geocoding
    
    Returns:
        Dictionary with address components
    """
    try:
        results = requests.get(url)
        # Add retry logic for rate limiting
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries and results.status_code == 429:
            retry_count += 1
            sleep_time = 2 ** retry_count
            time.sleep(sleep_time)
            results = requests.get(url)
            
        if results.status_code != 200:
            return {
                "formatted_address": None,
                "street_number": None,
                "street_name": None,
                "city": None,
                "county": None,
                "state": None,
                "state_code": None,
                "country": None,
                "country_code": None,
                "postcode": None,
                "latitude": None,
                "longitude": None,
                "accuracy": None,
                "google_place_id": None,
                "type": None,
                "number_of_results": 0,
                "status": f"HTTP Error: {results.status_code}"
            }
        
        results = results.json()
        
        if len(results.get('results', [])) == 0:
            output = {
                "formatted_address": None,
                "street_number": None,
                "street_name": None,
                "city": None,
                "county": None,
                "state": None,
                "state_code": None,
                "country": None,
                "country_code": None,
                "postcode": None,
                "latitude": None,
                "longitude": None,
                "accuracy": None,
                "google_place_id": None,
                "type": None
            }
        else:
            answer = results['results'][0]
            
            # Extract detailed address components
            components = {}
            for component in answer.get('address_components', []):
                types = component.get('types', [])
                long_name = component.get('long_name', '')
                short_name = component.get('short_name', '')
                
                if 'street_number' in types:
                    components['street_number'] = long_name
                elif 'route' in types:
                    components['street_name'] = long_name
                elif 'locality' in types:
                    components['city'] = long_name
                elif 'administrative_area_level_2' in types:
                    components['county'] = long_name
                elif 'administrative_area_level_1' in types:
                    components['state'] = long_name
                    components['state_code'] = short_name
                elif 'country' in types:
                    components['country'] = long_name
                    components['country_code'] = short_name
                elif 'postal_code' in types:
                    components['postcode'] = long_name
            
            output = {
                "formatted_address": answer.get('formatted_address'),
                "street_number": components.get('street_number'),
                "street_name": components.get('street_name'),
                "city": components.get('city'),
                "county": components.get('county'),
                "state": components.get('state'),
                "state_code": components.get('state_code'),
                "country": components.get('country'),
                "country_code": components.get('country_code'),
                "postcode": components.get('postcode'),
                "latitude": answer.get('geometry', {}).get('location', {}).get('lat'),
                "longitude": answer.get('geometry', {}).get('location', {}).get('lng'),
                "accuracy": answer.get('geometry', {}).get('location_type'),
                "google_place_id": answer.get("place_id"),
                "type": ",".join(answer.get('types', []))
            }
        
        output['number_of_results'] = len(results.get('results', []))
        output['status'] = results.get('status')
        return output
        
    except Exception as e:
        return {
            "formatted_address": None,
            "street_number": None,
            "street_name": None,
            "city": None,
            "county": None,
            "state": None,
            "state_code": None,
            "country": None,
            "country_code": None,
            "postcode": None,
            "latitude": None,
            "longitude": None,
            "accuracy": None,
            "google_place_id": None,
            "type": None,
            "number_of_results": 0,
            "status": f"Error: {str(e)}"
        }


def process_in_batches(urls, batch_size=100, max_workers=10, reverse_geocode=False):
    """
    Process URLs in batches with parallel processing.
    
    Args:
        urls: List of signed URLs
        batch_size: Number of URLs to process per batch
        max_workers: Maximum number of parallel workers
        reverse_geocode: If True, use reverse geocoding processor
    
    Returns:
        List of result dictionaries
    """
    all_results = []
    
    # Choose the appropriate processor
    processor = process_url_reverse if reverse_geocode else process_url
    
    # Process in batches to avoid overwhelming the API and memory
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i:i+batch_size]
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_results = list(executor.map(processor, batch_urls))
            
        all_results.extend(batch_results)
        
        # Provide progress update
        print(f"Processed {min(i+batch_size, len(urls))}/{len(urls)} URLs")
        
        # Optional: Add a small delay between batches to prevent rate limiting
        if i + batch_size < len(urls):
            time.sleep(1)
            
    return all_results


def fetch_google_results(signed_urls_df, reverse_geocode=False):
    """
    Sends requests to Google Maps API using signed URLs and parses the responses
    using parallel processing for improved performance.
    
    Args:
        signed_urls_df: DataFrame with 'Signed_URL' column
        reverse_geocode: If True, use reverse geocoding processor
    
    Returns:
        DataFrame with geocoding results
    """
    print(f"Processing {len(signed_urls_df)} URLs with parallel processing...")
    urls = signed_urls_df['Signed_URL'].tolist()
    results_dest = process_in_batches(urls, batch_size=100, max_workers=10, reverse_geocode=reverse_geocode)
    return pd.DataFrame(results_dest)


def get_directory_path(full_path):
    """
    Extracts the directory path from a full file path.

    Args:
        full_path: The full path to the file.

    Returns:
        The directory path of the file.
    """
    return os.path.dirname(full_path)


def signed_url_geocode(input_file, output_file, private_key, base_url, client, channel, 
                       geocode_only=False, dir='results', limit=None, reverse_geocode=False,
                       lat_col='latitude', lon_col='longitude'):
    """
    Main function to run the Google Maps API Signing and data retrieval script.
    
    Args:
        input_file: Path to input CSV file
        output_file: Name of output CSV file
        private_key: Google Maps API private key
        base_url: Google Maps API base URL
        client: Google Maps client ID
        channel: Google Maps channel
        geocode_only: If True, read existing signed URLs instead of generating new ones
        dir: Directory name for results
        limit: Limit number of rows to process (None for all)
        reverse_geocode: If True, perform reverse geocoding (lat/lon to address)
        lat_col: Name of latitude column (for reverse geocoding)
        lon_col: Name of longitude column (for reverse geocoding)
    
    Returns:
        DataFrame with combined results
    """
    # Create results directory if it doesn't exist
    cleaned_data_name = 'site_numbered_cleaned_data.csv'
    directory_path = get_directory_path(input_file)
    print(f"Working directory: {directory_path}")
    
    if geocode_only == False:
        file_path_full = os.path.join(directory_path, dir)
        os.makedirs(file_path_full, exist_ok=True)
        
        # Load data based on geocoding direction
        if reverse_geocode:
            print("=" * 60)
            print("REVERSE GEOCODING MODE: Converting lat/lon to addresses")
            print("=" * 60)
            data = load_data_reverse(input_file, nrows=limit, lat_col=lat_col, lon_col=lon_col)
        else:
            print("=" * 60)
            print("FORWARD GEOCODING MODE: Converting addresses to lat/lon")
            print("=" * 60)
            geocoder_instance = GoogleGeocoder()
            data = load_data(input_file, geocoder_instance, nrows=limit)
        
        print(f"Loaded {len(data)} records from {input_file}")
        
        # Add Site_Number to the original data
        data_rows = len(data)
        data['Site_Number'] = range(1, data_rows + 1)
        cleaned_data_path = os.path.join(file_path_full, cleaned_data_name)
        data.to_csv(cleaned_data_path, index=False)
        print(f"Saved cleaned data to {cleaned_data_path}")
        
        # Generate signed URLs
        if reverse_geocode:
            signed_urls_df = generate_signed_urls_reverse(data, private_key, base_url, client, channel, 
                                                         lat_col=lat_col, lon_col=lon_col)
        else:
            signed_urls_df = generate_signed_urls(data, private_key, base_url, client, channel)
        
        file_path_signed_csv = os.path.join(file_path_full, 'signed_urls.csv')
        signed_urls_df.to_csv(file_path_signed_csv, index=False)
        print("Signed URLs have been saved to signed_urls.csv")
        
        # Fetch Google results using improved parallel processing
        google_results_df = fetch_google_results(signed_urls_df, reverse_geocode=reverse_geocode)
        
        # Add Site_Number to the Google results dataframe
        google_results_df['Site_Number'] = range(1, len(google_results_df) + 1)
        google_results_path = os.path.join(file_path_full, 'google_results_df.csv')
        google_results_df.to_csv(google_results_path, index=False)
        print(f"Saved Google results to {google_results_path}")
    else:
        # Load existing data and signed URLs
        file_path_full = os.path.join(directory_path, dir)
        os.makedirs(file_path_full, exist_ok=True)
        file_path_cleaned = os.path.join(file_path_full, cleaned_data_name)
        data = pd.read_csv(file_path_cleaned)
        file_path_signed_csv = os.path.join(file_path_full, 'signed_urls.csv')
        signed_urls_df = pd.read_csv(file_path_signed_csv)
        print(f"Signed URLs have been read from {file_path_signed_csv}")
        
        # Fetch Google results using improved parallel processing
        google_results_df = fetch_google_results(signed_urls_df, reverse_geocode=reverse_geocode)
        
        # Add Site_Number to the Google results dataframe
        google_results_df['Site_Number'] = range(1, len(google_results_df) + 1)
        google_results_path = os.path.join(file_path_full, 'google_results_df.csv')
        google_results_df.to_csv(google_results_path, index=False)
        print(f"Saved Google results to {google_results_path}")
    
    try:
        # Check if the join key exists in both dataframes
        if 'Site_Number' not in google_results_df.columns:
            raise KeyError("'Site_Number' column not found in google_results_df")
        if 'Site_Number' not in data.columns:
            raise KeyError("'Site_Number' column not found in data")
        
        # Perform the merge operation
        google_results_df_combo = google_results_df.merge(data, on='Site_Number', how='inner')
        
        # Check if any records were matched
        if len(google_results_df_combo) == 0:
            print("Warning: No matching records found between the datasets")
        else:
            print(f"Successfully joined {len(google_results_df_combo)} records")
        
        # Save the combined dataframe to CSV
        file_path_csv_2 = os.path.join(file_path_full, output_file)
        google_results_df_combo.to_csv(file_path_csv_2, index=False)
        print(f"Combined data saved to {file_path_csv_2}")
        
    except Exception as e:
        print(f"Error joining datasets: {str(e)}")
        raise
    
    print("=" * 60)
    print(f"COMPLETE: Results saved to {output_file}")
    print("=" * 60)
    return google_results_df_combo

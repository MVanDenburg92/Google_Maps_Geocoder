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

def load_data(file_path, geocoder):
    data = pd.read_csv(file_path)
    
    print("Original columns:", data.columns)
    
    data, needs_geocoding = geocoder.cleanup_pd(data)
    
    print("Post-cleanup columns:", data.columns)
    
    if 'ADDRESS_FULL' not in data.columns:
        raise ValueError("Error: 'ADDRESS_FULL' column is missing after cleanup. Check input format.")
    
    return data


def sign_url(url, private_key):
    parsed_url = urllib.parse.urlparse(url)
    url_to_sign = parsed_url.path + "?" + parsed_url.query
    decoded_key = base64.urlsafe_b64decode(private_key)
    signature = hmac.new(decoded_key, url_to_sign.encode(), hashlib.sha1)
    encoded_signature = base64.urlsafe_b64encode(signature.digest()).decode("utf-8")
    return f"{url}&signature={encoded_signature}"

def generate_signed_urls(data, private_key, base_url, client, channel):
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

def process_in_batches(urls, batch_size=100, max_workers=10):
    all_results = []
    
    # Process in batches to avoid overwhelming the API and memory
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i:i+batch_size]
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_results = list(executor.map(process_url, batch_urls))
            
        all_results.extend(batch_results)
        
        # Provide progress update
        print(f"Processed {min(i+batch_size, len(urls))}/{len(urls)} URLs")
        
        # Optional: Add a small delay between batches to prevent rate limiting
        if i + batch_size < len(urls):
            time.sleep(1)
            
    return all_results

def fetch_google_results(signed_urls_df):
    """
    Sends requests to Google Maps API using signed URLs and parses the responses
    using parallel processing for improved performance.
    """
    print(f"Processing {len(signed_urls_df)} URLs with parallel processing...")
    urls = signed_urls_df['Signed_URL'].tolist()
    results_dest = process_in_batches(urls, batch_size=100, max_workers=10)
    return pd.DataFrame(results_dest)


def signed_url_geocode(input_file, output_file, private_key, base_url, client, channel, geocode_only = False,dir = 'results'):
    """
    Main function to run the Google Maps API Signing and data retrieval script.
    """
    # Create results directory if it doesn't exist
    cleaned_data_name = 'site_numbered_cleaned_data.csv'
    if geocode_only == False:
        os.makedirs(dir, exist_ok=True)
        
        geocoder = GoogleGeocoder()
        data = load_data(input_file, geocoder)
        print(f"Loaded {len(data)} records from {input_file}")
        
        # Add Site_Number to the original data
        data_rows = len(data)
        data['Site_Number'] = range(1, data_rows + 1)
        data.to_csv(cleaned_data_name)
        
        # Generate signed URLs
        signed_urls_df = generate_signed_urls(data, private_key, base_url, client, channel)
        file_path_signed_csv = os.path.join(dir, 'signed_urls.csv')
        signed_urls_df.to_csv(file_path_signed_csv, index=False)
        print("Signed URLs have been saved to signed_urls.csv")
        
        # Fetch Google results using improved parallel processing
        google_results_df = fetch_google_results(signed_urls_df)
        
        # Add Site_Number to the Google results dataframe
        google_results_df['Site_Number'] = range(1, len(google_results_df) + 1)
        google_results_df.to_csv(os.path.join(dir, 'google_results_df_0425.csv'))
    else:
        os.makedirs(dir, exist_ok=True)
        file_path_signed_csv = os.path.join(dir, cleaned_data_name)
        data = pd.read_csv(file_path_signed_csv)
        file_path_signed_csv = os.path.join(dir, 'signed_urls.csv')
        signed_urls_df = pd.read_csv(file_path_signed_csv)
        print("Signed URLs have been read from {}".format(file_path_signed_csv))
        
        # Fetch Google results using improved parallel processing
        google_results_df = fetch_google_results(signed_urls_df)
        
        # Add Site_Number to the Google results dataframe
        google_results_df['Site_Number'] = range(1, len(google_results_df) + 1)
        google_results_df.to_csv(os.path.join(dir, 'google_results_df_0425.csv'))

    
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
        file_path_csv = os.path.join(dir, output_file)
        google_results_df_combo.to_csv(file_path_csv, index=False)
        print(f"Combined data saved to {file_path_csv}")
        
    except Exception as e:
        print(f"Error joining datasets: {str(e)}")
        raise
    
    print(f"Google geocoding results have been saved to {output_file}")
    return google_results_df_combo
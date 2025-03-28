import hashlib
import hmac
import base64
import urllib.parse
import time
import pandas as pd
import requests
import os
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

def fetch_google_results(signed_urls_df):
    """
    Sends requests to Google Maps API using signed URLs and parses the responses.
    """
    results_dest = []
    
    for url in signed_urls_df['Signed_URL']:
        response = requests.get(url)
        results = response.json()

        # Default output in case of errors or no results
        if 'results' not in results or len(results['results']) == 0:
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
                "postcode": ",".join([
                    x['long_name'] for x in answer.get('address_components', [])
                    if 'postal_code' in x.get('types', [])
                ])
            }

        output['number_of_results'] = len(results.get('results', []))
        output['status'] = results.get('status')
        results_dest.append(output)

    return pd.DataFrame(results_dest)


def signed_url_geocode(input_file, output_file, private_key, base_url, client, channel, dir = 'results'):
    """
    Main function to run the Google Maps API Signing and data retrieval script.
    """
    geocoder = GoogleGeocoder()
    data = load_data(input_file, geocoder)
    print(data)
    signed_urls_df = generate_signed_urls(data, private_key, base_url, client, channel)
    file_path_signed_csv = os.path.join(dir, 'signed_urls.csv')
    signed_urls_df.to_csv(file_path_signed_csv, index=False)
    print("Signed URLs have been saved to signed_urls.csv")

    # Fetch Google results using signed URLs
    google_results_df = fetch_google_results(signed_urls_df)
    file_path_csv = os.path.join(dir, output_file)
    google_results_df.to_csv(file_path_csv, index=False)
    
    print(f"Google geocoding results have been saved to {output_file}")
# google_geocoder.py
import pandas as pd
import time
import re
import requests
import logging


class GoogleGeocoder:
    """
    A class for interacting with the Google Geocoding API and performing geocoding on datasets.
    """

    def __init__(self, api_key, return_full_results=False):
        """
        Initialize the GoogleGeocoder class.
        
        :param api_key: Google API key for accessing the Geocoding API.
        :param return_full_results: Boolean indicating if the full API response should be returned.
        """
        self.api_key = api_key
        self.return_full_results = return_full_results

        # Test the connection upon initialization
        self.test_connection()

    def test_connection(self):
        """
        Test the API key and internet connection by performing a sample geocode request.
        """
        test_address = "London, England"
        test_result = self.get_google_results(test_address)
        if (test_result['status'] != 'OK') or (test_result['formatted_address'] != 'London, UK'):
            logging.warning("There was an error when testing the Google Geocoder.")
            raise ConnectionError("Problem with test results from Google Geocode - check your API key and internet connection.")
        print("Google Geocoder API connection successful!")

    def cleanup_pd(self, destinations):
        """
        Cleans and preprocesses the input DataFrame for geocoding.
        
        :param destinations: DataFrame containing location data.
        :return: Tuple (cleaned DataFrame, boolean indicating if geocoding is needed).
        """
        try:
            destinations = destinations.dropna(how='all')
            filter_df_dest = destinations.filter(regex=re.compile(r"^lat.*|^Y$|^geo.*lat|^lon.*|^X$|^geo.*lon", re.IGNORECASE))
            dest_col_names = list(filter_df_dest.columns)
            if len(dest_col_names) > 0:
                destinations = destinations.rename(columns={dest_col_names[1]: 'Longitude', dest_col_names[0]: 'Latitude'})
                destinations['Coords'] = list(zip(destinations['Latitude'], destinations['Longitude']))
                if any(x[0] is None for x in destinations['Coords']):
                    destinations.drop(columns=['Latitude', 'Longitude', 'Coords'], inplace=True)
                    filter_df_dest = destinations.filter(regex=re.compile(r"address.*|city$|town$|state$|zip code.*|zipcode.*|zip*|Postal*|prov*", re.IGNORECASE))
                    destinations['ADDRESS_FULL'] = filter_df_dest.apply(lambda y: ','.join(y.dropna().astype(str)), axis=1)
        except Exception as e:
            print(f'Error cleaning destinations dataset: {e}')

        if 'Coords' not in destinations.columns:
            filter_df_dest = destinations.filter(regex=re.compile(r"address.*|city$|town$|state$|zip code.*|zipcode.*|zip*|Postal*|prov*", re.IGNORECASE))
            destinations['ADDRESS_FULL'] = filter_df_dest.apply(lambda y: ','.join(y.dropna().astype(str)), axis=1)
        return destinations, 'Coords' not in destinations.columns

    def get_google_results(self, address):
        """
        Fetch geocode results from the Google Maps Geocoding API.
        
        :param address: Address string to geocode.
        :return: Dictionary containing geocode information.
        """
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={self.api_key}"
        response = requests.get(geocode_url).json()

        if not response['results']:
            return {
                "formatted_address": None, "latitude": None, "longitude": None,
                "accuracy": None, "google_place_id": None, "type": None, "postcode": None,
                "input_string": address, "number_of_results": 0, "status": response.get('status')
            }
        
        answer = response['results'][0]
        return {
            "formatted_address": answer.get('formatted_address'),
            "latitude": answer.get('geometry', {}).get('location', {}).get('lat'),
            "longitude": answer.get('geometry', {}).get('location', {}).get('lng'),
            "accuracy": answer.get('geometry', {}).get('location_type'),
            "google_place_id": answer.get("place_id"),
            "type": ",".join(answer.get('types', [])),
            "postcode": ",".join([x['long_name'] for x in answer.get('address_components', []) if 'postal_code' in x.get('types', [])]),
            "input_string": address,
            "number_of_results": len(response['results']),
            "status": response.get('status'),
            "response": response if self.return_full_results else None
        }

    def geocode_addresses(self, destinations, destinations_value):
        """
        Geocodes a list of addresses and appends results to the DataFrame.
        
        :param destinations: DataFrame containing location data.
        :param destinations_value: Boolean indicating if geocoding is needed.
        :return: Updated DataFrame with geocoded coordinates.
        """
        if not destinations_value:
            print('Destinations are pre-geocoded and the Coords column is present.')
            return destinations

        addresses = destinations['ADDRESS_FULL'].tolist()
        results = []

        for address in addresses:
            while True:
                result = self.get_google_results(address)
                if result['status'] == 'OVER_QUERY_LIMIT':
                    print("Query limit reached. Backing off...")
                    time.sleep(60)  # Wait for 1 minute before retrying
                else:
                    results.append(result)
                    break

        geocoded_df = pd.DataFrame(results)
        destinations = pd.concat([destinations.reset_index(drop=True), geocoded_df], axis=1)
        destinations['Coords'] = list(zip(destinations['latitude'], destinations['longitude']))
        return destinations

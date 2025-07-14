# google_geocoder.py
import pandas as pd
import time
import re
import requests
import logging
import os


logging.basicConfig(
    filename="geocoder.log",
    level=logging.DEBUG,
    format="%(asctime)s = %(levelname)s - %(message)s"
)


class GoogleGeocoder:
    """
    A class for interacting with the Google Geocoding API and performing geocoding on datasets.
    """

    def __init__(self, api_key=None, return_full_results=False):
        """
        Initialize the GoogleGeocoder class.
        
        :param api_key: Google API key for accessing the Geocoding API.
        :param return_full_results: Boolean indicating if the full API response should be returned.
        """
        # self.api_key = api_key
        # self.return_full_results = return_full_results

        # #Test the connection upon initialization
        # self.test_connection()
        # logging.info("GoogleGeoCoder initialized")
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided either as a parameter or through the GOOGLE_API_KEY environment variable.")
        self.return_full_results = return_full_results
        logging.info("GoogleGeocoder initialized.")

    def test_connection(self):
        """
        Test the API key and internet connection by performing a sample geocode request.
        """
        test_address = "London, England"
        test_result = self.get_google_results(test_address)
        try:
            if (test_result['status'] != 'OK') or (test_result['formatted_address'] != 'London, UK'):
                logging.warning("Error testing the Google Geocoder API.")
                raise ConnectionError("Problem with test results from Google Geocode - check your API key and internet connection.")
            logging.info("Google Geocoder API connection successful!")
            print("Google Geocoder API connection successful!")
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            raise

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
                    filter_df_dest = destinations.filter(regex=re.compile(r"Street Address|address.*|city$|Street City|town$|state$|Street Zip|zip code.*|zipcode.*|zip*|Postal*|prov*", re.IGNORECASE))
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
        try:
            response = requests.get(geocode_url).json()

            if not response['results']:
                logging.warning(f"No results found for address: {address}")
                return {
                    "formatted_address": None, "latitude": None, "longitude": None,
                    "accuracy": None, "google_place_id": None, "type": None, "postcode": None,
                    "input_string": address, "number_of_results": 0, "status": response.get('status')
                }
            
            answer = response['results'][0]
            logging.info(f"Successfully retrieved results for address: {address}")
            print(f"Successfully retrieved results for address: {address}")
            return  {
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
        except requests.RequestException as e:
            logging.error(f"Requests failed for address {address}: {e}")
            raise
        except Exception as e:
            logging.error(f"Error processing results for address {address}: {e}")
            raise
    
    def geocode_single(self, address):
        """
        Fetch geocode results for a single address from the Google Maps Geocoding API.
        
        :param address: Address string to geocode.
        :return: Single entry dataframe containing the results of the call. 
        """
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={self.api_key}"
        response = requests.get(geocode_url).json()
        try:
            response = requests.get(geocode_url).json()

            if not response['results']:
                logging.warning(f"No results found for address: {address}")
                return {
                    "formatted_address": None, "latitude": None, "longitude": None,
                    "accuracy": None, "google_place_id": None, "type": None, "postcode": None,
                    "input_string": address, "number_of_results": 0, "status": response.get('status')
                }
            
            answer = response['results'][0]
            logging.info(f"Successfully retrieved results for address: {address}")
            print(f"Successfully retrieved results for address: {address}")
            rez =  {
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
            return pd.json_normalize(rez)
        except requests.RequestException as e:
            logging.error(f"Requests failed for address {address}: {e}")
            raise
        except Exception as e:
            logging.error(f"Error processing results for address {address}: {e}")
            raise
    
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
                try:
                    result = self.get_google_results(address)
                    if result['status'] == 'OVER_QUERY_LIMIT':
                        logging.warning("Query limit reached. Backing off...")
                        time.sleep(60)  # Wait for 1 minute before retrying
                    else:
                        results.append(result)
                        break
                except Exception as e:
                    logging.error(f"Error geocoding address {address}: {e}")
                    break

        geocoded_df = pd.DataFrame(results)
        destinations = pd.concat([destinations.reset_index(drop=True), geocoded_df], axis=1)
        destinations['Coords'] = list(zip(destinations['latitude'], destinations['longitude']))
        return destinations
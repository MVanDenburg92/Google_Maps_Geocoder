import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from google_maps_geocoder import GoogleGeocoder

class TestGoogleGeocoder(unittest.TestCase):

    @patch('requests.get')
    def test_init_connection_success(self, mock_get):
        # Simulate a successful API response for the test connection
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{'formatted_address': 'London, UK'}],
            'status': 'OK'
        }
        mock_get.return_value = mock_response

        geocoder = GoogleGeocoder(api_key="fake_api_key")

        # Test that the connection was successful
        self.assertIsInstance(geocoder, GoogleGeocoder)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_init_connection_failure(self, mock_get):
        # Simulate a failed API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [],
            'status': 'ZERO_RESULTS'
        }
        mock_get.return_value = mock_response

        with self.assertRaises(ConnectionError):
            GoogleGeocoder(api_key="fake_api_key")

    def test_cleanup_pd(self):
        # Example DataFrame to test cleanup_pd method
        data = {
            'address': ['123 Main St', '456 Elm St', None],
            'city': ['Boston', 'Chicago', 'New York'],
            'state': ['MA', 'IL', 'NY'],
            'lat': [None, None, 40.7128],
            'lon': [None, None, -74.0060]
        }
        df = pd.DataFrame(data)

        geocoder = GoogleGeocoder(api_key="fake_api_key")

        cleaned_df, geocode_needed = geocoder.cleanup_pd(df)

        # Check that the cleaned DataFrame has the 'ADDRESS_FULL' column
        self.assertIn('ADDRESS_FULL', cleaned_df.columns)
        self.assertTrue(geocode_needed)

    @patch('requests.get')
    def test_get_google_results_success(self, mock_get):
        # Simulate a successful API response for geocoding
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{
                'formatted_address': '1600 Amphitheatre Parkway, Mountain View, CA',
                'geometry': {'location': {'lat': 37.423021, 'lng': -122.083739}},
                'address_components': [{'types': ['postal_code'], 'long_name': '94043'}],
                'place_id': 'ChIJ2eUgeAK6j4ARbn5u_wfPfg0',
                'types': ['street_address']
            }],
            'status': 'OK'
        }
        mock_get.return_value = mock_response

        geocoder = GoogleGeocoder(api_key="fake_api_key")
        result = geocoder.get_google_results("1600 Amphitheatre Parkway, Mountain View, CA")

        # Check that the result matches the expected values
        self.assertEqual(result['formatted_address'], '1600 Amphitheatre Parkway, Mountain View, CA')
        self.assertEqual(result['latitude'], 37.423021)
        self.assertEqual(result['longitude'], -122.083739)
        self.assertEqual(result['postcode'], '94043')
        self.assertEqual(result['status'], 'OK')

    @patch('requests.get')
    def test_geocode_addresses(self, mock_get):
        # Simulate a successful API response for multiple addresses
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{
                'formatted_address': '1600 Amphitheatre Parkway, Mountain View, CA',
                'geometry': {'location': {'lat': 37.423021, 'lng': -122.083739}},
                'address_components': [{'types': ['postal_code'], 'long_name': '94043'}],
                'place_id': 'ChIJ2eUgeAK6j4ARbn5u_wfPfg0',
                'types': ['street_address']
            }],
            'status': 'OK'
        }
        mock_get.return_value = mock_response

        data = {
            'ADDRESS_FULL': ['1600 Amphitheatre Parkway, Mountain View, CA', 'Another Address']
        }
        df = pd.DataFrame(data)

        geocoder = GoogleGeocoder(api_key="fake_api_key")
        result_df = geocoder.geocode_addresses(df, destinations_value=True)

        # Check that the result DataFrame has the expected columns
        self.assertIn('latitude', result_df.columns)
        self.assertIn('longitude', result_df.columns)
        self.assertEqual(len(result_df), 2)  # There should be 2 addresses in the result

    @patch('requests.get')
    def test_handle_over_query_limit(self, mock_get):
        # Simulate 'OVER_QUERY_LIMIT' status from the API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [],
            'status': 'OVER_QUERY_LIMIT'
        }
        mock_get.return_value = mock_response

        geocoder = GoogleGeocoder(api_key="fake_api_key")
        result = geocoder.get_google_results("1600 Amphitheatre Parkway, Mountain View, CA")

        # Ensure the response handles OVER_QUERY_LIMIT and retries appropriately
        self.assertEqual(result['status'], 'OVER_QUERY_LIMIT')


if __name__ == '__main__':
    unittest.main()

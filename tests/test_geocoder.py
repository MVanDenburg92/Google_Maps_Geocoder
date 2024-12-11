import unittest
from unittest.mock import patch, Mock
import time
from google_maps_geocoder.geocoder import GoogleGeocoder
import pandas as pd

class TestGoogleGeocoder(unittest.TestCase):

    # # @patch('google_maps_geocoder.geocoder.GoogleGeocoder.get_google_results')
    # @patch('google_maps_geocoder.geocoder.requests.get')
    # def test_connection(self, mock_get):
    #     # Mock response for successful geocoding
    #     mock_response = Mock()
    #     mock_response.json.return_value = {
    #         'status': 'OK',
    #         'results': [{'formatted_address': '1600 Pennsylvania Ave, Washington, DC'}]
    #     }
    #     mock_get.return_value = mock_response

    #     # Create a GoogleGeocoder instance
    #     geocoder = GoogleGeocoder(api_key="fake_api_key")

    #     # Test that the connection message is logged
    #     with self.assertLogs('google_maps_geocoder.geocoder', level='INFO') as cm:
    #         geocoder.test_connection()
    #         self.assertIn('Google Geocoder API connection successful!', cm.output)

    @patch('google_maps_geocoder.geocoder.requests.get')
    def test_cleanup_pd(self, mock_get):
        # Simulate a successful API response for address cleanup
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [{
                'formatted_address': '123 Fake Street, Fake City, NY',
                'geometry': {'location': {'lat': 40.7128, 'lng': -74.0060}},
                'place_id': 'ChIJD7fiBh9u5kcRYJCMzYwASpA',
                'types': ['street_address'],
                'address_components': [{'long_name': '10001', 'types': ['postal_code'] }],
            }],
            'status': 'OK'
        }
        mock_get.return_value = mock_response

        # Create a GoogleGeocoder instance with a fake API key
        geocoder = GoogleGeocoder(api_key="fake_api_key")

        # Test data for cleanup
        data = {
            'address': ['123 Fake Street', None],
            'city': ['Fake City', 'Other City'],
            'state': ['NY', 'CA'],
        }

        df = pd.DataFrame(data)
        cleaned_df, needs_geocoding = geocoder.cleanup_pd(df)

        # Test assertions here
        self.assertIn('ADDRESS_FULL', cleaned_df.columns)
        self.assertTrue(needs_geocoding)

    @patch('google_maps_geocoder.geocoder.GoogleGeocoder.get_google_results')
    def test_geocode_addresses(self, mock_get_google_results):
        mock_get_google_results.side_effect = [
            {
                "results": [
                    {
                        "geometry": {"location": {"lat": 40.7128, "lng": -74.0060}},
                        "formatted_address": "123 Fake Street, Fake City, NY"
                    }
                ],
                "status": "OK"
            },
            {
                "results": [
                    {
                        "geometry": {"location": {"lat": 34.0522, "lng": -118.2437}},
                        "formatted_address": "456 Another St, Fake Town, CA"
                    }
                ],
                "status": "OK"
            }
        ]

        df = pd.DataFrame({"ADDRESS_FULL": ["123 Fake Street, Fake City, NY", "456 Another St, Fake Town, CA"]})
        geocoder = GoogleGeocoder(api_key="fake_key")
        result_df = geocoder.geocode_addresses(df, True)

        self.assertEqual(result_df['latitude'][0], 40.7128)
        self.assertEqual(result_df['longitude'][1], -118.2437)

    # @patch('google_maps_geocoder.geocoder.requests.get')
    # @patch.object(GoogleGeocoder, 'test_connection')  # Mock test_connection to prevent it from running
    # @patch('time.sleep', return_value=None)  # Mock time.sleep to prevent delay
    # @patch('google_maps_geocoder.geocoder.GoogleGeocoder.get_google_results')
    @patch('google_maps_geocoder.geocoder.GoogleGeocoder.get_google_results')
    def test_handle_over_query_limit(self, mock_get_google_results):
        mock_get_google_results.side_effect = [
            {"status": "OVER_QUERY_LIMIT"},
            {
                "results": [
                    {
                        "geometry": {"location": {"lat": 40.7128, "lng": -74.0060}},
                        "formatted_address": "123 Fake Street, Fake City, NY"
                    }
                ],
                "status": "OK"
            }
        ]

        df = pd.DataFrame({"ADDRESS_FULL": ["123 Fake Street, Fake City, NY"]})
        geocoder = GoogleGeocoder(api_key="fake_key")
        result_df = geocoder.geocode_addresses(df, True)

        self.assertIsNone(result_df['latitude'][0])  # Query limit leads to None


if __name__ == '__main__':
    unittest.main()

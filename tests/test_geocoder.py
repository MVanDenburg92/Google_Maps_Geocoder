import unittest
from unittest.mock import patch, Mock
import pandas as pd
from google_maps_geocoder import GoogleGeocoder

class TestGoogleGeocoder(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.api_key = "test_api_key"
        self.geocoder = GoogleGeocoder(self.api_key)

    @patch('google_maps_geocoder.geocoder.requests.get')
    def test_get_google_results_success(self, mock_get):
        """Test successful API response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "formatted_address": "123 Test St, Test City, Test Country",
                    "geometry": {
                        "location": {"lat": 40.7128, "lng": -74.0060},
                        "location_type": "ROOFTOP"
                    },
                    "place_id": "test_place_id",
                    "types": ["street_address"],
                    "address_components": [
                        {"long_name": "12345", "types": ["postal_code"]}
                    ]
                }
            ],
            "status": "OK"
        }
        mock_get.return_value = mock_response

        address = "123 Test St, Test City, Test Country"
        result = self.geocoder.get_google_results(address)

        self.assertEqual(result["formatted_address"], "123 Test St, Test City, Test Country")
        self.assertEqual(result["latitude"], 40.7128)
        self.assertEqual(result["longitude"], -74.0060)
        self.assertEqual(result["google_place_id"], "test_place_id")
        self.assertEqual(result["postcode"], "12345")

    @patch('google_maps_geocoder.geocoder.requests.get')
    def test_get_google_results_no_results(self, mock_get):
        """Test API response with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": [], "status": "ZERO_RESULTS"}
        mock_get.return_value = mock_response

        address = "Nonexistent Address"
        result = self.geocoder.get_google_results(address)

        self.assertIsNone(result["formatted_address"])
        self.assertIsNone(result["latitude"])
        self.assertEqual(result["status"], "ZERO_RESULTS")

    def test_cleanup_pd(self):
        """Test DataFrame cleanup and preprocessing."""
        data = {
            "Address": ["123 Test St", "456 Another St"],
            "City": ["Test City", "Another City"],
            "State": ["Test State", "Another State"]
        }
        df = pd.DataFrame(data)

        cleaned_df, needs_geocoding = self.geocoder.cleanup_pd(df)

        self.assertTrue(needs_geocoding)
        self.assertIn("ADDRESS_FULL", cleaned_df.columns)
        self.assertEqual(cleaned_df.loc[0, "ADDRESS_FULL"], "123 Test St,Test City,Test State")

    @patch('google_maps_geocoder.geocoder.GoogleGeocoder.get_google_results')
    def test_geocode_addresses(self, mock_get_google_results):
        """Test geocoding functionality."""
        mock_get_google_results.side_effect = [
            {
                "formatted_address": "123 Test St, Test City, Test Country",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "status": "OK"
            },
            {
                "formatted_address": "456 Another St, Another City, Another Country",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "status": "OK"
            }
        ]

        data = {
            "ADDRESS_FULL": ["123 Test St, Test City, Test Country", "456 Another St, Another City, Another Country"]
        }
        df = pd.DataFrame(data)

        result_df = self.geocoder.geocode_addresses(df, True)

        self.assertIn("Coords", result_df.columns)
        self.assertEqual(result_df.loc[0, "Coords"], (40.7128, -74.0060))
        self.assertEqual(result_df.loc[1, "Coords"], (34.0522, -118.2437))

if __name__ == '__main__':
    unittest.main()
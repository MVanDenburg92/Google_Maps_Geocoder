"""Custom exceptions for the Google Maps geocoder module."""

class GoogleMapsError(Exception):
    """Base exception for Google Maps API errors."""
    pass

class GeocodingAPIError(GoogleMapsError):
    """Raised when there's an error with the Geocoding API."""
    pass

class ValidationAPIError(GoogleMapsError):
    """Raised when there's an error with the Address Validation API."""
    pass

class CSVError(GoogleMapsError):
    """Raised when there's an error processing CSV files."""
    pass

class ConfigurationError(GoogleMapsError):
    """Raised when there's a configuration error."""
    pass

class RateLimitError(GoogleMapsError):
    """Raised when API rate limits are exceeded."""
    pass
import pandas as pd
import re
import logging
import time
import functools
from typing import Dict, Any, Optional, List, Callable
from .config import Config

def setup_logging(config: Config) -> logging.Logger:
    """Set up logging configuration."""
    # Create logger
    logger = logging.getLogger('google_maps_geocoder')
    
    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(config.log_format)
    
    # Create file handler
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(getattr(logging, config.log_level.upper()))
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.log_level.upper()))
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def concatenate_address_fields(address: str, city: str, state: str, zip_code: str) -> str:
    """
    Concatenate individual address fields into a complete address string.
    
    Parameters
    ----------
    address : str
        Street address
    city : str
        City name
    state : str
        State or province
    zip_code : str
        Postal/ZIP code
        
    Returns
    -------
    str
        Formatted complete address
    """
    # Handle NaN/None values
    address = str(address) if pd.notna(address) else ''
    city = str(city) if pd.notna(city) else ''
    state = str(state) if pd.notna(state) else ''
    zip_code = str(zip_code) if pd.notna(zip_code) else ''
    
    # Clean up any 'nan' strings that might result from pd.notna check
    address = address if address != 'nan' else ''
    city = city if city != 'nan' else ''
    state = state if state != 'nan' else ''
    zip_code = zip_code if zip_code != 'nan' else ''
    
    # Build address parts
    parts = []
    
    if address.strip():
        parts.append(address.strip())
    
    # City, State ZIP format
    location_parts = []
    if city.strip():
        location_parts.append(city.strip())
    
    if state.strip():
        location_parts.append(state.strip())
    
    if location_parts:
        location = ', '.join(location_parts)
        if zip_code.strip():
            location += f' {zip_code.strip()}'
        parts.append(location)
    elif zip_code.strip():
        parts.append(zip_code.strip())
    
    return ', '.join(parts)

def parse_validation_result(api_response: Dict) -> Dict:
    """
    Parse Google Address Validation API response.
    
    Parameters
    ----------
    api_response : Dict
        Raw API response from Google Address Validation API
        
    Returns
    -------
    Dict
        Parsed validation information
    """
    result = {
        'is_valid': False,
        'confidence': None,
        'formatted_address': None,
        'errors': None
    }
    
    # Check for API errors
    if 'error' in api_response:
        result['errors'] = api_response['error']
        return result
    
    try:
        # Extract validation result
        validation_result = api_response.get('result', {})
        
        # Check overall validation verdict
        verdict = validation_result.get('verdict', {})
        result['is_valid'] = verdict.get('addressComplete', False)
        
        # Get confidence score if available
        if 'geocode' in validation_result:
            geocode = validation_result['geocode']
            if 'placeId' in geocode:
                result['confidence'] = 'HIGH'
            else:
                result['confidence'] = 'MEDIUM'
        
        # Get formatted address
        if 'address' in validation_result:
            formatted = validation_result['address']
            if 'formattedAddress' in formatted:
                result['formatted_address'] = formatted['formattedAddress']
        
        # Collect any validation issues
        errors = []
        if 'addressComplete' in verdict and not verdict['addressComplete']:
            errors.append('Address incomplete')
        if 'hasUnconfirmedComponents' in verdict and verdict['hasUnconfirmedComponents']:
            errors.append('Has unconfirmed components')
        if 'hasInferredComponents' in verdict and verdict['hasInferredComponents']:
            errors.append('Has inferred components')
        if 'hasReplacedComponents' in verdict and verdict['hasReplacedComponents']:
            errors.append('Has replaced components')
        
        if errors:
            result['errors'] = '; '.join(errors)
            
    except Exception as e:
        result['errors'] = f"Error parsing API response: {e}"
    
    return result

def parse_geocoding_result(api_response: Dict) -> Dict:
    """
    Parse Google Geocoding API response (for compatibility with existing code).
    
    Parameters
    ----------
    api_response : Dict
        Raw API response from Google Geocoding API
        
    Returns
    -------
    Dict
        Parsed geocoding information
    """
    if not api_response.get('results'):
        return {
            "formatted_address": None,
            "latitude": None,
            "longitude": None,
            "accuracy": None,
            "google_place_id": None,
            "type": None,
            "postcode": None,
            "number_of_results": 0,
            "status": api_response.get('status', 'NO_RESULTS')
        }
    
    answer = api_response['results'][0]
    return {
        "formatted_address": answer.get('formatted_address'),
        "latitude": answer.get('geometry', {}).get('location', {}).get('lat'),
        "longitude": answer.get('geometry', {}).get('location', {}).get('lng'),
        "accuracy": answer.get('geometry', {}).get('location_type'),
        "google_place_id": answer.get("place_id"),
        "type": ",".join(answer.get('types', [])),
        "postcode": ",".join([x['long_name'] for x in answer.get('address_components', [])
                            if 'postal_code' in x.get('types', [])]),
        "number_of_results": len(api_response['results']),
        "status": api_response.get('status')
    }

def validate_csv_columns(df: pd.DataFrame, required_columns: List[str]) -> None:
    """Validate that required columns exist in DataFrame."""
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        from .exceptions import CSVError
        raise CSVError(f"Missing required columns: {missing_cols}")

def generate_validation_summary(df: pd.DataFrame) -> Dict:
    """
    Generate summary statistics for address validation results.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with validation results
        
    Returns
    -------
    Dict
        Summary statistics
    """
    total_addresses = len(df)
    valid_addresses = df['is_valid'].sum() if 'is_valid' in df.columns else 0
    invalid_addresses = total_addresses - valid_addresses
    
    summary = {
        'total_addresses': total_addresses,
        'valid_addresses': int(valid_addresses),
        'invalid_addresses': int(invalid_addresses),
        'validation_rate': round((valid_addresses / total_addresses) * 100, 2) if total_addresses > 0 else 0
    }
    
    # Error breakdown
    if 'validation_errors' in df.columns:
        error_counts = df['validation_errors'].value_counts()
        summary['common_errors'] = error_counts.head().to_dict()
    
    # Confidence breakdown
    if 'validation_confidence' in df.columns:
        confidence_counts = df['validation_confidence'].value_counts()
        summary['confidence_breakdown'] = confidence_counts.to_dict()
    
    return summary

def cleanup_address_dataframe(df: pd.DataFrame) -> tuple:
    """
    Enhanced version of the cleanup_pd function with better error handling.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with address data
        
    Returns
    -------
    tuple
        (cleaned DataFrame, needs_geocoding boolean)
    """
    try:
        df = df.dropna(how='all')
        
        # Check for existing coordinates
        coord_filter = df.filter(regex=re.compile(
            r"^lat.*|^Y$|^geo.*lat|^lon.*|^X$|^geo.*lon", re.IGNORECASE))
        coord_cols = list(coord_filter.columns)
        
        if len(coord_cols) >= 2:
            # Rename coordinate columns
            df = df.rename(columns={
                coord_cols[0]: 'Latitude', 
                coord_cols[1]: 'Longitude'
            })
            df['Coords'] = list(zip(df['Latitude'], df['Longitude']))
            
            # Check if coordinates are valid
            if any(pd.isna(x[0]) or pd.isna(x[1]) for x in df['Coords']):
                df.drop(columns=['Latitude', 'Longitude', 'Coords'], inplace=True)
                needs_geocoding = True
            else:
                needs_geocoding = False
        else:
            needs_geocoding = True
        
        # Create full address if needed
        if needs_geocoding or 'ADDRESS_FULL' not in df.columns:
            address_filter = df.filter(regex=re.compile(
                r"Street Address|address.*|city$|Street City|town$|state$|Street Zip|zip code.*|zipcode.*|zip*|Postal*|prov*", 
                re.IGNORECASE))
            df['ADDRESS_FULL'] = address_filter.apply(
                lambda y: ','.join(y.dropna().astype(str)), axis=1)
        
        return df, needs_geocoding
        
    except Exception as e:
        from .exceptions import CSVError
        raise CSVError(f'Error cleaning address DataFrame: {e}')

class RateLimiter:
    """Rate limiter class for API calls."""
    
    def __init__(self, requests_per_second: float = 10.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_call_time = 0.0
    
    def wait(self):
        """Wait if necessary to maintain rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        
        self.last_call_time = time.time()

def rate_limit(func: Optional[Callable] = None, *, requests_per_second: float = 10.0):
    """
    Decorator to add rate limiting to API calls.
    
    Parameters
    ----------
    func : Callable, optional
        Function to decorate
    requests_per_second : float
        Maximum requests per second
        
    Returns
    -------
    Callable
        Decorated function with rate limiting
    """
    def decorator(f):
        limiter = RateLimiter(requests_per_second)
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return f(*args, **kwargs)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

def batch_process(items: List[Any], batch_size: int, process_func: Callable) -> List[Any]:
    """
    Process items in batches.
    
    Parameters
    ----------
    items : List[Any]
        Items to process
    batch_size : int
        Size of each batch
    process_func : Callable
        Function to process each batch
        
    Returns
    -------
    List[Any]
        Processed results
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = process_func(batch)
        results.extend(batch_results)
    
    return results

def validate_region_code(region_code: str, supported_regions: Dict[str, str]) -> bool:
    """
    Validate if a region code is supported.
    
    Parameters
    ----------
    region_code : str
        ISO country code
    supported_regions : Dict[str, str]
        Dictionary of supported regions
        
    Returns
    -------
    bool
        True if region is supported
    """
    return region_code.upper() in supported_regions

def format_address_for_api(address_parts: Dict[str, str]) -> str:
    """
    Format address parts for API consumption.
    
    Parameters
    ----------
    address_parts : Dict[str, str]
        Dictionary with address components
        
    Returns
    -------
    str
        Formatted address string
    """
    required_fields = ['address', 'city', 'state', 'zip']
    
    # Check if we have the required fields
    if not all(field in address_parts for field in required_fields):
        missing = [field for field in required_fields if field not in address_parts]
        raise ValueError(f"Missing address fields: {missing}")
    
    return concatenate_address_fields(
        address_parts['address'],
        address_parts['city'],
        address_parts['state'],
        address_parts['zip']
    )

def calculate_processing_time(start_time: float, total_items: int, processed_items: int) -> Dict[str, Any]:
    """
    Calculate processing statistics.
    
    Parameters
    ----------
    start_time : float
        Processing start time
    total_items : int
        Total number of items
    processed_items : int
        Number of processed items
        
    Returns
    -------
    Dict[str, Any]
        Processing statistics
    """
    current_time = time.time()
    elapsed_time = current_time - start_time
    
    if processed_items == 0:
        return {
            'elapsed_time': elapsed_time,
            'items_per_second': 0,
            'estimated_remaining': 0,
            'progress_percentage': 0
        }
    
    items_per_second = processed_items / elapsed_time
    remaining_items = total_items - processed_items
    estimated_remaining = remaining_items / items_per_second if items_per_second > 0 else 0
    progress_percentage = (processed_items / total_items) * 100
    
    return {
        'elapsed_time': elapsed_time,
        'items_per_second': items_per_second,
        'estimated_remaining': estimated_remaining,
        'progress_percentage': progress_percentage
    }

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Parameters
    ----------
    filename : str
        Original filename
        
    Returns
    -------
    str
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure it's not empty
    if not filename:
        filename = 'output'
    
    return filename
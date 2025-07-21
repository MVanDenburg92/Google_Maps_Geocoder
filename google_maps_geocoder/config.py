import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Config:
    """Configuration class for Google Maps geocoder and address validator."""
    
    # API Configuration
    google_api_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_private_key: Optional[str] = None
    
    # API URLs
    geocoding_base_url: str = "https://maps.googleapis.com/maps/api/geocode/json"
    validation_base_url: str = "https://addressvalidation.googleapis.com/v1:validateAddress"
    
    # Default column names for CSV processing
    address_col: str = "Address"
    city_col: str = "City"
    state_col: str = "State"
    zip_col: str = "Zip"
    region_col: Optional[str] = None
    
    # Processing settings
    default_region: str = "US"
    batch_size: int = 100
    delay_seconds: float = 0.1
    max_retries: int = 3
    timeout: int = 30
    max_workers: int = 10
    
    # Signed URL specific settings
    channel: str = "geocoder"  # Channel identifier for signed URLs
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "geocoder.log"
    
    # Rate limiting
    requests_per_second: float = 10.0
    daily_request_limit: int = 40000
    
    # Supported regions for address validation
    supported_regions: Dict[str, str] = field(default_factory=lambda: {
        'AR': 'Argentina', 'AT': 'Austria', 'AU': 'Australia', 'BE': 'Belgium',
        'BG': 'Bulgaria', 'BR': 'Brazil', 'CA': 'Canada', 'CH': 'Switzerland',
        'CL': 'Chile', 'CO': 'Colombia', 'CZ': 'Czechia', 'DE': 'Germany',
        'DK': 'Denmark', 'EE': 'Estonia', 'ES': 'Spain', 'FI': 'Finland',
        'FR': 'France', 'GB': 'United Kingdom', 'HR': 'Croatia', 'HU': 'Hungary',
        'IE': 'Ireland', 'IN': 'India', 'IT': 'Italy', 'LT': 'Lithuania',
        'LU': 'Luxembourg', 'LV': 'Latvia', 'MX': 'Mexico', 'MY': 'Malaysia',
        'NL': 'Netherlands', 'NO': 'Norway', 'NZ': 'New Zealand', 'PL': 'Poland',
        'PR': 'Puerto Rico', 'PT': 'Portugal', 'SE': 'Sweden', 'SG': 'Singapore',
        'SI': 'Slovenia', 'SK': 'Slovakia', 'US': 'United States'
    })
    
    def __post_init__(self):
        """Post-initialization to load environment variables."""
        if not self.google_api_key:
            self.google_api_key = os.getenv('GOOGLE_API_KEY')
        if not self.google_client_id:
            self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not self.google_private_key:
            self.google_private_key = os.getenv('GOOGLE_MAPS_PRIVATE_KEY')
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create Config from environment variables."""
        config = cls()
        
        # Override with environment variables if they exist
        env_mappings = {
            'GOOGLE_API_KEY': 'google_api_key',
            'GOOGLE_CLIENT_ID': 'google_client_id', 
            'GOOGLE_PRIVATE_KEY': 'google_private_key',
            'DEFAULT_REGION': 'default_region',
            'BATCH_SIZE': 'batch_size',
            'DELAY_SECONDS': 'delay_seconds',
            'MAX_RETRIES': 'max_retries',
            'LOG_LEVEL': 'log_level',
            'MAX_WORKERS': 'max_workers',
            'CHANNEL': 'channel'  # NEW: Channel for signed URLs
        }
        
        for env_var, attr_name in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Convert types as needed
                if attr_name in ['batch_size', 'max_retries', 'max_workers']:
                    env_value = int(env_value)
                elif attr_name == 'delay_seconds':
                    env_value = float(env_value)
                setattr(config, attr_name, env_value)
        
        return config
    
    def validate(self) -> bool:
        """
        Validate configuration settings.
        
        Returns
        -------
        bool
            True if configuration is valid
            
        Raises
        ------
        ValueError
            If configuration is invalid
        """
        # Check that we have either API key OR client credentials
        has_api_key = bool(self.google_api_key)
        has_client_creds = bool(self.google_client_id and self.google_private_key)
        
        if not (has_api_key or has_client_creds):
            raise ValueError(
                "Either google_api_key OR (google_client_id AND google_private_key) must be provided"
            )
        
        # Validate region code
        if self.default_region not in self.supported_regions:
            raise ValueError(f"Unsupported region: {self.default_region}")
        
        # Validate numeric settings
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")
        
        return True
    
    def get_auth_method(self) -> str:
        """
        Determine which authentication method to use.
        
        Returns
        -------
        str
            'signed_url' or 'api_key'
        """
        if self.google_client_id and self.google_private_key:
            return 'signed_url'
        elif self.google_api_key:
            return 'api_key'
        else:
            raise ValueError("No valid authentication method available")

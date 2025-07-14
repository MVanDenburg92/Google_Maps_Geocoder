import pandas as pd
import requests
import time
from typing import Dict, Optional
import logging
import os
from .config import Config
from .utils import (
    concatenate_address_fields, 
    parse_validation_result, 
    setup_logging,
    validate_csv_columns,
    generate_validation_summary,
    rate_limit
)
from .exceptions import ValidationAPIError, CSVError, ConfigurationError

class AddressValidator:
    """Main class for address validation operations using Google's Address Validation API."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize AddressValidator.
        
        Parameters
        ----------
        config : Config, optional
            Configuration object. If None, loads from environment.
        """
        self.config = config or Config.from_env()
        self.logger = setup_logging(self.config)
        
        # Validate configuration
        if not self.config.google_api_key:
            raise ConfigurationError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable "
                "or provide it in the config."
            )
    
    @rate_limit
    def validate_single_address(
        self, 
        address: str, 
        region: str = None
    ) -> Dict:
        """
        Validate a single address using Google Address Validation API.
        
        Parameters
        ----------
        address : str
            Complete address string
        region : str, optional
            ISO country code. Uses config default if not provided.
            
        Returns
        -------
        Dict
            Google Address Validation API response
        """
        if region is None:
            region = self.config.default_region
            
        url = f'{self.config.validation_base_url}?key={self.config.google_api_key}'
        
        payload = {
            "address": {
                "addressLines": [address], 
                "regionCode": region
            }
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise ValidationAPIError(f"API request failed after {self.config.max_retries} retries: {e}")
                
                self.logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                time.sleep(self.config.delay_seconds * (attempt + 1))  # Exponential backoff
        
        return {"error": f"Failed after {self.config.max_retries} retries", "address": address}
    
    def validate_csv_addresses(
        self,
        csv_file_path: str,
        address_col: Optional[str] = None,
        city_col: Optional[str] = None, 
        state_col: Optional[str] = None,
        zip_col: Optional[str] = None,
        region_col: Optional[str] = None,
        default_region: Optional[str] = None,
        batch_size: Optional[int] = None,
        delay_seconds: Optional[float] = None,
        output_file: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Validate addresses from CSV by concatenating address fields.
        
        Parameters override config defaults when provided.
        """
        # Use config defaults if parameters not provided
        address_col = address_col or self.config.address_col
        city_col = city_col or self.config.city_col
        state_col = state_col or self.config.state_col
        zip_col = zip_col or self.config.zip_col
        region_col = region_col or self.config.region_col
        default_region = default_region or self.config.default_region
        batch_size = batch_size or self.config.batch_size
        delay_seconds = delay_seconds if delay_seconds is not None else self.config.delay_seconds
        
        try:
            # Load CSV file
            self.logger.info(f"Loading CSV file: {csv_file_path}")
            df = pd.read_csv(csv_file_path)
            self.logger.info(f"Loaded {len(df)} rows")
            
            # Validate required columns exist
            required_cols = [address_col, city_col, state_col, zip_col]
            validate_csv_columns(df, required_cols)
            
            # Handle optional region column
            if region_col and region_col in df.columns:
                df['region_code'] = df[region_col].fillna(default_region)
            else:
                df['region_code'] = default_region
                self.logger.info(f"Using default region: {default_region}")
            
            # Concatenate address fields
            self.logger.info("Concatenating address fields...")
            df['full_address'] = df.apply(lambda row: concatenate_address_fields(
                row[address_col], row[city_col], row[state_col], row[zip_col]
            ), axis=1)
            
            # Initialize validation result columns
            df['is_valid'] = None
            df['validation_confidence'] = None
            df['formatted_address'] = None
            df['validation_errors'] = None
            df['api_response'] = None
            
            # Process addresses in batches
            total_addresses = len(df)
            processed = 0
            
            for i in range(0, total_addresses, batch_size):
                batch_end = min(i + batch_size, total_addresses)
                self.logger.info(f"Processing batch {i//batch_size + 1}: rows {i+1} to {batch_end}")
                
                for idx in range(i, batch_end):
                    address = df.loc[idx, 'full_address']
                    region = df.loc[idx, 'region_code']
                    
                    if pd.isna(address) or address.strip() == '':
                        df.loc[idx, 'validation_errors'] = 'Empty address'
                        processed += 1
                        continue
                    
                    # Call validation API
                    try:
                        result = self.validate_single_address(address=address, region=region)
                        df.loc[idx, 'api_response'] = str(result)
                        
                        # Parse validation results
                        validation_info = parse_validation_result(result)
                        df.loc[idx, 'is_valid'] = validation_info['is_valid']
                        df.loc[idx, 'validation_confidence'] = validation_info['confidence']
                        df.loc[idx, 'formatted_address'] = validation_info['formatted_address']
                        df.loc[idx, 'validation_errors'] = validation_info['errors']
                        
                    except Exception as e:
                        self.logger.error(f"Error validating address at row {idx+1}: {e}")
                        df.loc[idx, 'validation_errors'] = str(e)
                    
                    processed += 1
                    
                    # Rate limiting delay
                    if delay_seconds > 0:
                        time.sleep(delay_seconds)
                    
                    # Progress update
                    if processed % 50 == 0:
                        self.logger.info(f"Progress: {processed}/{total_addresses} addresses processed")
                
                # Save intermediate results
                if output_file:
                    df.to_csv(f"{output_file}_temp.csv", index=False)
                    self.logger.info(f"Saved intermediate results to {output_file}_temp.csv")
            
            # Final statistics
            valid_count = df['is_valid'].sum()
            invalid_count = len(df) - valid_count
            self.logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid addresses")
            
            # Save final results
            if output_file:
                df.to_csv(output_file, index=False)
                self.logger.info(f"Final results saved to {output_file}")
                
                # Clean up temp file
                temp_file = f"{output_file}_temp.csv"
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}")
            raise

# Convenience function for direct usage
def validate_csv_addresses(
    csv_file_path: str,
    address_col: str = "Address",
    city_col: str = "City", 
    state_col: str = "State",
    zip_col: str = "Zip",
    region_col: Optional[str] = None,
    default_region: str = "US",
    batch_size: int = 100,
    delay_seconds: float = 0.1,
    output_file: Optional[str] = None,
    config: Optional[Config] = None
) -> pd.DataFrame:
    """
    Convenience function to validate addresses from CSV.
    
    Creates an AddressValidator instance and processes the CSV file.
    """
    validator = AddressValidator(config=config)
    return validator.validate_csv_addresses(
        csv_file_path=csv_file_path,
        address_col=address_col,
        city_col=city_col,
        state_col=state_col,
        zip_col=zip_col,
        region_col=region_col,
        default_region=default_region,
        batch_size=batch_size,
        delay_seconds=delay_seconds,
        output_file=output_file
    )
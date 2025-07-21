"""
Address validation functionality using Google's Address Validation API with signed URL support.
Supports both single address column and component column formats.
"""

import pandas as pd
import requests
import time
import hashlib
import hmac
import base64
import urllib.parse
import re
from typing import Dict, Optional, List, Union
import logging
import os
from concurrent.futures import ThreadPoolExecutor
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
    """Main class for address validation operations using Google's Address Validation API with signed URL support."""
    
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
        
        # Validate configuration - need either API key OR client credentials for signed URLs
        if not self.config.google_api_key and not (self.config.google_client_id and self.config.google_private_key):
            raise ConfigurationError(
                "Either Google API key OR client ID and private key are required. "
                "Set GOOGLE_API_KEY or (GOOGLE_CLIENT_ID and GOOGLE_PRIVATE_KEY) environment variables."
            )
        
        # Determine if we should use signed URLs
        self.use_signed_urls = bool(self.config.google_client_id and self.config.google_private_key)
        
        if self.use_signed_urls:
            self.logger.info("Using signed URL authentication for enterprise usage")
        else:
            self.logger.info("Using API key authentication")
    
    def sign_url(self, url: str, private_key: str) -> str:
        """
        Sign a URL for Google Maps API enterprise usage.
        
        Parameters
        ----------
        url : str
            The URL to sign
        private_key : str
            The private key for signing
            
        Returns
        -------
        str
            The signed URL
        """
        parsed_url = urllib.parse.urlparse(url)
        url_to_sign = parsed_url.path + "?" + parsed_url.query
        decoded_key = base64.urlsafe_b64decode(private_key)
        signature = hmac.new(decoded_key, url_to_sign.encode(), hashlib.sha1)
        encoded_signature = base64.urlsafe_b64encode(signature.digest()).decode("utf-8")
        return f"{url}&signature={encoded_signature}"
    
    def build_validation_url(self, address: str, region: str) -> str:
        """
        Build the validation URL with appropriate authentication.
        
        Parameters
        ----------
        address : str
            Address to validate
        region : str
            Region code
            
        Returns
        -------
        str
            Complete URL for validation request
        """
        if self.use_signed_urls:
            # Build URL with client ID for signed URL authentication
            query_params = {
                "client": self.config.google_client_id,
                "channel": getattr(self.config, 'channel', 'address_validator')
            }
            query_string = urllib.parse.urlencode(query_params)
            url = f"{self.config.validation_base_url}?{query_string}"
            return self.sign_url(url, self.config.google_private_key)
        else:
            # Build URL with API key
            return f'{self.config.validation_base_url}?key={self.config.google_api_key}'
    
    @rate_limit
    def validate_single_address(self, address: str, region: str = None) -> Dict:
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
        
        url = self.build_validation_url(address, region)
        payload = {
            "address": {
                "addressLines": [address], 
                "regionCode": region
            }
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(url, json=payload, timeout=self.config.timeout)
                
                # Handle rate limiting
                retry_count = 0
                max_retries = 3
                while retry_count < max_retries and response.status_code == 429:
                    retry_count += 1
                    sleep_time = 2 ** retry_count
                    self.logger.warning(f"Rate limited, retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    response = requests.post(url, json=payload, timeout=self.config.timeout)
                
                if response.status_code != 200:
                    self.logger.error(f"HTTP Error {response.status_code}: {response.text}")
                    return {
                        "error": f"HTTP Error: {response.status_code}",
                        "address": address,
                        "status": f"HTTP_{response.status_code}"
                    }
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise ValidationAPIError(f"API request failed after {self.config.max_retries} retries: {e}")
                
                self.logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                time.sleep(self.config.delay_seconds * (attempt + 1))
        
        return {"error": f"Failed after {self.config.max_retries} retries", "address": address}
    
    def _detect_single_address_format(self, df_sample: pd.DataFrame, suggestions: Dict) -> bool:
        """
        Detect if CSV has addresses in a single column format.
        
        Parameters
        ----------
        df_sample : pd.DataFrame
            Sample of the CSV data
        suggestions : Dict
            Column suggestions from pattern matching
            
        Returns
        -------
        bool
            True if this appears to be single-address format
        """
        # Check if we have a full address column suggestion
        if suggestions.get('full_address'):
            return True
        
        # Check if we have only 1-2 columns and no separate address components
        if len(df_sample.columns) <= 2:
            has_separate_components = any([
                suggestions.get('address'),
                suggestions.get('city'), 
                suggestions.get('state'),
                suggestions.get('zip')
            ])
            return not has_separate_components
        
        # Check if we have few columns and they don't look like separate address components
        if len(df_sample.columns) <= 3:
            component_count = sum([
                len(suggestions.get('address', [])),
                len(suggestions.get('city', [])),
                len(suggestions.get('state', [])),
                len(suggestions.get('zip', []))
            ])
            return component_count < 2
        
        return False
    
    def inspect_csv_columns(self, csv_file_path: str) -> Dict[str, any]:
        """
        Inspect CSV file and suggest address column mappings.
        
        Parameters
        ----------
        csv_file_path : str
            Path to CSV file
            
        Returns
        -------
        Dict[str, any]
            Dictionary with column information and suggestions
        """
        try:
            # Read just the first few rows to inspect columns
            df_sample = pd.read_csv(csv_file_path, nrows=5)
            columns = list(df_sample.columns)
            
            # Common patterns for address fields
            address_patterns = {
                'full_address': [
                    r'.*full.*address.*', r'.*address.*full.*', r'.*complete.*address.*',
                    r'.*addr.*full.*', r'.*full.*addr.*', r'.*address_full.*',
                    r'.*full_address.*', r'.*address_complete.*'
                ],
                'address': [
                    r'.*address.*', r'.*street.*', r'.*addr.*', r'.*line.*1.*',
                    r'.*location.*', r'.*premise.*'
                ],
                'city': [
                    r'.*city.*', r'.*town.*', r'.*municipality.*', r'.*locality.*'
                ],
                'state': [
                    r'.*state.*', r'.*province.*', r'.*region.*', r'.*prov.*',
                    r'.*st$', r'.*state_code.*'
                ],
                'zip': [
                    r'.*zip.*', r'.*postal.*', r'.*post.*code.*', r'.*zipcode.*',
                    r'.*postcode.*', r'.*zip_code.*'
                ],
                'country': [
                    r'.*country.*', r'.*nation.*', r'.*ctry.*'
                ]
            }
            
            suggestions = {}
            for field_type, patterns in address_patterns.items():
                matches = []
                for col in columns:
                    for pattern in patterns:
                        if re.match(pattern, col.lower()):
                            matches.append(col)
                            break
                suggestions[field_type] = matches
            
            # Show sample data for first few columns
            sample_data = {}
            for col in columns[:10]:  # Show first 10 columns
                sample_data[col] = df_sample[col].dropna().head(3).tolist()
            
            # Check if this looks like a single-column address file
            is_single_address_format = self._detect_single_address_format(df_sample, suggestions)
            
            return {
                'total_rows': len(pd.read_csv(csv_file_path)),
                'columns': columns,
                'suggestions': suggestions,
                'sample_data': sample_data,
                'file_path': csv_file_path,
                'is_single_address_format': is_single_address_format
            }
            
        except Exception as e:
            self.logger.error(f"Error inspecting CSV file: {e}")
            raise CSVError(f"Cannot inspect CSV file: {e}")
    
    def print_column_inspection(self, csv_file_path: str) -> None:
        """
        Print a user-friendly column inspection report.
        
        Parameters
        ----------
        csv_file_path : str
            Path to CSV file
        """
        inspection = self.inspect_csv_columns(csv_file_path)
        
        print(f"\n{'='*60}")
        print(f"CSV COLUMN INSPECTION: {os.path.basename(csv_file_path)}")
        print(f"{'='*60}")
        print(f"Total rows: {inspection['total_rows']:,}")
        print(f"Total columns: {len(inspection['columns'])}")
        
        # Check if this is single address format
        if inspection.get('is_single_address_format'):
            print(f"\n🎯 DETECTED: Single Address Column Format")
            full_addr_col = inspection['suggestions'].get('full_address')
            if full_addr_col:
                print(f"   Suggested full address column: {full_addr_col[0]}")
            else:
                # Find the most likely single address column
                likely_col = inspection['columns'][0]  # Default to first column
                print(f"   Likely address column: {likely_col}")
        
        print(f"\n📋 AVAILABLE COLUMNS:")
        for i, col in enumerate(inspection['columns'], 1):
            sample = inspection['sample_data'].get(col, [])
            sample_str = str(sample[:2])[1:-1] if sample else "No data"
            print(f"  {i:2d}. {col:<30} | Sample: {sample_str}")
        
        print(f"\n🎯 SUGGESTED MAPPINGS:")
        
        # Show single address format suggestion first
        if inspection.get('is_single_address_format'):
            full_addr_suggestions = inspection['suggestions'].get('full_address', [])
            if full_addr_suggestions:
                print(f"  FULL_ADDRESS: {full_addr_suggestions}")
            else:
                print(f"  FULL_ADDRESS: Consider using '{inspection['columns'][0]}'")
        
        # Show component mappings
        for field_type, matches in inspection['suggestions'].items():
            if field_type != 'full_address' and matches:
                print(f"  {field_type.upper():<8}: {matches}")
            elif field_type != 'full_address':
                print(f"  {field_type.upper():<8}: ❌ No suggestions found")
        
        print(f"\n💡 USAGE EXAMPLES:")
        
        # Single address format example
        if inspection.get('is_single_address_format'):
            full_addr_col = inspection['suggestions'].get('full_address')
            addr_col = full_addr_col[0] if full_addr_col else inspection['columns'][0]
            
            print(f"📍 Single Address Column Format:")
            print(f"validator.validate_csv_addresses(")
            print(f"    csv_file_path=r'{csv_file_path}',")
            print(f"    full_address_col='{addr_col}',")
            print(f"    output_file='validated_addresses.csv'")
            print(f")")
        
        # Component format example
        suggested_mapping = {}
        for field_type, matches in inspection['suggestions'].items():
            if field_type != 'full_address' and matches:
                suggested_mapping[f"{field_type}_col"] = matches[0]
        
        if suggested_mapping:
            print(f"\n📍 Component Address Format:")
            params = []
            for param, value in suggested_mapping.items():
                params.append(f'{param}="{value}"')
            
            print(f"validator.validate_csv_addresses(")
            print(f"    csv_file_path=r'{csv_file_path}',")
            for param in params:
                print(f"    {param},")
            print(f"    output_file='validated_addresses.csv'")
            print(f")")
        
        if not inspection.get('is_single_address_format') and not suggested_mapping:
            print("❌ Could not automatically detect address columns.")
            print("Please specify column names manually:")
            print("validator.validate_csv_addresses(")
            print("    csv_file_path=r'your_file.csv',")
            print("    full_address_col='YourFullAddressColumn',  # OR")
            print("    address_col='YourAddressColumn',")
            print("    city_col='YourCityColumn',")
            print("    state_col='YourStateColumn',")
            print("    zip_col='YourZipColumn'")
            print(")")
        
        print(f"{'='*60}\n")
    
    def auto_detect_columns(self, csv_file_path: str) -> Dict[str, Optional[str]]:
        """
        Automatically detect address columns in CSV.
        
        Parameters
        ----------
        csv_file_path : str
            Path to CSV file
            
        Returns
        -------
        Dict[str, Optional[str]]
            Dictionary mapping field types to column names
        """
        inspection = self.inspect_csv_columns(csv_file_path)
        
        mapping = {}
        for field_type, matches in inspection['suggestions'].items():
            if matches:
                mapping[f"{field_type}_col"] = matches[0]  # Take first match
            else:
                mapping[f"{field_type}_col"] = None
        
        return mapping
    
    def validate_columns_or_suggest(
        self, 
        csv_file_path: str,
        full_address_col: Optional[str] = None,
        address_col: Optional[str] = None,
        city_col: Optional[str] = None,
        state_col: Optional[str] = None,
        zip_col: Optional[str] = None,
        auto_detect: bool = True,
        show_suggestions: bool = True
    ) -> Dict[str, str]:
        """
        Validate column names or provide suggestions.
        
        Parameters
        ----------
        csv_file_path : str
            Path to CSV file
        full_address_col : str, optional
            Column name for complete address (alternative to component columns)
        address_col, city_col, state_col, zip_col : str, optional
            Column names for address components
        auto_detect : bool
            Whether to auto-detect columns
        show_suggestions : bool
            Whether to print suggestions
            
        Returns
        -------
        Dict[str, str]
            Validated column mapping
            
        Raises
        ------
        CSVError
            If required columns cannot be found or validated
        """
        df = pd.read_csv(csv_file_path, nrows=1)  # Just read headers
        available_columns = list(df.columns)
        
        # If no columns specified, try auto-detection
        if not any([full_address_col, address_col, city_col, state_col, zip_col]) and auto_detect:
            if show_suggestions:
                print("🔍 No column names specified. Attempting auto-detection...")
            
            inspection = self.inspect_csv_columns(csv_file_path)
            
            # Check if this is single address format
            if inspection.get('is_single_address_format'):
                auto_full_addr = inspection['suggestions'].get('full_address')
                if auto_full_addr:
                    full_address_col = auto_full_addr[0]
                else:
                    # Use first column as likely address column
                    full_address_col = available_columns[0]
                
                if show_suggestions:
                    print(f"✅ Detected single address format:")
                    print(f"   Full Address: {full_address_col}")
                
                return {'mode': 'single_address', 'full_address_col': full_address_col}
            else:
                # Try component detection
                auto_mapping = self.auto_detect_columns(csv_file_path)
                address_col = auto_mapping.get('address_col')
                city_col = auto_mapping.get('city_col')
                state_col = auto_mapping.get('state_col')
                zip_col = auto_mapping.get('zip_col')
                
                if show_suggestions:
                    print(f"✅ Auto-detected component columns:")
                    print(f"   Address: {address_col}")
                    print(f"   City: {city_col}")
                    print(f"   State: {state_col}")
                    print(f"   ZIP: {zip_col}")
        
        # If we have a full address column specified or detected
        if full_address_col:
            if full_address_col in available_columns:
                return {'mode': 'single_address', 'full_address_col': full_address_col}
            else:
                if show_suggestions:
                    print(f"\n❌ Specified full address column '{full_address_col}' not found")
                    print(f"📋 Available columns: {available_columns}")
                
                raise CSVError(
                    f"Full address column '{full_address_col}' not found. "
                    f"Available columns: {available_columns}"
                )
        
        # Use config defaults if still not specified (for component mode)
        address_col = address_col or self.config.address_col
        city_col = city_col or self.config.city_col
        state_col = state_col or self.config.state_col
        zip_col = zip_col or self.config.zip_col
        
        # Check which component columns exist
        specified_cols = {
            'Address': address_col,
            'City': city_col,
            'State': state_col,
            'ZIP': zip_col
        }
        
        missing_cols = []
        existing_cols = {}
        
        for field_name, col_name in specified_cols.items():
            if col_name and col_name in available_columns:
                existing_cols[field_name.lower() + '_col'] = col_name
            else:
                missing_cols.append(f"{field_name} (specified: '{col_name}')")
        
        # If we have missing columns, provide helpful error with suggestions
        if missing_cols:
            if show_suggestions:
                print(f"\n❌ Missing or invalid columns: {missing_cols}")
                print(f"\n📋 Available columns in your CSV:")
                for i, col in enumerate(available_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                print(f"\n🔍 Run this to see detailed column analysis:")
                print(f"validator.print_column_inspection(r'{csv_file_path}')")
                print(f"\n💡 Specify columns manually:")
                print(f"# For single address column:")
                print(f"validator.validate_csv_addresses(")
                print(f"    csv_file_path=r'{csv_file_path}',")
                print(f"    full_address_col='YourAddressColumn'")
                print(f")")
                print(f"# For component columns:")
                print(f"validator.validate_csv_addresses(")
                print(f"    csv_file_path=r'{csv_file_path}',")
                print(f"    address_col='YourAddressColumn',")
                print(f"    city_col='YourCityColumn',")
                print(f"    state_col='YourStateColumn',")
                print(f"    zip_col='YourZipColumn'")
                print(f")")
            
            raise CSVError(
                f"Missing required columns: {missing_cols}. "
                f"Available columns: {available_columns}. "
                f"Use validator.print_column_inspection('{csv_file_path}') for suggestions."
            )
        
        existing_cols['mode'] = 'components'
        return existing_cols
    
    def validate_csv_addresses(
        self,
        csv_file_path: str,
        full_address_col: Optional[str] = None,
        address_col: Optional[str] = None,
        city_col: Optional[str] = None, 
        state_col: Optional[str] = None,
        zip_col: Optional[str] = None,
        region_col: Optional[str] = None,
        default_region: Optional[str] = None,
        batch_size: Optional[int] = None,
        delay_seconds: Optional[float] = None,
        output_file: Optional[str] = None,
        auto_detect: bool = True,
        show_suggestions: bool = True
    ) -> pd.DataFrame:
        """
        Validate addresses from CSV with intelligent column detection.
        Supports both single address column and component column formats.
        
        Parameters
        ----------
        csv_file_path : str
            Path to CSV file containing addresses
        full_address_col : str, optional
            Column name for complete address (e.g., "123 Main St, Boston, MA 02101")
        address_col, city_col, state_col, zip_col : str, optional
            Column names for address components. Used if full_address_col not provided.
        region_col : str, optional
            Column name for region codes
        default_region : str, optional
            Default region code if region_col not provided
        batch_size : int, optional
            Batch size for processing
        delay_seconds : float, optional
            Delay between API calls
        output_file : str, optional
            Output file path
        auto_detect : bool, optional
            Whether to attempt automatic column detection (default: True)
        show_suggestions : bool, optional
            Whether to show column suggestions and help (default: True)
            
        Returns
        -------
        pd.DataFrame
            DataFrame with validation results
            
        Examples
        --------
        # Single address column (like your Test_set.csv)
        results = validator.validate_csv_addresses(
            'test_set.csv',
            full_address_col='FULL_Address'
        )
        
        # Auto-detect single address column
        results = validator.validate_csv_addresses('test_set.csv')
        
        # Component columns
        results = validator.validate_csv_addresses(
            'addresses.csv',
            address_col='Street_Address',
            city_col='City_Name',
            state_col='State_Code',
            zip_col='Postal_Code'
        )
        """
        try:
            # Validate and detect columns
            column_mapping = self.validate_columns_or_suggest(
                csv_file_path=csv_file_path,
                full_address_col=full_address_col,
                address_col=address_col,
                city_col=city_col,
                state_col=state_col,
                zip_col=zip_col,
                auto_detect=auto_detect,
                show_suggestions=show_suggestions
            )
            
            # Check if we're in single address mode or component mode
            is_single_address = column_mapping.get('mode') == 'single_address'
            
            if is_single_address:
                full_address_col = column_mapping['full_address_col']
                if show_suggestions:
                    print(f"✅ Using single address column: '{full_address_col}'")
            else:
                # Extract validated column names for components
                address_col = column_mapping['address_col']
                city_col = column_mapping['city_col']
                state_col = column_mapping['state_col']
                zip_col = column_mapping['zip_col']
                if show_suggestions:
                    print(f"✅ Using component columns: Address='{address_col}', City='{city_col}', State='{state_col}', ZIP='{zip_col}'")
            
            # Use config defaults for other parameters
            region_col = region_col or self.config.region_col
            default_region = default_region or self.config.default_region
            batch_size = batch_size or self.config.batch_size
            delay_seconds = delay_seconds if delay_seconds is not None else self.config.delay_seconds
            
            # Load and process CSV
            self.logger.info(f"Loading CSV file: {csv_file_path}")
            df = pd.read_csv(csv_file_path)
            self.logger.info(f"Loaded {len(df)} rows")
            
            # Handle optional region column
            if region_col and region_col in df.columns:
                df['region_code'] = df[region_col].fillna(default_region)
            else:
                df['region_code'] = default_region
                self.logger.info(f"Using default region: {default_region}")
            
            # Create or use full address
            if is_single_address:
                # Use existing full address column
                df['full_address'] = df[full_address_col].astype(str)
                self.logger.info(f"Using existing full address column: {full_address_col}")
            else:
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
                    
                    if pd.isna(address) or address.strip() == '' or address.strip() == 'nan':
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
            if "Missing required columns" in str(e):
                # Re-raise CSVError with helpful message
                raise
            else:
                self.logger.error(f"Error processing CSV: {e}")
                raise


def validate_csv_addresses(
    csv_file_path: str,
    full_address_col: str = None,  # NEW: Support for single address column
    address_col: str = None,
    city_col: str = None,
    state_col: str = None,
    zip_col: str = None,
    region_col: Optional[str] = None,
    default_region: str = "US",
    batch_size: int = 100,
    delay_seconds: float = 0.1,
    output_file: Optional[str] = None,
    config: Optional[Config] = None,
    auto_detect: bool = True,
    show_suggestions: bool = True
) -> pd.DataFrame:
    """
    Convenience function to validate addresses from CSV with intelligent column detection.
    Supports both single address column and component column formats.
    
    Parameters
    ----------
    csv_file_path : str
        Path to CSV file
    full_address_col : str, optional
        Column name for complete address (alternative to component columns)
    address_col, city_col, state_col, zip_col : str, optional
        Column names for address components. If None, will attempt auto-detection.
    auto_detect : bool
        Whether to attempt automatic column detection (default: True)
    show_suggestions : bool
        Whether to show helpful suggestions (default: True)
    
    Examples
    --------
    # Single address column (like Test_set.csv with FULL_Address column)
    results = validate_csv_addresses(
        'test_set.csv',
        full_address_col='FULL_Address'
    )
    
    # Auto-detect single address column
    results = validate_csv_addresses('test_set.csv')
    
    # Component columns
    results = validate_csv_addresses(
        'addresses.csv',
        address_col='Street_Address',
        city_col='City_Name',
        state_col='State_Code',
        zip_col='Postal_Code'
    )
    
    # Inspect columns first
    validator = AddressValidator()
    validator.print_column_inspection('test_set.csv')
    """
    validator = AddressValidator(config=config)
    return validator.validate_csv_addresses(
        csv_file_path=csv_file_path,
        full_address_col=full_address_col,
        address_col=address_col,
        city_col=city_col,
        state_col=state_col,
        zip_col=zip_col,
        region_col=region_col,
        default_region=default_region,
        batch_size=batch_size,
        delay_seconds=delay_seconds,
        output_file=output_file,
        auto_detect=auto_detect,
        show_suggestions=show_suggestions
    )


def inspect_csv_columns(csv_file_path: str) -> None:
    """
    Convenience function to inspect CSV columns.
    
    Parameters
    ----------
    csv_file_path : str
        Path to CSV file
        
    Examples
    --------
    # Inspect any CSV file
    inspect_csv_columns('test_set.csv')
    inspect_csv_columns('addresses.csv')
    """
    validator = AddressValidator()
    validator.print_column_inspection(csv_file_path)
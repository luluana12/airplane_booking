import os
import sys
import logging
from typing import List, Dict, Optional
import requests
import json
import pandas as pd
from dotenv import load_dotenv
from functools import lru_cache
from datetime import datetime, timedelta
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('amadeus_offers.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AmadeusOfferFinder:
    def __init__(self, airports_data_path: str):
        """
        Initialize the Amadeus Offer Finder with configuration and data loading
        
        :param airports_data_path: Path to the airports data file
        """
        # Load environment variables
        load_dotenv(r'C:\Users\alexa\Python Projects\Offer Website\API.env')
        
        # Validate configuration
        self._validate_config()
        
        # Load airports data
        self.airports_df = self._load_airports_data(airports_data_path)
        
        # Initialize caching for API responses
        self.offer_cache = {}
        
        # Authenticate and get access token
        self.access_token = self._get_access_token()

    def _validate_config(self):
        """
        Validate required environment variables
        """
        required_vars = ['AMADEUS_CLIENT_ID', 'AMADEUS_CLIENT_SECRET']
        for var in required_vars:
            if not os.getenv(var):
                logger.error(f"Missing required environment variable: {var}")
                raise ValueError(f"Please set the {var} environment variable")

    def _load_airports_data(self, data_path: str) -> pd.DataFrame:
        """
        Load and preprocess airports data
        
        :param data_path: Path to airports data file
        :return: Processed DataFrame with airport information
        """
        try:
            columns = ["id", "name", "city", "country", "iata_code", "icao_code", 
                       "latitude", "longitude", "altitude", "timezone_offset", 
                       "DST", "timezone_name", "type", "source"]
            df = pd.read_csv(data_path, names=columns, delimiter=',')
            
            # Validate DataFrame
            required_columns = ['city', 'iata_code', 'name']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("Missing required columns in airports data")
            
            return df[required_columns].dropna()
        
        except FileNotFoundError:
            logger.error(f"Airports data file not found at {data_path}")
            raise
        except pd.errors.EmptyDataError:
            logger.error("The airports data file is empty")
            raise
        except Exception as e:
            logger.error(f"Error loading airports data: {e}")
            raise

    def _get_access_token(self) -> str:
        """
        Retrieve access token from Amadeus API
        
        :return: Access token string
        """
        url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
        data = {
            'grant_type': 'client_credentials',
            'client_id': os.getenv('AMADEUS_CLIENT_ID'),
            'client_secret': os.getenv('AMADEUS_CLIENT_SECRET')
        }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token = response.json().get('access_token')
            logger.info("Successfully obtained access token")
            return token
        except requests.RequestException as e:
            logger.error(f"Token retrieval failed: {e}")
            raise RuntimeError("Unable to obtain access token")

    @lru_cache(maxsize=128)
    def get_iata_codes_by_city(self, city_name: str) -> List[str]:
        """
        Find IATA codes for a given city
        
        :param city_name: Name of the city
        :return: List of IATA codes
        """
        try:
            codes = self.airports_df[
                self.airports_df['city'].str.lower() == city_name.lower()
            ]['iata_code'].dropna().unique()
            
            return list(codes) if len(codes) > 0 else []
        except Exception as e:
            logger.error(f"Error finding IATA codes for {city_name}: {e}")
            return []

    @lru_cache(maxsize=128)
    def get_iata_codes_by_name(self, airport_name: str) -> List[str]:
        """
        Find IATA codes for a given airport name
        
        :param airport_name: Name of the airport
        :return: List of IATA codes
        """
        try:
            codes = self.airports_df[
                self.airports_df['name'].str.lower() == airport_name.lower()
            ]['iata_code'].dropna().unique()
            
            return list(codes) if len(codes) > 0 else []
        except Exception as e:
            logger.error(f"Error finding IATA codes for {airport_name}: {e}")
            return []

    def get_airport_name_by_iata(self, iata_code: str) -> str:
        """
        Get airport name for a given IATA code
        
        :param iata_code: IATA airport code
        :return: Airport name
        """
        try:
            name = self.airports_df[
                self.airports_df['iata_code'].str.upper() == iata_code.upper()
            ]['name'].iloc[0] if not self.airports_df[
                self.airports_df['iata_code'].str.upper() == iata_code.upper()
            ].empty else "IATA code not found"
            return name
        except Exception as e:
            logger.error(f"Error finding airport name for {iata_code}: {e}")
            return "IATA code not found"

    def fetch_flight_offers(self, origin: str, max_price: float) -> List[Dict]:
        destination_url = 'https://test.api.amadeus.com/v1/shopping/flight-destinations'
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'origin': origin,
            'maxPrice': max_price
        }

        try:
            # Add more detailed logging
            #logger.info(f"API Request - URL: {destination_url}")
            #logger.info(f"Headers: {headers}")
            #logger.info(f"Params: {params}")

            response = requests.get(destination_url, headers=headers, params=params)
        
            # Log the full response
            #logger.info(f"Response Status Code: {response.status_code}")
            #logger.info(f"Response Content: {response.text}")

            response.raise_for_status()
        
            offers = response.json().get('data', [])
        
            return offers
    
        except requests.RequestException as e:
            logger.error(f"Error fetching flight offers: {e}")
            logger.error(f"Full Error Response: {response.text if 'response' in locals() else 'No response'}")
            return []

    def display_offers(self, offers: List[Dict]):
        """
        Display flight offers in a formatted manner
        
        :param offers: List of flight offers
        """
        if not offers:
            print("No flight offers found.")
            return

        print("\n===== Available Flight Offers =====")
        for offer in offers:
            destination = offer.get('destination', 'N/A')
            price = offer.get('price', {}).get('total', 'N/A')
            departure_date = offer.get('departureDate', 'N/A')
            return_date = offer.get('returnDate', 'N/A')
            airport_name = self.get_airport_name_by_iata(destination)

            print(f"Destination: {destination} ({airport_name})")
            print(f"Price: ${price}")
            print(f"Departure Date: {departure_date}")
            print(f"Return Date: {return_date}")
            print("-----------------------------------")

def main():
    """
    Streamlit main function to orchestrate the flight offer search process
    """
    # Set page configuration
    st.set_page_config(page_title="Flight Offer Finder", page_icon="✈️", layout="wide")
    
    # Title and description
    st.title("✈️ Flight Offer Finder")
    st.markdown("Search for affordable flight offers based on your preferences.")
    
    # Sidebar for configuration
    st.sidebar.header("Search Parameters")
    
    # Path to airports data (consider making this configurable or using a relative path)
    data_path = "C:/Users/alexa/Python Projects/OfferFligthApp/airports.dat"
    
    # Initialize offer finder
    try:
        offer_finder = AmadeusOfferFinder(data_path)
    except Exception as e:
        st.error(f"Error initializing offer finder: {e}")
        return
    
    # Search type selection
    search_type = st.sidebar.radio("Select Search Type", ["City", "Airport"])
    
    # Max price input
    max_price = st.sidebar.number_input(
        "Max Price ($)", 
        min_value=0, 
        max_value=10000, 
        value=500, 
        step=50
    )
    iata_codes = []
    # Input based on search type
    if search_type == "City":
        city_name = st.sidebar.text_input("Enter Origin City Name")
        if city_name:
            # Get IATA codes for the city
            try:
                iata_codes = offer_finder.get_iata_codes_by_city(city_name)
            except Exception as e:
                st.error(f"Error finding IATA codes: {e}")
                iata_codes = []
    else:
        airport_name = st.sidebar.text_input("Enter Airport Name")
        if airport_name:
            # Get IATA codes for the airport
            try:
                iata_codes = offer_finder.get_iata_codes_by_name(airport_name)
            except Exception as e:
                st.error(f"Error finding IATA codes: {e}")
                iata_codes = []
    
    # Display available airports if codes are found
    if iata_codes:
        # Create a dictionary of airport details for selection
        airport_dict = {
            code: f"{code}: {offer_finder.get_airport_name_by_iata(code)}" 
            for code in iata_codes
        }
        
        # Airport selection
        selected_origin = st.sidebar.selectbox(
            "Select Origin Airport", 
            list(airport_dict.keys()),
            format_func=lambda x: airport_dict[x]
        )
        
        # Search button
        if st.sidebar.button("Search Flight Offers"):
            try:
                # Fetch flight offers
                offers = offer_finder.fetch_flight_offers(selected_origin, max_price)
                
                # Display offers
                if offers:
                    st.success(f"Found {len(offers)} flight offers!")
                    
                    # Create a DataFrame for nice display
                    import pandas as pd
                    offers_df = pd.DataFrame(offers)
                    
                    # Display offers in a table
                    st.dataframe(offers_df, use_container_width=True)
                else:
                    st.warning("No flight offers found matching your criteria.")
            
            except Exception as e:
                st.error(f"Error fetching flight offers: {e}")
                logger.error(f"Unexpected error: {e}")
    else:
        st.warning("Please enter a valid city or airport name to search.")
        
if __name__ == "__main__": 
    main()
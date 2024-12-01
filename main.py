import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import re  # Importing regex for parsing duration

# Amadeus API credentials
API_KEY = "aUs48EbXKLtjpIKVPLvLYS7TOxejCmIh"
API_SECRET = "kAzHTVjUd2X3mamn"

# Amadeus OAuth2 token URL
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
# Amadeus flight offers search URL
FLIGHTS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# Function to get an access token
def get_access_token():
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": API_KEY,
            "client_secret": API_SECRET
        }
    )
    if response.status_code != 200:
        st.error(f"Failed to get access token: {response.status_code} - {response.text}")
        return None
    return response.json().get("access_token")

# Function to format duration from ISO 8601 to a more readable format
def format_duration(duration):
    match = re.match(r'PT(\d+H)?(\d+M)?', duration)
    hours = match.group(1)[:-1] if match.group(1) else '0'
    minutes = match.group(2)[:-1] if match.group(2) else '0'
    return f"{hours}h {minutes}m"

# Function to search for flights
def search_flights(origin, destination, departure_date):
    token = get_access_token()
    if not token:
        return None
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date.strftime('%Y-%m-%d'),
        "adults": 1
    }
    response = requests.get(FLIGHTS_URL, headers=headers, params=params)
    return response.json()

# Initialize session state variables
if 'selected_flight' not in st.session_state:
    st.session_state['selected_flight'] = {}

if "selected_flight_id" not in st.session_state:
    st.session_state["selected_flight_id"] = {}

if "flight_data" not in st.session_state:
    st.session_state["flight_data"] = {}

# Streamlit UI
st.title("Flight Reservation System with Amadeus API")

# User inputs for origin and destination
location = st.text_input("Enter your origin location (IATA code)")
destination = st.text_input("Enter your destination (IATA code)")
departure_date = st.date_input("Select departure date", min_value=datetime.today())

# Add a "Search Flights" button to initiate the search
if st.button("Search Flights"):
    if location and destination and departure_date:
        st.header("Available Flights")

        flights_data = search_flights(location, destination, departure_date)
        st.session_state["flight_data"] = flights_data

# Process and display flights only if search results exist
if st.session_state["flight_data"]:
    flights_data = st.session_state["flight_data"]

    if flights_data and "data" in flights_data:
        flight_offers = flights_data["data"]
        flight_list = []
        for offer in flight_offers:
            segments = offer["itineraries"][0]["segments"]
            if segments[0]['departure']['iataCode'] == location and segments[-1]['arrival']['iataCode'] == destination:
                flight_info = {
                    'Flight ID': offer['id'],
                    'Departure': segments[0]['departure']['iataCode'],
                    'Arrival': segments[-1]['arrival']['iataCode'],
                    'Departure Time': segments[0]['departure']['at'],
                    'Arrival Time': segments[-1]['arrival']['at'],
                    'Duration': format_duration(offer['itineraries'][0]['duration']),
                    'Carrier': segments[0]['carrierCode'],
                    'Price': offer['price']['total']
                }
                flight_list.append(flight_info)

        if flight_list:
            flight_df = pd.DataFrame(flight_list)
            st.write(flight_df)

            # Flight selection with session state
            flight_ids = flight_df['Flight ID'].unique()
            selected_flight = st.selectbox(
                "Select your flight by Flight ID",
                flight_ids,
                index=flight_ids.tolist().index(st.session_state["selected_flight_id"]) if st.session_state["selected_flight_id"] in flight_ids else 0,
                key="flight_selection"
            )

            # Store the selected flight ID in session state
            st.session_state["selected_flight_id"] = selected_flight

            if selected_flight:
                st.session_state['selected_flight'] = selected_flight

                # Reservation system
                st.header("Reservation")
                passenger_name = st.text_input("Enter Passenger Name")
                seat_preference = st.selectbox("Select Seat Preference", ["Aisle", "Window", "Middle"])

                if st.button("Confirm Reservation"):
                    st.success(f"Reservation confirmed for {passenger_name}. Seat preference: {seat_preference}.")
        else:
            st.error("No flights found for the specified route.")
    else:
        st.error("No flights found.")


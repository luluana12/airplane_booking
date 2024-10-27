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

# Streamlit UI
st.title("Flight Reservation System with Amadeus API")

# User inputs for origin and destination
location = st.text_input("Enter your origin location (IATA code)")
destination = st.text_input("Enter your destination (IATA code)")
departure_date = st.date_input("Select departure date", min_value=datetime.today())

# Search for flights if location, destination, and date are provided
if location and destination and departure_date:
    st.header("Available Flights")

    flights_data = search_flights(location, destination, departure_date)

    # Process and display flights data
    if flights_data and "data" in flights_data:
        flight_offers = flights_data["data"]
        flight_list = []
        for offer in flight_offers:
            segments = offer["itineraries"][0]["segments"]
            # Filter flights to only show those from the specified location to destination
            if segments[0]['departure']['iataCode'] == location and segments[-1]['arrival']['iataCode'] == destination:
                flight_info = {
                    'Flight ID': offer['id'],
                    'Departure': segments[0]['departure']['iataCode'],
                    'Arrival': segments[-1]['arrival']['iataCode'],
                    'Departure Time': segments[0]['departure']['at'],
                    'Arrival Time': segments[-1]['arrival']['at'],
                    'Duration': format_duration(offer['itineraries'][0]['duration']),  # Use the formatting function
                    'Carrier': segments[0]['carrierCode'],
                    'Price': offer['price']['total']
                }
                flight_list.append(flight_info)
        
        # Display the flight information in a table
        if flight_list:
            flight_df = pd.DataFrame(flight_list)
            st.write(flight_df)

            # Select a flight
            selected_flight = st.selectbox("Select your flight by Flight ID", flight_df['Flight ID'].unique())

            if selected_flight:
                # Example seating chart
                seats = {
                    'First Class': {'Price': 500, 'Seats': ['A1', 'A2', 'A3', 'A4', 'A5']},
                    'Business Class': {'Price': 300, 'Seats': ['B1', 'B2', 'B3', 'B4', 'B5']},
                    'Coach': {'Price': 100, 'Seats': ['C1', 'C2', 'C3', 'C4', 'C5']}
                }

                # Load or initialize reservations
                try:
                    reservations = pd.read_csv('reservations.csv')
                except FileNotFoundError:
                    reservations = pd.DataFrame(columns=['Flight ID', 'Seat', 'Name'])

                # Function to save reservations
                def save_reservations():
                    reservations.to_csv('reservations.csv', index=False)

                st.header("Select Your Seat")

                for section, details in seats.items():
                    st.subheader(f"{section} - ${details['Price']}")

                    # Display seats
                    for seat in details['Seats']:
                        if not reservations[(reservations['Flight ID'] == selected_flight) & (reservations['Seat'] == seat)].empty:
                            st.button(f"{seat} (Taken)", disabled=True)
                        else:
                            if st.button(f"{seat}"):
                                name = st.text_input("Enter your name", key=seat)
                                if st.button(f"Reserve {seat}", key=f"reserve_{seat}"):
                                    new_reservation = {'Flight ID': selected_flight, 'Seat': seat, 'Name': name}
                                    reservations = reservations.append(new_reservation, ignore_index=True)
                                    save_reservations()
                                    st.success(f"Seat {seat} reserved for {name}")
        else:
            st.error("No flights found for the specified route.")
    else:
        st.error("No flights found")

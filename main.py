import streamlit as st
import pandas as pd
import requests

# Amadeus API credentials
API_KEY = "e20u7Ad0NZASNyT32ufVGJXTdKpGDzI6"
API_SECRET = "UK8bsoENpcq8PvVH"

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
    return response.json().get("access_token")

# Function to search for flights
def search_flights(origin, destination, departure_date):
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "originLocationCode": origin,
       # "destinationLocationCode": destination,
       # "departureDate": departure_date,
       # "adults": 1
    }
    response = requests.get(FLIGHTS_URL, headers=headers, params=params)
    return response.json()

# Streamlit UI
st.title("Flight Reservation System with Amadeus API")

# User inputs for origin and destination
location = st.text_input("Enter your location (IATA code)")
destination = st.text_input("Enter your destination (IATA code)")
departure_date = st.date_input("Select departure date")

# Search for flights if location, destination, and date are provided
if location and destination and departure_date:
    st.header("Available Flights")

    flights_data = search_flights(location, destination, departure_date)

    # Process and display flights data
    if "data" in flights_data:
        flight_offers = flights_data["data"]
        for offer in flight_offers:
            segments = offer["itineraries"][0]["segments"]
            for segment in segments:
                st.write(f"Flight from {segment['departure']['iataCode']} to {segment['arrival']['iataCode']}")
                st.write(f"Departure: {segment['departure']['at']}")
                st.write(f"Arrival: {segment['arrival']['at']}")
                st.write(f"Duration: {segment['duration']}")
                st.write(f"Carrier: {segment['carrierCode']}")
                st.write("---")
    else:
        st.error("No flights found")

#st.write("lu")
#data=pd.read_csv("data.csv")
#st.dataframe(data)

# Example data for flights
flights = {
    'Flight ID': [1, 2, 3, 4],
    'Departure': ['10:00 AM', '12:00 PM', '2:00 PM', '4:00 PM'],
    'Arrival': ['12:00 PM', '2:00 PM', '4:00 PM', '6:00 PM'],
}

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

# Streamlit UI
st.title("Flight Reservation System")

# User inputs for location and destination
location = st.text_input("Enter your location")
destination = st.text_input("Enter your destination")

if location and destination:
    st.header("Available Flights!")
    flight_df = pd.DataFrame(flights)
    st.write(flight_df)

    # Select a flight
    selected_flight = st.selectbox("Select your flight", flight_df['Flight ID'])

    if selected_flight:
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


import streamlit as st
import pandas as pd

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
    st.header("Available Flights")
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


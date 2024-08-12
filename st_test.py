import streamlit as st
from td_dp_lib_gen3 import DataLib
from components import independent_artist_filter, date_selector, song_card_pagination  # Import components
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()
uri = os.getenv('MONGODB_URI')
app_passcode = os.getenv('APP_PASSCODE')
spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Initialize Spotify API
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret))

# Initialize the data library
db = DataLib(uri)

# Streamlit App
st.title('Gen 3 A&R Dashboard')

# App passcode
passcode = st.text_input('Enter passcode', type='password')
if passcode != app_passcode:
    st.error('Incorrect passcode')
    st.stop()

# Define field options for search criteria
field_options = [
    'title', 'author', 'description', 'album', 'release_date',
    'timestamp', 'apple_music_rank', 'shazam_ranks', 'tiktok_rank', 
    'spotify_id', 'popularity'
]

# Button to upload JSON files
if st.button('Upload JSON files'):
    try:
        db.upload_json_files()
        st.success('Files uploaded successfully!')
    except Exception as e:
        st.error(f"Error uploading JSON files: {e}")

# Button to delete all songs
if st.button('Delete all data'):
    try:
        result = db.delete_all_songs()
        st.success(result)
    except Exception as e:
        st.error(f"Error deleting all data: {e}")

# Independent Artist Filter Toggle
independent_artist_filter()

# Date Filter Dropdown
selected_timestamp = date_selector(db)

# Initialize session state for criteria and loaded songs if not already present
if 'criteria' not in st.session_state:
    st.session_state['criteria'] = []
if 'loaded_songs' not in st.session_state:
    st.session_state['loaded_songs'] = 3

# Function to remove a criterion
def remove_criterion(index):
    st.session_state['criteria'].pop(index)

# Display the existing criteria
for i, criterion in enumerate(st.session_state['criteria']):
    col1, col2, col3 = st.columns([3, 3, 1])
    
    with col1:
        st.session_state['criteria'][i]['field'] = st.selectbox(
            f'Field {i+1}', field_options, index=field_options.index(criterion['field']), key=f'field_{i}'
        )
    
    with col2:
        st.session_state['criteria'][i]['value'] = st.text_input(
            f'Value {i+1}', value=criterion['value'], key=f'value_{i}'
        )
    
    with col3:
        if st.button('❌', key=f'remove_{i}'):
            remove_criterion(i)
            st.rerun()  # Immediately rerun to update the UI

# Add a new criterion
if st.button('Add new criterion'):
    st.session_state['criteria'].append({'field': 'title', 'value': ''})

# Apply button to filter the data
if st.button('Apply'):
    # Reset loaded songs count on filter apply
    st.session_state['loaded_songs'] = 3
    
    criteria = [(c['field'], c['value']) for c in st.session_state['criteria'] if c['value']]
    
    # Apply filters to the data
    filtered_data = db.search_songs(criteria)

    # If a specific timestamp is selected, filter by that timestamp
    if selected_timestamp:
        filtered_data = filtered_data[filtered_data['timestamp'] == selected_timestamp]

    # st.dataframe(filtered_data)  # Commented out the table display

    # Display paginated song cards
    song_card_pagination(filtered_data, spotify)
else:
    try:
        # Display data based on the selected timestamp filter
        song_data_df = db.get_song_data(specific_date=selected_timestamp)
        
        if st.session_state['criteria']:
            criteria = [(c['field'], c['value']) for c in st.session_state['criteria'] if c['value']]
            song_data_df = db.search_songs(criteria)
            if selected_timestamp:
                song_data_df = song_data_df[song_data_df['timestamp'] == selected_timestamp]
        
        # st.dataframe(song_data_df)  # Commented out the table display

        # Display paginated song cards
        song_card_pagination(song_data_df, spotify)

    except Exception as e:
        st.error(f"Error retrieving data: {e}")

import streamlit as st
from td_dp_lib import DataLib
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
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
st.title('A&R Dashboard')

# App passcode
passcode = st.text_input('Enter passcode', type='password')
if passcode != app_passcode:
    st.error('Incorrect passcode')
    st.stop()

# Sidebar
# Add company logo
st.sidebar.image('company_logo.svg', width=100)  # Adjust width to make the logo smaller

st.sidebar.title("Dakota")

# Week/Month Selector
timeframe = st.sidebar.selectbox('Select timeframe', ['Week', 'Month'])

# Checkbox to filter distrokid artists
filter_distrokid = st.sidebar.checkbox('Show only distrokid artists')

# Unique Artists List
st.sidebar.header("Artists")

# Get unique artists
if filter_distrokid:
    unique_artists = [artist for artist in db.get_unique_artists() if any(song.distrokid for song in db.get_songs_by_author(artist))]
else:
    unique_artists = db.get_unique_artists()

artist_selected = st.sidebar.selectbox('Select an artist', unique_artists)

# Placeholder for artist-specific songs
st.sidebar.header(f"Songs by {artist_selected}")

# Get unique songs for the selected artist
songs_by_artist = db.get_songs_by_author(artist_selected)
song_titles = [song.title for song in songs_by_artist]

# Display song titles as buttons
selected_song = None
for song_title in song_titles:
    if st.sidebar.button(song_title):
        selected_song = song_title

# Main Page
if selected_song:
    st.header(f"Graphs for {selected_song}")
    
    # Get the selected song data
    song_data = next((song for song in songs_by_artist if song.title == selected_song), None)
    
    if song_data:
        # Graph of the past seven days
        latest_occurrence = song_data.all_occurrences[-1]
        past_seven_days_graph = latest_occurrence['graph_values'][::-1]
        x_labels = list(range(-7, 0))
        fig1 = px.line(x=x_labels, y=past_seven_days_graph, labels={'x': 'Day', 'y': 'Value'}, title='Past 7 Days Graph')
        st.plotly_chart(fig1)
        
        # Graph of all available popularity data
        popularity_data = [occurrence['popularity'] for occurrence in song_data.all_occurrences if 'popularity' in occurrence]
        popularity_dates = [occurrence['timestamp'] for occurrence in song_data.all_occurrences if 'popularity' in occurrence]
        fig2 = px.line(x=popularity_dates, y=popularity_data, labels={'x': 'Date', 'y': 'Popularity'}, title='Popularity Over Time')
        st.plotly_chart(fig2)
        
        # Graph of all available view counts
        view_counts = [occurrence['viewCount'] for occurrence in song_data.all_occurrences if 'viewCount' in occurrence and occurrence['viewCount'] is not None]
        view_count_dates = [occurrence['timestamp'] for occurrence in song_data.all_occurrences if 'viewCount' in occurrence and occurrence['viewCount'] is not None]
        if view_counts and view_count_dates:  # Ensure there is data to plot
            fig3 = px.line(x=view_count_dates, y=view_counts, labels={'x': 'Date', 'y': 'View Count'}, title='View Count Over Time')
            st.plotly_chart(fig3)
        else:
            st.write("No view count data available for this song.")
        
        # Fetch song details from Spotify
        search_results = spotify.search(q=f"track:{selected_song} artist:{artist_selected}", type='track')
        if search_results['tracks']['items']:
            track = search_results['tracks']['items'][0]
            album_cover_url = track['album']['images'][0]['url']
            artist_image_url = None
            if 'images' in track['artists'][0] and track['artists'][0]['images']:
                artist_image_url = track['artists'][0]['images'][0]['url']
            preview_url = track['preview_url']
            if preview_url:
                st.audio(preview_url, format='audio/mp3')
            st.image(album_cover_url, caption='Album Cover', use_column_width=True)
            if artist_image_url:
                st.image(artist_image_url, caption='Artist Picture', use_column_width=True)
        
        # Convert duration to MM:SS format
        duration_minutes = song_data.duration_ms // 60000
        duration_seconds = (song_data.duration_ms % 60000) // 1000
        duration_formatted = f"{duration_minutes}:{duration_seconds:02}"
        
        # Radar chart for song features
        features = {
            "Acousticness": song_data.acousticness,
            "Danceability": song_data.danceability,
            "Energy": song_data.energy,
            "Instrumentalness": song_data.instrumentalness,
            "Liveness": song_data.liveness,
            "Speechiness": song_data.speechiness,
            "Valence": song_data.valence,
        }

        categories = list(features.keys())
        values = list(features.values())
        
        radar_fig = go.Figure(data=go.Scatterpolar(
            r=values + values[:1],
            theta=categories + categories[:1],
            fill='toself'
        ))
        radar_fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            title='Song Features'
        )
        st.plotly_chart(radar_fig)
        
        # Display additional song information
        st.subheader("Song Details")
        st.write(f"**Title:** {song_data.title}")
        st.write(f"**Author:** {song_data.author}")
        st.write(f"**Album:** {song_data.album}")
        st.write(f"**Release Date:** {song_data.release_date}")
        st.write(f"**Duration:** {duration_formatted}")
    else:
        st.write("No data available for the selected song.")
else:
    st.write("Choose a song from the side menu")

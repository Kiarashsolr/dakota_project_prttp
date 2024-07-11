import streamlit as st
from td_dp_lib import DataLib
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging

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
st.sidebar.image('company_logo.svg', width=50)  # Adjust width to make the logo smaller

st.sidebar.title("Dakota")

# Distributor Filters
st.sidebar.header("Distributor Filters")

distributors = ["DistroKid", "TuneCore", "CD Baby", "Ditto Music", "Amuse", "LANDR", "UnitedMasters", "Stem", "iMusician", "RouteNote", "Catapult Distribution", "SongCast", "Soundrop"]

# Dictionary to hold checkbox states
distributor_filters = {}
for distributor in distributors:
    distributor_filters[distributor] = st.sidebar.checkbox(distributor)

# Week/Month Selector
timeframe = st.sidebar.selectbox('Select timeframe', ['Week', 'Month'])

# Unique Artists List
st.sidebar.header("Artists")

# Get unique artists
unique_artists = db.get_unique_artists()

artist_selected = st.sidebar.selectbox('Select an artist', unique_artists)

# Placeholder for artist-specific songs
st.sidebar.header(f"Songs by {artist_selected}")

# Get unique songs for the selected artist
songs_by_artist = db.get_songs_by_author(artist_selected)
song_titles = [song.title for song in songs_by_artist]

# Filter songs based on distributor keywords
def filter_songs_by_distributor(songs, filters):
    selected_distributors = [distributor.lower() for distributor, checked in filters.items() if checked]
    if not selected_distributors:
        return songs
    
    filtered_songs = []
    for song in songs:
        description = song.description.lower()
        if any(distributor in description for distributor in selected_distributors):
            filtered_songs.append(song)
    
    return filtered_songs

filtered_songs_by_artist = filter_songs_by_distributor(songs_by_artist, distributor_filters)
filtered_song_titles = [song.title for song in filtered_songs_by_artist]

# Display song titles as buttons
selected_song = None
for song_title in filtered_song_titles:
    if st.sidebar.button(song_title):
        selected_song = song_title

# Main Page
if selected_song:
    st.header(f"Graphs for {selected_song}")
    
    # Get the selected song data
    song_data = next((song for song in songs_by_artist if song.title == selected_song), None)
    
    if song_data:
        # Graph of the past seven days
        try:
            latest_occurrence = song_data.all_occurrences[-1]
            past_seven_days_graph = latest_occurrence['graph_values'][::-1]
            x_labels = list(range(-7, 0))
            fig1 = px.line(x=x_labels, y=past_seven_days_graph, labels={'x': 'Day', 'y': 'Value'}, title='Past 7 Days Graph')
            st.plotly_chart(fig1)
        except Exception as e:
            st.error(f"Error displaying past seven days graph: {e}")
        
        # Graph of all available popularity data
        try:
            popularity_data = [occurrence['popularity'] for occurrence in song_data.all_occurrences if 'popularity' in occurrence]
            popularity_dates = [occurrence['timestamp'] for occurrence in song_data.all_occurrences if 'popularity' in occurrence]
            fig2 = px.line(x=popularity_dates, y=popularity_data, labels={'x': 'Date', 'y': 'Popularity'}, title='Popularity Over Time')
            st.plotly_chart(fig2)
        except Exception as e:
            st.error(f"Error displaying popularity data graph: {e}")
        
        # Graph of total streams and daily streams
        try:
            total_stream_counts = []
            daily_stream_counts = []
            stream_count_dates = []
            for date, counts in song_data.streamCountData.items():
                if counts['total'] is not None:
                    total_stream_counts.append(counts['total'])
                    daily_stream_counts.append(counts['daily'] if counts['daily'] is not None else 0)
                    stream_count_dates.append(date)
            
            if total_stream_counts and stream_count_dates:  # Ensure there is data to plot
                fig3 = go.Figure()

                # Add total stream counts as a line trace
                fig3.add_trace(go.Scatter(
                    x=stream_count_dates,
                    y=total_stream_counts,
                    name='Total Streams',
                    mode='lines+markers',
                    yaxis='y1'
                ))

                # Add daily stream counts as a bar trace
                fig3.add_trace(go.Bar(
                    x=stream_count_dates,
                    y=daily_stream_counts,
                    name='Daily Streams',
                    yaxis='y2',
                    opacity=0.6
                ))

                fig3.update_layout(
                    title='Total Streams and Daily Streams Over Time',
                    xaxis_title='Date',
                    yaxis=dict(
                        title='Total Streams',
                        side='left'
                    ),
                    yaxis2=dict(
                        title='Daily Streams',
                        overlaying='y',
                        side='right'
                    ),
                    legend=dict(
                        x=0,
                        y=1,
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    )
                )

                st.plotly_chart(fig3)
            else:
                st.write("No stream count data available for this song.")
        except Exception as e:
            st.error(f"Error displaying stream count data graph: {e}")
        
        # Fetch song details from Spotify
        try:
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
        except Exception as e:
            st.error(f"Error fetching song details from Spotify: {e}")
        
        # Convert duration to MM:SS format
        duration_minutes = song_data.duration_ms // 60000
        duration_seconds = (song_data.duration_ms % 60000) // 1000
        duration_formatted = f"{duration_minutes}:{duration_seconds:02}"
        
        # Radar chart for song features
        try:
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
        except Exception as e:
            st.error(f"Error displaying radar chart for song features: {e}")
        
        # Display additional song information
        st.subheader("Song Details")
        st.write(f"**Title:** {song_data.title}")
        st.write(f"**Author:** {song_data.author}")
        st.write(f"**Album:** {song_data.album}")
        st.write(f"**Release Date:** {song_data.release_date}")
        st.write(f"**Duration:** {duration_formatted}")
        st.write(f"**Description:** {song_data.description}")
        
        # Display interest names
        st.subheader("Interest Names")
        for interest in song_data.interest_names:
            st.write(f"- {interest}")
        
        # Display age distribution
        st.subheader("Age Distribution")
        try:
            age_distribution_df = pd.DataFrame(list(song_data.age_distribution.items()), columns=['Age Group', 'Percentage'])
            st.bar_chart(age_distribution_df.set_index('Age Group'))
        except Exception as e:
            st.error(f"Error displaying age distribution: {e}")
        
        # Display top regions
        st.subheader("Top Regions")
        try:
            for region in song_data.top_regions:
                st.write(f"**{region['rank']}:** {region['country']} (Score: {region['score']})")
        except Exception as e:
            st.error(f"Error displaying top regions: {e}")
    else:
        st.write("No data available for the selected song.")
else:
    # Show the latest top songs
    st.header("Latest Top Songs")

    # Retrieve the latest top songs by the latest timestamp
    song_data_df = db.get_song_data()
    latest_timestamp = song_data_df['timestamp'].max()
    latest_top_songs = song_data_df[song_data_df['timestamp'] == latest_timestamp]

    # Apply distributor filters to latest top songs
    filtered_latest_top_songs = filter_songs_by_distributor(latest_top_songs.itertuples(index=False), distributor_filters)

    for row in filtered_latest_top_songs:
        try:
            # Fetch song details from Spotify
            search_results = spotify.search(q=f"track:{row.title} artist:{row.author}", type='track')
            if search_results['tracks']['items']:
                track = search_results['tracks']['items'][0]
                album_cover_url = track['album']['images'][0]['url']
                preview_url = track['preview_url']

                col1, col2 = st.columns([1, 3])
                with col1:
                    if album_cover_url:
                        st.image(album_cover_url, use_column_width=True)
                        if preview_url:
                            st.audio(preview_url, format='audio/mp3')

                with col2:
                    st.subheader(row.title)
                    st.write(f"**Author:** {row.author}")
                    
                    # Display popularity
                    st.write(f"**Popularity:** {row.popularity}")

                    # Display stream count
                    stream_count_data = row.streamCountData
                    if isinstance(stream_count_data, dict):
                        latest_date = max(stream_count_data.keys(), default=None)
                        if latest_date:
                            latest_count = stream_count_data[latest_date].get('total', 'N/A')

                            # Fetch stream counts for the last three days
                            stream_counts_last_three_days = []
                            stream_dates_last_three_days = sorted(stream_count_data.keys(), reverse=True)[:3]

                            for date in stream_dates_last_three_days:
                                count = stream_count_data.get(date, {}).get('total', 0)
                                stream_counts_last_three_days.append(count)

                            # Calculate the change in stream counts
                            if len(stream_counts_last_three_days) >= 3:
                                stream_diff = stream_counts_last_three_days[0] - stream_counts_last_three_days[1]
                                stream_second_diff = (stream_counts_last_three_days[0] - stream_counts_last_three_days[1]) - \
                                                     (stream_counts_last_three_days[1] - stream_counts_last_three_days[2])
                                color = 'white'
                                if stream_second_diff > 10:
                                    color = 'green'
                                elif stream_second_diff < 0:
                                    color = 'red'
                                st.markdown(f"**Stream Count:** {latest_count} (<span style='color:{color}'>+{stream_diff}</span>)", unsafe_allow_html=True)
                            else:
                                st.write(f"**Stream Count:** {latest_count} (N/A)")
                        else:
                            st.write("**Stream Count:** N/A (No date available)")
                    else:
                        st.write("**Stream Count:** N/A (No stream count data)")

                    st.write(f"**Description:** {row.description}")
        except Exception as e:
            logging.error(f"Error displaying song {row.title}: {str(e)}")
            st.error(f"Error displaying song {row.title}: {str(e)}")

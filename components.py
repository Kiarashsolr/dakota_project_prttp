import streamlit as st

# Independent Artist Filter Toggle
def independent_artist_filter():
    independent_distributors = [
        "DistroKid", "TuneCore", "CDBaby", "Ditto Music", "Amuse", "LANDR", 
        "UnitedMasters", "Stem", "iMusician", "RouteNote", 
        "Catapult Distribution", "SongCast", "Soundrop"
    ]

    independent_filter = st.checkbox('Show Only Independent Artists')
    
    if independent_filter:
        st.session_state['criteria'] = [{'field': 'description', 'value': distributor} for distributor in independent_distributors]
    elif 'criteria' not in st.session_state:
        st.session_state['criteria'] = []

# Date Filter Dropdown
def date_selector(db):
    available_dates = db.get_available_dates()
    date_options = ['Today', 'All Data'] + available_dates

    selected_option = st.selectbox('Select Date', date_options)

    if selected_option == 'Today':
        selected_timestamp = available_dates[-1]  # Last item in the list
    elif selected_option == 'All Data':
        selected_timestamp = None  # No filtering by date
    else:
        selected_timestamp = selected_option

    return selected_timestamp

def song_card_pagination(songs, spotify, initial_count=3, batch_size=10):
    """
    Display song cards with pagination. Loads an initial number of cards and 
    provides a 'Load More' button to load more cards in batches.
    
    :param songs: DataFrame containing song data
    :param spotify: Spotipy client instance for fetching song details
    :param initial_count: Number of cards to display initially
    :param batch_size: Number of additional cards to load per click
    """
    # Display the current batch of song cards
    for _, song in songs.head(st.session_state['loaded_songs']).iterrows():
        song_card(song, spotify)

    # If there are more songs to load, show the 'Load More' button
    if st.session_state['loaded_songs'] < len(songs):
        if st.button('Load More'):
            st.session_state['loaded_songs'] += batch_size
            st.rerun()  # Rerun to load more songs

def song_card(song, spotify):
    try:
        # Fetch song details from Spotify
        album_cover_url = None
        preview_url = None
        spotify_link = None
        if song['spotify_id']:
            search_results = spotify.track(song['spotify_id'])
            album_cover_url = search_results['album']['images'][0]['url']
            preview_url = search_results['preview_url']
            spotify_link = f"https://open.spotify.com/track/{song['spotify_id']}"

        col1, col2 = st.columns([1, 3])
        with col1:
            if album_cover_url:
                st.image(album_cover_url, use_column_width=True)
            if preview_url:
                st.audio(preview_url, format='audio/mp3')

        with col2:
            st.subheader(song['title'])
            st.write(f"**Author:** {song['author']}")
            st.write(f"**Album:** {song['album']}")
            st.write(f"**Release Date:** {song['release_date']}")
            st.write(f"**Popularity:** {song.get('popularity', 'N/A')}")
            
            # Display YouTube Information
            if song.get('youtube_info'):
                st.write(f"**YouTube Title:** {song['youtube_info'].get('yttitle', 'N/A')}")
                st.write(f"**YouTube Channel:** {song['youtube_info'].get('channelTitle', 'N/A')}")
                st.write(f"**YouTube Views:** {song['youtube_info'].get('viewCount', 'N/A')}")
                st.write(f"**YouTube Description:** {song['youtube_info'].get('description', 'N/A')}")
                st.write(f"[Watch on YouTube](https://www.youtube.com/watch?v={song['videoId']})", unsafe_allow_html=True)

            # Spotify Link
            if spotify_link:
                st.write(f"[Open on Spotify]({spotify_link})", unsafe_allow_html=True)

            # Display Rankings
            if song.get('tiktok_rank'):
                st.write(f"**TikTok Rank:** {song['tiktok_rank']}")
            if song.get('apple_music_rank'):
                st.write(f"**Apple Music Rank:** {song['apple_music_rank']}")

    except Exception as e:
        st.error(f"Error displaying song {song['title']}: {e}")

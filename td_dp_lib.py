import os
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
from datetime import datetime

class Song:
    def __init__(self, data, all_occurrences):
        """
        Initialize a Song object with data.

        :param data: dict, the song data
        :param all_occurrences: list of dict, all occurrences of the song
        """
        self.id = data.get('_id')
        self.title = data.get('title')
        self.author = data.get('author')
        self.graph_values = data.get('graph_values', [])
        self.acousticness = data.get('acousticness')
        self.danceability = data.get('danceability')
        self.energy = data.get('energy')
        self.instrumentalness = data.get('instrumentalness')
        self.liveness = data.get('liveness')
        self.speechiness = data.get('speechiness')
        self.valence = data.get('valence')
        self.popularity = data.get('popularity')
        self.album = data.get('album')
        self.release_date = data.get('release_date')
        self.duration_ms = data.get('duration_ms')
        self.timestamp = data.get('timestamp')
        self.note = data.get('note')
        self.all_occurrences = all_occurrences
        
        # New attributes
        self.detail_url = data.get('detail_url')
        self.interest_names = data.get('interest_names', [])
        self.age_distribution = data.get('age_distribution', {})
        self.top_regions = data.get('top_regions', [])
        self.description = data.get('description')
        self.streamCountData = data.get('streamCountData', {})
        self.ai_predicted_data = data.get('AI predicted data', {})
        self.expected_rank_next_day = data.get('expected_rank_next_day')

    def graphs_7(self, index=0):
        """
        Return the graph data for the last 7 days for a specific occurrence.

        :param index: int, the index of the occurrence
        :return: list, the graph values
        """
        return self.all_occurrences[index]['graph_values'] if self.all_occurrences else []

    def __repr__(self):
        return f"Song(ID={self.id}, Title={self.title}, Author={self.author})"

class DataLib:
    def __init__(self, connection_string):
        """
        Initialize the DataLib with MongoDB connection.

        :param connection_string: str, the connection string for MongoDB Atlas
        """
        self.client = MongoClient(connection_string, server_api=ServerApi('1'))
        self.db_name = 'music_trends'
        self.collection_name = 'daily_trends'
        self.db = self.client[self.db_name]

        # Test the connection
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(f"An error occurred: {e}")

    def upload_data(self, data):
        """
        Upload data to the collection.

        :param data: list of dict, the data to upload
        """
        collection = self.db[self.collection_name]
        # Process the new data structure
        for item in data:
            # Convert timestamp to datetime object if it's a string
            if isinstance(item.get('timestamp'), str):
                item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
            
            # Ensure new fields are included
            item['AI predicted data'] = item.get('AI predicted data', {})
            item['expected_rank_next_day'] = item.get('expected_rank_next_day')

        collection.insert_many(data)
        print(f"Inserted {len(data)} documents into the collection {self.collection_name}")

    def get_song_data(self):
        """
        Retrieve song data from the collection.

        :return: pd.DataFrame, the song data as a pandas DataFrame
        """
        collection = self.db[self.collection_name]
        data = list(collection.find())
        # Convert the _id field to a string
        for record in data:
            record['_id'] = str(record['_id'])
        return pd.DataFrame(data)

    def get_song_by_id(self, song_id):
        """
        Retrieve a single song by its ID.

        :param song_id: str, the ID of the song to retrieve
        :return: Song, the song data
        """
        collection = self.db[self.collection_name]
        song_data = collection.find_one({'_id': song_id})
        all_occurrences = list(collection.find({'title': song_data['title'], 'author': song_data['author']}))
        return Song(song_data, all_occurrences) if song_data else None

    def get_songs_by_name(self, title):
        """
        Retrieve songs by title and aggregate their data.

        :param title: str, the title of the song to retrieve
        :return: list of Song, the list of aggregated songs with the given title
        """
        collection = self.db[self.collection_name]
        song_data = list(collection.find({'title': title}))

        # Aggregate songs by title and author
        aggregated_data = {}
        for data in song_data:
            key = (data['title'], data['author'])
            if key not in aggregated_data:
                aggregated_data[key] = {
                    '_id': str(data['_id']),
                    'title': data['title'],
                    'author': data['author'],
                    'graph_values': data['graph_values'],
                    'acousticness': data.get('acousticness'),
                    'danceability': data.get('danceability'),
                    'energy': data.get('energy'),
                    'instrumentalness': data.get('instrumentalness'),
                    'liveness': data.get('liveness'),
                    'speechiness': data.get('speechiness'),
                    'valence': data.get('valence'),
                    'popularity': data.get('popularity'),
                    'album': data.get('album'),
                    'release_date': data.get('release_date'),
                    'duration_ms': data.get('duration_ms'),
                    'timestamp': data['timestamp'],
                    'note': data.get('note'),
                    'detail_url': data.get('detail_url'),
                    'interest_names': data.get('interest_names', []),
                    'age_distribution': data.get('age_distribution', {}),
                    'top_regions': data.get('top_regions', []),
                    'description': data.get('description'),
                    'streamCountData': data.get('streamCountData', {}),
                    'ai_predicted_data': data.get('AI predicted data', {}),
                    'expected_rank_next_day': data.get('expected_rank_next_day'),
                    'all_occurrences': [data]
                }
            else:
                # Aggregate graph values
                aggregated_data[key]['graph_values'] = [
                    max(a, b) for a, b in zip(aggregated_data[key]['graph_values'], data['graph_values'])
                ]
                aggregated_data[key]['all_occurrences'].append(data)

        return [Song(data, data['all_occurrences']) for data in aggregated_data.values()]

    def get_songs_by_author(self, author):
        """
        Retrieve songs by author and aggregate their data.

        :param author: str, the author of the song to retrieve
        :return: list of Song, the list of aggregated songs by the given author
        """
        collection = self.db[self.collection_name]
        song_data = list(collection.find({'author': author}))

        # Aggregate songs by title and author
        aggregated_data = {}
        for data in song_data:
            key = (data['title'], 'author')
            if key not in aggregated_data:
                aggregated_data[key] = {
                    '_id': str(data['_id']),
                    'title': data['title'],
                    'author': data['author'],
                    'graph_values': data['graph_values'],
                    'acousticness': data.get('acousticness'),
                    'danceability': data.get('danceability'),
                    'energy': data.get('energy'),
                    'instrumentalness': data.get('instrumentalness'),
                    'liveness': data.get('liveness'),
                    'speechiness': data.get('speechiness'),
                    'valence': data.get('valence'),
                    'popularity': data.get('popularity'),
                    'album': data.get('album'),
                    'release_date': data.get('release_date'),
                    'duration_ms': data.get('duration_ms'),
                    'timestamp': data['timestamp'],
                    'note': data.get('note'),
                    'detail_url': data.get('detail_url'),
                    'interest_names': data.get('interest_names', []),
                    'age_distribution': data.get('age_distribution', {}),
                    'top_regions': data.get('top_regions', []),
                    'description': data.get('description'),
                    'streamCountData': data.get('streamCountData', {}),
                    'ai_predicted_data': data.get('AI predicted data', {}),
                    'expected_rank_next_day': data.get('expected_rank_next_day'),
                    'all_occurrences': [data]
                }
            else:
                # Aggregate graph values
                aggregated_data[key]['graph_values'] = [
                    max(a, b) for a, b in zip(aggregated_data[key]['graph_values'], data['graph_values'])
                ]
                aggregated_data[key]['all_occurrences'].append(data)

        return [Song(data, data['all_occurrences']) for data in aggregated_data.values()]

    # New method to get top regions for a song
    def get_top_regions(self, song_id):
        """
        Get the top regions for a specific song.

        :param song_id: str, the ID of the song
        :return: list, the top regions for the song
        """
        song = self.get_song_by_id(song_id)
        return song.top_regions if song else []

    # New method to get age distribution for a song
    def get_age_distribution(self, song_id):
        """
        Get the age distribution for a specific song.

        :param song_id: str, the ID of the song
        :return: dict, the age distribution for the song
        """
        song = self.get_song_by_id(song_id)
        return song.age_distribution if song else {}

    # New method to analyze stream count data
    def analyze_stream_count(self, song_id):
        """
        Analyze the stream count data for a specific song.

        :param song_id: str, the ID of the song
        :return: dict, analysis of the stream count data
        """
        song = self.get_song_by_id(song_id)
        if not song or not song.streamCountData:
            return None

        stream_data = song.streamCountData
        total_streams = max(data['total'] for data in stream_data.values() if isinstance(data, dict))
        daily_average = sum(data['daily'] for data in stream_data.values() if isinstance(data, dict) and data['daily'] is not None) / len(stream_data)

        return {
            'total_streams': total_streams,
            'daily_average': daily_average,
            'data': stream_data
        }

    # New method to get AI predicted data
    def get_ai_predicted_data(self, song_id):
        """
        Get the AI predicted data for a specific song.

        :param song_id: str, the ID of the song
        :return: dict, the AI predicted data for the song
        """
        song = self.get_song_by_id(song_id)
        return song.ai_predicted_data if song else {}

    # New method to get expected rank next day
    def get_expected_rank_next_day(self, song_id):
        """
        Get the expected rank for the next day for a specific song.

        :param song_id: str, the ID of the song
        :return: int, the expected rank for the next day
        """
        song = self.get_song_by_id(song_id)
        return song.expected_rank_next_day if song else None

    def analyze_ai_predictions(self, song_id):
        """
        Analyze the AI predicted data for a specific song.

        :param song_id: str, the ID of the song
        :return: dict, analysis of the AI predicted data
        """
        song = self.get_song_by_id(song_id)
        if not song or not song.ai_predicted_data:
            return None

        ai_data = song.ai_predicted_data
        max_predicted = max(ai_data.values())
        min_predicted = min(ai_data.values())
        avg_predicted = sum(ai_data.values()) / len(ai_data)

        return {
            'max_predicted': max_predicted,
            'min_predicted': min_predicted,
            'avg_predicted': avg_predicted,
            'data': ai_data
        }

    def upload_json_files(self, directory='.'):
        """
        Scan the directory for JSON files and upload them to the collection.

        :param directory: str, the directory to scan for JSON files (defaults to the current directory)
        """
        json_files = [f for f in os.listdir(directory) if f.endswith('.json') and f.startswith('trending_music_')]
        if not json_files:
            print("No JSON files found in the directory.")
            return

        print("Found the following JSON files:")
        for file in json_files:
            print(file)

        confirm = input("Do you want to upload these files to the database? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Upload cancelled.")
            return

        for file in json_files:
            file_path = os.path.join(directory, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                data_to_upload = file_data['data']
                for item in data_to_upload:
                    item['timestamp'] = file_data['timestamp']
                self.upload_data(data_to_upload)

        print("All files have been uploaded successfully.")

    def add_note_to_song(self, song_id, note):
        """
        Add a note to a specific song.

        :param song_id: str, the ID of the song to add a note to
        :param note: str, the note to add
        :return: str, confirmation message
        """
        collection = self.db[self.collection_name]
        collection.update_one({'_id': song_id}, {'$set': {'note': note}})
        return f'Note added to song with ID: {song_id}'

    def delete_song_by_id(self, song_id):
        """
        Delete a song by its ID.

        :param song_id: str, the ID of the song to delete
        :return: str, confirmation message
        """
        collection = self.db[self.collection_name]
        result = collection.delete_one({'_id': song_id})
        if result.deleted_count:
            return f'Song with ID: {song_id} deleted successfully.'
        else:
            return f'Song with ID: {song_id} not found.'

    def filter_by_date_range(self, start_date, end_date):
        """
        Retrieve songs within a specific date range.

        :param start_date: str, the start date in 'YYYY-MM-DD' format
        :param end_date: str, the end date in 'YYYY-MM-DD' format
        :return: pd.DataFrame, the song data within the date range as a pandas DataFrame
        """
        collection = self.db[self.collection_name]
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        data = list(collection.find({'timestamp': {'$gte': start_date, '$lte': end_date}}))
        for record in data:
            record['_id'] = str(record['_id'])
        return pd.DataFrame(data)

    def get_top_songs_comparison(self, date1, date2):
        """
        Compare the top songs between two dates.

        :param date1: str, the first date in 'YYYY-MM-DD' format
        :param date2: str, the second date in 'YYYY-MM-DD' format
        :return: pd.DataFrame, a DataFrame with the top songs from both dates side by side
        """
        collection = self.db[self.collection_name]
        data1 = list(collection.find({'timestamp': date1}))
        data2 = list(collection.find({'timestamp': date2}))
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
        df1['_id'] = df1['_id'].astype(str)
        df2['_id'] = df2['_id'].astype(str)
        return pd.concat([df1, df2], axis=1, keys=[date1, date2])

    def get_unique_songs(self):
        """
        Retrieve unique songs across the dataset.

        :return: pd.DataFrame, the unique song data as a pandas DataFrame
        """
        collection = self.db[self.collection_name]
        data = list(collection.aggregate([{'$group': {'_id': {'title': '$title', 'author': '$author'}, 'unique_ids': {'$addToSet': '$_id'}, 'graph_values': {'$first': '$graph_values'}, 'timestamp': {'$first': '$timestamp'}}}]))
        for record in data:
            record['_id'] = str(record['_id'])
        return pd.DataFrame(data)

    def get_unique_artists(self):
        """
        Retrieve unique artists from the dataset.

        :return: list, unique artist names
        """
        collection = self.db[self.collection_name]
        artists = collection.distinct('author')
        return sorted(artists)

    def get_daily_top_songs(self, date):
        """
        Retrieve the top songs for a specific day.

        :param date: str, the date in 'YYYY-MM-DD' format
        :return: pd.DataFrame, the song data for the specified date as a pandas DataFrame
        """
        collection = self.db[self.collection_name]
        data = list(collection.find({'timestamp': date}))
        for record in data:
            record['_id'] = str(record['_id'])
        return pd.DataFrame(data)
    
    def delete_all_songs(self):
        """
        Delete all songs in the collection.

        :return: str, confirmation message
        """
        collection = self.db[self.collection_name]
        result = collection.delete_many({})
        return f'Deleted {result.deleted_count} songs from the collection.'

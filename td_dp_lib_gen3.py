import os
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
from datetime import datetime

class DataLib:
    def __init__(self, connection_string):
        self.client = MongoClient(connection_string, server_api=ServerApi('1'))
        self.db_name = 'music_trends'
        self.collection_name = 'daily_trends_gen3'
        self.db = self.client[self.db_name]

        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(f"An error occurred: {e}")

    def upload_json_files(self, directory='.'):
        json_files = [f for f in os.listdir(directory) if f.endswith('.json') and f.startswith('trending_music_')]
        if not json_files:
            print("No JSON files found in the directory.")
            return

        for file in json_files:
            file_path = os.path.join(directory, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                data_to_upload = file_data['data']
                for item in data_to_upload:
                    # Extract just the date part (YYYY-MM-DD) from the timestamp
                    item['timestamp'] = file_data.get('timestamp', datetime.utcnow().isoformat()).split('T')[0]

                self.upload_data(data_to_upload)

        print("All files have been uploaded successfully.")

    # def upload_data(self, data):
    #     collection = self.db[self.collection_name]
    #     collection.insert_many(data)
    #     print(f"Inserted {len(data)} documents into the collection {self.collection_name}")

    # def delete_all_songs(self):
    #     collection = self.db[self.collection_name]
    #     result = collection.delete_many({})
    #     return f'Deleted {result.deleted_count} songs from the collection.'

    def search_songs(self, criteria):
        collection = self.db[self.collection_name]
        query = {'$or': [{field: {'$regex': value, '$options': 'i'}} for field, value in criteria]}
        data = list(collection.find(query))
        for record in data:
            record['_id'] = str(record['_id'])

        return pd.DataFrame(data)
    
    def get_song_data(self, specific_date=None):
        collection = self.db[self.collection_name]
        query = {}

        if specific_date:
            query = {'timestamp': specific_date}
        
        data = list(collection.find(query))
        for record in data:
            record['_id'] = str(record['_id'])
        return pd.DataFrame(data)

    def get_available_dates(self):
        collection = self.db[self.collection_name]
        timestamps = collection.distinct('timestamp')
        return sorted(timestamps)

import requests
import sys
from utils import *

class ContainerCache:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ContainerCache, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            # Initialize an empty dictionary to store cached responses
            self.cache = {}
            self._initialized = True
    
    def get(self, uri_container):
        """
        Fetch data from the server or return cached data if available.

        Args:
            uri_container (str): The URI to fetch.

        Returns:
            dict: The response data (either from the cache or the server).
        """
        # Check if the response for this URI is already cached
        if uri_container in self.cache:
            return self.cache[uri_container]
        
        # Define the request details
        url = "http://127.0.0.1:8080/jsonrpc"
        headers = {
            "Content-Type": "application/json"
        }
        body = {
            "jsonrpc": "2.0",
            "method": "Files.GetDirectory",
            "params": {
                "directory": uri_container,
                "media": "files",
                "properties": ["title", "plot", "art"]
            },
            "id": 1
        }
        
        # Make the request to the server
        response = requests.post(url, headers=headers, json=body).json()

        # log(response)
        response = response['result']['files']
        
        # Cache the response
        self.cache[uri_container] = response
        
        return response

    def get_favorites(self, uri_container):
        return [ListFieldsFiles_to_Favorites(uri_container, lff) for lff in self.get(uri_container)]
    
    def get_content(self, uri_container, channel_name="", containerLabel=""):
        to_return = []
        for fav in self.get_favorites(uri_container):
            to_return.append({
                            "url" : (sys.argv[0] + '?' + fav['uri']) if fav['isFolder'] else fav['uri'],
                            "listitem" : Favorite_to_ListItem(fav, channel_name, containerLabel),
                            "isFolder" : fav['isFolder']
                        })
        return to_return
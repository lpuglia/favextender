import requests
import sys
from utils import *

class ContainerCache:
    def __init__(self):
        # Initialize an empty dictionary to store cached responses
        self.cache = {}
    
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

    def get_DirItems(self, uri_container, channel_name="", containerLabel=""):
        # import web_pdb; web_pdb.set_trace()
        to_return = []
        for lff in self.get(uri_container):
            fav = ListFieldsFiles_to_Favorites(uri_container, lff)
            li = Favorite_to_ListItem(fav, channel_name, containerLabel)
            to_return.append(
                        {
                            "url" : (sys.argv[0] + '?' + lff['file']) if lff['filetype'] == 'directory' else lff['file'],
                            "listitem" : li,
                            "isFolder" : lff['filetype'] == 'directory'
                        }
                    )
        return to_return

    def get_Favorites(self, uri_container):
        return [ListFieldsFiles_to_Favorites(uri_container, lff) for lff in self.get(uri_container)]
import requests
import time
from urllib.parse import unquote

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
        
        return [self.make_favorite(uri_container, lff) for lff in response]

    def make_favorite(self, uri_container, lff):
        art = lff.get('art',{})
        art = {k:unquote(v.replace("image://", "").rstrip("/")) for k,v in art.items()}
            
        return {
            "favoriteLabel" : lff['label'],
            "label" : lff['label'],
            "label2" : "",
            "plot" : lff['plot'],
            "firstDiscovered": int(time.time()),
            "isFolder" : lff['filetype'] == 'directory',
            "isLive": False,
            "isDynamic": False,
            "autoplay": False,
            "addContent": False,
            "mediaSource": "",
            "uri" : lff['file'],
            "uri_container" : uri_container,
            "title" : lff['title'],
            "fanartPath" : art.get('fanart', ""),
            "posterPath" : art.get('poster', ""),
            "thumbPath" : art.get('thumb', ""),
            "icon" : art.get('icon', "")
        }
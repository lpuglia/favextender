import os
import sys
import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
import requests
import time
from urllib.parse import unquote, urlparse
import json
import base64


def b64encode(data):
    """
    Encode input to Base64.
    Handles both string and binary data (bytes).
    """
    if isinstance(data, str):
        # Convert string to bytes and encode
        data = data.encode()
    elif not isinstance(data, (bytes, bytearray)):
        raise TypeError("Input must be a string or bytes-like object.")
    # Encode to Base64
    return base64.b64encode(data).decode()

def is_url(file_path):
    parsed = urlparse(file_path)
    return parsed.scheme in ("http", "https", "ftp", "file")

def resolve_path(file_path):
    parsed = urlparse(file_path)
    if parsed.scheme in ("http", "https", "ftp", "file"): # is url:
        return file_path
    else: # is local resource:
        return xbmcvfs.translatePath("special://home/addons/") + file_path

def check_local_path_and_encode(key_prefix, path):
    # log(path)
    if is_url(path) or not path:
        return {
                f"{key_prefix}Path" : path,
                f"{key_prefix}Data" : None,
            }
    else: # if it is a local resource encode it in base64
        with open(path, "rb") as binary_file:
            binary_data = binary_file.read()

        base64_string = b64encode(binary_data)

        path = path.replace(xbmcvfs.translatePath("special://home/addons/"), "")

        return {
                f"{key_prefix}Path" : path,
                f"{key_prefix}Data" : base64_string,
            }


def ListFieldsFiles_to_Favorites(uri_container, lff):
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

def ListFieldsFiles_to_ListItem(lff):
    art = lff.get('art',{})
    art = {k:unquote(v.replace("image://", "").rstrip("/")) for k,v in art.items()}
        
    list_item = xbmcgui.ListItem(label=lff['label'], label2="")

    # Set additional properties for the ListItem
    list_item.setInfo('video', {
        'plot': lff['plot']
    })

    # Set the path to the media file (e.g., a video file)
    list_item.setPath(lff['file'])

    # Optionally, add an image (e.g., thumbnail or fanart)
    list_item.setArt({
        'thumb': art.get('thumb', ""),
        'fanart': art.get('fanart', ""),
        'poster': art.get('poster', ""),
        'icon': art.get('icon', ""),
    })

    list_item.setProperty('isPlayable', 'true')

    return list_item

def ListItem_to_Favorite(item, name, isLive, isDynamic, autoplay=True, addContent=False):
    # import web_pdb; web_pdb.set_trace()

    fav_dict = {
        "favoriteLabel" : name,
        "label" : item.getLabel(),
        "label2" : item.getLabel2(),
        "plot" : item.getVideoInfoTag().getPlot(),
        "firstDiscovered": int(time.time()),
        "isFolder" : item.isFolder(),
        "isLive": isLive,
        "isDynamic": isDynamic,
        "autoplay": autoplay,
        "addContent": addContent,
        "mediaSource": "",
        "uri" : item.getPath(),
        "uri_container" : xbmc.getInfoLabel('Container.FolderPath'),
        "title" : item.getLabel(),
    }

    fav_dict.update(check_local_path_and_encode("fanart", item.getArt('fanart')))
    fav_dict.update(check_local_path_and_encode("poster", item.getArt('poster')))
    fav_dict.update(check_local_path_and_encode("thumb", item.getArt('thumb')))
    return fav_dict

def Favorite_to_ListItem(fav):
    li = xbmcgui.ListItem(fav['favoriteLabel'])

    li.setArt({
        'thumb': resolve_path(fav['thumbPath']),
        'fanart': resolve_path(fav['fanartPath']),
        'poster': resolve_path(fav['posterPath'] if fav['posterPath'] else fav['thumbPath']) # when showing a normal folder thumb becomes also the poster, but here i show a folder of playable items
    })
    li.setInfo('video', {
        'title': fav['title'],
        'plot': fav['plot']
    })
    li.setProperty('isPlayable', 'true')

    custom_context_menu = [("Remove from FavExtender", "RunPlugin(plugin://your.plugin.id?action=custom_action)")]
    li.addContextMenuItems(custom_context_menu)
    return li

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

    def get_DirItems(self, uri_container):
        return [
                    {
                        "url" : (sys.argv[0] + '?' + lff['file']) if lff['filetype'] == 'directory' else lff['file'],
                        "listitem" : ListFieldsFiles_to_ListItem(lff) ,
                        "isFolder" : lff['filetype'] == 'directory'
                    }
                for lff in self.get(uri_container)]

    def get_Favorites(self, uri_container):
        return [ListFieldsFiles_to_Favorites(uri_container, lff) for lff in self.get(uri_container)]

def is_android():
    return xbmc.getCondVisibility('System.Platform.Android')

class FavManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FavManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, force_load=False):

        if not hasattr(self, "_initialized"):
            self.favorites = {}
            if is_android():
                storage_folder = xbmcvfs.translatePath("/storage/emulated/0/Download/")
            else:
                storage_folder = xbmcvfs.translatePath("special://home/")

            self.file_path = os.path.join(storage_folder, "exttv_favorite.json")
            self.load_favorites()
            self._initialized = True

        if force_load:
            self.load_favorites()


    def get_favorites(self, channel_name):
        cc = ContainerCache()
        to_return = []
        for fav in self.favorites[channel_name]:
            if fav['addContent']:
                content = cc.get_DirItems(fav['uri'])
                to_return.extend(content)
            else:
                if fav['uri_container'] and fav['isDynamic']:
                    container = cc.get_Favorites(fav['uri_container'])
                    matches = [c for c in container if c['uri'] == fav['uri']]
                    if not matches:
                        matches = [c for c in container if c['label'] == fav['label']]
                        if not matches:
                            matches = [fav]

                    match = matches[0]

                    # art = match.get('art', {})
                    # art = {k:unquote(v.replace("image://", "").rstrip("/")) for k,v in art.items()}

                    fav['thumbPath'] = match['thumbPath']
                    fav['fanartPath'] = match['fanartPath']
                    fav['posterPath'] = match['posterPath']
                    fav['plot'] = match['plot']
                # import web_pdb; web_pdb.set_trace()

                to_return.append(
                                    {
                                        "url" : (f"{sys.argv[0]}?uri={b64encode(fav['uri'])}") if fav["isFolder"] else fav['uri'],
                                        "listitem" : Favorite_to_ListItem(fav),
                                        "isFolder" : fav["isFolder"]
                                    }
                                )
                # xbmc.log(str(to_return[-1]), xbmc.LOGINFO)

        return to_return


    def get_channels(self):
        to_return = []
        addon = xbmcaddon.Addon()
        addon_path = addon.getAddonInfo('path')
        for channel, favs in self.favorites.items():
            li = xbmcgui.ListItem(channel)
            if len(favs)==1 and favs[0]['addContent']: # single program content channel
                li.setArt({
                    "fanart": favs[0]["fanartPath"],
                    "poster": favs[0]["posterPath"],
                    "thumb": favs[0]["thumbPath"]
                })
                li.setInfo('video', {
                    'title': favs[0]['title'],
                    'plot': favs[0]['plot']
                })
            else:
                li.setArt({
                    'thumb': addon_path+"resources/placeholder.png"
                })
                li.setInfo('video', {
                    'title': channel
                })
            custom_context_menu = [("Remove from FavExtender", "RunPlugin(plugin://your.plugin.id?action=custom_action)")]
            li.addContextMenuItems(custom_context_menu)
            to_return.append(li)
        return to_return

    def add_to_channel(self, channel_name, fav=None):

        if fav:
            if channel_name in self.favorites:
                self.favorites[channel_name].append(fav)
            else:
                self.favorites[channel_name] = [fav]

        self.dump_favorites()


    def load_favorites(self):
        try:
            # Check if the file exists and read the existing data
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as file:
                    self.favorites = json.load(file)
                
        except Exception as e:
            xbmc.log(f"Failed to load JSON file: {e}", xbmc.LOGERROR)

    def dump_favorites(self):
        try:
            # Write the updated list back to the file
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump(self.favorites, file, indent=4, ensure_ascii=False)

            xbmc.log(f"JSON file updated successfully at {self.file_path}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"Failed to update JSON file: {e}", xbmc.LOGERROR)

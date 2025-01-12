import os
import sys
import xbmc
import xbmcvfs
import xbmcaddon
import json

from containercache import ContainerCache
from utils import *

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


    def get_content(self, uri_container, channel_name="", containerLabel=""):
        cc = ContainerCache()
        to_return = []
        for fav in cc.get(uri_container):
            to_return.append({
                            "url" : f"{sys.argv[0]}?uri={b64encode(fav['uri'])}" if fav["isFolder"] else fav['uri'],
                            "listitem" : Favorite_to_ListItem(fav, channel_name, containerLabel),
                            "isFolder" : fav['isFolder']
                        })
        return to_return
    

    def get_favorites(self, channel_name):
        to_return = []
        for fav in self.favorites[channel_name]:
            if fav['addContent']:
                content = self.get_content(fav['uri'], channel_name, fav['favoriteLabel'])
                to_return.extend(content)
            else:
                if fav['uri_container'] and fav['isDynamic']:
                    fav = update_favorite(fav)

                to_return.append({
                                    "url" : f"{sys.argv[0]}?uri={b64encode(fav['uri'])}" if fav["isFolder"] else fav['uri'],
                                    "listitem" : Favorite_to_ListItem(fav, channel_name),
                                    "isFolder" : fav["isFolder"]
                                })
        return to_return


    def get_channels(self):
        to_return = []
        for channel, favs in self.favorites.items():

            if len(favs)==1 and favs[0]['addContent']: # single program content channel
                li = Favorite_to_ListItem(favs[0], channel)
            else:
                li = Channel_to_ListItem(channel)

            path = xbmcaddon.Addon().getAddonInfo('path') 
            custom_context_menu = [("Remove from FavExtender", f"RunScript({path}contextitem.py,remove_channel={channel})")]
            li.addContextMenuItems(custom_context_menu)
            to_return.append({
                                "url" : f"{sys.argv[0]}?channel={channel}",
                                "listitem" : li,
                                "isFolder" : True
                            })
        return to_return

    def add_to_channel(self, channel_name, fav=None):

        if fav:
            if channel_name in self.favorites:
                self.favorites[channel_name].append(fav)
            else:
                self.favorites[channel_name] = [fav]

        self.dump_favorites()

    def remove_from_channel(self, channel_name, fav_name):

        if channel_name in self.favorites:
            self.favorites[channel_name] = [fav for fav in self.favorites[channel_name] if fav['favoriteLabel'] != fav_name]

        self.dump_favorites()

    def remove_channel(self, channel_name):
        if channel_name in self.favorites:
            del self.favorites[channel_name]

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

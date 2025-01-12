import os
import sys
import xbmc
import xbmcvfs
import xbmcgui
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


    def get_favorites(self, channel_name):
        cc = ContainerCache()
        to_return = []
        for fav in self.favorites[channel_name]:
            if fav['addContent']:
                # import web_pdb; web_pdb.set_trace()
                content = cc.get_DirItems(fav['uri'], channel_name, fav['favoriteLabel'])
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
                                        "listitem" : Favorite_to_ListItem(fav, channel_name),
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
            path = xbmcaddon.Addon().getAddonInfo('path') 
            custom_context_menu = [("Remove from FavExtender", f"RunScript({path}contextitem.py,remove_channel={channel})")]
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

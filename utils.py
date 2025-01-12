import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon

import time
import base64
from urllib.parse import unquote, urlparse

def is_android():
    return xbmc.getCondVisibility('System.Platform.Android')

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

def ListItem_to_Favorite(item, name, isLive, isDynamic, autoplay=False, addContent=False):

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

    if addContent:
        from containercache import ContainerCache
        cc = ContainerCache()
        content = cc.get_Favorites(item.getPath())
        fav_dict["content"] = content

    return fav_dict

def Favorite_to_ListItem(fav, channel_name, containerLabel=None):
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
    path = xbmcaddon.Addon().getAddonInfo('path') 
    if containerLabel:
        custom_context_menu = [("Remove content parent from FavExtender", f"RunScript({path}contextitem.py,remove_channel={channel_name},remove_fav={containerLabel})")]
    else:
        custom_context_menu = [("Remove from FavExtender", f"RunScript({path}contextitem.py,remove_channel={channel_name},remove_fav={fav['favoriteLabel']})")]
    li.addContextMenuItems(custom_context_menu)
    return li
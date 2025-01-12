import xbmc
import xbmcplugin
import xbmcaddon
import sys
from urllib.parse import urlparse, unquote, parse_qs
import base64

from favmanager import FavManager, ContainerCache, Favorite_to_ListItem


def b64decode(base64_string):
    return base64.b64decode(base64_string).decode()

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo('name')


def log(message):
    xbmc.log("-----------------"+str(message), level=xbmc.LOGINFO)


def add_favorites_to_channel(dir_items, autoplay=False):
    """Add each favorite to the Kodi plugin directory"""
    log(addon_handle)
    for dir_item in dir_items:
        xbmcplugin.addDirectoryItem(
            handle = addon_handle,
            **dir_item
        )
    xbmcplugin.setContent(addon_handle, 'episodes')
    xbmcplugin.endOfDirectory(addon_handle)

    player = xbmc.Player()

    if autoplay and not player.isPlaying():
        li = dir_items[0]['listitem']
        xbmc.executebuiltin('RunPlugin("' + li.getPath() + '")')


def add_channels(items):

    for li in items:
        xbmcplugin.addDirectoryItem(
            handle = addon_handle,
            url = sys.argv[0] + '?' + li.getLabel(),
            listitem = li,
            isFolder = True
        )

    xbmcplugin.endOfDirectory(addon_handle)

if __name__ == '__main__':

    # import web_pdb; web_pdb.set_trace()
    addon_handle = int(sys.argv[1])  # Get the handle of the current plugin
    favs = FavManager()

    params = parse_qs(sys.argv[2].lstrip('?'))

    if favs.favorites:
        if sys.argv[2] == "":
            # get channel list
            add_channels(favs.get_channels())
        elif 'uri' not in params:
            # get channel content
            add_favorites_to_channel(favs.get_favorites(sys.argv[2][1:]), autoplay = favs.favorites[sys.argv[2][1:]][0]['autoplay'] if favs.favorites[sys.argv[2][1:]] else False)
        else:
            # xbmc.executebuiltin(f"RunPlugin({b64decode(params['uri'][0])})") # for some reason this won't work
            # get fav content
            cc = ContainerCache()
            add_favorites_to_channel(cc.get_content(b64decode(params['uri'][0])))

import xbmc
import xbmcplugin
import xbmcaddon
import sys
from urllib.parse import parse_qs
import base64

from favmanager import FavManager


def b64decode(base64_string):
    return base64.b64decode(base64_string).decode()

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo('name')


def log(message):
    xbmc.log("-----------------"+str(message), level=xbmc.LOGINFO)


def add_items(dir_items, autoplay=False):
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


if __name__ == '__main__':

    # import web_pdb; web_pdb.set_trace()
    addon_handle = int(sys.argv[1])  # Get the handle of the current plugin
    favs = FavManager()

    params = parse_qs(sys.argv[2].lstrip('?'))

    if favs.favorites:
        if params == {}:
            # get channel list
            add_items(favs.get_channels())
        elif 'channel' in params:
            # get channel content
            channel = params['channel'][0]
            add_items(favs.get_favorites(channel), autoplay = favs.favorites[channel][0]['autoplay'] if favs.favorites[channel] else False)
        elif 'uri' in params:
            # get fav content
            # xbmc.executebuiltin(f"RunPlugin({b64decode(params['uri'][0])})") # for some reason this won't work
            add_items(favs.get_content(b64decode(params['uri'][0])))
        else:
            log("Unknown params")

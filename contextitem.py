import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import time
import base64
import os

from favmanager import FavManager, ListItem_to_Favorite

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = ADDON.getAddonInfo('path')

def log(message):
    xbmc.log("-----------------"+str(message), level=xbmc.LOGINFO)

def add_favorite(name, options):
    autoplay = True if len(options)<3 else options[2]
    addContent = False if len(options)<3 else options[3]
    return ListItem_to_Favorite(sys.listitem,
                                name,
                                isLive = options[0],
                                isDynamic = options[1],
                                autoplay = autoplay,
                                addContent = addContent)

def create_favorite():
    # Create a dialog window
    dialog = xbmcgui.Dialog()

    # Step 1: Get user input with a text input dialog
    name = dialog.input("Enter favorite name", defaultt=sys.listitem.getLabel(), type=xbmcgui.INPUT_ALPHANUM)
    item = sys.listitem

    if name:
        # Step 2: Display checkboxes using a multi-select dialog
        options = ["Live Channel", "Dynamic preview"] + (["Autoplay first element", "Add content to channel"] if item.isFolder() else [])
        selected = dialog.multiselect("Choose options", options)

        # Step 3: Show the results
        selected_options = [i in selected for i,__ in enumerate(options)]
        return add_favorite(name, selected_options)

    return None


def add_to_channel_dialog(channels):
    # import web_pdb; web_pdb.set_trace()
    # Add "Add new option" to the list dynamically
    dynamic_options = channels + ["[Add to new channel]"]

    # Display dialog
    dialog = xbmcgui.Dialog()
    choice = dialog.select("Select channel", dynamic_options)

    if choice == -1:
        # User cancelled the dialog
        pass
    elif choice == len(dynamic_options) - 1:
        # User chose "Add New Option"
        new_option = dialog.input("Enter new channel name")
        if new_option:
            return new_option, create_favorite()
    else:
        return channels[choice], create_favorite()

    return None, None

if __name__ == '__main__':

    favs = FavManager()
    channel_name, fav = add_to_channel_dialog([channel_name for channel_name in favs.favorites])
    favs.add_to_channel(channel_name, fav)

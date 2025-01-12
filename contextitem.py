import xbmc
import xbmcgui

import sys
from favmanager import FavManager, ListItem_to_Favorite

def log(message):
    xbmc.log("-----------------"+str(message), level=xbmc.LOGINFO)

def add_favorite(name, options):
    autoplay = False#True if len(options)<3 else options[2]
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

def show_confirmation_dialog(params):
    dialog = xbmcgui.Dialog()
    if 'remove_fav' in params:
        return dialog.yesno("Remove", f"Are you sure you want to remove {params['remove_fav']} from favorites?")
    else:
        return dialog.yesno("Remove", f"Are you sure you want to remove {params['remove_channel']} channel?")

if __name__ == '__main__':
    favs = FavManager()
    params = dict(arg.split('=') for arg in sys.argv[1:] if '=' in arg)

    if 'remove_channel' in params:
        if show_confirmation_dialog(params):
            if 'remove_fav' in params:
                favs.remove_from_channel(params['remove_channel'], params['remove_fav'])
            else:
                favs.remove_channel(params['remove_channel'])
            xbmc.executebuiltin("Container.Refresh")
    else:
        channel_name, fav = add_to_channel_dialog([channel_name for channel_name in favs.favorites])
        favs.add_to_channel(channel_name, fav)

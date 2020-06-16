# Update All MiSTer
All-in-one script for keeping up-to-date with the [MiSTer](https://github.com/MiSTer-devel/Main_MiSTer/wiki) ecosystem.

This script chains the following scripts:
1. __Main MiSTer Updater__. Downloads most of cores and firmware. You are able to select between these two options:
    * [Official Main MiSTer Updater](https://github.com/MiSTer-devel/Updater_script_MiSTer) maintained by [Locutus73](https://github.com/Locutus73) in the [MiSTer-devel](https://github.com/MiSTer-devel) organization.
    * [DB9 Fork Main MiSTer Updater](https://github.com/theypsilon/Updater_script_MiSTer_DB9) with [Extended Native Controller Compatibility](https://github.com/theypsilon/Update_All_MiSTer/wiki#extended-native-controller-compatibility) for Genesis and NeoGeo/Supergun controllers. Requires [SNAC8](https://github.com/theypsilon/Update_All_MiSTer/wiki#snac8) compatible adapter.
2. [Jotego Cores Updater](https://github.com/jotego/Updater_script_MiSTer). Downloads many advanced cores made by [Jotego](https://github.com/jotego).
3. [Unofficial Cores Updater](https://github.com/theypsilon/Updater_script_MiSTer_Unofficial). Downloads [some cores](https://github.com/theypsilon/Updater_script_MiSTer_Unofficial/wiki) that are not yet released but are fairly stable. Disabled by default.
4. [LLAPI Cores Updater](https://github.com/theypsilon/Updater_script_MiSTer_Unofficial). Downloads [LLAPI cores](https://github.com/MiSTer-LLAPI/Updater_script_MiSTer/wiki) which are compatible with BlisSTer and [LLAMA](https://github.com/bootsector/LLAMA). Disabled by default.
5. [MAME and HBMAME Getter](https://github.com/MAME-GETTER/MiSTer_MAME_SCRIPTS) download roms from https://archive.org/
6. [Arcade Organizer](https://github.com/MAME-GETTER/_arcade-organizer). Creates a folder structure under `_Arcade/_Organized` for easy navigation to all the MRA files.

This script also contains some snippets from the __Updater script__ maintained by [Locutus73](https://github.com/Locutus73).

__MAME__ and __HBMAME Getters__ and __Arcade Organizer__ scripts are maintained by [amoore2600](https://www.youtube.com/channel/UC_IynEJIMqkYaCVjEk_EIlg).

## Setup

Download the file [update_all.sh](https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/update_all.sh) and place it in the `/Scripts` folder of your primary SD card.

Then turn on your __MiSTer__, go to the _Scripts_ section and run this script from there.

It will take around 30 minutes the first time you run it, but later runs should take much less time.

## Optimization

The __MAME__ and __HBMAME Getters__ are skipped if the __Updaters__ haven't downloaded any *MRA* in the current run.

If the __Updaters__ have downloaded standard *MRAs*, __MAME Getter__ will be executed if enabled.

If the __Updaters__ have downloaded any `MRA-Alternatives.zip` file, __HBMAME Getter__ will be executed if enabled.

__Arcade Organizer__ is also skipped if the __Updaters__ haven't downloaded any *MRA*.

Logs are checked to determine if the __Updaters__ downloaded *MRA* files or not.

## Configuration

You may create a `update_all.ini` file sitting next to where you have downloaded `update_all.sh`. In case you renamed `update_all.sh` you need to rename its .INI file too, so they both share the same basename.

You may change the following parameters:

```bash
# Base directory for all script’s tasks, "/media/fat" for SD root, "/media/usb0" for USB drive root.
BASE_PATH="/media/fat"

# Selects Main MiSTer Updater to be used.
## "false" to use the Official Main MiSTer Updater.
## "true" to use the DB9 Fork Main MiSTer Updater
## "dialog" to choose between both when you run this script first time.
ENCC_FORKS="dialog"

# "false" to skip the Main Updater entirely
MAIN_UPDATER="true"
# Specific INI settings for this script if you need it.
MAIN_UPDATER_INI="/media/fat/Scripts/update_all.ini"

# "false" to skip Jotego Updater entirely
JOTEGO_UPDATER="true"
# Specific INI settings for this script if you need it.
JOTEGO_UPDATER_INI="/media/fat/Scripts/update_all.ini"

# "true" to activate the unofficial cores Updater
UNOFFICIAL_UPDATER="false"
# Specific INI settings for this script if you need it.
UNOFFICIAL_UPDATER_INI="/media/fat/Scripts/update_all.ini"

# "true" to activate the LLAPI Updater
LLAPI_UPDATER="false"
# Specific INI settings for this script if you need it.
LLAPI_UPDATER_INI="/media/fat/Scripts/update_all.ini"

# "false" to skip downloading MAME roms.
MAME_GETTER="true"
# Specific INI settings for this script if you need it.
MAME_GETTER_INI="/media/fat/Scripts/update_mame-getter.ini"

# "false" to skip downloading HBMAME roms.
HBMAME_GETTER="true"
# Specific INI settings for this script if you need it.
HBMAME_GETTER_INI="/media/fat/Scripts/update_hbmame-getter.ini"

# "false" to skip running the arcade organizer.
ARCADE_ORGANIZER="true"
# Specific INI settings for this script if you need it.
ARCADE_ORGANIZER_INI="/media/fat/Scripts/update_arcade-organizer.ini"

# "false" to not reboot automatically after a system component has been updated.
# System component here means menu.rbf, MiSTer binary, Linux, and such.
AUTOREBOOT="true"

# Waiting time between scripts.
WAIT_TIME_FOR_READING=4

###########################
# Troubleshooting Options #
###########################

# Network resilience parameters
CURL_RETRY="--connect-timeout 15 --max-time 120 --retry 3 --retry-delay 5 --silent --show-error"
ALLOW_INSECURE_SSL="true"

# This will ignore optimizations and will always try to download ALL needed mame roms.
# Use it if some roms are not being downloaded, and you don't know why.
# Will become obsolete once MAME-GETTER has its own optimization logic.
MAME_GETTER_FORCE_FULL_RESYNC="false"
# This will ignore optimizations and will always try to download ALL needed hbmame roms.
# Use it if some roms are not being downloaded, and you don't know why.
# Will become obsolete once HBMAME-GETTER has its own optimization logic.
HBMAME_GETTER_FORCE_FULL_RESYNC="false"
# This will ignore optimizations and will always try to organize ALL installed MRAs.
# Use it if some MRAs are not being organized, and you don't know why.
# Will become obsolete once Arcade Organizer has its own optimization logic.
ARCADE_ORGANIZER_FORCE_FULL_RESYNC="false"
```
## Funding

Consider funding [Alexey Melnikov "Sorgelig"](https://www.patreon.com/FPGAMiSTer) for his invaluable work on the [MiSTer project](https://github.com/MiSTer-devel/Main_MiSTer/wiki).

## License

Copyright © 2020, [José Manuel Barroso Galindo](https://github.com/theypsilon).
Released under the [GPL v3 License](LICENSE).

# Update All
All-in-one script for keeping up-to-date with the [MiSTer](https://github.com/MiSTer-devel/Main_MiSTer/wiki) ecosystem.

This script chains the following scripts:
1. __Main MiSTer Updater__. Downloads most of cores and firmware. You are able to select between these two options:
    * [Official Main MiSTer Updater](https://github.com/MiSTer-devel/Updater_script_MiSTer) maintained by [Locutus73](https://github.com/Locutus73) in the [MiSTer-devel](https://github.com/MiSTer-devel) organization.
    * [DB9 Fork Main MiSTer Updater](https://github.com/theypsilon/Updater_script_MiSTer_DB9) with [Extended Native Controller Compatibility](https://github.com/theypsilon/Update_All_MiSTer/wiki#extended-native-controller-compatibility) for Genesis and NeoGeo/Supergun controllers. Requires [SNAC8](https://github.com/theypsilon/Update_All_MiSTer/wiki#snac8) compatible adapter.
2. [Jotego Cores Updater](https://github.com/jotego/Updater_script_MiSTer). Downloads many advanced cores made by [Jotego](https://github.com/jotego).
3. [Unofficial Cores Updater](https://github.com/theypsilon/Updater_script_MiSTer_Unofficial). Downloads [some cores](https://github.com/theypsilon/Updater_script_MiSTer_Unofficial/wiki) that are not yet released but are fairly stable. Disabled by default.
4. [LLAPI Cores Updater](https://github.com/MiSTer-LLAPI/Updater_script_MiSTer). Downloads [LLAPI cores](https://github.com/MiSTer-LLAPI/Updater_script_MiSTer/wiki) which are compatible with BlisSTer and [LLAMA](https://github.com/bootsector/LLAMA). Disabled by default.
5. [BIOS Getter](https://github.com/MAME-GETTER/MiSTer_BIOS_SCRIPTS) download bios for your installed systems from https://archive.org/
6. [MAME and HBMAME Getter](https://github.com/MAME-GETTER/MiSTer_MAME_SCRIPTS) download roms from https://archive.org/
7. [Names TXT Updater](https://github.com/theypsilon/Names_TXT_Updater_MiSTer). Downloads a community curated names.txt file that enables better core names in the menus.
8. [Arcade Organizer](https://github.com/MAME-GETTER/_arcade-organizer). Creates a folder structure under `_Arcade/_Organized` for easy navigation to all the MRA files.

This script also contains some snippets from the __Updater script__ maintained by [Locutus73](https://github.com/Locutus73).

__BIOS__, __MAME__ and __HBMAME Getters__ and __Arcade Organizer__ scripts are maintained by [amoore2600](https://www.youtube.com/channel/UC_IynEJIMqkYaCVjEk_EIlg).



## Setup

Download this [ZIP file](https://github.com/theypsilon/Update_All_MiSTer/raw/master/setups/update_all.zip) and extract `update_all.sh` to your `/Scripts` folder on your primary SD card.

Then turn on your __MiSTer__, go to the _Scripts_ menu and run this script from there.

It will take around 30 minutes the first time you run it, but later runs should take much less time.



## Alternative Setups

Other setups that might be useful for you:
- [DB9/SNAC8 ZIP](https://github.com/theypsilon/Update_All_MiSTer/raw/master/setups/update_all_db9_snac8.zip): Enables [Extended Native Controller Compatibility](https://github.com/theypsilon/Update_All_MiSTer/wiki#extended-native-controller-compatibility) for Genesis and NeoGeo/Supergun controllers.
- [usb0 ZIP](https://github.com/theypsilon/Update_All_MiSTer/raw/master/setups/update_all_usb0.zip): For people using USB as primary storage. You will be able to run this script from there and install all cores, roms, and MRAs on `/media/usb0`.


NOTE: You should extract also `update_all.ini` in these.



## Offline Setup

Check [updater-pc](./updater-pc) to download all the MiSTer files from your PC.

Useful if you can't connect your MiSTer to internet.



## Further Configuration

In case you would like to modify options by hand, you can create a `update_all.ini` file sitting next to where you have downloaded `update_all.sh`. In case you renamed `update_all.sh` you need to rename its INI file too, so they both share the same basename.

You may change the following parameters:

```bash
# Base directory for all script’s tasks, "/media/fat" for SD root, "/media/usb0" for USB drive root.
BASE_PATH="/media/fat"

# Selects Main MiSTer Updater to be used.
## "false" to use the Official Main MiSTer Updater.
## "true" to use the DB9 Fork Main MiSTer Updater
ENCC_FORKS="false"

# "false" to skip the Main Updater entirely
MAIN_UPDATER="true"
# Specific INI settings for this script if you need it.
MAIN_UPDATER_INI="update_all.ini"

# "false" to skip Jotego Updater entirely
JOTEGO_UPDATER="true"
# Specific INI settings for this script if you need it.
JOTEGO_UPDATER_INI="update_all.ini"

# "true" to activate the unofficial cores Updater
UNOFFICIAL_UPDATER="false"
# Specific INI settings for this script if you need it.
UNOFFICIAL_UPDATER_INI="update_all.ini"

# "true" to activate the LLAPI Updater
LLAPI_UPDATER="false"
# Specific INI settings for this script if you need it.
LLAPI_UPDATER_INI="update_all.ini"

# "false" to skip downloading BIOS for some systems.
BIOS_GETTER="true"
# Specific INI settings for this script if you need it.
BIOS_GETTER_INI="update_bios-getter.ini"

# "false" to skip downloading MAME roms.
MAME_GETTER="true"
# Specific INI settings for this script if you need it.
MAME_GETTER_INI="update_mame-getter.ini"

# "false" to skip downloading HBMAME roms.
HBMAME_GETTER="true"
# Specific INI settings for this script if you need it.
HBMAME_GETTER_INI="update_hbmame-getter.ini"

# "true" to enable the names.txt Updater
NAMES_TXT_UPDATER="false"
# Specific INI settings for this script if you need it.
NAMES_TXT_UPDATER_INI="update_names-txt.ini"
# Sets the downloaded names.txt Region Code to "US", "EU" or "JP"
NAMES_REGION="US"
# Sets the downloaded names.txt Char Code to "CHAR18" or "CHAR28"
NAMES_CHAR_CODE="CHAR18"
# Sets the downloaded names.txt Sort Code to "Manufacturer" or "Common"
NAMES_SORT_CODE="Common"

# "false" to skip running the arcade organizer.
ARCADE_ORGANIZER="true"
# Specific INI settings for this script if you need it.
ARCADE_ORGANIZER_INI="update_arcade-organizer.ini"

# "false" to not reboot automatically after a system component has been updated.
# System component here means menu.rbf, MiSTer binary, Linux, and such.
AUTOREBOOT="true"

# Waiting time between scripts.
WAIT_TIME_FOR_READING=4

###########################
# Troubleshooting Options #
###########################

# Network resilience parameters
CURL_RETRY="--connect-timeout 15 --max-time 240 --retry 3 --retry-delay 5 --silent --show-error"
ALLOW_INSECURE_SSL="true"
```



## Optimizations

The __MAME__ and __HBMAME Getters__ are skipped if no new MRA are detected in the device.

If there are new MRAs that contains MAME roms, __MAME Getter__ will be executed if enabled.

If there are new MRAs that contains HBMAME roms, __HBMAME Getter__ will be executed if enabled.

__Arcade Organizer__ is also skipped if there isn't any new MRA.

## Funding

Consider funding [Alexey Melnikov "Sorgelig"](https://www.patreon.com/FPGAMiSTer) for his invaluable work on the [MiSTer project](https://github.com/MiSTer-devel/Main_MiSTer/wiki).



## License

Copyright © 2020, [José Manuel Barroso Galindo](https://github.com/theypsilon).
Released under the [GPL v3 License](LICENSE).



## Warning

I take no responsibility for any data loss or any damage you may incur because of the usage of this script.

Please check the README.md of the scripts being called by Update All:

https://github.com/MiSTer-devel/Updater_script_MiSTer<br>
https://github.com/theypsilon/Updater_script_MiSTer_DB9<br>
https://github.com/jotego/Updater_script_MiSTer<br>
https://github.com/theypsilon/Updater_script_MiSTer_Unofficial<br>
https://github.com/MiSTer-LLAPI/Updater_script_MiSTer<br>
https://github.com/MAME-GETTER/MiSTer_MAME_SCRIPTS<br>
https://github.com/MAME-GETTER/_arcade-organizer<br>

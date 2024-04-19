# Update All ![ViewCount](https://views.whatilearened.today/views/github/theypsilon/Update_All_MiSTer.svg) ![GitHub all releases](https://img.shields.io/github/downloads/theypsilon/Update_All_MiSTer/total) ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/theypsilon/Update_All_MiSTer/build.yml?branch=master) <span class="badge-patreon"><a href="https://patreon.com/theypsilon" title="Donate to this project using Patreon"><img src="https://img.shields.io/badge/patreon-donate-yellow.svg" alt="Patreon donate button" /></a></span> [![Twitter](https://img.shields.io/twitter/url/https/twitter.com/josembarroso.svg?style=social&label=Follow%20%40josembarroso)](https://twitter.com/josembarroso)
All-in-one script for keeping up-to-date with the [MiSTer](https://github.com/MiSTer-devel/Main_MiSTer/wiki) ecosystem.

This script runs the [__MiSTer Downloader__](https://github.com/MiSTer-devel/Downloader_MiSTer/) under the hood. It expands it by selecting additional downloader databases.

Update All has a Settings Screen that allows you to configure which databases and tools you want to use. In said screen the menu includes:
1. __Main Distribution__. Downloads most essential files, including cores and firmware. You are able to select between two versions:
    * The [official MiSTer Distribution](https://github.com/MiSTer-devel/Distribution_MiSTer) in the [MiSTer-devel](https://github.com/MiSTer-devel) organization. **[Default option]**
    * The [DB9 Fork MiSTer Distribution](https://github.com/MiSTer-DB9/Distribution_MiSTer) with [Extended Native Controller Compatibility](https://github.com/theypsilon/Update_All_MiSTer/wiki#extended-native-controller-compatibility) for Genesis and NeoGeo/Supergun controllers. *Requires [SNAC8](https://github.com/theypsilon/Update_All_MiSTer/wiki#snac8) compatible adapter.*
2. [JTCORES for MiSTer](https://github.com/jotego/jtcores_mister). Downloads many cores made by [Jotego Team](https://github.com/jotego). **[Default option]** 
    * You may additionally enable patreon-only cores.
3. [Coin-Op Collection](https://github.com/Coin-OpCollection/Distribution-MiSTerFPGA). Downloads cores developed by [the Coin-Op Collection organization](https://github.com/Coin-OpCollection). **[Default option]**
4. **Other Cores**. A selection of curated databases that provide unofficial cores, including:
    * [Arcade Offset](https://github.com/toryalai1/Arcade_Offset). Downloads patched arcade games curated by [Toya](https://github.com/toryalai1). **[Disabled by default]**
    * [LLAPI Forks Folder](https://github.com/MiSTer-LLAPI/LLAPI_folder_MiSTer). Downloads [LLAPI cores](https://github.com/MiSTer-LLAPI/Updater_script_MiSTer/wiki) which are compatible with BlisSTer and [LLAMA](https://github.com/bootsector/LLAMA). **[Disabled by default]**
    * And more...
5. **Other Tools & Scripts**. Additional tools & scripts.
    * [Arcade Organizer](https://github.com/theypsilon/_arcade-organizer). Creates a folder structure under `_Arcade/_Organized` for easy navigation to all the MRA files. **[Default option]**
    * [Names TXT](https://github.com/ThreepwoodLeBrush/Names_MiSTer). Downloads a complete names.txt file curated by [Threepwood](https://github.com/ThreepwoodLeBrush) that enables better core names in the menus. **[Disabled by default]**
    * And more...
6. **Extra Content**. A selection of curated databases that provide extra content.
    * [BIOS Database](https://github.com/BigDendy/BiosDB_MiSTer). Downloads bios from https://archive.org/ for your installed systems. **[Disabled by default]**
    * [Arcade ROMs Database](https://github.com/BigDendy/ArcadeROMsDB_MiSTer). Downloads arcade roms from https://archive.org/ that are compatible with MRAs. **[Disabled by default]**
    * And more...
7. **Analogue Pocket**. Tools to connect your MiSTer with your Analogue Pocket.
8. **Patron Menu**. A menu with exclusive contents for members of my Patreon community.

## Setup

Download this [ZIP file](https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all.zip) and extract `update_all.sh` to your `/Scripts` folder on your primary SD card.

Then turn on your __MiSTer__, go to the _Scripts_ menu and run this script from there.

It will take around 15 minutes the first time you run it, but later runs should take much less time.


## Accessing the Settings Screen

![settings screen](https://github.com/theypsilon/Update_All_MiSTer/raw/master/setups/menu-2-1.jpg "Settings Screen")

The Settings screen will show up if you press UP in your controller or keyboard during the countdown showing up right after starting `update_all.sh` in your MiSTer. Please, don't forget to select `SAVE` to keep all the changes you have done before leaving.



## PC Launcher (for Windows, Mac, and Linux)

Check [MiSTer Downloader's PC Launcher](https://github.com/MiSTer-devel/Downloader_MiSTer/blob/main/docs/pc-launcher.md) to download all MiSTer files on your PC.
Useful if you can't connect your MiSTer to the internet.

To install the same files that you get with Update All, use the same `downloader.ini` file that you have in your MiSTer at the root of the SD card. Keep in mind that Update All writes into that file every time you change something in the Settings Screen.


## Funding

Consider funding [Alexey Melnikov "Sorgelig"](https://www.patreon.com/FPGAMiSTer) for his invaluable work on the [MiSTer project](https://github.com/MiSTer-devel/Main_MiSTer/wiki).

Check also other core developers that you might want to support:
* [Sergey Dvodnenko "srg320"](https://www.patreon.com/srg320)
* [José Tejada "jotego"](https://www.patreon.com/jotego)
* [Robert Peip "FPGAzumSpass"](https://www.patreon.com/FPGAzumSpass)
* [Josh Bassett "nullobject"](https://www.patreon.com/nullobject)
* [MiSTer-X](https://www.patreon.com/MrX_8B)
* [furrtek](https://www.patreon.com/furrtek)
* [Ace](https://ko-fi.com/ace9921)
* [Blackwine](https://www.patreon.com/blackwine)
* [atrac17](https://www.patreon.com/atrac17)
* [Darren](https://ko-fi.com/darreno)

And finally, if you would like to support my work, you may also subscribe to my patreon here: https://www.patreon.com/bePatron?u=37499475


## Supporters+ shout-out!

Blum Chillins, Daniel Tarsky, Koala Koa, Tony Escobar, turbochop3300 and Wayne Booker

Thank you so much for supporting this project on [Patreon](https://www.patreon.com/bePatron?u=37499475)! You'll show up here if you become a **Supporter+**!

Special thanks to [Locutus73](https://github.com/Locutus73) for all his great work on the older [__Updater script__](https://github.com/MiSTer-devel/Updater_script_MiSTer). That __Updater script__ is no longer used by __Update All__ but it was an amazing source of inspiration.

## License

Copyright © 2020-2024, [José Manuel Barroso Galindo](https://twitter.com/josembarroso). 
Released under the [GPL v3 License](LICENSE).



## Warning

MiSTer Scripts are run with root access in a pretty powerful device that has internet access. Be careful and do proper research before running any script on your device.

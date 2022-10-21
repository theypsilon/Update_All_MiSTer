# Update All ![ViewCount](https://views.whatilearened.today/views/github/theypsilon/Update_All_MiSTer.svg) [![Twitter](https://img.shields.io/twitter/url/https/twitter.com/josembarroso.svg?style=social&label=Follow%20%40josembarroso)](https://twitter.com/josembarroso) <span class="badge-buymeacoffee"><a href="https://ko-fi.com/theypsilon" title="Buy Me a Coffee at ko-fi.com'"><img src="https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg" alt="Buy Me a Coffee at ko-fi.com'" /></a></span>
All-in-one script for keeping up-to-date with the [MiSTer](https://github.com/MiSTer-devel/Main_MiSTer/wiki) ecosystem.

This script runs the [__MiSTer Downloader__](https://github.com/MiSTer-devel/Downloader_MiSTer/) tool configured with the following databases:
1. __Main Distribution__. Downloads most essential files, including cores and firmware. You are able to select between two versions:
    * The [official MiSTer Distribution](https://github.com/MiSTer-devel/Distribution_MiSTer) in the [MiSTer-devel](https://github.com/MiSTer-devel) organization. **[Default option]**
    * The [DB9 Fork MiSTer Distribution](https://github.com/MiSTer-DB9/Distribution_MiSTer) with [Extended Native Controller Compatibility](https://github.com/theypsilon/Update_All_MiSTer/wiki#extended-native-controller-compatibility) for Genesis and NeoGeo/Supergun controllers. *Requires [SNAC8](https://github.com/theypsilon/Update_All_MiSTer/wiki#snac8) compatible adapter.*
2. __JTCORES for MiSTer__. Downloads many cores made by [Jotego](https://github.com/jotego). You may select between two versions:
    * [jtcores](https://github.com/jotego/jtcores_mister). Public cores only. **[Default option]**
    * [jtpremium](https://github.com/jotego/jtpremium). Public + patreon-only cores in their latest versions.
3. [Names TXT](https://github.com/ThreepwoodLeBrush/Names_MiSTer). Downloads a complete names.txt file curated by [Threepwood](https://github.com/ThreepwoodLeBrush) that enables better core names in the menus. **[Disabled by default]**
4. [BIOS Database](https://github.com/theypsilon/BiosDB_MiSTer). Downloads bios from https://archive.org/ for your installed systems. **[Disabled by default]**
5. [Arcade ROMs Database](https://github.com/theypsilon/ArcadeROMsDB_MiSTer). Downloads arcade roms from https://archive.org/ that are compatible with MRAs. **[Disabled by default]**
6. **Unofficial Cores**. A selection of curated databases that provide unofficial cores, including:
   1. [Coin-Op Collection](https://github.com/atrac17/Coin-Op_Collection). Downloads cores developed by [Darren](https://github.com/va7deo) and [atrac17](https://github.com/atrac17). **[Disabled by default]**
   2. [Arcade Offset](https://github.com/atrac17/Arcade_Offset). Downloads patched arcade games curated by [atrac17](https://github.com/atrac17). **[Disabled by default]**
   3. [LLAPI Forks Folder](https://github.com/MiSTer-LLAPI/LLAPI_folder_MiSTer). Downloads [LLAPI cores](https://github.com/MiSTer-LLAPI/Updater_script_MiSTer/wiki) which are compatible with BlisSTer and [LLAMA](https://github.com/bootsector/LLAMA). **[Disabled by default]**
8. **Unofficial Scripts**. A selection of curated databases that provide unofficial scripts.  **[Disabled by default]**


Additionally, this script also runs the [Arcade Organizer](https://github.com/theypsilon/_arcade-organizer). Which creates a folder structure under `_Arcade/_Organized` for easy navigation to all the MRA files.


## Setup

Download this [ZIP file](https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all.zip) and extract `update_all.sh` to your `/Scripts` folder on your primary SD card.

Then turn on your __MiSTer__, go to the _Scripts_ menu and run this script from there.

It will take around 30 minutes the first time you run it, but later runs should take much less time.


## Further Configuration

In case you would like to configure Update All so it downloads exactly what you need, you can do it through the Settings screen.

![settings screen](https://github.com/theypsilon/Update_All_MiSTer/raw/master/setups/menu-2-0.jpeg "Settings Screen")

The Settings screen will show up if you press UP in your controller or keyboard during the countdown showing up right after starting `update_all.sh` in your MiSTer. Please, don't forget to select `SAVE` to keep all the changes you have done before leaving.



## MiSTer Offline Setup

Check [updater-pc](./updater-pc) to download all the MiSTer files from your PC.
Useful if you can't connect your MiSTer to internet.


## Funding

Consider funding [Alexey Melnikov "Sorgelig"](https://www.patreon.com/FPGAMiSTer) for his invaluable work on the [MiSTer project](https://github.com/MiSTer-devel/Main_MiSTer/wiki).

Check also other core developers that you might want to support:
* [Sergey Dvodnenko "srg320"](https://www.patreon.com/srg320)
* [José Tejada "jotego"](https://www.patreon.com/topapate)
* [Robert Peip "FPGAzumSpass"](https://www.patreon.com/FPGAzumSpass)
* [Josh Bassett "nullobject"](https://www.patreon.com/nullobject)
* [MiSTer-X](https://www.patreon.com/MrX_8B)
* [furrtek](https://www.patreon.com/furrtek)
* [Ace](https://ko-fi.com/ace9921)
* [Blackwine](https://www.patreon.com/blackwine)
* [atrac17](https://www.patreon.com/atrac17)
* [Darren](https://ko-fi.com/darreno)

And finally, if you would like to support my work, you may also subscribe to my patreon here:

<a href="https://www.patreon.com/bePatron?u=37499475"><img src="https://camo.githubusercontent.com/2b7105015397da52617ce6775a339b0b99d689d6f644c2ce911c5d472362bcbd/68747470733a2f2f63352e70617472656f6e2e636f6d2f65787465726e616c2f6c6f676f2f6265636f6d655f615f706174726f6e5f627574746f6e2e706e67"></img></a>



## Supporters+ shout-out!

atrac17, birdybro, Hard Rich, MiSTerFPGA.co.uk and Tony Escobar

Thank you so much for supporting this project on [Patreon](https://www.patreon.com/bePatron?u=37499475)! You'll show up here if you become a **Supporter+**!

Special thanks to [Locutus73](https://github.com/Locutus73) for all his great work on the older [__Updater script__](https://github.com/MiSTer-devel/Updater_script_MiSTer). That __Updater script__ is no longer used by __Update All__ but it was an amazing source of inspiration.

## License

Copyright © 2020-2022, [José Manuel Barroso Galindo](https://twitter.com/josembarroso). 
Released under the [GPL v3 License](LICENSE).



## Warning

MiSTer Scripts are run with root access in a pretty powerful device that has internet access. Be careful and do proper research before running any script on your device.

# Update All ![ViewCount](https://views.whatilearened.today/views/github/theypsilon/Update_All_MiSTer.svg) [![Twitter](https://img.shields.io/twitter/url/https/twitter.com/josembarroso.svg?style=social&label=Follow%20%40josembarroso)](https://twitter.com/josembarroso) <span class="badge-buymeacoffee"><a href="https://ko-fi.com/theypsilon" title="Buy Me a Coffee at ko-fi.com'"><img src="https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg" alt="Buy Me a Coffee at ko-fi.com'" /></a></span>
All-in-one script for keeping up-to-date with the [MiSTer](https://github.com/MiSTer-devel/Main_MiSTer/wiki) ecosystem.

This script runs the [__MiSTer Downloader__](https://github.com/MiSTer-devel/Downloader_MiSTer/) tool configured with the following databases:
1. __Main Distribution__. Downloads most essential files, including cores and firmware. You are able to select between two versions:
    * The [official MiSTer Distribution](https://github.com/MiSTer-devel/Distribution_MiSTer) in the [MiSTer-devel](https://github.com/MiSTer-devel) organization. **[Default option]**
    * The [DB9 Fork MiSTer Distribution](https://github.com/MiSTer-DB9/Distribution_MiSTer) with [Extended Native Controller Compatibility](https://github.com/theypsilon/Update_All_MiSTer/wiki#extended-native-controller-compatibility) for Genesis and NeoGeo/Supergun controllers. *Requires [SNAC8](https://github.com/theypsilon/Update_All_MiSTer/wiki#snac8) compatible adapter.*
2. __JTCORES for MiSTer__. Downloads many cores made by [Jotego](https://github.com/jotego). You may select between two versions:
    * [JTSTABLE](https://github.com/JTFPGA/JTSTABLE). Stable cores only. **[Default option]**
    * [jtbin](https://github.com/jotego/jtcores_mister). Stable + Beta cores in their latest versions.
4. [theypsilon Unofficial Distribution](https://github.com/theypsilon/Unofficial_Distribution_MiSTer/tree/main). Downloads [some cores](https://github.com/theypsilon/Updater_script_MiSTer_Unofficial/wiki) that are not yet released but are fairly stable. **[Disabled by default]**
5. [LLAPI Folder](https://github.com/MiSTer-LLAPI/LLAPI_folder_MiSTer). Downloads [LLAPI cores](https://github.com/MiSTer-LLAPI/Updater_script_MiSTer/wiki) which are compatible with BlisSTer and [LLAMA](https://github.com/bootsector/LLAMA). **[Disabled by default]**
6. [Arcade Offset](https://github.com/atrac17/Arcade_Offset). Downloads patched arcade games curated by [atrac17](https://github.com/atrac17). **[Disabled by default]**
7. [Names TXT](https://github.com/ThreepwoodLeBrush/Names_MiSTer). Downloads a complete names.txt file curated by [Threepwood](https://github.com/ThreepwoodLeBrush) that enables better core names in the menus. **[Disabled by default]**

Additionally, this script also chains the following scripts:
1. [BIOS Getter](https://github.com/theypsilon/MiSTer_BIOS_SCRIPTS) download bios for your installed systems from https://archive.org/
2. [MAME and HBMAME Getter](https://github.com/atrac17/MiSTer_MAME_SCRIPTS) download roms from https://archive.org/
3. [Arcade Organizer](https://github.com/theypsilon/_arcade-organizer). Creates a folder structure under `_Arcade/_Organized` for easy navigation to all the MRA files.

Special thanks to [Locutus73](https://github.com/Locutus73) for all his great work on the older [__Updater script__](https://github.com/MiSTer-devel/Updater_script_MiSTer). That __Updater script__ is no longer used by __Update All__ by default.


## Setup

Download this [ZIP file](https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all.zip) and extract `update_all.sh` to your `/Scripts` folder on your primary SD card.

Then turn on your __MiSTer__, go to the _Scripts_ menu and run this script from there.

It will take around 30 minutes the first time you run it, but later runs should take much less time.



## Alternative Setups

Other setups that might be useful for you:
- [JTBIN ZIP](https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all_jtbin.zip): Users that would like to download @jotego betas by default, can use this setup instead. You may also enable this option from the `Settings Screen` in the "Jotego Updater" submenu.
- [usb0 ZIP](https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all_usb0.zip): For people using USB as primary storage. You will be able to run this script from there and install all cores, roms, and MRAs on `/media/usb0`.
- [DB9/SNAC8 ZIP](https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all_db9_snac8.zip): Enables [Extended Native Controller Compatibility](https://github.com/theypsilon/Update_All_MiSTer/wiki#extended-native-controller-compatibility) for Genesis and NeoGeo/Supergun controllers.


NOTE: You should extract also all the INI files contained in these.



## MiSTer Offline Setup

Check [updater-pc](./updater-pc) to download all the MiSTer files from your PC.

Useful if you can't connect your MiSTer to internet.



## Further Configuration

In case you would like to configure Update All so it downloads exactly what you need, you can do it through the Settings screen.

![settings screen](https://github.com/theypsilon/Update_All_MiSTer/raw/master/setups/menu-1-4.jpeg "Settings Screen")

The Settings screen will show up if you press UP in your controller or keyboard during the countdown showing up right after starting `update_all.sh` in your MiSTer. Please, don't forget to select `SAVE` to keep all the changes you have done before leaving.



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

And finally, if you would like to support my work, you may also subscribe to my patreon here:

<a href="https://www.patreon.com/bePatron?u=37499475"><img src="https://camo.githubusercontent.com/2b7105015397da52617ce6775a339b0b99d689d6f644c2ce911c5d472362bcbd/68747470733a2f2f63352e70617472656f6e2e636f6d2f65787465726e616c2f6c6f676f2f6265636f6d655f615f706174726f6e5f627574746f6e2e706e67"></img></a>



## Supporters+ shout-out!

Antonio Villena, birdybro, J-f Gourin, Matt Hargett and Visa-Valtteri Pimiä

Thank you so much for supporting this project on [Patreon](https://www.patreon.com/bePatron?u=37499475)! You'll show up here if you become a **Supporter+**!



## License

Copyright © 2020-2021, [José Manuel Barroso Galindo](https://twitter.com/josembarroso). 
Released under the [GPL v3 License](LICENSE).



## Warning

I take no responsibility for any data loss or any damage you may incur because of the usage of this script.

Please check the README.md of the scripts being called by Update All:

https://github.com/MiSTer-devel/Downloader_MiSTer/<br>
https://github.com/theypsilon/Names_TXT_Updater_MiSTer<br>
https://github.com/atrac17/MiSTer_MAME_SCRIPTS<br>
https://github.com/theypsilon/_arcade-organizer<br>
https://github.com/theypsilon/MiSTer_BIOS_SCRIPTS<br>

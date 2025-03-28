# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## Version 2.2 - 2025-03-28

### Added
- Added update_all_mister database, which contains Update All files to improve the self-update process and enable more utilities to be installed in the future.
- Arcade Organizer is now part of Update All codebase, which improves execution speed, fixes bugs and simplifies maintenance. As result, the Arcade Organizer log now appears in update_all.log.
- New option to enable the distribution_main alternative database from Aitor Gómez which contains his custom version of the firmware (PR by Aitor Gómez).
- It is now possible to install Update All without remote code execution. The new section in the [README.md](README.md#how-to-avoid-executing-remote-code-altogether) shows how to do it.
- Added Patreon shoutout line that prints the supporter of the day at the end of the run.

### Changes
- The new update_all_mister database will be appended to downloader.ini automatically.
- The Arcade Organizer is now using to the new official [ArcadeDatabase](https://github.com/MiSTer-devel/ArcadeDatabase_MiSTer) for the metadata, which is a direct continuation of the work done by Toya, and still maintained by him.
- The downloader log is now correctly written to update_all.log, along with the rest of Update All's output.
- The launcher has been changed:
  - It now takes certificates installed by the distribution_mister database, substantially reducing the possibility of certificate problems.
  - It now runs update_all build faster by avoiding network checks when the build file `update_all.pyz` is present.
- When present, the build file from Downloader `downloader_latest.zip` is used instead of fetching it from the network.
- Optimized build process, which now uses less space and is faster to unzip and run.
- The initial output lines of Update All have been optimized by eliminating some unnecessary waits, resulting in a quicker startup.
- The local store of Update All is now saved in a JSON file instead of a ZIP, making loading and saving processes much faster.
- Enhanced debug script with additional capabilities for maintainers.

### Removed
- Removed deprecated distutils dependency.

## Version 2.1 - 2024-01-06

### Added
- Analogue Pocket menu with 2 utilities: Firmware Update & Backup.
- New Databases: Uberyoji Boot ROMs, RetroSpy, RGarciaLago Wallpaper Collection (by different authors).
- Adding more curl return codes to the SSL certs branch.
- Databases added months ago between releases: agg23's MiSTer Cores.
- Info button on the Other Cores menu.

### Changed
- The Settings Screen has been restructured to accommodate the new databases.
- Using the Arcade ROMs and Bios DBs from BigDendy instead.
- Using the Coin-Op Collection DB from the Coin-Op organization instead.
- Using different branch for MiSTer SAM DB.
- Using jtcores_mister always instead of jtpremium.
- Using raw url on wizzo extensions db_url.
- Options that could lead to copyrighted content display now a warning screen.
- Using curl instead of urllib, to solve some rare connectivity issues.
- More graceful error handling on connection errors.

## Version 2.0 - 2022-10-21

### Added
- Full python rewrite.
- Proper automated test suite with > 50% code coverage.
- New databases: Arcade ROMs DB, Coin-Op Collection, MiSTer SAM, MiSTer Extensions (wizzo), and 2oled DBs.
- New UI engine.
- New Settings Screen structure with friendlier texts.
- Color themes support for the Settings Screen.

### Changed
- More stylized CLI output.

### Removed
- MAME Getter & HBMAME Getter, which are now replaced by the Arcade ROMs DB.
- Following INI files: update_all.ini, update_jtcores.ini, and update_names-txt.ini
- Toggle for coming back to the old updater.
- Option for deleting all cores, as Downloader validation mechanisms makes this unnecessary.
- Support for KEEP_USBMOUNT_CONF option as it's no longer necessary.

## Version 1.4 - 2021-09-17

### Added
- **Downloader support**. Main cores, JT cores, LLAPI cores, and Unofficial cores can be installed now using the new [MiSTer Downloader](https://github.com/MiSTer-devel/Downloader_MiSTer/). New users or old users of *Update All* without custom setups (non-default options at `update.ini`, `update_unofficials.ini`, `update_llapi.ini` or `update_jtcores.ini`, except `DOWNLOAD_BETA_CORES` which doesn't count) will have it activated by default. Old users with custom setups may activate it through the Misc menu, like shown in [this video](https://www.youtube.com/watch?v=0DgLUXY3jvU). Keep in mind though, that your custom options will not be considered by the new Downloader, and everything will be installed at `/media/fat` by now.
- **Arcade Organizer 2.0**. Arcade Organizer changelog is [here](https://github.com/theypsilon/_arcade-organizer/blob/master/CHANGELOG.md). The Settings Screen offers a new Arcade Organizer menu that allows you to change many of the new options from the 2.0 version.
- **Arcade Offset**. Patched MRA files maintained by Atrac17. Check its [repository](https://github.com/atrac17/Arcade_Offset) for more info.
- KEEP_USBMOUNT_CONF option at update_all.ini. When set to true, it will keep the /etc/usbmount/usbmount.conf file between Linux updates.

### Changed
- Linux Updates are now always performed at the end.
- `Scripts/.cache` folder has been renamed to `Scripts/.config`.
- Installation ZIPs are now located at GitHub Releases.
- Minor tweaks and fixes.

## Version 1.3 - 2020-07-29

### Added
- Misc submenu in Settings screen.
- Toggle button in Settings screen to activate/deactivate scripts faster.
- Clean all cores in misc menu. [#9](https://github.com/theypsilon/Update_All_MiSTer/issues/9)
- Option to change Organized folder to _Arcade added.
- Option to change pause time added.
- Option to change countdown time added.
- Settings screen made compatible with updater-pc for windows.
- Added /nopause argument option for updater-pc windows runnables (update_all_win.bat and update_all_win_db9_snac8.bat).
- Added exit code return for updater-pc for windows.
- Added forced Settings screen when file 'settings-on' is present on the folder that contains update_all script. This file will be removed automatically after save.

### Changed
- Optimized MAME Getter, HBMAME Getter and Arcade Organizer for first runs.
- Autoreboot option moved to Misc submenu.
- Default updater INI files for clean setups are now: update.ini, update_jtcores.ini, update_unofficials.ini and update_llapi.ini.
- Removed support for INI options: *MAME_GETTER_FORCE_FULL_RESYNC*, *HBMAME_GETTER_FORCE_FULL_RESYNC*, *ARCADE_ORGANIZER_FORCE_FULL_RESYNC*.
- Fixes in INI handling, now it works correctly in some corner cases that weren't properly covered before.
- Cache files moved from Scripts/.update_all to Scripts/.cache/update_all
- Other minor fixes.

## Version 1.2 - 2020-07-03

### Added
- Settings screen with many options. [#14](https://github.com/theypsilon/Update_All_MiSTer/issues/14)
- Bios getter.
- "names.txt" updater. [#19](https://github.com/theypsilon/Update_All_MiSTer/issues/19)
- Clean folder options in settings menu. [#9](https://github.com/theypsilon/Update_All_MiSTer/issues/9)
- Minor fixes and improvements.
- Added INI options for Settings screen, BIOS Getter and "names.txt" Updater.

### Changed
- Updater for Windows and Linux (updater-pc) includes now dialog and other programs and files, so the Settings screen work there too. Users need to redownload the zip for this update, though.
- Deprecated INI options: *MAME_GETTER_FORCE_FULL_RESYNC*, *HBMAME_GETTER_FORCE_FULL_RESYNC*, *ARCADE_ORGANIZER_FORCE_FULL_RESYNC* (will still work for a few months).

## Version 1.1 - 2020-06-19

### Added
- Updater for Windows and Linux (updater-pc). [#8](https://github.com/theypsilon/Update_All_MiSTer/issues/8)
- LLAPI Updater. [#10](https://github.com/theypsilon/Update_All_MiSTer/issues/10)
- Support for `/media/usb0` [#7](https://github.com/theypsilon/Update_All_MiSTer/issues/7)
- Significant speed improvements, specially for incremental updates.
- Autoreboot. [#5](https://github.com/theypsilon/Update_All_MiSTer/issues/5)
- ZIP setup files, for convenience. [#16](https://github.com/theypsilon/Update_All_MiSTer/issues/16)
- Global log saved at: `/Scripts/.update_all/update_all.log` [#6](https://github.com/theypsilon/Update_All_MiSTer/issues/6)
- Fails if some script fails, and tells you which one failed.
- Deletes the following folders if they are empty: `/games/mame` `/games/hbmame` `/_Arcade/mame` `/_Arcade/hbmame` `/_Arcade/mra_backup`
- Removes broken symlinks in ORGDIR from Arcade Organizer. [#17](https://github.com/theypsilon/Update_All_MiSTer/issues/17) [#18](https://github.com/theypsilon/Update_All_MiSTer/issues/18)
- Added INI options: *MAME_GETTER_FORCE_FULL_RESYNC*, *HBMAME_GETTER_FORCE_FULL_RESYNC*, *ARCADE_ORGANIZER_FORCE_FULL_RESYNC*.

### Changed
- Blue dialog about ENCC_FORKS on first run removed.
- Deprecated INI options: *ALWAYS_ASSUME_NEW_STANDARD_MRA*, *ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA* (will still work for a few months).

## Version 1.0 - 2017-06-7

### Added
- MiSTer-devel Updater.
- DB9 / SNAC8 Updater.
- Jotego Updater.
- Unofficial Updater.
- MAME Getter.
- HBMAME Getter.
- Arcade Organizer.

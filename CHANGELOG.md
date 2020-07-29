# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

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

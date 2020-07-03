# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## Version 1.2 - 2020-07-03

### Added
- Settings screen with many options.
- Bios getter.
- "names.txt" updater.
- Clean folder options in settings menu.
- Minor fixes and improvements.
- Added INI options for Settings screen, BIOS Getter and "names.txt" Updater.

### Changed
- Updater for Windows and Linux (updater-pc) includes now dialog and other programs and files, so the Settings screen work there too.
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

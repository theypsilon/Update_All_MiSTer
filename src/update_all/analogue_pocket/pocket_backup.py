#!/usr/bin/env python3
"""Backup Analogue Pocket saves to MiSTer."""

import configparser
import datetime
import os.path
import shutil
import zipfile
from enum import Enum
from typing import Dict, TypedDict

# TODO: arcade high scores? dunno if that's a thing on AP
# TODO: restore backup to pocket
# TODO: optionally copy backups to other locations (cifs)
# TODO: check disk usage on backup locations
# TODO: check for AP firmware updates?
# TODO: there are also saves stored in the memories/save state folder
# TODO: mister saves/save states on usb/cifs
# TODO: make snapshots max configurable

INI_FILENAME: str = "pocket_backup.ini"
INI_SECTION: str = "pocket_backup"
# backup root location and working directory for operations
BACKUP_FOLDER: str = "/media/fat/pocket"
# storage for previous backups
SNAPSHOTS_FOLDER: str = os.path.join(BACKUP_FOLDER, "snapshots")
# prefix of backup files in snapshots folder
POCKET_BACKUP_PREFIX: str = "pocket-"
MISTER_BACKUP_PREFIX: str = "mister-"
SYNCED_BACKUP_PREFIX: str = "synced-"
# total number of snapshots to keep
SNAPSHOTS_MAX: int = 5

# potential USB mount locations on MiSTer
USB_MOUNTS: list[str] = [
    "/media/usb0",
    "/media/usb1",
    "/media/usb2",
    "/media/usb3",
    "/media/usb4",
    "/media/usb5",
    "/media/usb6",
    "/media/usb7",
]

# TODO: handle other locations
MISTER_SAVES_FOLDER: str = "/media/fat/saves"
MISTER_SAVESTATES_FOLDER: str = "/media/fat/savestates"

# special file telling us it's an AP storage device
POCKET_JSON: str = "Analogue_Pocket.json"
# which folders on the AP to backup
POCKET_BACKUP_FOLDERS: list[str] = [
    "Memories",
    "Saves",
    "Settings",
]

# cores that can be synced between AP and MiSTer (AP platform IDs)
SYNC_CORES: list[str] = [
    "gb",
]

# mapping for AP platform IDs to MiSTer core folder names
# NOTE: many items on this list may not have save files to sync
POCKET_CORES_MAP: Dict[str, list[str]] = {
    "2600": ["Atari2600", "ATARI7800"],
    "7800": ["ATARI7800"],
    "amiga": ["Amiga"],
    "arcadia": ["Arcadia"],
    "arduboy": ["Arduboy"],
    "avision": ["AVision"],
    "channel_f": ["ChannelF"],
    "coleco": ["Coleco"],
    "creativision": ["CreatiVision"],
    "gamate": ["Gamate"],
    "gameandwatch": ["GameNWatch", "Game and Watch"],
    "gb": ["GAMEBOY"],
    "gba": ["GBA"],
    "gbc": ["GBC", "GAMEBOY"],
    "genesis": ["MegaDrive", "Genesis"],
    "gg": ["GameGear", "SMS"],
    "intv": ["Intellivision"],
    "mega_duck": ["MegaDuck"],
    "nes": ["NES"],
    "ng": ["NEOGEO"],
    "odyssey2": ["ODYSSEY2"],
    "pce": ["TGFX16"],
    "pcecd": ["TGFX16-CD"],
    "pdp1": ["PDP1"],
    "poke_mini": ["PokemonMini"],
    "sg1000": ["SG1000", "Coleco", "SMS"],
    "sgb": ["SGB"],
    "sms": ["SMS"],
    "snes": ["SNES"],
    "supervision": ["SuperVision"],
    "tamagotchi_p1": ["Tamagotchi"],
    "wonderswan": ["WonderSwan", "WonderSwanColor"],
}


def reverse_cores_map() -> Dict[str, str]:
    """Reverse the cores map to get a map of MiSTer core folder names to AP platform IDs."""
    reverse_map: Dict[str, str] = {}
    for platform_id, core_folders in POCKET_CORES_MAP.items():
        for core_folder in core_folders:
            reverse_map[core_folder.lower()] = platform_id
    return reverse_map


MISTER_CORES_MAP = reverse_cores_map()


class BackupStatus(Enum):
    """Final status of a file operation during backup job."""

    NEW = 1
    UPDATED = 2
    UNCHANGED = 3
    DELETED = 4


def get_pocket_mount(mounts: list[str]) -> str or None:
    """Search for the Pocket folder in list of mounts and return the first match."""
    for mount in mounts:
        if os.path.exists(os.path.join(mount, POCKET_JSON)):
            return mount
    return None


def backup_pocket_folder(pocket_mount: str, pocket_subfolder: str) -> dict:
    """Copy a folder from the Pocket to the backup location, skipping unchanged files
    and syncing deletions using the Pocket as the source of truth.
    Returns a generator that yields a dict for each file copied, with the result.
    """
    mister_path = os.path.join(BACKUP_FOLDER, pocket_subfolder)
    if not os.path.exists(mister_path):
        os.mkdir(mister_path)

    pocket_path = os.path.join(pocket_mount, pocket_subfolder)

    for root, dirs, files in os.walk(pocket_path):
        # create any missing directories
        for pocket_dir in dirs:
            relative_root = os.path.relpath(root, pocket_path)
            mister_dir = os.path.join(mister_path, relative_root, pocket_dir)

            if not os.path.exists(mister_dir):
                os.mkdir(mister_dir)

        # copy any missing or updated files
        for file in files:
            pocket_file = os.path.join(root, file)
            relative_file = os.path.relpath(pocket_file, pocket_path)
            mister_file = os.path.join(mister_path, relative_file)

            if os.path.exists(mister_file):
                if os.path.getmtime(pocket_file) > os.path.getmtime(mister_file):
                    shutil.copy2(pocket_file, mister_file)
                    yield {
                        "file": file,
                        "status": BackupStatus.UPDATED,
                    }
                else:
                    yield {
                        "file": file,
                        "status": BackupStatus.UNCHANGED,
                    }
            else:
                shutil.copy2(pocket_file, mister_file)
                yield {
                    "file": file,
                    "status": BackupStatus.NEW,
                }

        # delete any files that no longer exist on pocket
        mister_root = os.path.join(mister_path, os.path.relpath(root, pocket_path))
        for file in os.listdir(mister_root):
            pocket_file = os.path.join(root, file)
            mister_file = os.path.join(mister_root, file)

            if not os.path.exists(pocket_file):
                if os.path.isdir(mister_file):
                    shutil.rmtree(mister_file)
                else:
                    os.remove(mister_file)
                yield {
                    "file": file,
                    "status": BackupStatus.DELETED,
                }


def zip_backup(prefix: str):
    """Create a zip file from all backed up folders and save it to the snapshots folder."""
    path = os.path.join(
        SNAPSHOTS_FOLDER,
        prefix + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".zip",
    )
    if os.path.exists(path):
        raise Exception("Snapshot already exists: {}".format(path))

    zipf = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)

    for folder in POCKET_BACKUP_FOLDERS:
        for root, dirs, files in os.walk(os.path.join(BACKUP_FOLDER, folder)):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), BACKUP_FOLDER),
                )

    zipf.close()


def zip_mister():
    """Create a zip file of saves and save states on MiSTer."""
    path = os.path.join(
        SNAPSHOTS_FOLDER,
        MISTER_BACKUP_PREFIX + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".zip",
    )
    if os.path.exists(path):
        raise Exception("Snapshot already exists: {}".format(path))

    zipf = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)

    for folder in [MISTER_SAVES_FOLDER, MISTER_SAVESTATES_FOLDER]:
        for root, dirs, files in os.walk(folder):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), os.path.dirname(folder)),
                )

    zipf.close()


def cleanup_snapshots():
    """Delete old snapshots if we're over the limit."""
    snapshots = os.listdir(SNAPSHOTS_FOLDER)
    for snapshot_type in [POCKET_BACKUP_PREFIX, MISTER_BACKUP_PREFIX, SYNCED_BACKUP_PREFIX]:
        files = [s for s in snapshots if s.startswith(snapshot_type) and s.endswith(".zip")]
        files.sort(reverse=True)
        if len(files) > SNAPSHOTS_MAX:
            for snapshot in files[SNAPSHOTS_MAX:]:
                os.remove(os.path.join(SNAPSHOTS_FOLDER, snapshot))


class Config(TypedDict):
    """User configuration options from .ini file."""

    mounts: list[str]


def get_config() -> Config:
    """Get user configuration options from .ini file."""
    config: Config = {
        "mounts": list(USB_MOUNTS),
    }

    ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), INI_FILENAME)
    if not os.path.exists(ini_path):
        return config

    parser = configparser.ConfigParser()
    parser.read(ini_path)

    if not parser.has_section(INI_SECTION):
        return config

    if parser.has_option(INI_SECTION, "mounts"):
        mounts = config["mounts"]
        for mount in parser.get(INI_SECTION, "mounts").split("|"):
            clean = mount.strip()
            if clean != "" and clean not in mounts:
                mounts.append(clean)
        config["mounts"] = mounts

    return config


def setup():
    """Set up environment for backup jobs."""
    if not os.path.exists(BACKUP_FOLDER):
        os.mkdir(BACKUP_FOLDER)

    if not os.path.exists(SNAPSHOTS_FOLDER):
        os.mkdir(SNAPSHOTS_FOLDER)


def pocket_backup(logger=None):
    """Main entry point for the script."""
    config = get_config()

    pocket_folder = get_pocket_mount(config["mounts"])
    if pocket_folder is None:
        logger.print(
            "Pocket not found, check it's plugged in and USB SD Access is enabled in the Developer menu."
        )
        return False
    else:
        logger.print("Pocket found at: {}".format(pocket_folder))

    setup()

    logger.print("Starting backup...")

    for folder in POCKET_BACKUP_FOLDERS:
        logger.print("Backing up {}...".format(folder), end="", flush=True)

        for result in backup_pocket_folder(pocket_folder, folder):
            if result["status"] == BackupStatus.NEW:
                logger.print("*", end="", flush=True)
            elif result["status"] == BackupStatus.UPDATED:
                logger.print("^", end="", flush=True)
            elif result["status"] == BackupStatus.DELETED:
                logger.print("x", end="", flush=True)
            else:
                logger.print(".", end="", flush=True)

        logger.print("...Done!", flush=True)

    logger.print("Backup complete!", flush=True)

    logger.print("Creating Pocket snapshot...", end="", flush=True)
    zip_backup(POCKET_BACKUP_PREFIX)
    logger.print("Done!", flush=True)

    logger.print("Creating MiSTer snapshot...", end="", flush=True)
    zip_mister()
    logger.print("Done!", flush=True)

    # TODO: sync goes here

    # TODO: create merged snapshot here

    logger.print("Cleaning up old snapshots...", end="", flush=True)
    cleanup_snapshots()
    logger.print("Done!", flush=True)

    return True

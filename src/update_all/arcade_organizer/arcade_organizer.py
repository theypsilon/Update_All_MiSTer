# Copyright (C) 2020-2024 Andrew Moore "amoore2600", José Manuel Barroso Galindo "theypsilon"
# This file is part of the Arcade Organizer
#
# Arcade Organizer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Arcade Organizer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

import sys
import subprocess
from pathlib import Path
import configparser
from inspect import currentframe, getframeinfo
import itertools
import os
import hashlib
import datetime
import difflib
import shutil
import json
import xml.etree.cElementTree as ET
from enum import IntEnum, unique
from typing import List, Dict, Any, Protocol, Tuple

from update_all.other import strtobool


@unique
class BoolFlagPresence(IntEnum):
    DEACTIVATED = 0
    ONLY_IN_OWN_FOLDER = 1
    EVERYWHERE = 2


class IniParser:
    def __init__(self, ini_file_path):
        self._ini_file_path = ini_file_path

    def initialize(self):
        ini_parser = configparser.ConfigParser()
        if self._ini_file_path.is_file():
            try:
                ini_parser.read(self._ini_file_path)
            except:
                with self._ini_file_path.open() as fp:
                    ini_parser.read_file(itertools.chain(['[DEFAULT]'], fp), source=self._ini_file_path)

        self._ini_args = ini_parser['DEFAULT']

    def get_string(self, key, default) -> str:
        result = self._ini_args.get(key, None)
        if result is None:
            return default
        return result.strip('"\' ')

    def get_bool(self, key, default):
        return strtobool(self.get_string(key, 'true' if default else 'false')) == 0

    def get_int(self, key, default):
        result = self.get_string(key, None)
        if result is None:
            return default

        return to_int(result, default)

    def get_bool_flag_presence(self, key, default):
        result = self.get_int(key, None)
        return default if result is None else BoolFlagPresence(result)

    def get_str_list(self, key, default):
        result = [s for s in [s.strip('"\' ') for s in self.get_string(key, '')] if s != '']
        if len(result) > 0:
            return result
        else:
            return default

    def get_int_list(self, key, default):
        result = [s for s in [to_int(s, None) for s in self.get_str_list(key, [])] if s is not None]
        if len(result) > 0:
            return result
        else:
            return default


def to_int(n, default):
    try:
        return int(n)
    except:
        if isinstance(default, Exception):
            raise default
        return default


def to_ini(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, BoolFlagPresence):
        return int(value)
    if value is None:
        return ''
    return value


def guess_arcade_organizer_ini_file() -> str:
    original_script_path = subprocess.run('ps | grep "^ *%s " | grep -o "[^ ]*$"' % os.getppid(), shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE).stdout.decode().strip()
    if original_script_path == '-bash':
        original_script_path = sys.argv[0]
    try:
        ini_file_str = Path(original_script_path).with_suffix('.ini').absolute()
    except ValueError as _:
        ini_file_str = 'wrong_ini_file'

    env_inifile = os.getenv('INI_FILE', None)
    if env_inifile is not None:
        ini_file_str = env_inifile

    return ini_file_str


class ArcadeOrganizerService:
    def __init__(self, printer: 'AoLogger'):
        self._printer = printer

    def make_arcade_organizer_config(self, ini_file_str: str):
        ini_file_path = Path(ini_file_str)
        ini_parser = IniParser(ini_file_path)
        ini_parser.initialize()

        config = dict()
        config['MAD_DB'] = ini_parser.get_string('MAD_DB', "/media/fat/Scripts/.config/arcade-organizer/mad_db.json.zip")
        if config['MAD_DB'] == "https://raw.githubusercontent.com/misteraddons/MiSTer_Arcade_MAD/db/mad_db.json.zip":
            config['MAD_DB'] = "https://raw.githubusercontent.com/theypsilon/misteraddons_Arcade_MAD/db/mad_db.json.zip"
        config['MRADIR'] = ini_parser.get_string('MRADIR', "/media/fat/_Arcade/")
        config['ORGDIR'] = ini_parser.get_string('ORGDIR', "/media/fat/_Arcade/_Organized")
        config['SKIPALTS'] = ini_parser.get_bool('SKIPALTS', True)
        config['VERBOSE'] = ini_parser.get_bool('VERBOSE', False)
        config['AZ_DIR'] = ini_parser.get_bool('AZ_DIR', True)
        config['ARCADE_OFFSET_DIRECTORY'] = "%s_Arcade Offset" % config['MRADIR']
        config['NO_SYMLINKS'] = ini_parser.get_bool('NO_SYMLINKS', False)

        config['REGION_MAIN'] = ini_parser.get_string('REGION_MAIN', 'DEV PREFERRED')
        config['REGION_OTHERS'] = ini_parser.get_bool_flag_presence('REGION_OTHERS', BoolFlagPresence.ONLY_IN_OWN_FOLDER)

        config['RESOLUTION_15KHZ'] = ini_parser.get_bool('RESOLUTION_15KHZ', True)
        config['RESOLUTION_24KHZ'] = ini_parser.get_bool('RESOLUTION_24KHZ', True)
        config['RESOLUTION_31KHZ'] = ini_parser.get_bool('RESOLUTION_31KHZ', True)

        config['ROTATION_0'] = ini_parser.get_bool('ROTATION_0', True)
        config['ROTATION_90'] = ini_parser.get_bool('ROTATION_90', True)
        config['ROTATION_180'] = ini_parser.get_bool('ROTATION_180', True)
        config['ROTATION_270'] = ini_parser.get_bool('ROTATION_270', True)
        config['FLIP'] = ini_parser.get_bool('FLIP', True)

        config['MOVE_INPUTS_NOT_SUPPORTED'] = ini_parser.get_str_list('MOVE_INPUTS_NOT_SUPPORTED', [])
        config['SPECIAL_CONTROLS_NOT_SUPPORTED'] = ini_parser.get_str_list('SPECIAL_CONTROLS_NOT_SUPPORTED', [])
        config['PLAYERS_NOT_SUPPORTED'] = ini_parser.get_int_list('PLAYERS_NOT_SUPPORTED', [])
        config['NUM_BUTTONS_MAXIMUM'] = ini_parser.get_int('NUM_BUTTONS_MAXIMUM', 9999)
        config['YEAR_LOW'] = ini_parser.get_int('YEAR_LOW', 0)
        config['YEAR_HIGH'] = ini_parser.get_int('YEAR_LOW', 9999)
        config['PREPEND_YEAR'] = ini_parser.get_bool('PREPEND_YEAR', False)
        config['DECADES_DIR'] = ini_parser.get_bool('DECADES_DIR', True)

        config['BOOTLEG'] = ini_parser.get_bool_flag_presence('BOOTLEG', BoolFlagPresence.ONLY_IN_OWN_FOLDER)
        config['HOMEBREW'] = ini_parser.get_bool_flag_presence('HOMEBREW', BoolFlagPresence.ONLY_IN_OWN_FOLDER)

        config['ROTATION_DIR'] = ini_parser.get_bool('ROTATION_DIR', True)
        config['RESOLUTION_DIR'] = ini_parser.get_bool('RESOLUTION_DIR', True)
        config['REGION_DIR'] = ini_parser.get_bool('REGION_DIR', True)
        config['YEAR_DIR'] = ini_parser.get_bool('YEAR_DIR', True)
        config['NUM_BUTTONS_DIR'] = ini_parser.get_bool('NUM_BUTTONS_DIR', True)
        config['MOVE_INPUTS_DIR'] = ini_parser.get_bool('MOVE_INPUTS_DIR', True)
        config['PLAYERS_DIR'] = ini_parser.get_bool('PLAYERS_DIR', True)
        config['CORE_DIR'] = ini_parser.get_bool('CORE_DIR', True)
        config['MANUFACTURER_DIR'] = ini_parser.get_bool('MANUFACTURER_DIR', True)
        config['CATEGORY_DIR'] = ini_parser.get_bool('CATEGORY_DIR', True)
        config['SERIES_DIR'] = ini_parser.get_bool('SERIES_DIR', True)
        config['PLATFORM_DIR'] = ini_parser.get_bool('PLATFORM_DIR', True)
        config['SPECIAL_CONTROLS_DIR'] = ini_parser.get_bool('SPECIAL_CONTROLS_DIR', True)
        config['NUM_MONITORS_DIR'] = ini_parser.get_bool('NUM_MONITORS_DIR', True)
        config['BEST_OF_DIR'] = ini_parser.get_bool('BEST_OF_DIR', True)

        config['TOPDIR'] = ini_parser.get_string('TOPDIR', None)

        # config['ALTERNATIVE'] = ini_parser.get_bool('ALTERNATIVE', True)
        # config['SPINNER'] = ini_parser.get_bool('SPINNER', True)
        # config['TRACKBALL'] = ini_parser.get_bool('TRACKBALL', True)
        # config['TWIN_STICK'] = ini_parser.get_bool('TWIN_STICK', True)
        # config['TANK_STICK'] = ini_parser.get_bool('TANK_STICK', True)
        # config['POSITIONAL_STICK'] = ini_parser.get_bool('POSITIONAL_STICK', True)
        # config['TILT_STICK'] = ini_parser.get_bool('TILT_STICK', True)

        config['INI_KEYS'] = list(config)
        config['INI_FILE_PATH'] = ini_file_path
        config['PRINT_SYMLINKS'] = os.getenv('PRINT_SYMLINKS', 'false') == 'true'
        config['REGION_DEV_PREFERRED'] = config['REGION_MAIN'] == 'DEV PREFERRED'

        ###############################

        CACHE_ARCADE_ORGANIZER_PATH = "/media/fat/Scripts/.cache/arcade-organizer"
        CONFIG_ARCADE_ORGANIZER_PATH = "/media/fat/Scripts/.config/arcade-organizer"
        if Path(CACHE_ARCADE_ORGANIZER_PATH).is_dir():
            Path("/media/fat/Scripts/.config").mkdir(parents=True, exist_ok=True)
            shutil.move(CACHE_ARCADE_ORGANIZER_PATH, CONFIG_ARCADE_ORGANIZER_PATH)

        config['ARCADE_ORGANIZER_VERSION'] = "2.0"
        config['ARCADE_ORGANIZER_WORK_PATH'] = os.getenv('ARCADE_ORGANIZER_WORK_PATH', "/media/fat/Scripts/.config/arcade-organizer")
        names_txt_file = os.getenv('ARCADE_ORGANIZER_NAMES_TXT', "/media/fat/Scripts/.config/arcade_names/arcade_names.txt")
        if names_txt_file == "/media/fat/names.txt":
            names_txt_file = "/media/fat/Scripts/.config/arcade_names/arcade_names.txt"
        config['ARCADE_ORGANIZER_NAMES_TXT'] = Path(names_txt_file)
        config['CACHED_DATA_ZIP'] = Path("%s/data.zip" % config['ARCADE_ORGANIZER_WORK_PATH'])
        config['ORGDIR_FOLDERS_FILE'] = Path("%s/orgdir-folders" % config['ARCADE_ORGANIZER_WORK_PATH'])
        config['SSL_SECURITY_OPTION'] = os.getenv('SSL_SECURITY_OPTION', '--insecure')
        config['CURL_RETRY'] = '--max-time 30 --show-error'
        config['TMP_DATA_ZIP'] = "/tmp/data.zip"

        #####Organized Directories#####
        config['ORGDIR_09'] = "%s/_1 0-9" % config['ORGDIR']
        config['ORGDIR_AE'] = "%s/_1 A-E" % config['ORGDIR']
        config['ORGDIR_FK'] = "%s/_1 F-K" % config['ORGDIR']
        config['ORGDIR_LQ'] = "%s/_1 L-Q" % config['ORGDIR']
        config['ORGDIR_RT'] = "%s/_1 R-T" % config['ORGDIR']
        config['ORGDIR_UZ'] = "%s/_1 U-Z" % config['ORGDIR']

        config['ORGDIR_Region'] = "%s/_2 Region" % config['ORGDIR']
        config['ORGDIR_Collections'] = "%s/_3 Collections" % config['ORGDIR']
        config['ORGDIR_VideoNInputs'] = "%s/_4 Video & Inputs" % config['ORGDIR']
        config['ORGDIR_ExtraSoftware'] = "%s/_5 Extra Software" % config['ORGDIR']

        config['ORGDIR_Platform'] = "%s/_1 By Platform" % config['ORGDIR_Collections']
        config['ORGDIR_Core'] = "%s/_2 By MiSTer Core" % config['ORGDIR_Collections']
        config['ORGDIR_Year'] = "%s/_3 By Year" % config['ORGDIR_Collections']
        config['ORGDIR_Category'] = "%s/_4 By Genre" % config['ORGDIR_Collections']
        config['ORGDIR_Manufacturer'] = "%s/_5 By Manufacturer" % config['ORGDIR_Collections']
        config['ORGDIR_Series'] = "%s/_6 By Series" % config['ORGDIR_Collections']
        config['ORGDIR_BestOf'] = "%s/_7 Best-Of Lists" % config['ORGDIR_Collections']

        config['ORGDIR_Resolution'] = "%s/_1 Resolution" % config['ORGDIR_VideoNInputs']
        config['ORGDIR_Rotation'] = "%s/_2 Rotation" % config['ORGDIR_VideoNInputs']
        config['ORGDIR_MoveInputs'] = "%s/_3 Move Inputs" % config['ORGDIR_VideoNInputs']
        config['ORGDIR_NumButtons'] = "%s/_4 Num Buttons" % config['ORGDIR_VideoNInputs']
        config['ORGDIR_SpecialControls'] = "%s/_5 Special Inputs" % config['ORGDIR_VideoNInputs']
        config['ORGDIR_Players'] = "%s/_6 Players" % config['ORGDIR_VideoNInputs']
        config['ORGDIR_Cocktail'] = "%s/_7 Cocktail" % config['ORGDIR_VideoNInputs']
        config['ORGDIR_NumMonitors'] = "%s/_8 Num Monitors" % config['ORGDIR_VideoNInputs']

        config['ORGDIR_Bootleg'] = "%s/_1 Bootleg" % config['ORGDIR_ExtraSoftware']
        config['ORGDIR_Homebrew'] = "%s/_2 Homebrew" % config['ORGDIR_ExtraSoftware']
        config['ORGDIR_Enhancements'] = "%s/_3 Enhancements" % config['ORGDIR_ExtraSoftware']
        config['ORGDIR_Translations'] = "%s/_4 Translations" % config['ORGDIR_ExtraSoftware']
        config['ORGDIR_Hacks'] = "%s/_5 Hacks" % config['ORGDIR_ExtraSoftware']

        config['ORGDIR_DIRECTORIES'] = [
            config['ORGDIR_09'],
            config['ORGDIR_AE'],
            config['ORGDIR_FK'],
            config['ORGDIR_LQ'],
            config['ORGDIR_RT'],
            config['ORGDIR_UZ'],
            config['ORGDIR_Region'],
            config['ORGDIR_Collections'],
            config['ORGDIR_VideoNInputs'],
            config['ORGDIR_ExtraSoftware'],
        ]

        config['ROTATION_DIRECTORIES'] = {
            0: "Horizontal",
            90: "Vertical (CW)",
            180: "Horizontal (180)",
            270: "Vertical (CCW)",
        }

        return config

    def run_arcade_organizer_organize_all_mras(self, config: Dict[str, Any]) -> bool:
        infra = Infrastructure(config, self._printer)
        mra_finder = MraFinder(config, infra)
        ao = ArcadeOrganizer(config, infra, mra_finder, self._printer)
        ao.organize_all_mras()
        return check_pass_errors(infra.errors(), self._printer)


    def run_arcade_organizer_print_orgdir_folders(self, config: Dict[str, Any]) -> Tuple[List[str], bool]:
        infra = Infrastructure(config, self._printer)
        mra_finder = MraFinder(config, infra)
        ao = ArcadeOrganizer(config, infra, mra_finder, self._printer)

        folders = ao.calculate_orgdir_folders()
        return folders, check_pass_errors(infra.errors(), self._printer)


    def run_arcade_organizer_print_ini_options(self, config: Dict[str, Any]) -> bool:
        infra = Infrastructure(config, self._printer)
        mra_finder = MraFinder(config, infra)
        ao = ArcadeOrganizer(config, infra, mra_finder, self._printer)

        for key, value in sorted(ao.calculate_ini_options().items()):
            self._printer.print("%s=%s" % (key, value))

        return check_pass_errors(infra.errors(), self._printer)

def lineno():
    return getframeinfo(currentframe().f_back).lineno


class AoLogger(Protocol):
    def print(self, *args, sep='', end='\n', flush=False):
        pass


class Printer:
    def __init__(self, config):
        self._config = config

    def __enter__(self):
        try:
            self._logfile = open(self._config['ARCADE_ORGANIZER_WORK_PATH'] + "/issues.log", "w")
        except:
            pass
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._logfile.close()
        except:
            pass

    def print(self, *args, sep='', end='\n', flush=False):
        print(*args, sep=sep, end=end, flush=flush)
        try:
            print(*args, sep=sep, end=end, file=self._logfile, flush=flush)
        except:
            pass


def between_chars(char, left, right):
    return char >= ord(left) and char <= ord(right)


def is_path_alternative(mra_path):
    return any(p.name.lower() == '_alternatives' for p in mra_path.parents)


def datetime_from_ctime(entry):
    try:
        return datetime.datetime.fromtimestamp(entry.stat().st_ctime, tz=datetime.timezone.utc)
    except FileNotFoundError:
        return None


class MraFinder:
    def __init__(self, config, infra):
        self._config = config
        self._infra = infra
        self._not_in_directory = []
        self._newer_than = None

    def not_in_directory(self, directory):
        self._not_in_directory.append(directory)

    def newer_than(self, date_text):
        self._newer_than = self._infra.text_to_date(date_text)

    def find_all_mras(self):
        return sorted(self._scan(self._config['MRADIR']), key=lambda mra: mra.name.lower())

    def _scan(self, directory):
        try:
            for entry in os.scandir(directory):
                if entry.is_dir(follow_symlinks=False) and entry.path not in self._not_in_directory:
                    yield from self._scan(entry.path)
                elif entry.name.lower().endswith(".mra"):
                    if self._newer_than is None:
                        yield Path(entry.path)
                    else:
                        entry_dt = datetime_from_ctime(entry)
                        if entry_dt is not None and entry_dt > self._newer_than:
                            yield Path(entry.path)
        except FileNotFoundError:
            pass


class Infrastructure:
    def __init__(self, config, printer):
        self._config = config
        self._printer = printer
        self._init_private_variables()
        self._os_errors = []

    def errors(self):
        return self._os_errors

    def _init_private_variables(self):
        self._last_run_path = Path("%s/last_run" % self._config['ARCADE_ORGANIZER_WORK_PATH'])
        self._cached_names_path = Path("%s/installed_names.txt" % self._config['ARCADE_ORGANIZER_WORK_PATH'])
        self._tmp_data_zip_path = Path(self._config['TMP_DATA_ZIP'])

    def make_symlink(self, mra_path, name, directory):
        target_str = "%s/%s" % (directory, name)
        target = Path(target_str.replace(':', '-'))
        if target.is_file() or target.is_symlink():
            return
        try:
            self.make_directory(target.parent)
        except Exception as e:
            self._printer.print("Line %s || %s (%s)" % (lineno(), e, mra_path))
            return
        src = str(mra_path.absolute())
        dst = str(target.absolute())
        if self._config['PRINT_SYMLINKS']:
            self._printer.print("make_symlink: src %s dst %s" % (src, dst))
        else:
            try:
                if self._config['NO_SYMLINKS']:
                    shutil.copy(src, dst)
                else:
                    os.symlink(src, dst)
            except FileExistsError:
                pass
            except OSError as e:
                self._printer.print("Line %s || %s (%s)" % (lineno(), e, mra_path))
                self._os_errors.append((mra_path, e))

    def download_mad_db_zip(self):
        self._printer.print("Downloading Mister Arcade Descriptions database")

        if not self._config['MAD_DB'].startswith('http'):
            src = self._config['MAD_DB']
            try:
                shutil.copyfile(src, self._config['TMP_DATA_ZIP'])
            except FileNotFoundError as _e:
                self._printer.print("Couldn't find %s" % src)
                self._printer.print()
                return None

            with open(self._config['TMP_DATA_ZIP'], 'rb') as tmp_data_zip:
                self._printer.print("MD5 Hash: %s" % hashlib.md5(tmp_data_zip.read()).hexdigest())
                self._printer.print()
                return self._tmp_data_zip_path

        zip_output = subprocess.run('curl %s %s -o %s %s' % (self._config['CURL_RETRY'], self._config['SSL_SECURITY_OPTION'], self._config['TMP_DATA_ZIP'], self._config['MAD_DB']), shell=True,
                                    stderr=subprocess.DEVNULL)

        if zip_output.returncode != 0 or not self._tmp_data_zip_path.is_file():
            self._printer.print("Couldn't download %s : Network Problem" % self._config['MAD_DB'])
            self._printer.print()
            return None

        md5_output = subprocess.run('curl %s %s %s.md5' % (self._config['CURL_RETRY'], self._config['SSL_SECURITY_OPTION'], self._config['MAD_DB']), shell=True, stderr=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE)
        if md5_output.returncode != 0:
            self._printer.print("Couldn't download %s.md5 : Network Problem" % self._config['MAD_DB'])
            self._printer.print()
            self._tmp_data_zip_path.unlink()
            return None

        md5hash = md5_output.stdout.splitlines()[0].decode()
        self._printer.print("MD5 Hash: %s" % md5hash)
        self._printer.print()
        with open(self._config['TMP_DATA_ZIP'], 'rb') as tmp_data_zip:
            if hashlib.md5(tmp_data_zip.read()).hexdigest() != md5hash:
                self._printer.print("Corrupted database downloaded : Network Problem")
                self._printer.print()
                self._tmp_data_zip_path.unlink()
                return None

        return self._tmp_data_zip_path

    def remove_orgdir_directories(self, orgdir_folders_file):
        if orgdir_folders_file.is_file():
            for directory in self.read_orgdir_file_folders():
                self._remove_dir(directory)
            orgdir_folders_file.unlink()
        for directory in self._config['ORGDIR_DIRECTORIES']:
            self._remove_dir(directory)
        for directory in self.read_topdir_folders():
            self._remove_dir(directory)

    def remove_all_broken_symlinks(self):
        for directory in self.read_orgdir_file_folders():
            self._remove_broken_symlinks(directory)

    def get_ini_date(self):
        ini_file_path = self._config['INI_FILE_PATH']
        self._printer.print("Reading INI (%s):" % ini_file_path.name)

        ini_date = ''
        if ini_file_path.is_file():
            ctime = datetime_from_ctime(self._config['INI_FILE_PATH'])
            ini_date = ctime.strftime('%Y-%m-%dT%H:%M:%SZ')
            self._printer.print("OK")
        else:
            self._printer.print("Not found.")

        return ini_date

    def get_now_date(self):
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def read_last_run_file(self):
        last_ini_date = ''
        last_mra_date = ''
        last_version = ''
        if self._last_run_path.is_file():
            with self._last_run_path.open() as f:
                content = f.readlines()
                content = [x.strip() for x in content]
                if len(content) > 0:
                    last_version = content[0]
                if len(content) > 1:
                    last_ini_date = content[1]
                if len(content) > 2:
                    last_mra_date = content[2]

        return [last_version, last_ini_date, last_mra_date]

    def write_last_run_file(self, ini_date, mra_date):
        with self._last_run_path.open("w") as f:
            f.write(self._config['ARCADE_ORGANIZER_VERSION'] + "\n")
            f.write(ini_date + "\n")
            f.write(mra_date + "\n")

    def cache_names_file(self):
        if self._config['ARCADE_ORGANIZER_NAMES_TXT'].is_file():
            shutil.copy(str(self._config['ARCADE_ORGANIZER_NAMES_TXT']), str(self._cached_names_path))

    def handle_orgdir_outside_mra_folder(self):
        org_rp = Path(os.path.realpath(self._config['ORGDIR']))
        mra_rp = Path(os.path.realpath(self._config['MRADIR']))

        org_cores = Path("%s/cores" % self._config['ORGDIR'])
        mra_cores = Path("%s/cores" % self._config['MRADIR'])
        if mra_rp not in org_rp.parents and not org_cores.is_dir() and mra_cores.is_dir():
            os.symlink(str(mra_cores.absolute()), str(org_cores.absolute()))
            orgdir_folders_file = self._config['ORGDIR_FOLDERS_FILE']
            with orgdir_folders_file.open("a") as f:
                f.write(str(org_cores) + "\n")

    def write_orgdir_folders_file(self):
        orgdir_folders_file = self._config['ORGDIR_FOLDERS_FILE']

        with orgdir_folders_file.open("a") as f:
            orgdir_lines = self.read_orgdir_file_folders()
            for directory in (list(self._config['ORGDIR_DIRECTORIES']) + self.read_topdir_folders()):
                if Path(directory).is_dir():
                    if not os.listdir(directory):
                        self._remove_dir(directory)
                    elif directory not in orgdir_lines:
                        f.write(directory + "\n")

    def read_orgdir_file_folders(self):
        result = list()
        orgdir_folders_file = self._config['ORGDIR_FOLDERS_FILE']
        if orgdir_folders_file.is_file():
            with orgdir_folders_file.open() as f:
                for line in f:
                    directory = line.strip()
                    path = Path(directory)
                    if path.is_dir():
                        result.append(directory)
        return result

    def read_topdir_folders(self):
        files = list(self._scan_topdir_files())

        dirs = []
        if self._config['TOPDIR'] == 'platform':
            dirs = list(self._scan_folders(self._config['ORGDIR_Platform']))
        elif self._config['TOPDIR'] == 'core':
            dirs = list(self._scan_folders(self._config['ORGDIR_Core']))
        elif self._config['TOPDIR'] == 'year':
            dirs = list(self._scan_folders(self._config['ORGDIR_Year']))

        intersection = self._make_pathstr_names_set(files) & self._make_pathstr_names_set(dirs)

        return [f for f in files if Path(f).name in intersection]

    def _make_pathstr_names_set(self, paths):
        return set([Path(p).name for p in paths])

    def _scan_topdir_files(self):
        try:
            for entry in os.scandir(self._config['ORGDIR']):
                if entry.is_file(follow_symlinks=True) and entry.name.startswith('_'):
                    yield str(Path(entry.path).absolute())
        except FileNotFoundError:
            pass

    def _scan_folders(self, directory):
        try:
            for entry in os.scandir(directory):
                if entry.is_dir(follow_symlinks=False):
                    yield str(Path(entry.path).absolute())
        except FileNotFoundError:
            pass

    def remove_any_previous_mad_db_files_in_tmp(self):
        if self._tmp_data_zip_path.is_file():
            self._tmp_data_zip_path.unlink()

    def get_cached_data_zip(self):
        return self._config['CACHED_DATA_ZIP']

    def are_files_different(self, left_file, right_file):
        return (not left_file.is_file() and right_file.is_file()) or \
            (not right_file.is_file() and left_file.is_file()) or \
            self._are_files_md5_different(left_file, right_file)

    def copy_file(self, from_file, to_file):
        shutil.copy(str(from_file), str(to_file))

    def remove_file(self, file_path):
        file_path.unlink()

    def check_if_orgdir_directories_are_missing(self):
        return not Path(self._config['ORGDIR_09']).is_dir() or \
            not Path(self._config['ORGDIR_AE']).is_dir() or \
            not Path(self._config['ORGDIR_FK']).is_dir() or \
            not Path(self._config['ORGDIR_LQ']).is_dir() or \
            not Path(self._config['ORGDIR_RT']).is_dir() or \
            not Path(self._config['ORGDIR_UZ']).is_dir()

    def check_if_names_txt_is_new(self):
        return self._config['ARCADE_ORGANIZER_NAMES_TXT'].is_file() \
            and (
                        not self._cached_names_path.is_file()
                        or self._are_files_different(self._config['ARCADE_ORGANIZER_NAMES_TXT'], self._cached_names_path)
                )

    def read_mra_fields(self, mra_path, tags):
        fields = {i: '' for i in tags}

        try:
            context = ET.iterparse(str(mra_path), events=("start",))
            for event, elem in context:
                elem_tag = elem.tag.lower()
                if elem_tag in tags:
                    tags.remove(elem_tag)
                    elem_value = elem.text
                    if isinstance(elem_value, str):
                        fields[elem_tag] = elem_value
                    if len(tags) == 0:
                        break
        except Exception as e:
            self._printer.print("Line %s || %s (%s)" % (lineno(), e, mra_path))

        return fields

    def read_mad_db(self):
        if self._config['CACHED_DATA_ZIP'].is_file():
            output = subprocess.run("unzip -p %s" % self._config['CACHED_DATA_ZIP'], shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
            if output.returncode == 0:
                return json.loads(output.stdout.decode())

            self._printer.print("Error while reading %s from %s" % (self._config['MAD_DB'], self._config['CACHED_DATA_ZIP']))

        return {}

    def text_is_date(self, date_text):
        if self.text_to_date(date_text) is None:
            return False
        else:
            return True

    def text_to_date(self, date_text):
        try:
            date = datetime.datetime.strptime(date_text, '%Y-%m-%dT%H:%M:%SZ')
            return date
        except Exception as e:
            self._printer.print("Line %s || %s (%s)" % (lineno(), e, date_text))
            return None

    def make_directory(self, directory_path):
        directory_path.mkdir(parents=True, exist_ok=True)

    def _are_files_different(self, file1, file2):
        with file1.open() as f1, file2.open() as f2:
            diffs = list(difflib.unified_diff(f1.readlines(), f2.readlines()))
            return len(diffs) > 0

    def _are_files_md5_different(self, path1, path2):
        with path1.open('rb') as path1_file, path2.open('rb') as path2_file:
            return hashlib.md5(path1_file.read()).hexdigest() != hashlib.md5(path2_file.read()).hexdigest()

    def _remove_dir(self, directory):
        path = Path(directory)
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(directory)
        elif path.is_symlink():
            path.unlink()
        else:
            return
        parent = str(path.parent)
        if not os.listdir(parent):
            shutil.rmtree(parent)

    def _remove_broken_symlinks(self, directory):
        output = subprocess.run('find "%s/" -xtype l -exec rm \{\} \;' % directory, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if output.returncode != 0:
            self._printer.print("Couldn't clean broken symlinks at " + directory)
            self._printer.print(output.stderr.decode())


class ArcadeOrganizer:
    def __init__(self, config, infra, mra_finder, printer):
        self._config = config
        self._infra = infra
        self._mra_finder = mra_finder
        self._printer = printer
        self._init_cores_dict()
        self._init_names_txt_dict()
        self._cached_db = None

    def _init_cores_dict(self):
        cores_dir = Path("%s/cores/" % self._config['MRADIR'])
        self._cores_dict = dict()
        if cores_dir.is_dir():
            for core_path in cores_dir.iterdir():
                core_name = core_path.name.rsplit('_', 1)[0]
                self._cores_dict[core_name.upper()] = core_name

    def _init_names_txt_dict(self):
        self._names_txt_dict = dict()
        if self._config['ARCADE_ORGANIZER_NAMES_TXT'].is_file():
            with self._config['ARCADE_ORGANIZER_NAMES_TXT'].open() as f:
                for line in f:
                    if ":" not in line:
                        continue
                    splits = line.split(':', 1)
                    self._names_txt_dict[splits[0].upper()] = splits[1].strip()

    def read_description(self, setname):
        return self.mad_dict.get(setname, {})

    def organize_topdir(self):
        if self._config['TOPDIR'] == 'platform' and Path(self._config['ORGDIR_Platform']).is_dir():
            try:
                for entry in os.scandir(self._config['ORGDIR_Platform']):
                    if entry.is_dir(follow_symlinks=False):
                        self._infra.make_symlink(Path(entry.path), entry.name, self._config['ORGDIR'])
            except FileNotFoundError:
                pass
        elif self._config['TOPDIR'] == 'core' and Path(self._config['ORGDIR_Core']).is_dir():
            try:
                for entry in os.scandir(self._config['ORGDIR_Core']):
                    if entry.is_dir(follow_symlinks=False):
                        self._infra.make_symlink(Path(entry.path), entry.name, self._config['ORGDIR'])
            except FileNotFoundError:
                pass
        elif self._config['TOPDIR'] == 'year' and Path(self._config['ORGDIR_Year']).is_dir():
            try:
                for entry in os.scandir(self._config['ORGDIR_Year']):
                    if entry.is_dir(follow_symlinks=False):
                        self._infra.make_symlink(Path(entry.path), entry.name, self._config['ORGDIR'])
            except FileNotFoundError:
                pass

    def ensure_description_or_default(self, key, default):
        if key not in self._description:
            self._description[key] = default

    def organize_single_mra(self, mra_path):

        self._mra_path = mra_path

        self._fields = self._infra.read_mra_fields(mra_path, [
            'setname',
            'rbf',
        ])

        if self._fields['setname'].strip() == '':
            self._basename_mra = str(Path(mra_path).name)
            self.log_skipped("**** Skipping empty setname ****")
            return

        self._description = self.read_description(self._fields['setname'])

        # self.ensure_description_or_default('name', ''),
        self.ensure_description_or_default('file', mra_path.name)
        self.ensure_description_or_default('rotation', 0)
        self.ensure_description_or_default('flip', False)
        self.ensure_description_or_default('resolution', "15kHz")
        self.ensure_description_or_default('region', '')
        self.ensure_description_or_default('homebrew', False)
        self.ensure_description_or_default('bootleg', False)
        self.ensure_description_or_default('year', 9999)
        self.ensure_description_or_default('manufacturer', [])
        self.ensure_description_or_default('platform', [])
        self.ensure_description_or_default('category', [])
        self.ensure_description_or_default('series', [])
        self.ensure_description_or_default('players', '1')
        self.ensure_description_or_default('move_inputs', [])
        self.ensure_description_or_default('special_controls', [])
        self.ensure_description_or_default('num_buttons', 1)
        self.ensure_description_or_default('num_monitors', 1)
        self.ensure_description_or_default('cocktail', '')
        self.ensure_description_or_default('best_of', [])
        self.ensure_description_or_default('alternative', is_path_alternative(mra_path))
        # @TODO Activate PR #38
        # self.ensure_description_or_default('parent', ''),

        # @TODO Reactivate once dbs handle name correctly?
        # self._name = self._description['name']
        # self._name = self._name.replace(':', '¦')
        # self._name = self._name.replace('*', '•')
        # self._name = self._name.replace('?', '¿')

        self._basename_mra = self._description['file']

        if self._description['homebrew']:
            if self._config['HOMEBREW'] == BoolFlagPresence.DEACTIVATED:
                self.log_skipped("**** Skipping Homebrew ****")
                return
            elif self._config['HOMEBREW'] == BoolFlagPresence.ONLY_IN_OWN_FOLDER:
                self.log_skipped("**** Only Homebrew ****")
                self.prepare_run()
                self.create_homebrew()
                return

        if self._description['bootleg']:
            if self._config['BOOTLEG'] == BoolFlagPresence.DEACTIVATED:
                self.log_skipped("**** Skipping Bootleg ****")
                return
            elif self._config['BOOTLEG'] == BoolFlagPresence.ONLY_IN_OWN_FOLDER:
                self.log_skipped("**** Only Bootleg ****")
                self.prepare_run()
                self.create_bootleg()
                return

        if self._description['region'] == "US":
            self._description['region'] = 'USA'

        region_is_dev_preferred = not self._description['alternative'] and self._config['REGION_DEV_PREFERRED']
        region_matching_main = self._description['region'] == self._config['REGION_MAIN']
        if not region_is_dev_preferred and not region_matching_main:
            if self._config['REGION_OTHERS'] == BoolFlagPresence.DEACTIVATED:
                self.log_skipped("**** Skipping Region ****")
                return
            elif self._config['REGION_OTHERS'] == BoolFlagPresence.ONLY_IN_OWN_FOLDER:
                self.log_skipped("**** Only Region ****")
                self.prepare_run()
                self.create_region()
                return

        if self._description['resolution'] == "15kHz" and not self._config['RESOLUTION_15KHZ']:
            self.log_skipped("**** Skipping Resolution 15kHz ****")
            return
        elif self._description['resolution'] == "24kHz" and not self._config['RESOLUTION_24KHZ']:
            self.log_skipped("**** Skipping Resolution 24kHz ****")
            return
        elif self._description['resolution'] == "31kHz" and not self._config['RESOLUTION_31KHZ']:
            self.log_skipped("**** Skipping Resolution 31kHz ****")
            return

        if self.skip_rotation(0, 'ROTATION_0', 'ROTATION_180') or \
                self.skip_rotation(90, 'ROTATION_90', 'ROTATION_270') or \
                self.skip_rotation(180, 'ROTATION_180', 'ROTATION_0') or \
                self.skip_rotation(270, 'ROTATION_270', 'ROTATION_90'):
            self.log_skipped("**** Only Rotation ****")
            self.prepare_run()
            self.create_rotation()
            return

        if self._description['players'] in self._config['PLAYERS_NOT_SUPPORTED']:
            self.log_skipped("**** Skipping players not supported ****")
            return

        if self._description['num_buttons'] > self._config['NUM_BUTTONS_MAXIMUM']:
            self.log_skipped("**** Skipping buttons (#%s) not supported (Max: %s) ****" % (self._description['num_buttons'], self._config['NUM_BUTTONS_MAXIMUM']))
            return

        if len(self._description['move_inputs']) > 0 and len(set(self._description['move_inputs']) - set(self._config['MOVE_INPUTS_NOT_SUPPORTED'])) == 0:
            self.log_skipped("**** Skipping move inputs not supported ****")
            return

        if len(self._description['special_controls']) > 0 and len(set(self._description['special_controls']) - set(self._config['SPECIAL_CONTROLS_NOT_SUPPORTED'])) == 0:
            self.log_skipped("**** Skipping special controls not supported ****")
            return

        if isinstance(self._description['year'], int) and (self._description['year'] < self._config['YEAR_LOW'] or self._description['year'] > self._config['YEAR_HIGH']):
            self.log_skipped("**** Skipping not fitting desired year range ****")
            return

        self.prepare_run()

        if self._config['SKIPALTS'] and self._description['alternative']:
            self.log_skipped("**** Only Alternative Fields ****")

            if (not self._description['homebrew'] and not self._description['bootleg']) \
                    or (self._description['region'] != 'World' and self._description['region'] != 'USA' and self._description['region'] != 'Japan'):
                self.create_region()

            self.create_best_of()
            self.create_bootleg()
            self.create_homebrew()
            return

        self.create_alphabetic()
        self.create_region()
        self.create_core()
        self.create_year()
        self.create_category()
        self.create_platform()
        self.create_manufacturer()
        self.create_series()
        self.create_best_of()
        self.create_resolution()
        self.create_rotation()
        self.create_players()
        self.create_move_inputs()
        self.create_special_controls()
        self.create_num_buttons()
        self.create_cocktail()
        self.create_num_monitors()
        self.create_bootleg()
        self.create_homebrew()

    def log_skipped(self, message):
        if self._config['VERBOSE']:
            log_message = "%s: %s" % (self._basename_mra, message)
            self._printer.print(log_message)

    def prepare_run(self):
        rbf = self.fix_core(self._fields['rbf'])

        self._printer.print('%-44s' % self._basename_mra[0:44], end='')
        self._printer.print(' %-10s' % rbf[0:10], end='')
        self._printer.print(' %-4s' % str(self._description['year'])[0:4], end='')
        self._printer.print(' %-10s' % self._description['manufacturer'][0][0:10] if len(self._description['manufacturer']) > 0 else '', end='')
        self._printer.print(' %-8s' % self._description['category'][0].replace('/', '')[0:8] if len(self._description['category']) > 0 else '', end='')
        self._printer.print()

        self._description['rbf'] = self.better_core_name(rbf)

        if self._config['PREPEND_YEAR']:
            special_char = '}' if isinstance(self._description['year'], int) and self._description['year'] < 2000 else '~'
            self._year_name = "%s%s %s" % (special_char, str(self._description['year'])[-2:], self._basename_mra)

    def create_symlink(self, directory):
        self._infra.make_symlink(self._mra_path, self._basename_mra, directory)
        if self._config['PREPEND_YEAR']:
            self._infra.make_symlink(self._mra_path, self._year_name, directory)

    def create_symlink_name_prefix(self, prefix, directory):
        self._infra.make_symlink(self._mra_path, "%s. %s" % (prefix, self._basename_mra), directory)
        if self._config['PREPEND_YEAR']:
            self._infra.make_symlink(self._mra_path, "%s. %s" % (prefix, self._year_name), directory)

    def impl_create_array_links(self, config_dir_check, description_field, orgdir):
        if self._config[config_dir_check]:
            if not isinstance(self._description[description_field], list):
                self._description[description_field] = [self._description[description_field]]
            for entry in self._description[description_field]:
                self.create_symlink("%s/_%s/" % (self._config[orgdir], entry))

    def impl_create_single_link(self, config_dir_check, description_field, orgdir):
        if self._config[config_dir_check] and description_field in self._description:
            self.create_symlink("%s/_%s/" % (self._config[orgdir], self._description[description_field]))

    def impl_create_bool_link(self, description_field, orgdir):
        if self._description[description_field]:
            self.create_symlink("%s/" % self._config[orgdir])

    def create_region(self):
        if 'region' in self._description and self._description['region'].strip() == '':
            return

        self.impl_create_single_link('REGION_DIR', 'region', 'ORGDIR_Region')

    def create_alphabetic(self):
        if self._config['AZ_DIR']:
            first_letter_char = ord(self._basename_mra.upper()[0])
            if between_chars(first_letter_char, '0', '9'):
                self.create_symlink(self._config['ORGDIR_09'])
            elif between_chars(first_letter_char, 'A', 'E'):
                self.create_symlink(self._config['ORGDIR_AE'])
            elif between_chars(first_letter_char, 'F', 'K'):
                self.create_symlink(self._config['ORGDIR_FK'])
            elif between_chars(first_letter_char, 'L', 'Q'):
                self.create_symlink(self._config['ORGDIR_LQ'])
            elif between_chars(first_letter_char, 'R', 'T'):
                self.create_symlink(self._config['ORGDIR_RT'])
            elif between_chars(first_letter_char, 'U', 'Z'):
                self.create_symlink(self._config['ORGDIR_UZ'])

    def create_core(self):
        self.impl_create_single_link('CORE_DIR', 'rbf', 'ORGDIR_Core')

    def create_year(self):
        self.impl_create_single_link('YEAR_DIR', 'year', 'ORGDIR_Year')

        if self._config['YEAR_DIR'] and isinstance(self._description['year'], int) and self._config['DECADES_DIR']:
            if self._description['year'] < 1980:
                self.create_symlink("%s/_%s/" % (self._config['ORGDIR_Year'], "The 1970s"))

            elif self._description['year'] < 1990:
                self.create_symlink("%s/_%s/" % (self._config['ORGDIR_Year'], "The 1980s"))

            elif self._description['year'] < 2000:
                self.create_symlink("%s/_%s/" % (self._config['ORGDIR_Year'], "The 1990s"))

            elif self._description['year'] < 2010:
                self.create_symlink("%s/_%s/" % (self._config['ORGDIR_Year'], "The 2000s"))

            elif self._description['year'] < 2020:
                self.create_symlink("%s/_%s/" % (self._config['ORGDIR_Year'], "The 2010s"))

            elif self._description['year'] < 2030:
                self.create_symlink("%s/_%s/" % (self._config['ORGDIR_Year'], "The 2020s"))

    def create_manufacturer(self):
        self.impl_create_array_links('MANUFACTURER_DIR', 'manufacturer', 'ORGDIR_Manufacturer')

    def create_category(self):
        self.impl_create_array_links('CATEGORY_DIR', 'category', 'ORGDIR_Category')

    def create_rotation(self):
        if self._config['ROTATION_DIR']:
            self.create_rotation_symlink(0, 180)
            self.create_rotation_symlink(90, 270)
            self.create_rotation_symlink(180, 0)
            self.create_rotation_symlink(270, 90)

    def create_resolution(self):
        self.impl_create_single_link('RESOLUTION_DIR', 'resolution', 'ORGDIR_Resolution')

    def create_series(self):
        self.impl_create_array_links('SERIES_DIR', 'series', 'ORGDIR_Series')

    def create_platform(self):
        self.impl_create_array_links('PLATFORM_DIR', 'platform', 'ORGDIR_Platform')

    def create_players(self):
        self.impl_create_array_links('PLAYERS_DIR', 'players', 'ORGDIR_Players')

    def create_move_inputs(self):
        self.impl_create_array_links('MOVE_INPUTS_DIR', 'move_inputs', 'ORGDIR_MoveInputs')

    def create_num_buttons(self):
        self.impl_create_single_link('NUM_BUTTONS_DIR', 'num_buttons', 'ORGDIR_NumButtons')

    def create_special_controls(self):
        self.impl_create_array_links('SPECIAL_CONTROLS_DIR', 'special_controls', 'ORGDIR_SpecialControls')

    def create_best_of(self):
        if self._config['BEST_OF_DIR']:
            for best_of in self._description['best_of']:
                if 'pos' in best_of:
                    self.create_symlink_name_prefix(best_of['pos'], "%s/_%s/" % (self._config['ORGDIR_BestOf'], best_of['val']))
                elif 'val' in best_of:
                    self.create_symlink("%s/_%s/" % (self._config['ORGDIR_BestOf'], best_of['val']))
                else:
                    # @TODO This branch has to go once the db is updated
                    self.create_symlink("%s/_%s/" % (self._config['ORGDIR_BestOf'], best_of))

    def create_cocktail(self):
        self.impl_create_bool_link('cocktail', 'ORGDIR_Cocktail')

    def create_num_monitors(self):
        self.impl_create_single_link('NUM_MONITORS_DIR', 'num_monitors', 'ORGDIR_NumMonitors')

    def create_bootleg(self):
        self.impl_create_bool_link('bootleg', 'ORGDIR_Bootleg')

    def create_homebrew(self):
        self.impl_create_bool_link('homebrew', 'ORGDIR_Homebrew')

    def create_rotation_symlink(self, condition, flip_condition):
        if self._description['rotation'] == condition or (self._description['rotation'] == flip_condition and self._description['flip']):
            self.create_symlink("%s/_%s/" % (self._config['ORGDIR_Rotation'], self._config['ROTATION_DIRECTORIES'][condition]))

    def skip_rotation(self, condition, config, flip_config):
        if self._description['rotation'] == condition:
            if not self._config[config]:
                self.log_skipped("**** Skipping %s ****" % config)
                return True
            elif not self._config[flip_config] and self._description['flip'] != "yes":
                self.log_skipped("**** Skipping %s + flip ****" % flip_config)
                return True

        return False

    def fix_core(self, core_name):
        if core_name == "":
            return ""
        return self._cores_dict.get(core_name.upper().strip(".RBF"), core_name)

    def better_core_name(self, core_name):
        if core_name == "":
            return ""

        upper_core = core_name.upper()
        arcade_core_name = 'ARCADE_%s' % upper_core
        if arcade_core_name in self._names_txt_dict:
            return self._names_txt_dict[arcade_core_name]
        elif upper_core in self._names_txt_dict:
            return self._names_txt_dict[upper_core]

        return core_name

    def calculate_ini_options(self):
        return {key: to_ini(self._config[key]) for key in sorted(self._config['INI_KEYS'])}

    def calculate_orgdir_folders(self):
        dir_set = set()
        for directory in self._config['ORGDIR_DIRECTORIES']:
            if Path(directory).is_dir():
                dir_set.add(directory)

        for directory in self._infra.read_orgdir_file_folders():
            dir_set.add(directory)

        for directory in self._infra.read_topdir_folders():
            dir_set.add(directory)

        return sorted(dir_set)

    @property
    def mad_dict(self):
        if self._cached_db is None:
            self._cached_db = self._infra.read_mad_db()
        return self._cached_db

    def organize_all_mras(self):
        self._infra.make_directory(Path(self._config['ARCADE_ORGANIZER_WORK_PATH']))

        ini_date = self._infra.get_ini_date()

        self._printer.print()
        self._printer.print('Arcade Organizer %s' % self._config['ARCADE_ORGANIZER_VERSION'])
        self._printer.print('Arguments:')
        for key, value in sorted(self.calculate_ini_options().items()):
            self._printer.print("%s=%s" % (key, value))
        self._printer.print()

        self._infra.remove_any_previous_mad_db_files_in_tmp()

        tmp_data_file = self._infra.download_mad_db_zip()

        last_version, last_ini_date, last_mra_date = self._infra.read_last_run_file()

        from_scatch = False

        if self._config['ARCADE_ORGANIZER_VERSION'] != last_version:
            from_scatch = True
            self._printer.print("Different AO version detected.")
            self._printer.print()

        if self._infra.check_if_orgdir_directories_are_missing():
            from_scatch = True
            self._printer.print("Some ORGDIR directories are missing.")
            self._printer.print()

        if not self._infra.text_is_date(last_mra_date):
            from_scatch = True
            self._printer.print("Last run file not found.")
            self._printer.print()

        if self._infra.check_if_names_txt_is_new():
            from_scatch = True
            self._printer.print("The installed arcade_names.txt is new.")
            self._printer.print()

        if ini_date != last_ini_date:
            from_scatch = True
            if last_ini_date != '':
                self._printer.print("INI file has been modified.")
                self._printer.print()

        if tmp_data_file is not None:
            cached_data_file = self._infra.get_cached_data_zip()
            if self._infra.are_files_different(tmp_data_file, cached_data_file):
                self._infra.copy_file(tmp_data_file, cached_data_file)
                from_scatch = True
                self._printer.print("The MAD database is new.")
                self._printer.print()
            self._infra.remove_file(tmp_data_file)

        self._mra_finder.not_in_directory(self._config['ARCADE_OFFSET_DIRECTORY'])
        for directory in (list(self._config['ORGDIR_DIRECTORIES']) + self._infra.read_topdir_folders()):
            self._mra_finder.not_in_directory(directory)

        if not from_scatch:
            self._mra_finder.newer_than(last_mra_date)

        orgdir_folders_file = self._config['ORGDIR_FOLDERS_FILE']
        mra_date = self._infra.get_now_date()
        if from_scatch:
            self._printer.print("Performing a full build.")
            self._infra.remove_orgdir_directories(orgdir_folders_file)
        else:
            self._printer.print("Performing an incremental build.")
            self._printer.print("NOTE: Remove the Organized folders if you wish to start from scratch.")
            self._infra.remove_all_broken_symlinks()

        self._printer.print()

        updated_mras = self._mra_finder.find_all_mras()

        if len(updated_mras) == 0:
            self._printer.print("No new MRAs detected")
            self._printer.print()
            self._printer.print("Skipping Arcade Organizer...")
            self._printer.print()
            return

        self._printer.print("Organizing %s MRAs." % len(updated_mras))
        self._printer.print()
        self._printer.print('%-44s' % "MRA", end='')
        self._printer.print(' %-10s' % "Core", end='')
        self._printer.print(' %-4s' % "Year", end='')
        self._printer.print(' %-10s' % "Manufactu.", end='')
        self._printer.print(' %-8s' % "Category", end='')
        self._printer.print()
        self._printer.print("################################################################################")

        for mra in updated_mras:
            self.organize_single_mra(mra)

        self.organize_topdir()

        self._infra.write_orgdir_folders_file()

        self._infra.handle_orgdir_outside_mra_folder()

        self._infra.write_last_run_file(ini_date, mra_date)

        self._infra.cache_names_file()

        self._printer.print("################################################################################")
        self._printer.print('%s ver. by theypsilon' % self._config['ARCADE_ORGANIZER_VERSION'])


def check_pass_errors(errors: List[str], printer: AoLogger) -> bool:
    errors_amount = len(errors)
    if errors_amount > 0:
        printer.print("")
        printer.print("There were " + str(errors_amount) + " errors in some symlinks. Check the logs to report them to the maintainers.")
        if errors_amount > 500:
            return False

    return True


def show_help(ao_service: ArcadeOrganizerService):
    config = ao_service.make_arcade_organizer_config(guess_arcade_organizer_ini_file())
    with Printer(config) as printer:
        printer.print("Invalid arguments.")
        printer.print("Usage: %s --print-orgdir-folders" % sys.argv[0])
        printer.print("       %s --print-ini-options" % sys.argv[0])
        printer.print("       %s" % sys.argv[0])


def run_arcade_organizer_cli():
    success: bool

    config = ArcadeOrganizerService.make_arcade_organizer_config(None, guess_arcade_organizer_ini_file())
    with Printer(config) as printer:
        ao_service = ArcadeOrganizerService(printer)
        if len(sys.argv) == 2 and sys.argv[1] == "--print-orgdir-folders":
            folders, success = ao_service.run_arcade_organizer_print_orgdir_folders(config)
            for directory in folders:
                printer.print(directory)

        elif len(sys.argv) == 2 and sys.argv[1] == "--print-ini-options":
            success = ao_service.run_arcade_organizer_print_ini_options(config)

        elif len(sys.argv) != 1:
            show_help(ao_service)
            success = False

        else:
            success = ao_service.run_arcade_organizer_organize_all_mras(config)

        if not success:
            sys.exit(1)


if __name__ == '__main__':
    run_arcade_organizer_cli()

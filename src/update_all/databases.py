# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# You can download the latest version of this tool from:
# https://github.com/theypsilon/Update_All_MiSTer
from dataclasses import dataclass
from functools import cache
from typing import Dict, List, Tuple


@dataclass
class Database:
    db_id: str
    db_url: str
    title: str

    def with_title(self, title: str):
        return Database(self.db_id, self.db_url, title)


DB_ID_DISTRIBUTION_MISTER = 'distribution_mister'
DB_ID_NAMES_TXT = 'names_txt'
DB_ID_ARCADE_NAMES_TXT = 'arcade_names_txt'
DB_URL_JTPREMIUM_DEPRECATED = 'https://raw.githubusercontent.com/jotego/jtpremium/main/jtbindb.json.zip'
DB_URL_MISTERSAM_FILES_DEPRECATED = 'https://raw.githubusercontent.com/mrchrisster/MiSTer_SAM/main/MiSTer_SAMdb.json'
DB_ID_COIN_OP_COLLECTION_DEPRECATED = 'atrac17/Coin-Op_Collection'
DB_ID_UBERYOJI_BOOT_ROMS_DEPRECATED = 'uberyoji_mister_boot_roms'


class AllDBs:
    UPDATE_ALL_MISTER = Database(db_id='update_all_mister', db_url='https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/db/update_all_db.json', title='Update All files')

    # Distribution MiSTer
    MISTER_DEVEL_DISTRIBUTION_MISTER = Database(db_id=DB_ID_DISTRIBUTION_MISTER, db_url='https://raw.githubusercontent.com/MiSTer-devel/Distribution_MiSTer/main/db.json.zip', title='Main Distribution: MiSTer-devel')
    MISTER_DB9_DISTRIBUTION_MISTER = Database(db_id=DB_ID_DISTRIBUTION_MISTER, db_url='https://raw.githubusercontent.com/MiSTer-DB9/Distribution_MiSTer/main/dbencc.json.zip', title='Main Distribution: DB9 / SNAC8')
    MISTER_AITORGOMEZ_DISTRIBUTION_MISTER = Database(db_id=DB_ID_DISTRIBUTION_MISTER, db_url='https://www.aitorgomez.net/static/mistermain/db.json.zip', title='Main Distribution: AitorGomez Fork')

    # JT
    JTCORES = Database(db_id='jtcores', db_url='https://raw.githubusercontent.com/jotego/jtcores_mister/main/jtbindb.json.zip', title='JTCORES for MiSTer')

    # NAMES TXT
    NAMES_CHAR54_MANUFACTURER_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR54_Manufacturer_EU.json', title='Names TXT: CHAR54 Manufacturer EU')
    NAMES_CHAR28_MANUFACTURER_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Manufacturer_EU.json', title='Names TXT: CHAR28 Manufacturer EU')
    NAMES_CHAR28_MANUFACTURER_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Manufacturer_US.json', title='Names TXT: CHAR28 Manufacturer US')
    NAMES_CHAR28_MANUFACTURER_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Manufacturer_JP.json', title='Names TXT: CHAR28 Manufacturer JP')
    NAMES_CHAR28_COMMON_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Common_EU.json', title='Names TXT: CHAR28 Common EU')
    NAMES_CHAR28_COMMON_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Common_US.json', title='Names TXT: CHAR28 Common US')
    NAMES_CHAR28_COMMON_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Common_JP.json', title='Names TXT: CHAR28 Common JP')
    NAMES_CHAR18_MANUFACTURER_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Manufacturer_EU.json', title='Names TXT: CHAR18 Manufacturer EU')
    NAMES_CHAR18_MANUFACTURER_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Manufacturer_US.json', title='Names TXT: CHAR18 Manufacturer US')
    NAMES_CHAR18_MANUFACTURER_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Manufacturer_JP.json', title='Names TXT: CHAR18 Manufacturer JP')
    NAMES_CHAR18_COMMON_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Common_EU.json', title='Names TXT: CHAR18 Common EU')
    NAMES_CHAR18_COMMON_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Common_US.json', title='Names TXT: CHAR18 Common US')
    NAMES_CHAR18_COMMON_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Common_JP.json', title='Names TXT: CHAR18 Common JP')

    # ARCADE NAMES TXT
    ARCADE_NAMES_EU_TXT = Database(db_id=DB_ID_ARCADE_NAMES_TXT, db_url='https://raw.githubusercontent.com/PigSaint/ArcadeNames_MiSTer/dbs/arcade_names_EU.json', title='Arcade Names TXT: EU')
    ARCADE_NAMES_US_TXT = Database(db_id=DB_ID_ARCADE_NAMES_TXT, db_url='https://raw.githubusercontent.com/PigSaint/ArcadeNames_MiSTer/dbs/arcade_names_US.json', title='Arcade Names TXT: US')
    ARCADE_NAMES_JP_TXT = Database(db_id=DB_ID_ARCADE_NAMES_TXT, db_url='https://raw.githubusercontent.com/PigSaint/ArcadeNames_MiSTer/dbs/arcade_names_JP.json', title='Arcade Names TXT: JP')

    # ROMS
    BIOS = Database(db_id='bios_db', db_url='https://raw.githubusercontent.com/ajgowans/BiosDB_MiSTer/db/bios_db.json.zip', title='BIOS Database')
    ARCADE_ROMS = Database(db_id='arcade_roms_db', db_url='https://raw.githubusercontent.com/zakk4223/ArcadeROMsDB_MiSTer/db/arcade_roms_db.json.zip', title='Arcade ROMs Database')
    UBERYOJI_BOOT_ROMS = Database(db_id='uberyoji_mister_boot_roms_mgl', db_url='https://raw.githubusercontent.com/uberyoji/mister-boot-roms/main/db/uberyoji_mister_boot_roms_mgl.json', title='Uberyoji Boot ROMs')

    # UNOFFICIAL CORES
    THEYPSILON_UNOFFICIAL_DISTRIBUTION = Database(db_id='theypsilon_unofficial_distribution', db_url='https://raw.githubusercontent.com/theypsilon/Distribution_Unofficial_MiSTer/main/unofficialdb.json.zip', title='theypsilon Unofficial Distribution')
    LLAPI_FOLDER = Database(db_id='llapi_folder', db_url='https://raw.githubusercontent.com/MiSTer-LLAPI/LLAPI_folder_MiSTer/main/llapidb.json.zip', title='LLAPI Folder')
    ARCADE_OFFSET_FOLDER = Database(db_id='arcade_offset_folder', db_url='https://raw.githubusercontent.com/Toryalai1/Arcade_Offset/db/arcadeoffsetdb.json.zip', title='Arcade Offset folder')
    COIN_OP_COLLECTION = Database(db_id='Coin-OpCollection/Distribution-MiSTerFPGA', db_url='https://raw.githubusercontent.com/Coin-OpCollection/Distribution-MiSTerFPGA/db/db.json.zip', title='Coin-Op Collection')
    AGG23_DB = Database(db_id='agg23_db', db_url='https://raw.githubusercontent.com/agg23/mister-repository/db/manifest.json', title="agg23's MiSTer Cores")
    YC_BUILDS = Database(db_id='MikeS11/YC_Builds-MiSTer', db_url='https://raw.githubusercontent.com/MikeS11/YC_Builds-MiSTer/db/db.json.zip', title='Y/C Builds')

    # UNOFFICIAL SCRIPTS
    TTY2OLED_FILES = Database(db_id='tty2oled_files', db_url='https://raw.githubusercontent.com/venice1200/MiSTer_tty2oled/main/tty2oleddb.json', title='tty2oled files')
    I2C2OLED_FILES = Database(db_id='i2c2oled_files', db_url='https://raw.githubusercontent.com/venice1200/MiSTer_i2c2oled/main/i2c2oleddb.json', title='i2c2oled files')
    MISTERSAM_FILES = Database(db_id='MiSTer_SAM_files', db_url='https://raw.githubusercontent.com/mrchrisster/MiSTer_SAM/db/db.json.zip', title='MiSTer SAM files')
    WIZZO_MREXT_FILES = Database(db_id='mrext/all', db_url='https://raw.githubusercontent.com/wizzomafizzo/mrext/main/releases/all.json', title='MiSTer Extensions (wizzo)')
    RETROSPY = Database(db_id='retrospy/retrospy-MiSTer', db_url='https://raw.githubusercontent.com/retrospy/retrospy-MiSTer/db/db.json.zip', title='RetroSpy')

    # BORDERS
    DINIERTO_GBA_BORDERS = Database(db_id='Dinierto/MiSTer-GBA-Borders', db_url='https://raw.githubusercontent.com/Dinierto/MiSTer-GBA-Borders/db/db.json.zip', title='Dinierto GBA Borders')

    # WALLPAPERS
    RANNYSNICE_WALLPAPERS = Database(db_id='Ranny-Snice/Ranny-Snice-Wallpapers', db_url='https://raw.githubusercontent.com/Ranny-Snice/Ranny-Snice-Wallpapers/db/db.json.zip', title='Ranny Snice Wallpapers')
    RGARCIALAGO_WALLPAPER_COLLECTION = Database(db_id='RGarciaLago/Wallpaper_Collection', db_url='https://raw.githubusercontent.com/RGarciaLago/Wallpaper_Collection/db/db.json.zip', title='RGarciaLago Wallpaper Collection (by different authors)')


@cache
def dbs_to_model_variables_pairs() -> List[Tuple[str, List[Database]]]:
    mapping = databases_by_ids()
    return [(variable, mapping[db_id]) for variable, db_id in db_ids_to_model_variable_pairs()]


def changed_db_ids() -> Dict[str, str]:
    return {
        DB_ID_COIN_OP_COLLECTION_DEPRECATED: AllDBs.COIN_OP_COLLECTION.db_id,
        DB_ID_UBERYOJI_BOOT_ROMS_DEPRECATED: AllDBs.UBERYOJI_BOOT_ROMS.db_id,
    }

def removed_db_ids() -> dict[str, str]:
    return {
        'n64_dev': 'https://raw.githubusercontent.com/RobertPeip/Mister64/db/db.json.zip'
    }


@cache
def ids_sequence() -> List[str]:
    result = []
    accounting = set()
    for field, db in AllDBs.__dict__.items():
        if field.startswith('_') or db.db_id in accounting:
            continue

        result.append(db.db_id)
        accounting.add(db.db_id)

    return result


@cache
def db_ids_to_model_variable_pairs() -> List[Tuple[str, str]]:
    return [(_old_ini_variables_to_db_ids[db_id] if db_id in _old_ini_variables_to_db_ids else db_id, db_id) for db_id in ids_sequence()]


@cache
def model_variables_by_db_id() -> Dict[str, str]:
    return {db_id: variable for variable, db_id in db_ids_to_model_variable_pairs()}


@cache
def db_ids_by_model_variables() -> Dict[str, str]:
    return {variable: db_id for variable, db_id in db_ids_to_model_variable_pairs()}


@cache
def all_dbs_list() -> List[Database]:
    return [db for field_name, db in AllDBs.__dict__.items() if not field_name.startswith('_')]


@cache
def databases_by_ids() -> Dict[str, List[Database]]:
    result = {}
    for db in all_dbs_list():
        if db.db_id not in result:
            result[db.db_id] = []

        result[db.db_id].append(db)
    return result

def db_distribution_mister_by_encc_forks(encc_forks: str) -> Database:
    if encc_forks == "db9":
        return AllDBs.MISTER_DB9_DISTRIBUTION_MISTER
    elif encc_forks == "aitorgomez":
        return AllDBs.MISTER_AITORGOMEZ_DISTRIBUTION_MISTER
    else:
        return AllDBs.MISTER_DEVEL_DISTRIBUTION_MISTER

def db_jtcores_by_download_beta_cores(download_beta_cores: bool) -> Database:
    return AllDBs.JTCORES.with_title(AllDBs.JTCORES.title + ' (+betas)') if download_beta_cores else AllDBs.JTCORES


def db_names_txt_by_locale(region: str, char_code: str, sort_code: str) -> Database:
    return _names_dict.get(region, {}).get(char_code, {}).get(sort_code, AllDBs.NAMES_CHAR18_COMMON_JP_TXT)


def names_locale_by_db_url(db_url) -> (str, str, str):
    for region in _names_dict:
        for char_code in _names_dict[region]:
            for sort_code, db in _names_dict[region][char_code].items():
                if db_url == db.db_url:
                    return region, char_code, sort_code

    if db_url == AllDBs.NAMES_CHAR18_COMMON_JP_TXT.db_url:
        raise ValueError('Could not find a value for DB_NAMES_CHAR18_COMMON_JP_TXT')

    return names_locale_by_db_url(AllDBs.NAMES_CHAR18_COMMON_JP_TXT.db_url)


_names_dict = {
    'JP': {
        'CHAR18': {
            'Common': AllDBs.NAMES_CHAR18_COMMON_JP_TXT,
            'Manufacturer': AllDBs.NAMES_CHAR18_MANUFACTURER_JP_TXT
        },
        'CHAR28': {
            'Common': AllDBs.NAMES_CHAR28_COMMON_JP_TXT,
            'Manufacturer': AllDBs.NAMES_CHAR28_MANUFACTURER_JP_TXT
        }
    },
    'US': {
        'CHAR18': {
            'Common': AllDBs.NAMES_CHAR18_COMMON_US_TXT,
            'Manufacturer': AllDBs.NAMES_CHAR18_MANUFACTURER_US_TXT
        },
        'CHAR28': {
            'Common': AllDBs.NAMES_CHAR28_COMMON_US_TXT,
            'Manufacturer': AllDBs.NAMES_CHAR28_MANUFACTURER_US_TXT
        }
    },
    'EU': {
        'CHAR18': {
            'Common': AllDBs.NAMES_CHAR18_COMMON_EU_TXT,
            'Manufacturer': AllDBs.NAMES_CHAR18_MANUFACTURER_EU_TXT
        },
        'CHAR28': {
            'Common': AllDBs.NAMES_CHAR28_COMMON_EU_TXT,
            'Manufacturer': AllDBs.NAMES_CHAR28_MANUFACTURER_EU_TXT
        },
        'CHAR54': {
            'Manufacturer': AllDBs.NAMES_CHAR54_MANUFACTURER_EU_TXT
        }
    }
}


def db_arcade_names_txt_by_locale(region: str) -> Database:
    return _arcade_names_dict.get(region, AllDBs.ARCADE_NAMES_JP_TXT)


_arcade_names_dict = {
    'JP': AllDBs.ARCADE_NAMES_JP_TXT,
    'US': AllDBs.ARCADE_NAMES_US_TXT,
    'EU': AllDBs.ARCADE_NAMES_EU_TXT
}


# Old INI variables mapped to DB IDs
_old_ini_variables_to_db_ids = {
    DB_ID_DISTRIBUTION_MISTER: "main_updater",
    AllDBs.JTCORES.db_id: "jotego_updater",
    AllDBs.THEYPSILON_UNOFFICIAL_DISTRIBUTION.db_id: "unofficial_updater",
    AllDBs.LLAPI_FOLDER.db_id: "llapi_updater",
    AllDBs.COIN_OP_COLLECTION.db_id: "coin_op_collection_downloader",
    AllDBs.ARCADE_OFFSET_FOLDER.db_id: "arcade_offset_downloader",
    AllDBs.TTY2OLED_FILES.db_id: "tty2oled_files_downloader",
    AllDBs.I2C2OLED_FILES.db_id: "i2c2oled_files_downloader",
    AllDBs.MISTERSAM_FILES.db_id: "mistersam_files_downloader",
    AllDBs.BIOS.db_id: "bios_getter",
    AllDBs.ARCADE_ROMS.db_id: "arcade_roms_db_downloader",
    DB_ID_NAMES_TXT: "names_txt_updater",
}

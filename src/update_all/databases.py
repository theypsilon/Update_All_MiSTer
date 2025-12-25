# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse


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
    def __init__(self):
        self.UPDATE_ALL_MISTER = Database(db_id='update_all_mister', db_url='https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/db/update_all_db.json', title='Update All files')

        # Distribution MiSTer
        self.MISTER_DEVEL_DISTRIBUTION_MISTER = Database(db_id=DB_ID_DISTRIBUTION_MISTER, db_url='https://raw.githubusercontent.com/MiSTer-devel/Distribution_MiSTer/main/db.json.zip', title='Main Distribution: MiSTer-devel')
        self.MISTER_DB9_DISTRIBUTION_MISTER = Database(db_id=DB_ID_DISTRIBUTION_MISTER, db_url='https://raw.githubusercontent.com/MiSTer-DB9/Distribution_MiSTer/main/dbencc.json.zip', title='Main Distribution: DB9 / SNAC8')
        self.MISTER_AITORGOMEZ_DISTRIBUTION_MISTER = Database(db_id=DB_ID_DISTRIBUTION_MISTER, db_url='https://www.aitorgomez.net/static/mistermain/db.json.zip', title='Main Distribution: AitorGomez Fork')

        # JT
        self.JTCORES = Database(db_id='jtcores', db_url='https://raw.githubusercontent.com/jotego/jtcores_mister/main/jtbindb.json.zip', title='JTCORES for MiSTer')

        # NAMES TXT
        self.NAMES_CHAR54_MANUFACTURER_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR54_Manufacturer_EU.json', title='Names TXT: CHAR54 Manufacturer EU')
        self.NAMES_CHAR28_MANUFACTURER_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Manufacturer_EU.json', title='Names TXT: CHAR28 Manufacturer EU')
        self.NAMES_CHAR28_MANUFACTURER_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Manufacturer_US.json', title='Names TXT: CHAR28 Manufacturer US')
        self.NAMES_CHAR28_MANUFACTURER_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Manufacturer_JP.json', title='Names TXT: CHAR28 Manufacturer JP')
        self.NAMES_CHAR28_COMMON_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Common_EU.json', title='Names TXT: CHAR28 Common EU')
        self.NAMES_CHAR28_COMMON_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Common_US.json', title='Names TXT: CHAR28 Common US')
        self.NAMES_CHAR28_COMMON_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR28_Common_JP.json', title='Names TXT: CHAR28 Common JP')
        self.NAMES_CHAR18_MANUFACTURER_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Manufacturer_EU.json', title='Names TXT: CHAR18 Manufacturer EU')
        self.NAMES_CHAR18_MANUFACTURER_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Manufacturer_US.json', title='Names TXT: CHAR18 Manufacturer US')
        self.NAMES_CHAR18_MANUFACTURER_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Manufacturer_JP.json', title='Names TXT: CHAR18 Manufacturer JP')
        self.NAMES_CHAR18_COMMON_EU_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Common_EU.json', title='Names TXT: CHAR18 Common EU')
        self.NAMES_CHAR18_COMMON_US_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Common_US.json', title='Names TXT: CHAR18 Common US')
        self.NAMES_CHAR18_COMMON_JP_TXT = Database(db_id=DB_ID_NAMES_TXT, db_url='https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/dbs/names_CHAR18_Common_JP.json', title='Names TXT: CHAR18 Common JP')

        # ARCADE NAMES TXT
        self.ARCADE_NAMES_EU_TXT = Database(db_id=DB_ID_ARCADE_NAMES_TXT, db_url='https://raw.githubusercontent.com/PigSaint/ArcadeNames_MiSTer/dbs/arcade_names_EU.json', title='Arcade Names TXT: EU')
        self.ARCADE_NAMES_US_TXT = Database(db_id=DB_ID_ARCADE_NAMES_TXT, db_url='https://raw.githubusercontent.com/PigSaint/ArcadeNames_MiSTer/dbs/arcade_names_US.json', title='Arcade Names TXT: US')
        self.ARCADE_NAMES_JP_TXT = Database(db_id=DB_ID_ARCADE_NAMES_TXT, db_url='https://raw.githubusercontent.com/PigSaint/ArcadeNames_MiSTer/dbs/arcade_names_JP.json', title='Arcade Names TXT: JP')

        # ROMS
        self.BIOS = Database(db_id='bios_db', db_url='https://raw.githubusercontent.com/ajgowans/BiosDB_MiSTer/db/bios_db.json.zip', title='BIOS Database')
        self.ARCADE_ROMS = Database(db_id='arcade_roms_db', db_url='https://raw.githubusercontent.com/zakk4223/ArcadeROMsDB_MiSTer/db/arcade_roms_db.json.zip', title='Arcade ROMs Database')
        self.UBERYOJI_BOOT_ROMS = Database(db_id='uberyoji_mister_boot_roms_mgl', db_url='https://raw.githubusercontent.com/uberyoji/mister-boot-roms/main/db/uberyoji_mister_boot_roms_mgl.json', title='Uberyoji Boot ROMs')

        # UNOFFICIAL CORES
        self.THEYPSILON_UNOFFICIAL_DISTRIBUTION = Database(db_id='theypsilon_unofficial_distribution', db_url='https://raw.githubusercontent.com/theypsilon/Distribution_Unofficial_MiSTer/main/unofficialdb.json.zip', title='theypsilon Unofficial Distribution')
        self.LLAPI_FOLDER = Database(db_id='llapi_folder', db_url='https://raw.githubusercontent.com/MiSTer-LLAPI/LLAPI_folder_MiSTer/main/llapidb.json.zip', title='LLAPI Folder')
        self.ARCADE_OFFSET_FOLDER = Database(db_id='arcade_offset_folder', db_url='https://raw.githubusercontent.com/Toryalai1/Arcade_Offset/db/arcadeoffsetdb.json.zip', title='Arcade Offset folder')
        self.COIN_OP_COLLECTION = Database(db_id='Coin-OpCollection/Distribution-MiSTerFPGA', db_url='https://raw.githubusercontent.com/Coin-OpCollection/Distribution-MiSTerFPGA/db/db.json.zip', title='Coin-Op Collection')
        self.AGG23_DB = Database(db_id='agg23_db', db_url='https://raw.githubusercontent.com/agg23/mister-repository/db/manifest.json', title="agg23's MiSTer Cores")
        self.YC_BUILDS = Database(db_id='MikeS11/YC_Builds-MiSTer', db_url='https://raw.githubusercontent.com/MikeS11/YC_Builds-MiSTer/db/db.json.zip', title='Y/C Builds')
        self.ALT_CORES = Database(db_id='ajgowans/alt-cores', db_url='https://raw.githubusercontent.com/ajgowans/alt-cores/db/db.json.zip', title='Alt Cores')

        # UNOFFICIAL SCRIPTS
        self.TTY2OLED_FILES = Database(db_id='tty2oled_files', db_url='https://raw.githubusercontent.com/venice1200/MiSTer_tty2oled/main/tty2oleddb.json', title='tty2oled files')
        self.I2C2OLED_FILES = Database(db_id='i2c2oled_files', db_url='https://raw.githubusercontent.com/venice1200/MiSTer_i2c2oled/main/i2c2oleddb.json', title='i2c2oled files')
        self.MISTERSAM_FILES = Database(db_id='MiSTer_SAM_files', db_url='https://raw.githubusercontent.com/mrchrisster/MiSTer_SAM/db/db.json.zip', title='MiSTer SAM files')
        self.WIZZO_MREXT_FILES = Database(db_id='mrext/all', db_url='https://raw.githubusercontent.com/wizzomafizzo/mrext/main/releases/all.json', title='MiSTer Extensions (wizzo)')
        self.RETROSPY = Database(db_id='retrospy/retrospy-MiSTer', db_url='https://raw.githubusercontent.com/retrospy/retrospy-MiSTer/db/db.json.zip', title='RetroSpy')

        # BORDERS
        self.DINIERTO_GBA_BORDERS = Database(db_id='Dinierto/MiSTer-GBA-Borders', db_url='https://raw.githubusercontent.com/Dinierto/MiSTer-GBA-Borders/db/db.json.zip', title='Dinierto GBA Borders')

        # WALLPAPERS
        self.RANNYSNICE_WALLPAPERS = Database(db_id='Ranny-Snice/Ranny-Snice-Wallpapers', db_url='https://raw.githubusercontent.com/Ranny-Snice/Ranny-Snice-Wallpapers/db/db.json.zip', title='Ranny Snice Wallpapers')

    def all_dbs_list(self) -> List[Database]:
        return [db for field_name, db in self.__dict__.items() if not field_name.startswith('_')]

    def databases_by_ids(self) -> Dict[str, List[Database]]:
        result = {}
        for db in self.all_dbs_list():
            if db.db_id not in result:
                result[db.db_id] = []

            result[db.db_id].append(db)
        return result

    def db_distribution_mister_by_encc_forks(self, encc_forks: str) -> Database:
        if encc_forks == "db9":
            return self.MISTER_DB9_DISTRIBUTION_MISTER
        elif encc_forks == "aitorgomez":
            return self.MISTER_AITORGOMEZ_DISTRIBUTION_MISTER
        else:
            return self.MISTER_DEVEL_DISTRIBUTION_MISTER

    def encc_forks_by_distribution_mister_db_url(self, db_url: Optional[str]) -> str:
        if db_url is not None:
            db_url = db_url.lower()
            if db_url == self.MISTER_DB9_DISTRIBUTION_MISTER.db_url.lower():
                return 'db9'
            elif db_url == self.MISTER_AITORGOMEZ_DISTRIBUTION_MISTER.db_url.lower():
                return 'aitorgomez'

        return 'devel'

    def should_download_beta_cores(self, db_url: Optional[str], jt_filter: Optional[str]) -> bool:
        if db_url is None:
            db_url = self.JTCORES.db_url
        if db_url.lower() == DB_URL_JTPREMIUM_DEPRECATED.lower():
            return True
        elif jt_filter is not None and '!jtbeta' not in jt_filter.replace(' ', '').lower():
            return True

        return False

    def db_jtcores_by_download_beta_cores(self, download_beta_cores: bool) -> Database:
        return self.JTCORES.with_title(self.JTCORES.title + ' (+betas)') if download_beta_cores else self.JTCORES

    def dbs_to_model_variables_pairs(self) -> List[Tuple[str, List[Database]]]:
        mapping = self.databases_by_ids()
        return [(variable, mapping[db_id]) for variable, db_id in db_ids_to_model_variable_pairs()]

    def db_names_txt_by_locale(self, region: str, char_code: str, sort_code: str) -> Database:
        return self._names_dict.get(region, {}).get(char_code, {}).get(sort_code, self.NAMES_CHAR18_COMMON_JP_TXT)

    def db_arcade_names_txt_by_locale(self, region: str) -> Database:
        return self._arcade_names_dict.get(region, self.ARCADE_NAMES_JP_TXT)

    def names_locale_by_db_url(self, db_url: Optional[str]) -> tuple[str, str, str]:
        names_dict = self._names_dict
        for region in names_dict:
            for char_code in names_dict[region]:
                for sort_code, db in names_dict[region][char_code].items():
                    if db_url == db.db_url:
                        return region, char_code, sort_code

        if db_url == self.NAMES_CHAR18_COMMON_JP_TXT.db_url:
            raise ValueError('Could not find a value for DB_NAMES_CHAR18_COMMON_JP_TXT')

        return self.names_locale_by_db_url(self.NAMES_CHAR18_COMMON_JP_TXT.db_url)

    @property
    def _names_dict(self): return {
        'JP': {
            'CHAR18': {
                'Common': self.NAMES_CHAR18_COMMON_JP_TXT,
                'Manufacturer': self.NAMES_CHAR18_MANUFACTURER_JP_TXT
            },
            'CHAR28': {
                'Common': self.NAMES_CHAR28_COMMON_JP_TXT,
                'Manufacturer': self.NAMES_CHAR28_MANUFACTURER_JP_TXT
            }
        },
        'US': {
            'CHAR18': {
                'Common': self.NAMES_CHAR18_COMMON_US_TXT,
                'Manufacturer': self.NAMES_CHAR18_MANUFACTURER_US_TXT
            },
            'CHAR28': {
                'Common': self.NAMES_CHAR28_COMMON_US_TXT,
                'Manufacturer': self.NAMES_CHAR28_MANUFACTURER_US_TXT
            }
        },
        'EU': {
            'CHAR18': {
                'Common': self.NAMES_CHAR18_COMMON_EU_TXT,
                'Manufacturer': self.NAMES_CHAR18_MANUFACTURER_EU_TXT
            },
            'CHAR28': {
                'Common': self.NAMES_CHAR28_COMMON_EU_TXT,
                'Manufacturer': self.NAMES_CHAR28_MANUFACTURER_EU_TXT
            },
            'CHAR54': {
                'Manufacturer': self.NAMES_CHAR54_MANUFACTURER_EU_TXT
            }
        }
    }

    @property
    def _arcade_names_dict(self): return {
        'JP': self.ARCADE_NAMES_JP_TXT,
        'US': self.ARCADE_NAMES_US_TXT,
        'EU': self.ARCADE_NAMES_EU_TXT
    }

ALL_DB_IDS: dict[str, str] = {name: db.db_id for name, db in AllDBs().__dict__.items() if not name.startswith('_') and isinstance(db, Database)}

MIRROR_MYSTICAL_REALM_ORG = 'mysticalrealm'

def all_mirrors(): return (
    MIRROR_MYSTICAL_REALM_ORG
)

class AllDBsMysticalRealmOrgMirror(AllDBs):
    def __init__(self):
        super().__init__()

        githubusercontent_domain = 'https://raw.githubusercontent.com/'

        for name, db in self.__dict__.items():
            if name.startswith('_'):
                continue

            if isinstance(db, Database):
                res_path: str
                if db.db_url.startswith(githubusercontent_domain):
                    res_path = db.db_url[len(githubusercontent_domain):]
                else:
                    parsed = urlparse(db.db_url)
                    res_path = parsed.netloc + parsed.path

                db.db_url = 'https://uam-mirror.mysticalrealm.org/' + res_path

def all_dbs(mirror: Optional[str]) -> AllDBs:
    if not mirror or mirror == 'off':
        return AllDBs()

    if mirror == MIRROR_MYSTICAL_REALM_ORG:
        return AllDBsMysticalRealmOrgMirror()

    raise ValueError(f'Unknown mirror: {mirror}')

def changed_db_ids() -> Dict[str, str]:
    return {
        DB_ID_COIN_OP_COLLECTION_DEPRECATED: ALL_DB_IDS['COIN_OP_COLLECTION'],
        DB_ID_UBERYOJI_BOOT_ROMS_DEPRECATED: ALL_DB_IDS['UBERYOJI_BOOT_ROMS'],
    }

def removed_db_ids() -> dict[str, str]:
    return {
        'n64_dev': 'https://raw.githubusercontent.com/RobertPeip/Mister64/db/db.json.zip',
        'RGarciaLago/Wallpaper_Collection': 'https://raw.githubusercontent.com/RGarciaLago/Wallpaper_Collection/db/db.json.zip'
    }

def ids_sequence() -> List[str]:
    result = []
    accounting = set()
    for field, db_id in ALL_DB_IDS.items():
        if field.startswith('_') or db_id in accounting:
            continue

        result.append(db_id)
        accounting.add(db_id)

    return result

def db_ids_to_model_variable_pairs() -> List[Tuple[str, str]]:
    return [(_old_ini_variables_to_db_ids[db_id] if db_id in _old_ini_variables_to_db_ids else db_id, db_id) for db_id in ids_sequence()]

def model_variables_by_db_id() -> Dict[str, str]:
    return {db_id: variable for variable, db_id in db_ids_to_model_variable_pairs()}

def db_ids_by_model_variables() -> Dict[str, str]:
    return {variable: db_id for variable, db_id in db_ids_to_model_variable_pairs()}

# Old INI variables mapped to DB IDs
_old_ini_variables_to_db_ids = {
    DB_ID_DISTRIBUTION_MISTER: "main_updater",
    ALL_DB_IDS['JTCORES']: "jotego_updater",
    ALL_DB_IDS['THEYPSILON_UNOFFICIAL_DISTRIBUTION']: "unofficial_updater",
    ALL_DB_IDS['LLAPI_FOLDER']: "llapi_updater",
    ALL_DB_IDS['COIN_OP_COLLECTION']: "coin_op_collection_downloader",
    ALL_DB_IDS['ARCADE_OFFSET_FOLDER']: "arcade_offset_downloader",
    ALL_DB_IDS['TTY2OLED_FILES']: "tty2oled_files_downloader",
    ALL_DB_IDS['I2C2OLED_FILES']: "i2c2oled_files_downloader",
    ALL_DB_IDS['MISTERSAM_FILES']: "mistersam_files_downloader",
    ALL_DB_IDS['BIOS']: "bios_getter",
    ALL_DB_IDS['ARCADE_ROMS']: "arcade_roms_db_downloader",
    DB_ID_NAMES_TXT: "names_txt_updater",
}

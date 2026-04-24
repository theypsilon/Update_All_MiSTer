# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
        self.DUAL_RAM_CONSOLE_CORES = Database(db_id='TheJesusFish/Dual-Ram-Console-Cores', db_url='https://raw.githubusercontent.com/TheJesusFish/Dual-Ram-Console-Cores/db/db.json.zip', title='Dual RAM Console Cores (TheJesusFish)')

        # UNOFFICIAL SCRIPTS
        self.TTY2OLED_FILES = Database(db_id='tty2oled_files', db_url='https://raw.githubusercontent.com/venice1200/MiSTer_tty2oled/main/tty2oleddb.json', title='tty2oled files')
        self.I2C2OLED_FILES = Database(db_id='i2c2oled_files', db_url='https://raw.githubusercontent.com/venice1200/MiSTer_i2c2oled/main/i2c2oleddb.json', title='i2c2oled files')
        self.MISTERSAM_FILES = Database(db_id='MiSTer_SAM_files', db_url='https://raw.githubusercontent.com/mrchrisster/MiSTer_SAM/db/db.json.zip', title='MiSTer SAM files')
        self.WIZZO_MREXT_FILES = Database(db_id='mrext/all', db_url='https://raw.githubusercontent.com/wizzomafizzo/mrext/main/releases/all.json', title='MiSTer Extensions (wizzo)')
        self.RETROSPY = Database(db_id='retrospy/retrospy-MiSTer', db_url='https://raw.githubusercontent.com/retrospy/retrospy-MiSTer/db/db.json.zip', title='RetroSpy')
        self.ANIME0T4KU_MISTER_SCRIPTS = Database(db_id='anime0t4ku_mister_scripts', db_url='https://raw.githubusercontent.com/Anime0t4ku/0t4ku-mister-scripts/db/db/scripts.json.zip', title='Anime0t4ku MiSTer Scripts')

        # BORDERS
        self.DINIERTO_GBA_BORDERS = Database(db_id='Dinierto/MiSTer-GBA-Borders', db_url='https://raw.githubusercontent.com/Dinierto/MiSTer-GBA-Borders/db/db.json.zip', title='Dinierto GBA Borders')

        # WALLPAPERS
        self.RANNYSNICE_WALLPAPERS = Database(db_id='Ranny-Snice/Ranny-Snice-Wallpapers', db_url='https://raw.githubusercontent.com/Ranny-Snice/Ranny-Snice-Wallpapers/db/db.json.zip', title='Ranny Snice Wallpapers')
        self.ANIME0T4KU_WALLPAPERS = Database(db_id='anime0t4ku_wallpapers', db_url='https://raw.githubusercontent.com/Anime0t4ku/MiSTerWallpapers/db/db/0t4kuwallpapers.json.zip', title='Anime0t4ku Wallpapers')
        self.PCN_CHALLENGE_WALLPAPERS = Database(db_id='pcn_challenge_wallpapers', db_url='https://raw.githubusercontent.com/Anime0t4ku/MiSTerWallpapers/db/db/pcnchallenge.json.zip', title='PCN Challenge Wallpapers')

        # MANUALS
        self.MANUALSDB_3DO = Database(db_id='ajgowans/manualsdb-3do', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-3do/db/db.json.zip', title='3DO Manuals')
        self.MANUALSDB_ARCADIA2001 = Database(db_id='ajgowans/manualsdb-arcadia2001', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-arcadia2001/db/db.json.zip', title='Arcadia 2001 Manuals')
        self.MANUALSDB_ATARI2600 = Database(db_id='ajgowans/manualsdb-atari2600', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-atari2600/db/db.json.zip', title='Atari 2600 Manuals')
        self.MANUALSDB_ATARI5200 = Database(db_id='ajgowans/manualsdb-atari5200', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-atari5200/db/db.json.zip', title='Atari 5200 Manuals')
        self.MANUALSDB_ATARI7800 = Database(db_id='ajgowans/manualsdb-atari7800', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-atari7800/db/db.json.zip', title='Atari 7800 Manuals')
        self.MANUALSDB_ATARILYNX = Database(db_id='ajgowans/manualsdb-atarilynx', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-atarilynx/db/db.json.zip', title='Atari Lynx Manuals')
        self.MANUALSDB_ATARIXEGS = Database(db_id='ajgowans/manualsdb-atarixegs', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-atarixegs/db/db.json.zip', title='Atari XEGS Manuals')
        self.MANUALSDB_AVISION = Database(db_id='ajgowans/manualsdb-avision', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-avision/db/db.json.zip', title='AVision Manuals')
        self.MANUALSDB_BALLYASTROCADE = Database(db_id='ajgowans/manualsdb-ballyastrocade', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-ballyastrocade/db/db.json.zip', title='Bally Astrocade Manuals')
        self.MANUALSDB_BBCBRIDGE = Database(db_id='ajgowans/manualsdb-bbcbridge', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-bbcbridge/db/db.json.zip', title='BBC Bridge Manuals')
        self.MANUALSDB_CDI = Database(db_id='ajgowans/manualsdb-cdi', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-cdi/db/db.json.zip', title='CD-i Manuals')
        self.MANUALSDB_CHANNELF = Database(db_id='ajgowans/manualsdb-channelf', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-channelf/db/db.json.zip', title='Channel F Manuals')
        self.MANUALSDB_COLECOVISION = Database(db_id='ajgowans/manualsdb-colecovision', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-colecovision/db/db.json.zip', title='ColecoVision Manuals')
        self.MANUALSDB_CREATIVISION = Database(db_id='ajgowans/manualsdb-creativision', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-creativision/db/db.json.zip', title='CreatiVision Manuals')
        self.MANUALSDB_FDS = Database(db_id='ajgowans/manualsdb-fds', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-fds/db/db.json.zip', title='FDS Manuals')
        self.MANUALSDB_GAMEANDWATCH = Database(db_id='ajgowans/manualsdb-gameandwatch', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-gameandwatch/db/db.json.zip', title='Game & Watch Manuals')
        self.MANUALSDB_GAMEBOY = Database(db_id='ajgowans/manualsdb-gameboy', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-gameboy/db/db.json.zip', title='Game Boy Manuals')
        self.MANUALSDB_GAMEGEAR = Database(db_id='ajgowans/manualsdb-gamegear', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-gamegear/db/db.json.zip', title='Game Gear Manuals')
        self.MANUALSDB_GBA = Database(db_id='ajgowans/manualsdb-gba', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-gba/db/db.json.zip', title='GBA Manuals')
        self.MANUALSDB_GBC = Database(db_id='ajgowans/manualsdb-gbc', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-gbc/db/db.json.zip', title='Game Boy Color Manuals')
        self.MANUALSDB_INTELLIVISION = Database(db_id='ajgowans/manualsdb-intellivision', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-intellivision/db/db.json.zip', title='Intellivision Manuals')
        self.MANUALSDB_JAGUAR = Database(db_id='ajgowans/manualsdb-jaguar', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-jaguar/db/db.json.zip', title='Jaguar Manuals')
        self.MANUALSDB_JAGUARCD = Database(db_id='ajgowans/manualsdb-jaguarcd', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-jaguarcd/db/db.json.zip', title='Jaguar CD Manuals')
        self.MANUALSDB_LCDHANDHELDS = Database(db_id='ajgowans/manualsdb-lcdhandhelds', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-lcdhandhelds/db/db.json.zip', title='LCD Handhelds Manuals')
        self.MANUALSDB_MEGADRIVE = Database(db_id='ajgowans/manualsdb-megadrive', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-megadrive/db/db.json.zip', title='Mega Drive Manuals')
        self.MANUALSDB_N64 = Database(db_id='ajgowans/manualsdb-n64', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-n64/db/db.json.zip', title='N64 Manuals')
        self.MANUALSDB_NEOGEOAES = Database(db_id='ajgowans/manualsdb-neogeoaes', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-neogeoaes/db/db.json.zip', title='Neo Geo AES Manuals')
        self.MANUALSDB_NEOGEOCD = Database(db_id='ajgowans/manualsdb-neogeocd', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-neogeocd/db/db.json.zip', title='Neo Geo CD Manuals')
        self.MANUALSDB_NES = Database(db_id='ajgowans/manualsdb-nes', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-nes/db/db.json.zip', title='NES Manuals')
        self.MANUALSDB_NGP = Database(db_id='ajgowans/manualsdb-ngp', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-ngp/db/db.json.zip', title='Neo Geo Pocket Manuals')
        self.MANUALSDB_NGPC = Database(db_id='ajgowans/manualsdb-ngpc', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-ngpc/db/db.json.zip', title='Neo Geo Pocket Color Manuals')
        self.MANUALSDB_ODYSSEY2 = Database(db_id='ajgowans/manualsdb-odyssey2', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-odyssey2/db/db.json.zip', title='Odyssey 2 Manuals')
        self.MANUALSDB_POKEMONMINI = Database(db_id='ajgowans/manualsdb-pokemonmini', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-pokemonmini/db/db.json.zip', title='Pokemon Mini Manuals')
        self.MANUALSDB_PSX = Database(db_id='ajgowans/manualsdb-psx', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-psx/db/db.json.zip', title='PSX Manuals')
        self.MANUALSDB_PYUUTAJR = Database(db_id='ajgowans/manualsdb-pyuutajr', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-pyuutajr/db/db.json.zip', title='Pyuuta Jr Manuals')
        self.MANUALSDB_SEGA32X = Database(db_id='ajgowans/manualsdb-sega32x', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-sega32x/db/db.json.zip', title='Sega 32X Manuals')
        self.MANUALSDB_SEGACD = Database(db_id='ajgowans/manualsdb-segacd', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-segacd/db/db.json.zip', title='Sega CD Manuals')
        self.MANUALSDB_SEGASATURN = Database(db_id='ajgowans/manualsdb-segasaturn', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-segasaturn/db/db.json.zip', title='Sega Saturn Manuals')
        self.MANUALSDB_SEGASG1000 = Database(db_id='ajgowans/manualsdb-segasg1000', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-segasg1000/db/db.json.zip', title='Sega SG-1000 Manuals')
        self.MANUALSDB_SMS = Database(db_id='ajgowans/manualsdb-sms', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-sms/db/db.json.zip', title='SMS Manuals')
        self.MANUALSDB_SNES = Database(db_id='ajgowans/manualsdb-snes', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-snes/db/db.json.zip', title='SNES Manuals')
        self.MANUALSDB_SUPERVISION = Database(db_id='ajgowans/manualsdb-supervision', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-supervision/db/db.json.zip', title='Supervision Manuals')
        self.MANUALSDB_TURBOGRAFX16 = Database(db_id='ajgowans/manualsdb-turbografx16', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-turbografx16/db/db.json.zip', title='TurboGrafx-16 Manuals')
        self.MANUALSDB_TURBOGRAFXCD = Database(db_id='ajgowans/manualsdb-turbografxcd', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-turbografxcd/db/db.json.zip', title='TurboGrafx CD Manuals')
        self.MANUALSDB_VC4000 = Database(db_id='ajgowans/manualsdb-vc4000', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-vc4000/db/db.json.zip', title='VC 4000 Manuals')
        self.MANUALSDB_VECTREX = Database(db_id='ajgowans/manualsdb-vectrex', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-vectrex/db/db.json.zip', title='Vectrex Manuals')
        self.MANUALSDB_WONDERSWANC = Database(db_id='ajgowans/manualsdb-wonderswanc', db_url='https://raw.githubusercontent.com/ajgowans/manualsdb-wonderswanc/db/db.json.zip', title='WonderSwan Color Manuals')

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

def ajgowans_manualsdbs() -> List[Database]:
    dbs = AllDBs()
    return [getattr(dbs, name) for name, db_id in ALL_DB_IDS.items() if db_id.startswith('ajgowans/manualsdb-')]

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

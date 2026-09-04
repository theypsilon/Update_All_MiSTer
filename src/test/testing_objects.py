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
from pathlib import Path

from update_all.constants import MEDIA_FAT, DOWNLOADER_INI_STANDARD_PATH, FILE_update_all_ini, \
    FILE_update_names_txt_ini, FILE_update_jtcores_ini, ARCADE_ORGANIZER_INI, FILE_update_all_zipped_storage, \
    DOWNLOADER_STORE_STANDARD_PATH, FILE_update_all_storage, FILE_pocket_firmware_details_json, \
    DOWNLOADER_AJGOWANS_MANUALSDB_INI, DOWNLOADER_CHIPSTER6502_ARTWORKDB_INI
from update_all.databases import all_dbs, ajgowans_manualsdbs, chipster6502_artworkdbs

downloader_ini = f'{MEDIA_FAT}/{DOWNLOADER_INI_STANDARD_PATH}'
manuals_ini = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'
artwork_ini = f'{MEDIA_FAT}/{DOWNLOADER_CHIPSTER6502_ARTWORKDB_INI}'
downloader_store = f'{MEDIA_FAT}/{DOWNLOADER_STORE_STANDARD_PATH}'
update_all_ini = f'{MEDIA_FAT}/{FILE_update_all_ini}'
update_names_txt_ini = f'{MEDIA_FAT}/{FILE_update_names_txt_ini}'
update_jtcores_ini = f'{MEDIA_FAT}/{FILE_update_jtcores_ini}'
update_arcade_organizer_ini = f'{MEDIA_FAT}/{ARCADE_ORGANIZER_INI}'
pocket_firmware_details_json = f'{MEDIA_FAT}/{FILE_pocket_firmware_details_json}'
store_json_zip = f'{MEDIA_FAT}/{FILE_update_all_zipped_storage}'
store_json = f'{MEDIA_FAT}/{FILE_update_all_storage}'

def ini_with_db_ids(*db_ids: str) -> str:
    dbs_by_id = {db.db_id: db for db in all_dbs('').all_dbs_list()}
    return '\n'.join(f'[{db_id}]\ndb_url = {db_url_for(db_id, dbs_by_id)}\n' for db_id in db_ids)


def db_url_for(db_id: str, dbs_by_id) -> str:
    if db_id in dbs_by_id:
        return dbs_by_id[db_id].db_url

    return 'https://example.com/external-db.json.zip'


def all_manuals_db_ids() -> list[str]:
    return [db.db_id for db in ajgowans_manualsdbs()]


def all_artwork_db_ids() -> list[str]:
    return [db.db_id for db in chipster6502_artworkdbs()]


def default_downloader_ini_content():
    return Path('test/fixtures/downloader_ini/default_downloader.ini').read_text()


def downloader_ini_content_only_update_all_db():
    return Path('test/fixtures/downloader_ini/downloader_ini_empty_but_update_all.ini').read_text()

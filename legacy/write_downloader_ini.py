#!/bin/python3
# Copyright (c) 2020-2021 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

import sys
import os
import configparser
import json
import re

def main():
    db_url_mister_devel_distribution_mister = 'https://raw.githubusercontent.com/MiSTer-devel/Distribution_MiSTer/main/db.json.zip'
    db_url_mister_db9_distribution_mister = 'https://raw.githubusercontent.com/MiSTer-DB9/Distribution_MiSTer/main/dbencc.json.zip'
    db_id_distribution_mister = 'distribution_mister'

    db_url_jtbin_jtcores = 'https://raw.githubusercontent.com/theypsilon/JT_Cores_MiSTer/jtbin/jtbindb.json.zip'
    db_url_jtstable_jtcores = 'https://raw.githubusercontent.com/theypsilon/JT_Cores_MiSTer/jtstable/jtstabledb.json.zip'
    db_id_jtcores = 'jtcores'

    db_url_llapi_folder = 'https://raw.githubusercontent.com/MiSTer-LLAPI/LLAPI_folder_MiSTer/main/llapidb.json.zip'
    db_id_llapi_folder = 'llapi_folder'

    db_url_theypsilon_unofficial_distribution = 'https://raw.githubusercontent.com/theypsilon/Distribution_Unofficial_MiSTer/main/unofficialdb.json.zip'
    db_id_theypsilon_unofficial_distribution = 'theypsilon_unofficial_distribution'

    db_url_arcade_offset_folder = 'https://raw.githubusercontent.com/theypsilon/Arcade_Offset_Folder_MiSTer/db/arcadeoffsetdb.json.zip'
    db_id_arcade_offset_folder = 'arcade_offset_folder'

    def env(name):
        return os.environ.get(name, 'false') == 'true'

    def log(text=''):
        if env('TEST'):
            print(text)

    main_updater = env('MAIN_UPDATER')
    encc_forks = env('ENCC_FORKS')
    jotego_updater = env('JOTEGO_UPDATER')
    download_beta_cores = env('DOWNLOAD_BETA_CORES')
    unofficial_updater = env('UNOFFICIAL_UPDATER')
    llapi_updater = env('LLAPI_UPDATER')
    arcade_offset_downloader = env('ARCADE_OFFSET_DOWNLOADER')


    ini_path = sys.argv[1]

    if not env('TEST') and (ini_path != '/media/fat/downloader.ini' or ini_path != '/tmp/downloader.ini'):
        print('Try: export TEST=true')
        raise Exception('Improper call to this script.')

    ini = {}
    before = ''
    try:
        config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
        config.read(ini_path)
        ini = {header.lower(): {k.lower(): v for k, v in section.items()} for header, section in config.items() if header.lower() != 'default'}
        before = json.dumps(ini)
    except Exception as e:
        print('Could not read ini file %s' % ini_path)

    def section(id):
        if id not in ini:
            ini[id] = {}
        return ini[id]

    key_db_url = 'db_url'

    if main_updater:
        section(db_id_distribution_mister)[key_db_url] = db_url_mister_db9_distribution_mister if encc_forks else db_url_mister_devel_distribution_mister
    elif db_id_distribution_mister in ini:
        ini.pop(db_id_distribution_mister)

    if jotego_updater:
        section(db_id_jtcores)[key_db_url] = db_url_jtbin_jtcores if download_beta_cores else db_url_jtstable_jtcores
    elif db_id_jtcores in ini:
        ini.pop(db_id_jtcores)

    if unofficial_updater:
        section(db_id_theypsilon_unofficial_distribution)[key_db_url] = db_url_theypsilon_unofficial_distribution
    elif db_id_theypsilon_unofficial_distribution in ini:
        ini.pop(db_id_theypsilon_unofficial_distribution)

    if llapi_updater:
        section(db_id_llapi_folder)[key_db_url] = db_url_llapi_folder
    elif db_id_llapi_folder in ini:
        ini.pop(db_id_llapi_folder)

    if arcade_offset_downloader:
        section(db_id_arcade_offset_folder)[key_db_url] = db_url_arcade_offset_folder
    elif db_id_arcade_offset_folder in ini:
        ini.pop(db_id_arcade_offset_folder)

    after = json.dumps(ini)

    if before == after:
        log('No changes')
    else:
        mister_section = ''
        if 'mister' in ini:
            ini.pop('mister')
            header_regex = re.compile('\s*\[([-_a-z0-9]+)\].*', re.I)
            with open(ini_path, 'r') as configfile:
                on_mister = False
                
                for line in configfile.readlines():
                    match = header_regex.match(line)
                    if on_mister:
                        if bool(match):
                            break
                        mister_section += line
                    else:
                        if bool(match) and match[1].lower() == 'mister':
                            on_mister = True
                            mister_section += line

        config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
        for header, section in ini.items():
            config[header] = section

        with open(ini_path, 'w') as configfile:
            if mister_section != '':
                configfile.write(mister_section.strip() + '\n\n')
            config.write(configfile)
        
        log('Written changes on ' + ini_path)

if __name__ == '__main__':
    main()

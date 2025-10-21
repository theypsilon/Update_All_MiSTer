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

from update_all.config import Config
from update_all.constants import FILE_names_txt
from update_all.encryption import Encryption, EncryptionResult
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.other import GenericProvider

import tempfile
import json
from typing import Any


class Timeline:
    def __init__(self, logger: Logger, config_provider: GenericProvider[Config], file_system: FileSystem, encryption: Encryption):
        self._logger = logger
        self._config_provider = config_provider
        self._file_system = file_system
        self._encryption = encryption
        self._names_dict = {}

    def load_timeline_doc(self, env_check_skip: bool = False) -> list[str]:
        config = self._config_provider.get()

        timeline_plus_model = None
        timeline_model = None
        if not self._file_system.is_file(config.timeline_plus_path):
            self._logger.debug('timeline_plus_path does not exist:', config.timeline_plus_path)
        else:
            with tempfile.NamedTemporaryFile() as temp_file:
                if env_check_skip:
                    self._logger.debug('Skipping environment check for timeline decryption')
                    self._encryption.skip_environment_check()
                decrypt_result = self._encryption.decrypt_file(config.timeline_plus_path, temp_file.name)
                if decrypt_result == EncryptionResult.Success:
                    timeline_plus_model = self._file_system.load_dict_from_file(temp_file.name, '.json')
                else:
                    self._logger.debug(f'Could not decrypt timeline_plus_file: {decrypt_result}')
        if timeline_plus_model is None:
            if not self._file_system.is_file(config.timeline_short_path):
                self._logger.debug('timeline_short_path does not exist:', config.timeline_short_path)
            else:
                timeline_model = self._file_system.load_dict_from_file(config.timeline_short_path, '.json')

        names_dict = self._load_names_dict(FILE_names_txt)

        if timeline_model is not None:
            timeline_doc = create_timeline_doc(timeline_model, names_dict)
            timeline_doc.append("\n")
            timeline_doc.append("[!!] This Timeline only covers the latest 7 days of updates [!!]\n")
            timeline_doc.append("\n")
            if self._file_system.is_file(config.patreon_key_path):
                timeline_doc.append("Your Patreon Key is expired since 2025-10-17!\n")
                timeline_doc.append("Get a new Patreon Key at www.patreon.com/theypsilon\n")
                timeline_doc.append("And you'll unlock an extended Timeline of 12 months!\n")
                timeline_doc.append("\n")
                timeline_doc.append("<theypsilon> Thank you so much for supporting my work!!\n")
            else:
                timeline_doc.append("For an extended Timeline of 12 months:\n")
                timeline_doc.append(" • Get your Patreon Key at www.patreon.com/theypsilon\n")
                timeline_doc.append(" • Place it at /media/fat/Scripts/update_all.patreonkey\n")
                timeline_doc.append("\n")
        elif timeline_plus_model is not None:
            timeline_doc = create_timeline_doc(timeline_plus_model, names_dict)
            timeline_doc.append("\n")
            timeline_doc.append("<theypsilon> That's all! Thank you so much for supporting my work!!\n")
        else:
            timeline_doc = []

        return timeline_doc

    def _load_names_dict(self, names_path: str) -> dict[str, str]:
        names_dict = {}

        if self._file_system.is_file(names_path) is False:
            self._logger.debug(f"Names file {names_path} does not exist, skipping name mappings")
            return names_dict

        try:
            names_txt: str = self._file_system.read_file_contents(names_path)
            for line in names_txt.splitlines():
                line = line.strip()
                if not line or ':' not in line:
                    continue

                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key and value:
                    names_dict[key] = value
        except Exception as e:
            self._logger.debug(f"Error reading names file {names_path}.")
            self._logger.debug(e)

        return names_dict

def create_timeline_doc(model, names_dict: dict[str, str]):
    doc = []
    sections = model.get("sections", [])

    doc.append("=" * 80 + "\n")
    doc.append("================================================================================\n")
    doc.append("=============  ====  =       ==       =====  ====        =        ==============\n")
    doc.append("=============  ====  =  ====  =  ====  ===    ======  ====  ====================\n")
    doc.append("=============  ====  =  ====  =  ====  ==  ==  =====  ====  ====================\n")
    doc.append("=============  ====  =  ====  =  ====  =  ====  ====  ====  ====================\n")
    doc.append("=============  ====  =       ==  ====  =  ====  ====  ====      ================\n")
    doc.append("=============  ====  =  =======  ====  =        ====  ====  ====================\n")
    doc.append("=============  ====  =  =======  ====  =  ====  ====  ====  ====================\n")
    doc.append("=============   ==   =  =======  ====  =  ====  ====  ====  ====================\n")
    doc.append("==============      ==  =======       ==  ====  ====  ====        ==============\n")
    doc.append("================================================================================\n")
    doc.append("################################################################################\n")
    doc.append("#######        #    #  #####  #        #  #######    #  #######  #        ######\n")
    doc.append("##########  #####  ##   ###   #  #######  ########  ##   ######  #  ############\n")
    doc.append("##########  #####  ##  #   #  #  #######  ########  ##    #####  #  ############\n")
    doc.append("##########  #####  ##  ## ##  #  #######  ########  ##  ##  ###  #  ############\n")
    doc.append("##########  #####  ##  #####  #      ###  ########  ##  ###  ##  #      ########\n")
    doc.append("##########  #####  ##  #####  #  #######  ########  ##  ####  #  #  ############\n")
    doc.append("##########  #####  ##  #####  #  #######  ########  ##  #####    #  ############\n")
    doc.append("##########  #####  ##  #####  #  #######  ########  ##  ######   #  ############\n")
    doc.append("##########  ####    #  #####  #        #        #    #  #######  #        ######\n")
    doc.append("################################################################################\n")
    doc.append("#" * 80 + "\n")
    doc.append("\n")

    if not sections:
        doc.append(model.get("summary", {}).get("no_sections_msg", "Timeline is empty."))
        return doc

    for section in sections:
        add_doc_section(doc, section, names_dict)

    doc.append("=" * 80 + "\n")

    return doc

def add_doc_section(doc: list[str], section: dict[str, Any], names_dict: dict[str, str]):
    title = section["title"]
    categories = section.get("categories", [])

    if not categories:
        return

    doc.append(f'>>> {title.upper()}:\n')
    doc.append("-" * 60 + "\n")

    for category in categories:
        formatted_category = category['category']
        if formatted_category in ('system'):
            formatted_category = f"{formatted_category.capitalize()} file"
        else:
            formatted_category = formatted_category.capitalize()

        if len(category["files"]) > 1:
            if formatted_category == 'utility':
                formatted_category = 'Utilities'
            else:
                formatted_category += 's'
            doc.append(f' [{formatted_category}]\n')
            for file_entry in category["files"]:
                formatted_file = format_file_entry(file_entry, names_dict)
                if not formatted_file:
                    continue

                doc.append(f"  • {formatted_file}\n")

        elif len(category["files"]) == 1:
            file_entry = category["files"][0]
            formatted_file = format_file_entry(file_entry, names_dict)
            doc.append(f" [{formatted_category}] {formatted_file}\n")

        doc.append("\n")

def format_file_entry(file_entry, names_dict):
    if file_entry["type"] == "standalone":
        name = file_entry["name"]
        return names_dict.get(name, name)

    return ""


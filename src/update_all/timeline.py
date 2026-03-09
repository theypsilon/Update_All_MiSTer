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

from update_all.config import Config
from update_all.constants import FILE_names_txt, FILE_timeline_plus2
from update_all.encryption import Encryption, EncryptionResult
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.other import GenericProvider, terminal_size
from update_all.retroaccount import RetroAccountService

import tempfile
from typing import Any



class Timeline:
    def __init__(self, logger: Logger, config_provider: GenericProvider[Config], file_system: FileSystem, encryption: Encryption, retroaccount: RetroAccountService):
        self._logger = logger
        self._config_provider = config_provider
        self._file_system = file_system
        self._encryption = encryption
        self._retroaccount = retroaccount
        self._names_dict = {}

    def load_timeline_doc(self, env_check_skip: bool = False) -> list[str]:
        config = self._config_provider.get()

        timeline_model = None
        timeline_plus_model = None
        not_yet_updated = False

        if self._file_system.is_file(config.timeline_plus_path):
            with tempfile.NamedTemporaryFile() as temp_file:
                if env_check_skip:
                    self._logger.debug('Timeline: Skipping environment check for timeline decryption')
                    self._encryption.skip_environment_check()

                timeline_plus_model, not_yet_updated = self._extract_plus_model(config.timeline_plus_path, temp_file.name)
                if not_yet_updated and self._file_system.is_file(FILE_timeline_plus2):
                    self._logger.debug("Timeline: Attempting to extract from timeline_plus2.")
                    timeline_plus_model, not_yet_updated = self._extract_plus_model(FILE_timeline_plus2, temp_file.name)

        if timeline_plus_model is None and self._file_system.is_file(config.timeline_short_path):
            timeline_model = self._file_system.load_dict_from_file(config.timeline_short_path, '.json')

        names_dict = self._load_names_dict(FILE_names_txt)

        if timeline_model is not None:
            timeline_doc = create_timeline_doc(timeline_model, names_dict)
            timeline_doc.append("\n")
            timeline_doc.append("[!!] This Timeline only covers the latest 7 days of updates [!!]\n")
            timeline_doc.append("\n")
            if not_yet_updated:
                timeline_doc.append("The Extended Timeline is being calculated, try again soon!:\n")
            else:
                timeline_doc.append("For an extended Timeline of 12 months:\n")
                timeline_doc.append(" • Support www.patreon.com/theypsilon\n")
                timeline_doc.append(" • Login in the Settings Screen\n")
            timeline_doc.append("\n")
        elif timeline_plus_model is not None:
            timeline_doc = create_timeline_doc(timeline_plus_model, names_dict)
            timeline_doc.append("\n")
            timeline_doc.append("<theypsilon> That's all! Thank you so much for supporting my work!!\n")
        else:
            timeline_doc = []

        return timeline_doc

    def _extract_plus_model(self, timeline_plus_model_path: str, output: str) -> tuple[Any, bool]:
        timeline_plus_model = None
        not_yet_updated = False

        decrypt_result = self._encryption.decrypt_file(timeline_plus_model_path, output)
        if decrypt_result == EncryptionResult.Success:
            timeline_plus_model = self._file_system.load_dict_from_file(output, '.json')
        elif decrypt_result == EncryptionResult.MissingKey:
            pass
        elif decrypt_result == EncryptionResult.InvalidKey:
            if self._retroaccount.is_update_all_extras_active():
                not_yet_updated = True
                self._logger.debug("Timeline: Your Patreon Key is not yet updated.")
            else:
                self._logger.debug("Timeline: Your Patreon Key is expired.")
        elif decrypt_result == EncryptionResult.ImproperEnvironment:
            self._logger.debug('Timeline: Please run Update All on MiSTer to load the Extended Update Timeline.')
        else:
            self._logger.debug(f'Timeline: Could not decrypt timeline_plus_file: {decrypt_result}')

        return timeline_plus_model, not_yet_updated

    def _load_names_dict(self, names_path: str) -> dict[str, str]:
        names_dict = {}

        if self._file_system.is_file(names_path) is False:
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
            self._logger.debug(f"Timeline: Error reading names file {names_path}.")
            self._logger.debug(e)

        return names_dict

def create_timeline_doc(model, names_dict: dict[str, str]):
    doc = []
    sections = model.get("sections", [])

    ts = terminal_size()
    columns = ts.columns - ts.cols_overscan * 2
    if columns < 80:
        doc.append("        ".center(columns))
        doc.append(" UPDATE ".center(columns))
        doc.append("TIMELINE".center(columns))
        doc.append("        ".center(columns))
    else:
        def _pad(line, fill):
            left = (columns - len(line)) // 2
            right = columns - len(line) - left
            return fill * left + line + fill * right + "\n"

        doc.append("\n")
        doc.append("=" * columns + "\n")
        for line in [
            "================================================================================",
            "=============  ====  =       ==       =====  ====        =        ==============",
            "=============  ====  =  ====  =  ====  ===    ======  ====  ====================",
            "=============  ====  =  ====  =  ====  ==  ==  =====  ====  ====================",
            "=============  ====  =  ====  =  ====  =  ====  ====  ====  ====================",
            "=============  ====  =       ==  ====  =  ====  ====  ====      ================",
            "=============  ====  =  =======  ====  =        ====  ====  ====================",
            "=============  ====  =  =======  ====  =  ====  ====  ====  ====================",
            "=============   ==   =  =======  ====  =  ====  ====  ====  ====================",
            "==============      ==  =======       ==  ====  ====  ====        ==============",
            "================================================================================",
        ]:
            doc.append(_pad(line, "="))
        for line in [
            "################################################################################",
            "#######        #    #  #####  #        #  #######    #  #######  #        ######",
            "##########  #####  ##   ###   #  #######  ########  ##   ######  #  ############",
            "##########  #####  ##  #   #  #  #######  ########  ##    #####  #  ############",
            "##########  #####  ##  ## ##  #  #######  ########  ##  ##  ###  #  ############",
            "##########  #####  ##  #####  #      ###  ########  ##  ###  ##  #      ########",
            "##########  #####  ##  #####  #  #######  ########  ##  ####  #  #  ############",
            "##########  #####  ##  #####  #  #######  ########  ##  #####    #  ############",
            "##########  #####  ##  #####  #  #######  ########  ##  ######   #  ############",
            "##########  ####    #  #####  #        #        #    #  #######  #        ######",
            "################################################################################",
        ]:
            doc.append(_pad(line, "#"))
        doc.append("#" * columns + "\n")
        doc.append("\n")

    if not sections:
        doc.extend(model.get("summary", {}).get("no_sections_msg", ["Timeline is empty."]))
        return doc

    for section in sections:
        add_doc_section(doc, section, names_dict)

    ts = terminal_size()
    doc.append("=" * (ts.columns - ts.cols_overscan * 2) + "\n")

    return doc

def add_doc_section(doc: list[str], section: dict[str, Any], names_dict: dict[str, str]):
    title = section["title"]
    categories = section.get("categories", [])

    if not categories:
        return

    doc.append(f'>>> {title.upper()}:\n')
    ts = terminal_size()
    doc.append("-" * (ts.columns - ts.cols_overscan * 2) + "\n")

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


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
from collections import OrderedDict
from typing import Optional, Dict, Iterable, Iterator, List, Tuple

from update_all.config import Config
from update_all.constants import DOWNLOADER_INI_STANDARD_PATH, ARCADE_ORGANIZER_INI, DOWNLOADER_STORE_STANDARD_PATH, \
    DOWNLOADER_BIOS_DB_INI, DOWNLOADER_ARCADE_ROMS_DB_INI, DOWNLOADER_AJGOWANS_MANUALSDB_INI, \
    DOWNLOADER_CHIPSTER6502_ARTWORKDB_INI
from update_all.databases import Database, DB_ID_DISTRIBUTION_MISTER, all_dbs, ALL_DB_IDS, ajgowans_manualsdbs, \
    chipster6502_artworkdbs, chipster6502_artwork_db_with_style, coin_op_collection_filter_by_releases
from update_all.downloader_ini_document import DownloaderIniDocument, IniSection, RepeatedSection
from update_all.downloader_ini_reader import DownloaderIniReader, IniSections, first_definitions, read_ini_contents, \
    sort_drop_in_ini_paths
from update_all.file_system import FileSystem
from update_all.other import str_to_bool
from update_all.ini_parser import IniParser
from update_all.logger import Logger
from update_all.os_utils import OsUtils

SEPARATE_DB_INI_FILES: Dict[str, str] = {
    ALL_DB_IDS['BIOS'].lower(): DOWNLOADER_BIOS_DB_INI,
    ALL_DB_IDS['ARCADE_ROMS'].lower(): DOWNLOADER_ARCADE_ROMS_DB_INI,
    **{db.db_id.lower(): DOWNLOADER_CHIPSTER6502_ARTWORKDB_INI for db in chipster6502_artworkdbs()},
    **{db.db_id.lower(): DOWNLOADER_AJGOWANS_MANUALSDB_INI for db in ajgowans_manualsdbs()},
}


def _build_separate_db_ini_files_by_filename() -> Dict[str, List[str]]:
    lower_to_canonical = {db_id.lower(): db_id for db_id in ALL_DB_IDS.values()}
    result: Dict[str, List[str]] = {}
    for lower_id, filename in SEPARATE_DB_INI_FILES.items():
        result.setdefault(filename, []).append(lower_to_canonical.get(lower_id, lower_id))
    return result


SEPARATE_DB_INI_FILES_BY_FILENAME: Dict[str, List[str]] = _build_separate_db_ini_files_by_filename()


class IniRepository:

    def __init__(self, logger: Logger, file_system: FileSystem, os_utils: OsUtils, downloader_ini_reader: DownloaderIniReader):
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._downloader_ini_reader = downloader_ini_reader
        self._base_path = None
        self._downloader_ini = None
        self._arcade_organizer_ini = None
        self._resolved_database_sections: Dict[str, IniParser] = {}

    def initialize_downloader_ini_base_path(self, base_path: str) -> None:
        self._base_path = base_path

    def get_downloader_ini(self, cached: bool = True) -> Dict[str, Dict[str, str]]:
        if cached and self._downloader_ini is not None:
            return self._downloader_ini

        result, _ = self._read_downloader_ini()
        if cached:
            self._downloader_ini = result
        return result

    def get_arcade_organizer_ini(self, cached: bool = True) -> IniParser:
        if cached and self._arcade_organizer_ini is not None:
            return self._arcade_organizer_ini

        result = self.read_old_ini_file(ARCADE_ORGANIZER_INI)
        if cached:
            self._arcade_organizer_ini = result
        return result

    def _read_downloader_ini(self) -> Tuple[IniSections, List[RepeatedSection]]:
        contents = self._read_downloader_ini_rawtext()
        if contents is None:
            return {}, []
        document = DownloaderIniDocument(contents)
        return self._downloader_sections(document), document.repeated_sections

    def _downloader_sections(self, document: DownloaderIniDocument) -> IniSections:
        path = self.downloader_ini_standard_path()
        try:
            return document.section_values(literal_percent=True)
        except Exception as e:
            self._logger.debug(f'Could not read Downloader INI file at: {path}')
            self._logger.debug(f'contents: {document.original}')
            self._logger.debug(e)
            return {}

    def _read_downloader_ini_rawtext(self) -> Optional[str]:
        path = self.downloader_ini_standard_path()
        contents = ''
        try:
            return self._file_system.read_file_contents(path)
        except Exception as e:
            self._logger.debug(f'Could not read Downloader INI file at: {path}')
            self._logger.debug(f'contents: {contents}')
            self._logger.debug(e)
            return None

    def read_old_ini_file(self, path: str) -> IniParser:
        if not self._file_system.is_file(path):
            return IniParser({})

        contents = ''
        try:
            contents = f'[default]\n{self._file_system.read_file_contents(path).lower()}'
            parser = read_ini_contents(contents)
        except Exception as e:
            self._logger.debug(f'Incorrect old INI format at: {path}')
            self._logger.debug(f'contents: {contents}')
            self._logger.debug(e)
            return IniParser({})

        return IniParser(parser['default'])

    def downloader_ini_standard_path(self) -> str:
        if self._base_path is None:
            raise IniRepositoryInitializationError("DownloaderIniRepository needs to be initialized.")

        return f'{self._base_path}/{DOWNLOADER_INI_STANDARD_PATH}'

    def downloader_store_standard_path(self) -> str:
        if self._base_path is None:
            raise IniRepositoryInitializationError("DownloaderIniRepository needs to be initialized.")

        return f'{self._base_path}/{DOWNLOADER_STORE_STANDARD_PATH}'

    def write_downloader_ini(self, config: Config) -> None:
        self.refresh_database_sources(config)
        document = self._main_document_for_save()
        if document is None:
            return
        changed, repeated = self._edit_downloader_document(document, config, candidate_databases(config))
        if changed:
            self._save_ini_document(self.downloader_ini_standard_path(), document, separate_sections=True, ending='\n\n')
            self._log_repeated_sections(self.downloader_ini_standard_path(), repeated)

    def _main_document_for_save(self) -> Optional[DownloaderIniDocument]:
        if not self._file_system.is_file(self.downloader_ini_standard_path()):
            return DownloaderIniDocument('')
        contents = self._read_downloader_ini_rawtext()
        return DownloaderIniDocument(contents) if contents is not None else None

    def _save_ini_document(self, path: str, document: DownloaderIniDocument, *, delete_empty: bool = False,
                           separate_sections: bool = False, ending: Optional[str] = None) -> None:
        contents = document.render(separate_sections=separate_sections, ending=ending)
        if delete_empty and not contents.strip():
            if self._file_system.is_file(path):
                self._file_system.unlink(path, verbose=False)
        elif contents != document.original:
            self._file_system.make_dirs_parent(path)
            self._file_system.write_file_contents(path, contents)
        else:
            return
        document.original = contents
        if path == self.downloader_ini_standard_path():
            self._downloader_ini = None

    def _log_repeated_sections(self, path: str, repeated_sections: Dict[str, str]) -> None:
        for section, contents in repeated_sections.items():
            self._logger.print(f'WARNING! Section [{section}] was repeated in {path}, only the first one has been kept.')
            self._logger.debug('Repeated section removed from ', path, ':\n', contents)

    def replace_db_ids_in_ini_and_fs(self, changed_ids: Dict[str, str], downloader_ini: Dict[str, IniParser]) -> None:
        downloader_ini_txt = self._read_downloader_ini_rawtext()
        if downloader_ini_txt is None:
            self._logger.debug(f'WARNING! Could not replace db_id because downloader ini is not readable.')
            return

        document = DownloaderIniDocument(downloader_ini_txt)
        replaced_ids, removed_sections = document.rename_sections(changed_ids)

        if len(replaced_ids) == 0:
            self._logger.debug(f'WARNING! Could not replace db_id because downloader ini does not contain it.')
            return

        # Updating downloader.ini
        self._save_ini_document(self.downloader_ini_standard_path(), document, ending='')
        for old_id in removed_sections:
            self._logger.print(f'WARNING! Section [{old_id}] has been removed from {self.downloader_ini_standard_path()} because [{changed_ids[old_id]}] was already there.')
        if removed_sections:
            self._logger.debug('Sections removed from ', self.downloader_ini_standard_path(), ':\n', ''.join(removed_sections.values()).removesuffix('\n'))

        # Updating downloader_ini object
        for old_id in replaced_ids:
            new_id = changed_ids[old_id]
            if new_id.lower() not in downloader_ini:
                downloader_ini[new_id.lower()] = downloader_ini[old_id.lower()]
            del downloader_ini[old_id.lower()]

        # Updating downloader store from now on:
        store_path = self.downloader_store_standard_path()
        if not self._file_system.is_file(store_path):
            return

        store = self._file_system.load_dict_from_file(store_path)
        if 'dbs' not in store:
            self._logger.debug(f'Downloader store was not initialized yet.')
            return

        replaced_stores = []
        for old_id in replaced_ids:
            new_id = changed_ids[old_id]
            self._logger.debug(f'Replacing db_id {old_id} with {new_id} in downloader store.')
            if old_id.lower() in store['dbs']:
                replaced_stores.append((old_id.lower(), new_id.lower()))

        if len(replaced_stores) == 0:
            self._logger.debug(f'Could not replace any db_id because downloader store does not contain it.')
            return

        for old_id, new_id in replaced_stores:
            store['dbs'][new_id] = store['dbs'][old_id]
            del store['dbs'][old_id]

        self._file_system.save_json(store, store_path)

    def remove_db_ids_in_ini_and_fs(self, removed_ids: set[str], downloader_ini: Dict[str, IniParser]) -> None:
        downloader_ini_txt = self._read_downloader_ini_rawtext()
        if downloader_ini_txt is None:
            self._logger.debug(f'WARNING! Could not replace db_id because downloader ini is not readable.')
            return

        # Updating downloader.ini
        document = DownloaderIniDocument(downloader_ini_txt)
        document.remove_sections(removed_ids)
        self._save_ini_document(self.downloader_ini_standard_path(), document, ending='')

        # Updating downloader_ini object
        for rem_id in removed_ids:
            del downloader_ini[rem_id.lower()]

        # Updating downloader store from now on:
        store_path = self.downloader_store_standard_path()
        if not self._file_system.is_file(store_path):
            return

        store = self._file_system.load_dict_from_file(store_path)
        if 'dbs' not in store:
            self._logger.debug(f'Downloader store was not initialized yet.')
            return

        removed_stores = []
        for rem_id in removed_ids:
            self._logger.debug(f'Removing db_id {rem_id} in downloader store.')
            if rem_id.lower() in store['dbs']:
                removed_stores.append(rem_id.lower())

        if len(removed_stores) == 0:
            self._logger.debug(f'Could not remove any db_id because downloader store does not contain it.')
            return

        for old_id in removed_stores:
            del store['dbs'][old_id]

        self._file_system.save_json(store, store_path)

    def extract_dbs_to_separate_ini(self, db_ids: List[str], target_ini_filename: str, downloader_ini: Dict[str, IniParser]) -> List[str]:
        lower_to_canonical = {db_id.lower(): db_id for db_id in db_ids}
        present = [db_id for db_id in db_ids if db_id.lower() in downloader_ini]
        if not present:
            return []

        downloader_ini_txt = self._read_downloader_ini_rawtext()
        if downloader_ini_txt is None:
            self._logger.debug(f'WARNING! Could not extract dbs because downloader ini is not readable.')
            return []

        source = DownloaderIniDocument(downloader_ini_txt)
        if not any(name in source.sections for name in lower_to_canonical):
            return []

        target_path = f'{self._base_path}/{target_ini_filename}'
        target = self._read_separate_document(target_path)
        if target is None:
            return []

        repeated_sections = source.deduplicate(lower_to_canonical)
        extracted_sections = source.remove_sections(lower_to_canonical)
        target.deduplicate()
        target.put_sections({lower_to_canonical[name]: section for name, section in extracted_sections.items()})

        self._save_ini_document(target_path, target, separate_sections=True, ending='\n')
        self._save_ini_document(self.downloader_ini_standard_path(), source, ending='\n')
        self._log_repeated_sections(self.downloader_ini_standard_path(), repeated_sections)

        for lower_id in extracted_sections:
            if lower_id in downloader_ini:
                del downloader_ini[lower_id]

        return [lower_to_canonical[lid] for lid in extracted_sections if lid in lower_to_canonical]

    def _read_separate_document(self, target_path: str) -> Optional[DownloaderIniDocument]:
        # None means that the file is there but could not be read, so it must not be overwritten.
        if not self._file_system.is_file(target_path):
            return DownloaderIniDocument('')

        try:
            return DownloaderIniDocument(self._file_system.read_file_contents(target_path))
        except Exception as e:
            self._logger.debug(f'Could not read existing separate DB INI file at: {target_path}')
            self._logger.debug(e)
            return None

    def read_extra_db_ini_files(self) -> Tuple[Dict[str, IniParser], Dict[str, List[str]]]:
        """Scans every ini file that the MiSTer Downloader picks up besides downloader.ini, namely
        '{base_path}/downloader_*.ini' and '{base_path}/downloader/*.ini' (non-hidden), and returns:
          - sections: db_id (lower case) -> parsed section (first file wins on duplicates)
          - sources:  db_id (lower case) -> list of relative file paths where it was found, excluding the
            dedicated file of that database, which Update All writes. Anywhere else the database is "read-only"
            for adds: it is reflected in the settings screen and removed from there when toggled off, but
            never written to when toggled on."""
        sections, sources = self._extra_sections(self._iter_extra_documents())
        return {db_id: IniParser(section) for db_id, section in sections.items()}, self._external_sources(sources)

    def _read_extra_document(self, relative_path: str) -> Optional[DownloaderIniDocument]:
        target_path = relative_path if relative_path.startswith('/') else f'{self._extra_db_ini_base_path()}/{relative_path}'
        try:
            return DownloaderIniDocument(self._file_system.read_file_contents(target_path))
        except Exception as e:
            self._logger.debug(f'Could not read DB INI file at: {target_path}')
            self._logger.debug(e)
            return None

    def _iter_extra_documents(self) -> Iterator[Tuple[str, Optional[DownloaderIniDocument]]]:
        for path in self._downloader_ini_reader.drop_in_ini_paths(self._extra_db_ini_base_path()):
            yield path, self._read_extra_document(path)

    def _extra_sections(self, documents: Iterable[Tuple[str, Optional[DownloaderIniDocument]]]) -> Tuple[IniSections, Dict[str, List[str]]]:
        readable_files: List[Tuple[str, IniSections]] = []
        for relative_path, document in documents:
            if document is None:
                continue
            try:
                readable_files.append((relative_path, document.section_values(literal_percent=True)))
            except Exception as e:
                self._logger.debug(f'Could not read DB INI file at: {self._extra_db_ini_base_path()}/{relative_path}')
                self._logger.debug(e)

        return first_definitions(readable_files)

    @staticmethod
    def _external_sources(all_sources: Dict[str, List[str]]) -> Dict[str, List[str]]:
        sources: Dict[str, List[str]] = {}
        for db_id, relative_paths in all_sources.items():
            not_owned = [path for path in relative_paths if path.lower() != SEPARATE_DB_INI_FILES.get(db_id, '').lower()]
            if len(not_owned) > 0:
                sources[db_id] = not_owned

        return sources

    def resolve_all_database_sections(
            self,
            downloader_ini: Dict[str, IniParser],
    ) -> Tuple[Dict[str, IniParser], Dict[str, List[str]]]:
        extra_ini, extra_sources = self.read_extra_db_ini_files()
        self._resolved_database_sections = {**extra_ini, **downloader_ini}
        return self._resolved_database_sections, extra_sources

    def resolved_database_url(self, db_id: str) -> Optional[str]:
        section = self._resolved_database_sections.get(db_id.lower())
        return section.get_string('db_url', None) if section is not None else None

    def refresh_database_sources(self, config: Config) -> None:
        _, sources = self.read_extra_db_ini_files()
        config.database_sources = sources

    def _extra_db_ini_base_path(self) -> str:
        downloader_ini_path = self.downloader_ini_standard_path()
        suffix = '/' + DOWNLOADER_INI_STANDARD_PATH
        if downloader_ini_path.endswith(suffix):
            return downloader_ini_path[:-len(suffix)]
        return downloader_ini_path.rsplit('/', 1)[0]

    def strip_db_ids_from_extra_files(self, sources: Dict[str, List[str]]) -> None:
        """Removes the given db_id sections from the extra (non-owned) ini files where they live. Files that
        become empty after the removal are deleted. `sources` maps db_id (lower case) -> list of relative paths."""
        paths = dict.fromkeys(path for paths in sources.values() for path in paths)
        documents = {path: self._read_extra_document(path) for path in paths}
        for path in self._remove_extra_sections(sources, documents):
            target = path if path.startswith('/') else f'{self._extra_db_ini_base_path()}/{path}'
            self._save_ini_document(target, documents[path], delete_empty=True, ending='\n')

    @staticmethod
    def _remove_extra_sections(sources: Dict[str, List[str]], documents: Dict[str, Optional[DownloaderIniDocument]]) -> set:
        ids_by_file: Dict[str, set] = {}
        for db_id, relative_paths in sources.items():
            for relative_path in relative_paths:
                ids_by_file.setdefault(relative_path, set()).add(db_id.lower())

        changed = set()
        for path, ids in ids_by_file.items():
            document = documents.get(path)
            if document is not None and document.remove_sections(ids):
                changed.add(path)
        return changed

    def write_separate_db_ini_files(self, config: Config) -> None:
        documents = dict(self._iter_extra_documents())
        sources = self._extra_sections(documents.items())[1]
        preserved = self._preserved_separate_sections(self._main_document_for_save(), documents, sources)
        warnings = self._edit_separate_documents(config, candidate_databases(config), documents, preserved)
        self._save_extra_documents(documents, set(warnings), warnings)

    def _preserved_separate_sections(self, main: Optional[DownloaderIniDocument],
                                     documents: Dict[str, Optional[DownloaderIniDocument]],
                                     sources: Dict[str, List[str]]) -> Dict[str, IniSection]:
        # Keep the complete winning definition before any file is edited. Later
        # definitions must not contribute options that the user was not using.
        sections = {name: documents[paths[0]].sections[name]
                    for name, paths in sources.items() if name in SEPARATE_DB_INI_FILES}
        if main is not None:
            sections.update({name: main.sections[name] for name in self._downloader_sections(main)
                             if name in SEPARATE_DB_INI_FILES})
        return sections

    def _edit_separate_documents(self, config: Config, candidates: List[Tuple[str, Database]],
                                 documents: Dict[str, Optional[DownloaderIniDocument]],
                                 preserved: Dict[str, IniSection]) -> Dict[str, Dict[str, str]]:
        active = {db.db_id.lower(): db for _, db in candidates if db.db_id in config.databases}
        warnings: Dict[str, Dict[str, str]] = {}

        loaded_paths = {path.lower() for path in documents}
        for ini_filename in SEPARATE_DB_INI_FILES_BY_FILENAME:
            if ini_filename.lower() not in loaded_paths:
                documents[ini_filename] = self._read_separate_document(f'{self._base_path}/{ini_filename}')

        # Reuse the discovered spelling and document on case-preserving filesystems.
        for ini_filename, document in documents.items():
            canonical_db_ids = SEPARATE_DB_INI_FILES_BY_FILENAME.get(ini_filename.lower())
            if canonical_db_ids is None or document is None:
                continue
            active_dbs = [active[db_id.lower()] for db_id in canonical_db_ids if db_id.lower() in active]
            warnings[ini_filename] = document.deduplicate()
            document.remove_sections(db_id for db_id in canonical_db_ids if db_id.lower() not in active)
            for db in active_dbs:
                original = preserved.get(db.db_id.lower())
                if original is not None and original is not document.sections.get(db.db_id.lower()):
                    document.put_sections({db.db_id: original})
                options: Dict[str, Optional[str]] = {'db_url': db.db_url}
                if db.db_id.lower() == ALL_DB_IDS['ARCADE_ROMS'].lower():
                    options['filter'] = '!hbmame' if config.hbmame_filter else None
                document.set_options(db.db_id, options)
            document.order_sections(db.db_id for db in active_dbs)
        return warnings

    def _save_extra_documents(self, documents: Dict[str, Optional[DownloaderIniDocument]], paths: set,
                              warnings: Dict[str, Dict[str, str]]) -> None:
        for path in sort_drop_in_ini_paths(paths):
            target = f'{self._extra_db_ini_base_path()}/{path}'
            self._save_ini_document(target, documents[path], delete_empty=True, separate_sections=path in warnings, ending='\n')
            self._log_repeated_sections(target, warnings.get(path, {}))

    def write_database_configuration(self, config: Config) -> None:
        """Persists the complete database selection from config.

        Read a fresh snapshot, apply every edit in memory, then write each changed
        file once. Source discovery and the database catalog are shared by all writers.
        """
        documents = dict(self._iter_extra_documents())
        sources = self._extra_sections(documents.items())[1]
        config.database_sources = self._external_sources(sources)
        candidates = candidate_databases(config)
        main = self._main_document_for_save()
        preserved = self._preserved_separate_sections(main, documents, sources)
        managed_db_ids = {db.db_id.lower() for _, db in candidates}
        inactive_sources = {
            db_id: relative_paths
            for db_id, relative_paths in config.database_sources.items()
            if db_id in managed_db_ids and not config.is_database_enabled(db_id)
        }
        changed_extras = self._remove_extra_sections(inactive_sources, documents)
        changed, repeated = False, {}
        if main is not None:
            changed, repeated = self._edit_downloader_document(main, config, candidates)
        warnings = self._edit_separate_documents(config, candidates, documents, preserved)
        if changed:
            self._save_ini_document(self.downloader_ini_standard_path(), main, separate_sections=True, ending='\n\n')
            self._log_repeated_sections(self.downloader_ini_standard_path(), repeated)
        self._save_extra_documents(documents, changed_extras | set(warnings), warnings)
        extra_sections, sources = self._extra_sections((path, documents[path]) for path in sort_drop_in_ini_paths(documents))
        config.database_sources = self._external_sources(sources)
        main_sections = self._downloader_sections(main) if main is not None else {}
        self._resolved_database_sections = {name: IniParser(values) for name, values in {**extra_sections, **main_sections}.items()}

    def write_arcade_organizer_active_at_arcade_organizer_ini(self, config: Config) -> None:
        contents = ''
        if self._file_system.is_file(ARCADE_ORGANIZER_INI):
            contents = self._file_system.read_file_contents(ARCADE_ORGANIZER_INI).strip()
            if 'arcade_organizer' in contents.lower():
                return
            contents += '\n'

        contents += f'ARCADE_ORGANIZER={str(config.arcade_organizer).lower()}\n'
        self._save_arcade_organizer_contents(contents + '\n')

    def write_arcade_organizer(self, props: Dict[str, str]) -> None:
        contents = ''
        for k, v in props.items():
            contents += f'{k.upper()}={v}\n'
        self._save_arcade_organizer_contents(contents + '\n')

    def _save_arcade_organizer_contents(self, contents):
        self._file_system.make_dirs_parent(ARCADE_ORGANIZER_INI)
        self._file_system.write_file_contents(ARCADE_ORGANIZER_INI, contents)
        self._arcade_organizer_ini = None

    def does_downloader_ini_need_save(self, config: Config) -> bool:
        self.refresh_database_sources(config)
        document = self._main_document_for_save()
        if document is None:
            return False
        changed, _ = self._edit_downloader_document(document, config, candidate_databases(config))
        return changed and document.render().strip().lower() != document.original.strip().lower()

    @staticmethod
    def _add_new_downloader_ini_changes(ini, config: Config, candidates: List[Tuple[str, Database]]) -> None:
        for _, db in candidates:
            db_id = db.db_id.lower()
            if db_id in SEPARATE_DB_INI_FILES:
                if db_id in ini:
                    del ini[db_id]
                continue
            if db.db_id in config.databases:
                if db_id in config.database_sources and db_id not in ini:
                    # Active and defined only in an extra ini file we don't own. Leave it there instead
                    # of materializing a higher-precedence duplicate section in downloader.ini. When
                    # downloader.ini already contains the db, it is the winning definition and must be
                    # updated normally even if ignored duplicates also exist in drop-ins.
                    continue
                if db_id not in ini:
                    ini[db_id] = {}
                ini[db_id]['db_url'] = db.db_url
            elif db_id in ini:
                del ini[db_id]

        for db_id, filter_addition in [(ALL_DB_IDS['RANNYSNICE_WALLPAPERS'], config.rannysnice_wallpapers_filter)]:
            if db_id not in config.databases:
                continue

            if db_id.lower() not in ini:
                continue

            ini[db_id.lower()]['filter'] = filter_addition

        for db_id, beta_cores_active in [(ALL_DB_IDS['JTCORES'], config.download_beta_cores)]:
            if db_id not in config.databases:
                continue

            lower_id = db_id.lower()
            if lower_id not in ini:
                continue

            filter_value = ini[lower_id].get('filter', '').strip().lower()
            if beta_cores_active and filter_value == '':
                ini[lower_id]['filter'] = '[MiSTer]'
            elif beta_cores_active and '!jtbeta' in filter_value:
                ini[lower_id]['filter'] = filter_value.replace('!jtbeta', '').strip()
            elif not beta_cores_active and filter_value == '[mister]':
                del ini[lower_id]['filter']
            elif not beta_cores_active and filter_value != '' and '!jtbeta' not in filter_value:
                ini[lower_id]['filter'] = f'{filter_value} !jtbeta'

        coin_op_lower_id = ALL_DB_IDS['COIN_OP_COLLECTION'].lower()
        if ALL_DB_IDS['COIN_OP_COLLECTION'] in config.databases and coin_op_lower_id in ini:
            coin_op_filter = coin_op_collection_filter_by_releases(config.coin_op_collection_releases)
            if coin_op_filter is None:
                ini[coin_op_lower_id].pop('filter', None)
            else:
                ini[coin_op_lower_id]['filter'] = coin_op_filter

        update_linux_value = bool(str_to_bool(ini.get('mister', {}).get('update_linux', 'true')))
        if config.update_linux and not update_linux_value:
            if 'mister' in ini and 'update_linux' in ini['mister']:
                del ini['mister']['update_linux']
                if not ini['mister']:
                    del ini['mister']
        elif not config.update_linux and update_linux_value:
            ini.setdefault('mister', {})['update_linux'] = 'false'

    def _edit_downloader_document(self, document: DownloaderIniDocument, config: Config,
                                  candidates: List[Tuple[str, Database]]) -> Tuple[bool, Dict[str, str]]:
        before = self._downloader_sections(document)
        ini = {name: dict(values) for name, values in before.items()}
        self._add_new_downloader_ini_changes(ini, config, candidates)
        ordered_ini: OrderedDict[str, Dict[str, str]] = into_ordered_ini_dict(ini, [DB_ID_DISTRIBUTION_MISTER], [ALL_DB_IDS['UPDATE_ALL_MISTER']])
        if list(before.items()) == list(ordered_ini.items()) and not document.repeated_sections:
            return False, {}

        repeated = document.deduplicate()
        db_ids = {db.db_id.lower(): db.db_id for _, db in candidates}
        document.remove_sections(name for name in db_ids if name not in ordered_ini)
        for name, values in ordered_ini.items():
            if name in db_ids:
                document.set_options(db_ids[name], values, replace=True, canonical_name=True)

        update_linux = ordered_ini.get('mister', {}).get('update_linux')
        previous_update_linux = before.get('mister', {}).get('update_linux')
        if previous_update_linux != update_linux:
            document.set_options('mister', {'update_linux': update_linux})
            document.remove_empty_sections(('mister',))
        document.order_sections(['mister'] + [name for name in ordered_ini if name in db_ids])
        return True, repeated


def candidate_databases(config: Config) -> List[Tuple[str, Database]]:
    dbs_def = all_dbs(config.mirror)
    configurable_dbs = {
        'main_updater': dbs_def.db_distribution_mister_by_encc_forks(config.encc_forks),
        'jotego_updater': dbs_def.db_jtcores_by_download_beta_cores(config.download_beta_cores),
        'names_txt_updater': dbs_def.db_names_txt_by_locale(config.names_region, config.names_char_code, config.names_sort_code),
        'arcade_names_txt': dbs_def.db_arcade_names_txt_by_locale(config.names_region)
    }
    result = []
    for variable, dbs in dbs_def.dbs_to_model_variables_pairs():
        if variable in configurable_dbs:
            result.append((variable, configurable_dbs[variable]))
            continue

        if len(dbs) != 1:
            raise ValueError(f"Needs to be length 1, but is '{len(dbs)}', or must be contained in configurable_dbs.")

        db = dbs[0]
        if db.db_id.lower().startswith('chipster6502/artworkdb-'):
            db = chipster6502_artwork_db_with_style(db, config.artwork_style_for(db.db_id))
        result.append((variable, db))
    return result


def active_databases(config: Config) -> list[Database]:
    return [db for var, db in candidate_databases(config) if db.db_id in config.databases]


class IniRepositoryInitializationError(Exception):
    pass


def into_ordered_ini_dict(ini: Dict[str, Dict[str, str]], first_sections: List[str], last_sections: List[str]) -> OrderedDict[str, Dict[str, str]]:
    ordered_ini = OrderedDict()

    for db_id in first_sections:
        if db_id in ini:
            ordered_ini[db_id] = ini.pop(db_id)

    ordered_ini.update(ini)

    for db_id in last_sections:
        if db_id in ordered_ini:
            ordered_ini[db_id] = ordered_ini.pop(db_id)

    ini.clear()

    return ordered_ini

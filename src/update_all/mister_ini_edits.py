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
from typing import Any, Dict, Optional, Tuple, Union

from update_all.constants import FILE_MiSTer_ini
from update_all.logger import Logger
from update_all.mister_ini_repository import MisterIniRepository


@dataclass(frozen=True)
class MisterIniAdd:
    """Model-declared "add these keys to MiSTer.ini" edit, applied at save time.

    `target` is a section -> {key: value} tree. For each section, every key=value is
    written if not already there (a key with a different value gets updated; a missing
    section or file gets created). Idempotent.
    """
    variable: str
    target: Dict[str, Dict[str, str]]


@dataclass(frozen=True)
class MisterIniDel:
    """Model-declared "remove these keys from MiSTer.ini" edit, applied at save time.

    `target` is a section -> {key: value-filter} tree. For each section, every key
    whose value matches the filter is removed (None removes the key regardless of its
    value). A section left empty is removed too; the INI file itself is never deleted.
    """
    variable: str
    target: Dict[str, Dict[str, Optional[str]]]


MisterIniEdit = Union[MisterIniAdd, MisterIniDel]


def parse_mister_ini_add(effect: Dict[str, Any]) -> MisterIniAdd:
    return MisterIniAdd(variable=effect['variable'], target=effect['target'])


def parse_mister_ini_del(effect: Dict[str, Any]) -> MisterIniDel:
    return MisterIniDel(variable=effect['variable'], target=effect['target'])


def needs_save_label(spec: MisterIniEdit) -> str:
    return ', '.join(f'[{section}]' for section in spec.target)


def would_change(repository: MisterIniRepository, spec: MisterIniEdit, logger: Logger) -> bool:
    changed, _contents = _apply(repository, spec, logger, dry_run=True)
    return changed


def apply(repository: MisterIniRepository, spec: MisterIniEdit, logger: Logger) -> Tuple[bool, str]:
    return _apply(repository, spec, logger, dry_run=False)


def _apply(repository: MisterIniRepository, spec: MisterIniEdit, logger: Logger, dry_run: bool) -> Tuple[bool, str]:
    if isinstance(spec, MisterIniAdd):
        return _apply_add(repository, spec, logger, dry_run)
    return _apply_del(repository, spec, logger, dry_run)


def _apply_add(repository: MisterIniRepository, spec: MisterIniAdd, logger: Logger, dry_run: bool) -> Tuple[bool, str]:
    changed = False
    contents = ''
    for section, keys in spec.target.items():
        missing = {}
        for key, value in keys.items():
            if repository.has_mister_ini_key((section,), key, value):
                _log(logger, dry_run, f'[{section}] already has {key}={value}, skipping')
            else:
                missing[key] = value

        if len(missing) == 0:
            continue

        for key, value in missing.items():
            _log(logger, dry_run, f'added {key}={value} to [{section}]')

        try:
            section_changed, contents = repository.ensure_mister_ini_keys(
                section,
                missing,
                create_if_missing=True,
                replace_existing=True,
                prepend_section=False,
                dry_run=dry_run,
            )
        except Exception as e:
            logger.print(f'ERROR! Could not update {FILE_MiSTer_ini} ([{section}])')
            logger.debug(e)
            continue

        changed = changed or section_changed

    _log(logger, dry_run, f"mister_ini_add '{spec.variable}': MiSTer.ini {'written' if changed else 'unchanged'}")
    return changed, contents


def _apply_del(repository: MisterIniRepository, spec: MisterIniDel, logger: Logger, dry_run: bool) -> Tuple[bool, str]:
    changed = False
    contents = ''
    for section, keys in spec.target.items():
        for key, value in keys.items():
            try:
                key_changed, contents = repository.remove_mister_ini_key_from_sections(
                    (section,),
                    key,
                    value,
                    remove_empty_section=True,
                    dry_run=dry_run,
                )
            except Exception as e:
                logger.print(f'ERROR! Could not update {FILE_MiSTer_ini} ([{section}])')
                logger.debug(e)
                continue

            changed = changed or key_changed
            if key_changed:
                _log(logger, dry_run, f'removed {key} from [{section}]')
            else:
                _log(logger, dry_run, f'[{section}] has no {key} to remove, skipping')

    _log(logger, dry_run, f"mister_ini_del '{spec.variable}': MiSTer.ini {'written' if changed else 'unchanged'}")
    return changed, contents


def _log(logger: Logger, dry_run: bool, message: str) -> None:
    if not dry_run:
        logger.debug(message)

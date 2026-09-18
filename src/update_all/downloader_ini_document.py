# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Downloader INI syntax and text editing, independent of application settings.

A document keeps the original text and one small object per section. Lines are
scanned only while reading or editing; there is no persistent tree of tokens.
"""

import configparser
import io
from typing import Dict, Iterable, Iterator, List, NamedTuple, Optional, Tuple

IniSections = Dict[str, Dict[str, str]]


class RepeatedSection(NamedTuple):
    name: str
    line: int
    first_line: int


class IniLine(NamedTuple):
    text: str
    header: Optional[str]
    option: Optional[str]
    value: Optional[str]
    indent: str


class IniSection:
    __slots__ = ('name', 'text', 'line')

    def __init__(self, name: str, text: str, line: int = 0):
        self.name = name
        self.text = text
        self.line = line

    def renamed(self, name: str) -> 'IniSection':
        return IniSection(name, self.text.replace(f'[{self.name}]', f'[{name}]', 1), self.line)


class DownloaderIniDocument:
    def __init__(self, contents: str):
        self.original = contents
        self.preamble = ''
        self.sections: Dict[str, IniSection] = {}
        self._blocks: List[IniSection] = []
        self._parser: Optional[configparser.ConfigParser] = None
        self._values: Optional[Tuple[bool, IniSections]] = None
        lines: List[str] = []
        name = None
        first_line = 0
        for number, (text, header) in enumerate(ini_lines_with_header(contents), start=1):
            if header is not None:
                if name is None:
                    self.preamble = ''.join(lines)
                else:
                    self._blocks.append(IniSection(name, ''.join(lines), first_line))
                name, first_line, lines = header, number, []
            lines.append(text)
        if name is None:
            self.preamble = ''.join(lines)
        else:
            self._blocks.append(IniSection(name, ''.join(lines), first_line))
        self._index_sections()

    def _index_sections(self) -> None:
        self.sections = {}
        for section in self._blocks:
            self.sections.setdefault(section.name.lower(), section)
        self._parser = None
        self._values = None

    @property
    def repeated_sections(self) -> List[RepeatedSection]:
        return [RepeatedSection(section.name, section.line, self.sections[section.name.lower()].line)
                for section in self._blocks
                if section is not self.sections[section.name.lower()]]

    def parser(self) -> configparser.ConfigParser:
        if self._parser is None:
            # DEFAULT is configparser's special options container, not a database.
            blocks = [self.preamble] + [section.text for section in self._blocks
                      if section is self.sections[section.name.lower()] or section.name == configparser.DEFAULTSECT]
            parser = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
            parser.read_string(_join_blocks(blocks))
            self._parser = parser
        return self._parser

    def section_values(self, literal_percent: bool = False) -> IniSections:
        if self._values is None or self._values[0] != literal_percent:
            self._values = literal_percent, parser_sections(self.parser(), literal_percent)
            # Keep compact values between edits, not a ConfigParser and its SectionProxy objects per file.
            self._parser = None
        return {name: dict(values) for name, values in self._values[1].items()}

    def deduplicate(self, names: Optional[Iterable[str]] = None) -> Dict[str, str]:
        selected = set(self.sections) if names is None else {name.lower() for name in names}
        removed: Dict[str, List[str]] = {}
        kept = []
        for section in self._blocks:
            key = section.name.lower()
            if key in selected and section is not self.sections[key]:
                removed.setdefault(key, []).append(section.text)
            else:
                kept.append(section)
        if removed:
            self._blocks = kept
            self._index_sections()
        return {name: ''.join(texts) for name, texts in removed.items()}

    def remove_sections(self, names: Iterable[str]) -> Dict[str, IniSection]:
        selected = {name.lower() for name in names}
        removed = {name: section for name, section in self.sections.items() if name in selected}
        if removed:
            self._blocks = [section for section in self._blocks if section.name.lower() not in selected]
            self._index_sections()
        return removed

    def put_sections(self, sections: Dict[str, IniSection]) -> None:
        self.remove_sections(sections)
        self._blocks.extend(section.renamed(name) for name, section in sections.items())
        self._index_sections()

    def remove_empty_sections(self, names: Iterable[str]) -> None:
        self.remove_sections(name for name in names if name.lower() in self.sections and
                             not any(line.strip() for line in self.sections[name.lower()].text.splitlines()[1:]))

    def set_options(self, name: str, values: Dict[str, Optional[str]], *, replace: bool = False,
                    literal_values: bool = True, canonical_name: bool = False) -> None:
        section = self.sections.get(name.lower())
        original_text = section.text if section is not None else None
        if section is None:
            section = IniSection(name, f'[{name}]\n')
            self._blocks.append(section)
            self.sections[name.lower()] = section
        if canonical_name and section.name != name:
            renamed = section.renamed(name)
            section.name, section.text = renamed.name, renamed.text
        section.text = with_ini_options(section.text, values, replace=replace, literal_values=literal_values)
        if section.text != original_text:
            self._parser = None
            self._values = None

    def order_sections(self, names: Iterable[str]) -> None:
        order = dict.fromkeys(name.lower() for name in names)
        blocks_by_name: Dict[str, List[IniSection]] = {}
        for section in self._blocks:
            blocks_by_name.setdefault(section.name.lower(), []).append(section)
        blocks = [section for name in order for section in blocks_by_name.pop(name, [])] + [
            section for blocks in blocks_by_name.values() for section in blocks]
        if blocks != self._blocks:
            self._blocks = blocks
            self._index_sections()

    def rename_sections(self, changes: Dict[str, str]) -> Tuple[set, Dict[str, str]]:
        """Rename sections and their bracketed references. Existing targets win collisions."""
        changes = {old: new for old, new in changes.items() if old.lower() in self.sections}
        by_name = {old.lower(): (old, new) for old, new in changes.items()}
        occupied = set(self.sections)
        references = {old: new for old, new in changes.items() if new.lower() not in occupied}
        removed: Dict[str, List[str]] = {}
        blocks = []
        for section in self._blocks:
            change = by_name.get(section.name.lower())
            if change is not None:
                old, new = change
                if new.lower() in occupied:
                    removed.setdefault(old, []).append(section.text)
                    continue
                section = section.renamed(new)
                occupied.add(new.lower())
            section.text = _replace_references(section.text, references)
            blocks.append(section)
        if changes:
            self.preamble = _replace_references(self.preamble, references)
            self._blocks = blocks
            self._index_sections()
        return set(changes), {old: ''.join(texts) for old, texts in removed.items()}

    def render(self, *, separate_sections: bool = False, ending: Optional[str] = None) -> str:
        """Render safely, optionally normalizing section spacing and the file's ending."""
        parts = ([self.preamble] if self.preamble else []) + [section.text for section in self._blocks]
        if separate_sections:
            contents = '\n\n'.join(part.rstrip('\r\n') for part in parts)
        else:
            contents = _join_blocks(parts)
        return contents.rstrip('\r\n') + ending if ending is not None and contents else contents


def _terminated(text: str) -> str:
    return text + '\n' if text and not text.endswith('\n') else text


def _join_blocks(blocks: List[str]) -> str:
    return ''.join(_terminated(block) for block in blocks[:-1]) + (blocks[-1] if blocks else '')


def parser_sections(parser: configparser.ConfigParser, literal_percent: bool = False) -> IniSections:
    return {header.lower(): {key.lower(): _ini_value(section, key, literal_percent) for key in section}
            for header, section in parser.items() if header.lower() != 'default'}


def _ini_value(section: configparser.SectionProxy, key: str, literal_percent: bool) -> str:
    try:
        return section[key]
    except configparser.InterpolationError:
        if not literal_percent:
            raise
        return section.get(key, raw=True)


def _replace_references(text: str, changes: Dict[str, str]) -> str:
    for old, new in changes.items():
        needle = f'[{old.lower()}]'
        lower = text.lower()
        parts = []
        start = 0
        index = lower.find(needle)
        while index != -1:
            parts.extend((text[start:index], f'[{new}]'))
            start = index + len(needle)
            index = lower.find(needle, start)
        if parts:
            parts.append(text[start:])
            text = ''.join(parts)
    return text


def ini_lines(contents: str) -> Iterator[IniLine]:
    """Recognize comments, headers, options and continuations using configparser's rules."""
    option = None
    indent_level = 0
    for text in io.StringIO(contents):
        content = without_ini_comment(text).strip()
        if not content:
            yield IniLine(text, None, None, None, '')
            continue
        indent = text[:len(text) - len(text.lstrip())]
        if option is not None and len(indent) > indent_level:
            yield IniLine(text, None, option, None, indent)
            continue
        indent_level = len(indent)
        match = configparser.ConfigParser.SECTCRE.match(content)
        if match is not None:
            option = None
            yield IniLine(text, match.group('header'), None, None, indent)
        else:
            option, value = _split_ini_option(content)
            yield IniLine(text, None, option, value, indent)


def ini_lines_with_header(contents: str) -> Iterator[Tuple[str, Optional[str]]]:
    """Put real headers at column zero so moving/removing a section cannot make them continuations."""
    for line in ini_lines(contents):
        yield (line.text.lstrip() if line.header is not None else line.text), line.header


def with_ini_options(section_text: str, values: Dict[str, Optional[str]], *, replace: bool = False,
                     literal_values: bool = False) -> str:
    """Apply option edits together, keeping untouched text and the section's option indentation."""
    desired = {key.lower(): value.replace('%', '%%') if literal_values and value is not None else value
               for key, value in values.items()}
    if replace:
        # Replacing the complete option set also gives it the supplied order.
        header = section_text.split('\n', 1)[0]
        return header + '\n' + ''.join(_option_text(key, value, '') for key, value in desired.items()
                                       if value is not None) + '\n'
    lines = []
    option_lines: Dict[str, List[int]] = {}
    current: Dict[str, List[str]] = {}
    options_indent = None
    insert_at = 0
    for line in ini_lines(section_text):
        if line.header is not None:
            insert_at = len(lines) + 1
        if line.option is not None:
            key = line.option.lower()
            if options_indent is None:
                options_indent = line.indent
            if key in desired:
                option_lines.setdefault(key, []).append(len(lines))
                if line.value is not None:
                    current[key] = [line.value]
                else:
                    current.setdefault(key, []).append(without_ini_comment(line.text).strip())
        lines.append(line.text)
    changes = {key: value for key, value in desired.items()
               if ('\n'.join(current[key]).rstrip() if key in current else None) != value}
    if not changes:
        return section_text
    removed_lines = {index for key in changes for index in option_lines.get(key, [])}
    indent = options_indent or ''
    additions = [_option_text(key, value, indent) for key, value in changes.items() if value is not None]
    return ''.join(_terminated(text) for text in lines[:insert_at]) + ''.join(additions) + ''.join(
        _terminated(text) for index, text in enumerate(lines) if index >= insert_at and index not in removed_lines)


def _option_text(key: str, value: str, indent: str) -> str:
    return f'{indent}{key} = ' + value.replace('\n', '\n' + indent + '\t') + '\n'


def without_ini_comment(line: str) -> str:
    if ';' not in line and '#' not in line:
        return line
    for index, char in enumerate(line):
        if char in ';#' and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _split_ini_option(content: str) -> Tuple[str, str]:
    separators = [index for index in (content.find('='), content.find(':')) if index != -1]
    if not separators:
        return content, ''
    return content[:min(separators)].strip(), content[min(separators) + 1:].strip()

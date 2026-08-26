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
import unittest

from test.logger_tester import NoLogger
from test.mister_ini_repository_tester import MisterIniRepositoryTester
from update_all.constants import FILE_MiSTer_ini
from update_all.mister_ini_edits import (
    apply,
    needs_save_label,
    parse_mister_ini_add,
    parse_mister_ini_del,
    would_change,
)


# Declared exactly as in the model.
RETROACHIEVEMENTS_ADD = {
    "type": "mister_ini_add",
    "variable": "theypsilon/RetroAchievementsDB_MiSTer",
    "target": {"RA_*": {"main": "MiSTer_RA"}},
}

ZAPAROO_FRONTEND_ADD = {
    "type": "mister_ini_add",
    "variable": "zaparoo_frontend_active",
    "target": {"mister": {"main": "zaparoo/MiSTer_Zaparoo"}},
}

ZAPAROO_FRONTEND_DEL = {
    "type": "mister_ini_del",
    "variable": "zaparoo_frontend_active",
    "target": {
        "mister": {"main": "zaparoo/MiSTer_Zaparoo"},
        "menu": {"main": "zaparoo/MiSTer_Zaparoo"},
    },
}


def _repo(content=None):
    files = {FILE_MiSTer_ini: {'content': content}} if content is not None else {}
    return MisterIniRepositoryTester(files=files)


def _apply(repo, spec):
    return apply(repo, spec, NoLogger())


def _mister_ini_writes(repo):
    return [
        record for record in repo.file_system.write_records
        if record['scope'] == 'write_file_contents' and record['data'][0].endswith('.mister.ini.new')
    ]


class TestParsing(unittest.TestCase):
    def test_add___reads_variable_and_target(self):
        spec = parse_mister_ini_add(RETROACHIEVEMENTS_ADD)

        self.assertEqual('theypsilon/RetroAchievementsDB_MiSTer', spec.variable)
        self.assertEqual({'RA_*': {'main': 'MiSTer_RA'}}, spec.target)

    def test_del___reads_variable_and_target(self):
        spec = parse_mister_ini_del(ZAPAROO_FRONTEND_DEL)

        self.assertEqual('zaparoo_frontend_active', spec.variable)
        self.assertEqual(
            {'mister': {'main': 'zaparoo/MiSTer_Zaparoo'}, 'menu': {'main': 'zaparoo/MiSTer_Zaparoo'}},
            spec.target,
        )


class TestNeedsSaveLabel(unittest.TestCase):
    def test_single_section(self):
        self.assertEqual('[RA_*]', needs_save_label(parse_mister_ini_add(RETROACHIEVEMENTS_ADD)))

    def test_multiple_sections(self):
        self.assertEqual('[mister], [menu]', needs_save_label(parse_mister_ini_del(ZAPAROO_FRONTEND_DEL)))


class TestAdd(unittest.TestCase):
    def test_retroachievements___adds_block_at_end(self):
        repo = _repo('[mister]\nfoo=bar\n\n[menu]\nvideo_mode=8\n')

        changed, _ = _apply(repo, parse_mister_ini_add(RETROACHIEVEMENTS_ADD))

        self.assertTrue(changed)
        self.assertEqual(
            '[mister]\nfoo=bar\n\n[menu]\nvideo_mode=8\n\n[RA_*]\nmain=MiSTer_RA\n',
            repo.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_retroachievements___without_mister_ini___creates_block(self):
        repo = _repo()

        _apply(repo, parse_mister_ini_add(RETROACHIEVEMENTS_ADD))

        self.assertEqual('[RA_*]\nmain=MiSTer_RA\n', repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_retroachievements___already_present___does_not_rewrite(self):
        original = '[mister]\nfoo=bar\n\n[RA_*]\nmain=MiSTer_RA\n'
        repo = _repo(original)

        changed, _ = _apply(repo, parse_mister_ini_add(RETROACHIEVEMENTS_ADD))

        self.assertFalse(changed)
        self.assertEqual([], _mister_ini_writes(repo))
        self.assertEqual(original, repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_zaparoo___appends_mister_section_when_missing(self):
        repo = _repo('[menu]\nvideo_mode=8\n')

        _apply(repo, parse_mister_ini_add(ZAPAROO_FRONTEND_ADD))

        self.assertEqual(
            '[menu]\nvideo_mode=8\n\n[mister]\nmain=zaparoo/MiSTer_Zaparoo\n',
            repo.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_zaparoo___replaces_different_main(self):
        repo = _repo('[mister]\nmain=menu.rbf\nfoo=bar\n')

        _apply(repo, parse_mister_ini_add(ZAPAROO_FRONTEND_ADD))

        self.assertEqual(
            '[mister]\nmain=zaparoo/MiSTer_Zaparoo\nfoo=bar\n',
            repo.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_multi_key_section___adds_every_missing_key(self):
        repo = _repo('[mister]\nfoo=bar\n')
        spec = parse_mister_ini_add({
            "type": "mister_ini_add", "variable": "v",
            "target": {"mister": {"a": "1", "b": "2"}},
        })

        _apply(repo, spec)

        self.assertEqual('[mister]\nfoo=bar\na=1\nb=2\n', repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_multi_key_section___writes_only_the_missing_keys(self):
        repo = _repo('[mister]\na=1\n')
        spec = parse_mister_ini_add({
            "type": "mister_ini_add", "variable": "v",
            "target": {"mister": {"a": "1", "b": "2"}},
        })

        _apply(repo, spec)

        self.assertEqual('[mister]\na=1\nb=2\n', repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_multiple_sections___adds_to_each(self):
        repo = _repo('[mister]\nfoo=bar\n')
        spec = parse_mister_ini_add({
            "type": "mister_ini_add", "variable": "v",
            "target": {"mister": {"a": "1"}, "menu": {"b": "2"}},
        })

        _apply(repo, spec)

        self.assertEqual(
            '[mister]\nfoo=bar\na=1\n\n[menu]\nb=2\n',
            repo.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_would_change___when_missing___true_without_writing(self):
        repo = _repo()

        self.assertTrue(would_change(repo, parse_mister_ini_add(RETROACHIEVEMENTS_ADD), NoLogger()))
        self.assertFalse(repo.file_system.is_file(FILE_MiSTer_ini))

    def test_would_change___when_present___false(self):
        repo = _repo('[RA_*]\nmain=MiSTer_RA\n')

        self.assertFalse(would_change(repo, parse_mister_ini_add(RETROACHIEVEMENTS_ADD), NoLogger()))


class TestDel(unittest.TestCase):
    def test_zaparoo___removes_from_mister_section(self):
        repo = _repo('[mister]\nmain=zaparoo/MiSTer_Zaparoo\nfoo=bar\n[menu]\nvideo_mode=8\n')

        _apply(repo, parse_mister_ini_del(ZAPAROO_FRONTEND_DEL))

        self.assertEqual(
            '[mister]\nfoo=bar\n[menu]\nvideo_mode=8\n',
            repo.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_zaparoo___removes_from_menu_section(self):
        repo = _repo('[mister]\nfoo=bar\n[menu]\nmain=zaparoo/MiSTer_Zaparoo\nvideo_mode=8\n')

        _apply(repo, parse_mister_ini_del(ZAPAROO_FRONTEND_DEL))

        self.assertEqual(
            '[mister]\nfoo=bar\n[menu]\nvideo_mode=8\n',
            repo.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_emptied_section___gets_dropped(self):
        repo = _repo('[mister]\nfoo=bar\n\n[RA_*]\nmain=MiSTer_RA\n')
        spec = parse_mister_ini_del({
            "type": "mister_ini_del", "variable": "v",
            "target": {"RA_*": {"main": "MiSTer_RA"}},
        })

        _apply(repo, spec)

        self.assertEqual('[mister]\nfoo=bar\n', repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_emptied_file___keeps_the_file(self):
        repo = _repo('[mister]\nmain=zaparoo/MiSTer_Zaparoo\n')
        spec = parse_mister_ini_del({
            "type": "mister_ini_del", "variable": "v",
            "target": {"mister": {"main": "zaparoo/MiSTer_Zaparoo"}},
        })

        _apply(repo, spec)

        self.assertTrue(repo.file_system.is_file(FILE_MiSTer_ini))
        self.assertEqual('', repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_none_value___strips_key_with_any_value(self):
        repo = _repo('[mister]\nmain=menu.rbf\nfoo=bar\n')
        spec = parse_mister_ini_del({
            "type": "mister_ini_del", "variable": "v",
            "target": {"mister": {"main": None}},
        })

        _apply(repo, spec)

        self.assertEqual('[mister]\nfoo=bar\n', repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_value_filter___keeps_key_with_different_value(self):
        original = '[mister]\nmain=menu.rbf\nfoo=bar\n'
        repo = _repo(original)
        spec = parse_mister_ini_del({
            "type": "mister_ini_del", "variable": "v",
            "target": {"mister": {"main": "zaparoo/MiSTer_Zaparoo"}},
        })

        changed, _ = _apply(repo, spec)

        self.assertFalse(changed)
        self.assertEqual(original, repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_multi_key_section___removes_every_matching_key(self):
        repo = _repo('[mister]\na=1\nb=2\nfoo=bar\n')
        spec = parse_mister_ini_del({
            "type": "mister_ini_del", "variable": "v",
            "target": {"mister": {"a": "1", "b": None}},
        })

        _apply(repo, spec)

        self.assertEqual('[mister]\nfoo=bar\n', repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_would_change___when_absent___false(self):
        repo = _repo('[mister]\nfoo=bar\n')

        self.assertFalse(would_change(repo, parse_mister_ini_del(ZAPAROO_FRONTEND_DEL), NoLogger()))

    def test_would_change___does_not_write(self):
        original = '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n'
        repo = _repo(original)

        self.assertTrue(would_change(repo, parse_mister_ini_del(ZAPAROO_FRONTEND_DEL), NoLogger()))
        self.assertEqual(original, repo.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_without_mister_ini___does_not_fail(self):
        repo = _repo()

        changed, _ = _apply(repo, parse_mister_ini_del(ZAPAROO_FRONTEND_DEL))

        self.assertFalse(changed)
        self.assertFalse(repo.file_system.is_file(FILE_MiSTer_ini))


class TestApplyErrors(unittest.TestCase):
    def test_failing_section___logs_the_error_and_continues_with_the_rest(self):
        repo = _repo()
        spec = parse_mister_ini_add({
            "type": "mister_ini_add", "variable": "v",
            "target": {
                "DUKE3D": {"main": "Mister_duke3d", "vga_scaler": "0"},
                "Mister_duke3d": {"main": "Mister_duke3d", "vga_scaler": "0"},
            },
        })

        original = repo.ensure_mister_ini_keys

        def flaky_ensure(section, *args, **kwargs):
            if section == 'DUKE3D':
                raise OSError('SD card error')
            return original(section, *args, **kwargs)

        repo.ensure_mister_ini_keys = flaky_ensure

        changed, _ = _apply(repo, spec)

        self.assertTrue(changed)
        self.assertEqual(
            '[Mister_duke3d]\nmain=Mister_duke3d\nvga_scaler=0\n',
            repo.file_system.read_file_contents(FILE_MiSTer_ini),
        )

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
import re
import unittest
from pathlib import Path

from update_all.databases import AllDBs, Database


class TestDatabaseIdsValidation(unittest.TestCase):
    """Integration test to validate ALL_DB_IDS usage across the codebase."""

    def test_all_db_ids_keys_used_in_codebase_exist_in_all_dbs(self):
        """
        Scan all update_all/ modules for ALL_DB_IDS usage and verify
        that all keys used exist as Database attributes in AllDBs.
        """
        # Pattern to match ALL_DB_IDS['KEY'] or ALL_DB_IDS["KEY"]
        pattern = re.compile(r"ALL_DB_IDS\[(['\"])(.*)\1\]")

        # Find all Python files in update_all/
        update_all_dir = Path(__file__).parent.parent.parent / 'update_all'
        python_files = list(update_all_dir.glob('**/*.py'))

        # Collect all keys used in the codebase
        used_keys = set()
        for file_path in python_files:
            content = file_path.read_text()
            matches = pattern.findall(content)
            # matches is a list of tuples: [("'", "KEY"), ...]
            for _, key in matches:
                used_keys.add(key)

        # Verify we found some usages (sanity check)
        self.assertGreater(
            len(used_keys), 0,
            "Expected to find at least some ALL_DB_IDS usages in the codebase"
        )

        # Get all Database attributes from AllDBs
        all_dbs_instance = AllDBs()
        valid_keys = set()
        for attr_name in dir(all_dbs_instance):
            if attr_name.startswith('_'):
                continue
            attr = getattr(all_dbs_instance, attr_name)
            if isinstance(attr, Database):
                valid_keys.add(attr_name)

        # Verify all used keys exist in AllDBs
        invalid_keys = used_keys - valid_keys

        self.assertEqual(
            len(invalid_keys), 0,
            f"Found ALL_DB_IDS keys used in codebase that don't exist in AllDBs: {sorted(invalid_keys)}\n"
            f"Used keys: {sorted(used_keys)}\n"
            f"Valid keys: {sorted(valid_keys)}"
        )

    def test_all_db_ids_usages_must_use_string_literals(self):
        """
        Scan all update_all/ modules and verify that ALL_DB_IDS is only
        accessed with string literals, not variables or expressions.
        """
        # Pattern to match ALL_DB_IDS[anything]
        all_usages_pattern = re.compile(r"ALL_DB_IDS\[([^\]]+)\]")

        # Find all Python files in update_all/
        update_all_dir = Path(__file__).parent.parent.parent / 'update_all'
        python_files = list(update_all_dir.glob('**/*.py'))

        # Collect invalid usages (non-string literals)
        invalid_usages = []

        for file_path in python_files:
            content = file_path.read_text()
            lines = content.split('\n')

            # Find all ALL_DB_IDS usages
            for line_num, line in enumerate(lines, 1):
                matches = all_usages_pattern.findall(line)
                for match in matches:
                    # Check if this is NOT a quoted string literal
                    stripped = match.strip()
                    if not (stripped.startswith("'") and stripped.endswith("'")) and \
                       not (stripped.startswith('"') and stripped.endswith('"')):
                        relative_path = file_path.relative_to(update_all_dir.parent)
                        invalid_usages.append((relative_path, line_num, match.strip()))

        # Fail if there are non-string-literal usages
        self.assertEqual(
            len(invalid_usages), 0,
            f"Found ALL_DB_IDS usages with non-string-literal keys. "
            f"All keys must be string literals like ALL_DB_IDS['KEY']:\n" +
            "\n".join(f"  {file}:{line}  ALL_DB_IDS[{usage}]" for file, line, usage in invalid_usages)
        )

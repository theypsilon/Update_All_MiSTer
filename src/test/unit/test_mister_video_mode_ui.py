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
from unittest.mock import patch

from test.mister_video_mode_service_tester import MisterVideoModeServiceTester
from update_all.config import Config
from update_all.mister_video_mode_service import read_video_mode_from_contents, read_video_ini_state_from_contents
from update_all.mister_video_mode_ui import MisterVideoModeMenu, MisterVideoAdjustMenu, _countdown_timeout_ms
from update_all.ui_engine import EffectChain
from update_all.ui_model_utilities import Key

MODES = [
    ('1 320x240', '320,13,31,52,240,2,3,16,6515'),
    ('2 384x224', '384,16,37,63,224,10,3,24,7830'),
    ('3 640x240', '640,30,60,70,240,4,4,14,12587'),
    ('4 320x240 (compact)', '320,8,32,24,240,4,3,16,6048'),
]


def _model_resolutions():
    return [{'name': name, 'video_mode': video_mode} for name, video_mode in MODES]


class TestMisterVideoModeUi(unittest.TestCase):
    def test_save_unsaved_kept_mode_to_active_ini___writes_pending_mode_to_current_active_ini(self):
        logger = _LoggerStub()
        config = Config(base_path='/media/fat')
        sut = MisterVideoModeServiceTester(logger=logger, config=config, files={
            '/media/fat/MiSTer.ini': {'content': '[menu]\nvideo_mode=320,13,31,52,240,2,3,16,6515\n', 'hash': 'x', 'size': 1},
            '/media/fat/MiSTer_alt.ini': {'content': '[menu]\nvideo_mode=384,16,37,63,224,10,3,24,7830\n', 'hash': 'y', 'size': 1},
        })
        file_system = sut.file_system
        sut._active_ini_path = lambda: '/media/fat/MiSTer_alt.ini'
        sut.remember_unsaved_kept_mode(MODES[2][1])

        result = sut.save_unsaved_kept_mode_to_active_ini()

        writes = [
            record['data']
            for record in file_system.write_records
            if record['scope'] == 'write_file_contents'
        ]
        self.assertTrue(result)
        self.assertFalse(sut.has_unsaved_kept_mode())
        self.assertEqual(
            [
                ['/media/fat/.mister_alt.ini.new', '[menu]\nvideo_mode=640,30,60,70,240,4,4,14,12587\nvga_scaler=1\n'],
            ],
            writes,
        )
        self.assertEqual(
            '[menu]\nvideo_mode=640,30,60,70,240,4,4,14,12587\nvga_scaler=1\n',
            file_system.read_file_contents('/media/fat/MiSTer_alt.ini'),
        )

    def test_save_unsaved_kept_mode_to_active_ini___adds_menu_section_when_missing(self):
        logger = _LoggerStub()
        config = Config(base_path='/media/fat')
        sut = MisterVideoModeServiceTester(logger=logger, config=config, files={
            '/media/fat/MiSTer.ini': {'content': '[mister]\ndirect_video=1\n'},
        })
        sut._active_ini_path = lambda: '/media/fat/MiSTer.ini'
        sut.remember_unsaved_kept_mode(MODES[0][1])

        result = sut.save_unsaved_kept_mode_to_active_ini()

        self.assertTrue(result)
        self.assertEqual(
            '[mister]\ndirect_video=1\n\n[menu]\nvideo_mode=320,13,31,52,240,2,3,16,6515\nvga_scaler=1\n',
            sut.file_system.read_file_contents('/media/fat/MiSTer.ini'),
        )

    def test_save_unsaved_kept_mode_to_active_ini___forces_vga_scaler_and_removes_direct_video_from_menu_section(self):
        logger = _LoggerStub()
        config = Config(base_path='/media/fat')
        sut = MisterVideoModeServiceTester(logger=logger, config=config, files={
            '/media/fat/MiSTer.ini': {'content': '\n[mister]\ndirect_video=1\n\n[menu]\ndirect_video=1\nvga_scaler=0\nother=keep\n'},
        })
        sut._active_ini_path = lambda: '/media/fat/MiSTer.ini'
        sut.remember_unsaved_kept_mode(MODES[1][1])

        result = sut.save_unsaved_kept_mode_to_active_ini()

        self.assertTrue(result)
        self.assertEqual(
            '\n[mister]\ndirect_video=1\n\n[menu]\nvga_scaler=1\nother=keep\nvideo_mode=384,16,37,63,224,10,3,24,7830\n',
            sut.file_system.read_file_contents('/media/fat/MiSTer.ini'),
        )

    def test_restore_mode_before_unsaved_keeps___restores_first_unsaved_mode(self):
        logger = _LoggerStub()
        sut = _video_mode_service(logger)
        sut.apply_mode = lambda mode_str: setattr(sut, '_restored_mode', mode_str) or True
        sut.remember_unsaved_kept_mode(MODES[1][1], MODES[0][1])
        sut.remember_unsaved_kept_mode(MODES[2][1], MODES[1][1])

        result = sut.restore_mode_before_unsaved_keeps()

        self.assertTrue(result)
        self.assertEqual(MODES[0][1], sut._restored_mode)
        self.assertFalse(sut.has_unsaved_kept_mode())

    def test_countdown_timeout_ms___waits_until_displayed_countdown_changes(self):
        self.assertEqual(230, _countdown_timeout_ms(4.23, 5))
        self.assertEqual(1000, _countdown_timeout_ms(4.0, 4))
        self.assertEqual(1, _countdown_timeout_ms(3.0001, 4))

    def test_apply_mode___invalid_mode_does_not_open_mister_cmd(self):
        logger = _LoggerStub()
        sut = _video_mode_service(logger)

        with patch('update_all.mister_video_mode_service.os.open') as open_mock:
            result = sut.apply_mode('320,13,31')

        self.assertFalse(result)
        open_mock.assert_not_called()
        self.assertEqual('MisterVideoModeService: Invalid video mode', logger.debugs[0])

    def test_apply_mode___blocks_video_mode_with_too_high_hfreq(self):
        logger = _LoggerStub()
        sut = _video_mode_service(logger)

        with patch('update_all.mister_video_mode_service.os.open') as open_mock:
            result = sut.apply_mode('320,1,1,1,240,2,3,16,12587')

        self.assertFalse(result)
        open_mock.assert_not_called()
        self.assertEqual('MisterVideoModeService: Invalid video mode', logger.debugs[0])
        self.assertEqual('video_mode_cmd: BLOCKED. hfreq=38969Hz is outside 15625-16500Hz safe range.', str(logger.debugs[1]))

    def test_apply_mode___blocks_video_mode_with_too_low_hfreq(self):
        logger = _LoggerStub()
        sut = _video_mode_service(logger)

        with patch('update_all.mister_video_mode_service.os.open') as open_mock:
            result = sut.apply_mode('320,100,100,100,240,2,3,16,6048')

        self.assertFalse(result)
        open_mock.assert_not_called()
        self.assertEqual('MisterVideoModeService: Invalid video mode', logger.debugs[0])
        self.assertEqual('video_mode_cmd: BLOCKED. hfreq=9755Hz is outside 15625-16500Hz safe range.', str(logger.debugs[1]))

    def test_apply_mode___blocks_video_mode_with_zero_vact(self):
        logger = _LoggerStub()
        sut = _video_mode_service(logger)

        with patch('update_all.mister_video_mode_service.os.open') as open_mock:
            result = sut.apply_mode('320,13,31,52,0,2,3,16,6515')

        self.assertFalse(result)
        open_mock.assert_not_called()
        self.assertEqual('MisterVideoModeService: Invalid video mode', logger.debugs[0])
        self.assertEqual(
            'video_mode_cmd: BLOCKED. vertical timing contains invalid values: vact=0 vfp=2 vs=3 vbp=16.',
            str(logger.debugs[1])
        )

    def test_apply_mode___blocks_video_mode_with_negative_vertical_timing(self):
        logger = _LoggerStub()
        sut = _video_mode_service(logger)

        with patch('update_all.mister_video_mode_service.os.open') as open_mock:
            result = sut.apply_mode('320,13,31,52,240,-1,3,16,6515')

        self.assertFalse(result)
        open_mock.assert_not_called()
        self.assertEqual('MisterVideoModeService: Invalid video mode', logger.debugs[0])
        self.assertEqual(
            'video_mode_cmd: BLOCKED. vertical timing contains invalid values: vact=240 vfp=-1 vs=3 vbp=16.',
            str(logger.debugs[1])
        )

    def test_read_video_mode_from_contents___menu_section_overrides_mister_section(self):
        result = read_video_mode_from_contents('''
[mister]
video_mode=320,13,31,52,240,2,3,16,6515

[menu]
video_mode=384,16,37,63,224,10,3,24,7830
''')

        self.assertEqual(MODES[1][1], result)

    def test_read_video_mode_from_contents___uses_default_ntsc_mode_when_direct_video_is_enabled(self):
        result = read_video_mode_from_contents('''
[mister]
direct_video=1
''')

        self.assertEqual('640,30,60,70,240,4,4,14,12587', result)

    def test_read_video_mode_from_contents___uses_default_pal_mode_when_direct_video_and_menu_pal_are_enabled(self):
        result = read_video_mode_from_contents('''
[mister]
direct_video=1
menu_pal=1
video_mode=384,16,37,63,224,10,3,24,7830
''')

        self.assertEqual('640,30,60,70,288,6,4,14,12587', result)

    def test_read_video_ini_state_from_contents___reads_vga_scaler_and_direct_video_when_equal_to_1(self):
        result = read_video_ini_state_from_contents('''
[mister]
vga_scaler=1
direct_video=1
''')

        self.assertIsNone(result.video_mode)
        self.assertTrue(result.vga_scaler)
        self.assertTrue(result.direct_video)

    def test_read_video_ini_state_from_contents___does_not_treat_direct_video_2_as_enabled(self):
        result = read_video_ini_state_from_contents('''
[mister]
vga_scaler=1
direct_video=2

[menu]
video_mode=384,16,37,63,224,10,3,24,7830
''')

        self.assertEqual(MODES[1][1], result.video_mode)
        self.assertTrue(result.vga_scaler)
        self.assertFalse(result.direct_video)

    def test_video_mode_menu___confirming_a_new_mode_keeps_it_and_returns_back(self):
        service = _VideoModeServiceStub(current_mode=MODES[0][1])
        drawer = _DrawerStub([Key.DOWN, Key.ENTER, Key.LEFT, Key.ENTER, Key.RIGHT, Key.ENTER])
        sut = MisterVideoModeMenu(drawer, service, {'header': 'Video Mode', 'resolutions': _model_resolutions()})

        result = sut.process_key()

        self.assertEqual([MODES[1][1]], service.apply_calls)
        self.assertEqual(MODES[1][1], service.current_mode())
        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)

    def test_video_mode_menu___renders_resolutions_from_model(self):
        custom_modes = [
            {'name': 'Compact custom', 'video_mode': MODES[3][1]},
        ]
        service = _VideoModeServiceStub(current_mode=MODES[3][1])
        drawer = _DrawerStub([27])
        sut = MisterVideoModeMenu(drawer, service, {'header': 'Video Mode', 'resolutions': custom_modes})

        sut.process_key()

        self.assertEqual([
            ('Compact custom', 'Active', True),
            ('Back', '', False),
        ], drawer.menu_entries)
        self.assertEqual(1, drawer.overscan_preview_calls)

    def test_video_mode_menu___selects_resolutions_from_model(self):
        custom_modes = [
            {'name': 'Tiny custom', 'video_mode': '100,1,2,3,100,4,5,6,7000'},
            {'name': 'Wide custom', 'video_mode': '200,1,2,3,100,4,5,6,7000'},
        ]
        service = _VideoModeServiceStub(current_mode=custom_modes[0]['video_mode'])
        drawer = _DrawerStub([Key.DOWN, Key.ENTER, Key.LEFT, Key.ENTER, Key.RIGHT, Key.ENTER])
        sut = MisterVideoModeMenu(drawer, service, {'header': 'Video Mode', 'resolutions': custom_modes})

        result = sut.process_key()

        self.assertEqual([custom_modes[1]['video_mode']], service.apply_calls)
        self.assertEqual(custom_modes[1]['video_mode'], service.current_mode())
        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)

    def test_video_mode_menu___renders_multiple_text_lines_from_model(self):
        custom_modes = [
            {'name': '1 Compact custom', 'video_mode': MODES[3][1]},
        ]
        service = _VideoModeServiceStub(current_mode=MODES[3][1])
        drawer = _DrawerStub([27])
        sut = MisterVideoModeMenu(drawer, service, {
            'header': 'Video Mode',
            'text': ['First instruction.', 'Second instruction.'],
            'resolutions': custom_modes,
        })

        sut.process_key()

        self.assertEqual([
            'Current: Compact custom',
            'First instruction.',
            'Second instruction.',
        ], drawer.text_lines)

    def test_video_adjust_menu___left_arrow_updates_mode_and_enter_keeps_it(self):
        service = _VideoModeServiceStub(current_mode=MODES[0][1])
        drawer = _DrawerStub([Key.LEFT, Key.ENTER, Key.LEFT, Key.ENTER])
        sut = MisterVideoAdjustMenu(drawer, service, {'header': 'Adjust'})

        result = sut.process_key()

        self.assertEqual(['320,14,31,51,240,2,3,16,6515'], service.apply_calls)
        self.assertEqual('320,14,31,51,240,2,3,16,6515', service.current_mode())
        self.assertEqual([-1, 300], drawer.timeout_calls)
        self.assertNotIn('It will revert', '\n'.join(drawer.text_lines))
        self.assertIn('The adjusted position is active.', drawer.text_lines)
        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)

    def test_video_adjust_menu___done_reverts_changed_mode_when_not_kept(self):
        service = _VideoModeServiceStub(current_mode=MODES[0][1])
        drawer = _DrawerStub([Key.LEFT, Key.ENTER, Key.ENTER])
        sut = MisterVideoAdjustMenu(drawer, service, {'header': 'Adjust'})

        result = sut.process_key()

        self.assertEqual(['320,14,31,51,240,2,3,16,6515', MODES[0][1]], service.apply_calls)
        self.assertEqual(MODES[0][1], service.current_mode())
        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)

    def test_video_adjust_menu___renders_multiple_text_lines_from_model(self):
        service = _VideoModeServiceStub(current_mode=MODES[0][1])
        drawer = _DrawerStub([Key.ENTER])
        sut = MisterVideoAdjustMenu(drawer, service, {
            'header': 'Adjust',
            'text': ['Move the picture.', 'Confirm when it is aligned.'],
        })

        sut.process_key()

        self.assertEqual([
            'Move the picture.',
            'Confirm when it is aligned.',
            ' ',
            'hfp=13  hs=31  hbp=52',
            'vfp=2  vs=3  vbp=16',
        ], drawer.text_lines)
        self.assertEqual(1, drawer.overscan_preview_calls)

    def test_video_adjust_menu___escape_restores_the_original_position_before_exiting(self):
        service = _VideoModeServiceStub(current_mode=MODES[0][1])
        drawer = _DrawerStub([Key.LEFT, 27, Key.ENTER, 27])
        sut = MisterVideoAdjustMenu(drawer, service, {'header': 'Adjust'})

        result = sut.process_key()

        self.assertEqual(['320,14,31,51,240,2,3,16,6515', MODES[0][1]], service.apply_calls)
        self.assertEqual(MODES[0][1], service.current_mode())
        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)


def _video_mode_service(logger):
    return MisterVideoModeServiceTester(logger=logger)


class _VideoModeServiceStub:
    def __init__(self, current_mode=None):
        self._current_mode = current_mode
        self.apply_calls = []
        self.kept_modes = []

    def current_mode(self):
        return self._current_mode

    def apply_mode(self, mode_str):
        self.apply_calls.append(mode_str)
        self._current_mode = mode_str
        return True

    def remember_unsaved_kept_mode(self, mode_str, previous_mode=None):
        self.kept_modes.append((mode_str, previous_mode))


class _LoggerStub:
    def __init__(self):
        self.debugs = []

    def debug(self, message):
        self.debugs.append(message)


class _OsUtilsStub:
    def sleep(self, _seconds):
        pass


class _DrawerStub:
    def __init__(self, keys):
        self._keys = list(keys)
        self.timeout_calls = []
        self.menu_entries = []
        self.text_lines = []
        self.overscan_preview_calls = 0

    def start(self, data):
        pass

    def add_text_line(self, text):
        self.text_lines.append(text)

    def add_menu_entry(self, option, info, is_selected=False):
        self.menu_entries.append((option, info, is_selected))

    def add_action(self, action, is_selected=False):
        pass

    def show_overscan_preview(self):
        self.overscan_preview_calls += 1

    def paint(self):
        return self._keys.pop(0)

    def clear(self):
        pass

    def set_key_timeout(self, timeout_ms):
        self.timeout_calls.append(timeout_ms)

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


def _crt_warning(target): return {
    "ui": "confirm",
    "header": "CRT WARNING",
    "alert_level": "red",
    "text": [
        "Access this only if you are reading this from an old TV-style CRT right now.",
        "Flat screens, PC CRT monitors and other 24-31 KHz CRTs are not supported.",
        "If you are not sure, go back.",
    ],
    "preselected_action": "Back",
    "actions": [
        {"title": "Continue", "type": "fixed", "fixed": [_crt_direct_video_warning(target)]},
        {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
    ],
}


def _crt_direct_video_warning(target): return {
    "type": "condition",
    "variable": "mister_video_direct_video_warning",
    "true": [{
        "ui": "confirm",
        "header": "DIRECT VIDEO WARNING",
        "alert_level": "red",
        "text": [
            "direct_video=1 is enabled in the active MiSTer config.",
            "Saving a CRT resolution change will remove direct_video=1 and use vga_scaler=1 instead.",
            "Do not continue if you are using a Direct Video HDMI-to-VGA DAC.",
            "Continue only if that matches your setup.",
        ],
        "preselected_action": "Back",
        "actions": [
            {"title": "Continue", "type": "fixed", "fixed": [{"type": "navigate", "target": target}]},
            {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
        ],
    }],
    "false": [{"type": "navigate", "target": target}],
}


_ALL_AJGOWANS_MANUALS_ESTIMATED_BYTES = 23506059264  # ~21.9 GB at 128KB cluster, see estimate_manuals_db_space.json


def _enable_all_manuals_confirm(): return {
    "ui": "confirm",
    "header": "Enable All Manuals DBs?",
    "text": [
        "This will activate all manuals databases.",
        "That is a large download, 8010 files and around 22 GB.",
        "It will take hours!",
        "Free space on /media/fat: {media_fat_available_space:bytes_to_gb}.",
        "Are you sure you want to continue?",
    ],
    "actions": [
        {"title": "Continue", "type": "fixed", "fixed": [
            {"type": "select_all_ajgowans_manuals_dbs", "action": "toggle"},
            {"type": "navigate", "target": "back"},
        ]},
        {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
    ],
}


def _not_enough_space_for_manuals_warning(): return {
    "ui": "confirm",
    "header": "Not Enough Free Space!",
    "alert_level": "black",
    "text": [
        "Enabling all manuals DBs requires 8010 files and around 22 GB.",
        "Only {media_fat_available_space:bytes_to_gb} is available on /media/fat.",
        "Installing all manuals will likely fill up your storage and cause problems.",
        "Free up space or enable only individual manuals instead.",
    ],
    "preselected_action": "Back",
    "actions": [
        {"title": "Continue", "type": "fixed", "fixed": [
            {"type": "select_all_ajgowans_manuals_dbs", "action": "toggle"},
            {"type": "navigate", "target": "back"},
        ]},
        {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
    ],
}


def _try_select_all_ajgowans_manuals_dbs(): return [
    {
        "type": "condition",
        "variable": "ajgowans_manuals_dbs_general_selector",
        "true": [{"type": "select_all_ajgowans_manuals_dbs", "action": "toggle"}],
        "false": [
            {
                "type": "compare_bigger",
                "left": _ALL_AJGOWANS_MANUALS_ESTIMATED_BYTES,
                "right": "media_fat_available_space",
                "target": "manuals_space_fits"
            },
            {
                "type": "condition",
                "variable": "manuals_space_fits",
                "left": [_not_enough_space_for_manuals_warning()],
                "right": [_enable_all_manuals_confirm()],
                "equal": [_not_enough_space_for_manuals_warning()],
            }
        ]
    }
]


def _try_toggle_big_manual_db(target, title, count, size): return [
    {
        "type": "condition",
        "variable": target,
        "true": [
            {"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"},
            {"type": "rotate_variable", "target": target},
        ],
        "false": [{
            "ui": "confirm",
            "header": f"Enable {title}?",
            "text": [
                f"This will activate {title}.",
                f"Around {count} files | {size}.",
                "It could take more than one hour!",
                "Are you sure you want to continue?",
            ],
            "actions": [
                {"title": "Continue", "type": "fixed", "fixed": [
                    {"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"},
                    {"type": "rotate_variable", "target": target},
                    {"type": "navigate", "target": "back"},
                ]},
                {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
            ],
        }],
    }
]


def _try_toggle_mrext_with_zaparoo_prompt(): return [
    {
        "type": "condition",
        "variable": "mrext/all",
        "true": [{"type": "rotate_variable", "target": "mrext/all"}],
        "false": [
            {
                "type": "condition",
                "variable": "ZaparooProject/Zaparoo_MiSTer",
                "true": [{"type": "rotate_variable", "target": "mrext/all"}],
                "false": [
                    {"type": "rotate_variable", "target": "mrext/all"},
                    {
                        "ui": "confirm",
                        "header": "Activate Zaparoo?",
                        "preselected_action": "Yes",
                        "text": [
                            "Do you also want to activate Zaparoo?",
                        ],
                        "actions": [
                            {"title": "Yes", "type": "fixed", "fixed": [
                                *_activate_zaparoo_and_ask_options(_navigate_back_effects()),
                            ]},
                            {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                        ],
                    },
                ],
            },
        ],
    },
]


def _try_toggle_zaparoo_database_with_install_prompts(): return [
    {
        "type": "condition",
        "variable": "ZaparooProject/Zaparoo_MiSTer",
        "true": [{"type": "rotate_variable", "target": "ZaparooProject/Zaparoo_MiSTer"}],
        "false": _activate_zaparoo_and_ask_options(_no_zaparoo_follow_up_prompt_effects()),
    },
]


def _activate_zaparoo_and_ask_options(when_done): return [
    {"type": "rotate_variable", "target": "ZaparooProject/Zaparoo_MiSTer"},
    *_maybe_zaparoo_default_frontend_prompt(when_done),
]


def _maybe_zaparoo_default_frontend_prompt(when_done): return [
    {
        "type": "condition",
        "variable": "zaparoo_frontend_default",
        "true": when_done,
        "false": [_zaparoo_default_frontend_prompt()],
    },
]


def _navigate_back_effects(): return [{"type": "navigate", "target": "back"}]


def _no_zaparoo_follow_up_prompt_effects(): return [
    {"type": "set_variable", "target": "zaparoo_frontend_default", "value": "true"},
]


def _zaparoo_default_frontend_prompt(): return {
    "ui": "confirm",
    "header": "Zaparoo Frontend",
    "preselected_action": "Yes",
    "text": [
        "Do you want the Zaparoo frontend to be",
        "the default frontend after being installed?",
    ],
    "actions": [
        {"title": "Yes", "type": "fixed", "fixed": [
            {"type": "set_variable", "target": "zaparoo_frontend_default", "value": "true"},
            {"type": "navigate", "target": "back"},
        ]},
        {"title": "No", "type": "fixed", "fixed": [
            {"type": "set_variable", "target": "zaparoo_frontend_default", "value": "false"},
            {"type": "navigate", "target": "back"},
        ]},
    ],
}


def _manuals_early_access_notice(target): return {
    "ui": "message",
    "header": "Manuals on MiSTer",
    "text": [
        "Manuals on MiSTer should still be considered an early access feature.",
        "There are still rough edges, including a viewer that needs improvement.",
        "Manuals DBs are also fairly large and download many files.",
        "That means installs will take more time when they are enabled.",
    ],
    "effects": [{"type": "navigate", "target": target}],
}


def settings_screen_model(): return {
    "formatters": {
        "yesno": {"false": "No", "true": "Yes"},
        "yesno_reverse": {"false": "Yes", "true": "No"},
        "enabled": {"false": "Off.", "true": "On."},
        "encc_forks": {"devel": "MiSTer-devel", "db9": "MiSTer-DB9", "aitorgomez": "AitorGomez Fork"},
        "encc_forks_description": {"devel": "Official Cores from MiSTer-devel", "db9": "DB9 / SNAC8 forks with ENCC", "aitorgomez": "AitorGomez Fork"},
        "download_beta_cores": {"false": "jtcores", "true": "jtpremium"},
# @TODO (mirror)       "mirror": {"": "Off.", "off": "Off.", "mysticalrealm": "Mystical Realm"},
        "overscan": {"none": "None", "low": "Low", "medium": "Medium", "high": "High", "maximum": "Max"},
        "bytes_to_gb": {},
        "device_label_message": {},
        "bool_flag_presence_text": {
            "0": "Ignore them entirely",
            "1": "Place them only on its {0} folder",
            "2": "Place them everywhere",
        }
    },
    "variables": {
        # Global variables
        "update_all_version": {"default": "2.8"},
        "device_label": {"default": ""},
        "zaparoo_frontend_default": {"group": "store", "default": "false", "values": ["false", "true"]},
        "main_updater": {"group": ["ua_ini", "db"], "default": "true", "values": ["false", "true"]},        
        "encc_forks": {"group": "ua_ini", "default": "devel", "values": ["devel", "db9", "aitorgomez"]},
        "jotego_updater": {"group": ["ua_ini", "db"], "default": "true", "values": ["false", "true"]},
        "download_beta_cores": {"group": "jt_ini", "default": "false", "values": ["false", "true"]},
        "bios_getter": {"group": ["ua_ini", "separate_db"], "default": "false", "values": ["false", "true"]},
        "arcade_roms_db_downloader": {"group": ["ua_ini", "separate_db"], "default": "false", "values": ["false", "true"]},
        "names_txt_updater": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
        "arcade_organizer": {"group": ["ua_ini", "ao_ini"], "default": "false", "values": ["false", "true"]},

        # Internal variables
        "file_exists": {"default": "false", "values": ["false", "true"]},
        "needs_save": {"default": "false", "values": ["false", "true"]},
        "needs_save_file_list": {"default": ""},
        "mister_video_direct_video_warning": {"default": "false", "values": ["false", "true"]},
        "media_fat_available_space": {"default": "-1"},
        "manuals_space_fits": {"default": ""},
        "has_arcade_organizer_folders": {"default": "false", "values": ["false", "true"]},
        "has_right_available_code": {"default": "false", "values": ["false", "true"]},
    },
    "base_types": {
        "dialog_sub_menu": {
            "type": "ui",
            "ui": "menu",
            "hotkeys": [{"keys": [27], "action": [{"type": "navigate", "target": "back"}]}],
            "actions": [
                {"title": "Select", "type": "symbol", "symbol": "ok"},
                {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
            ],
            "entries": [
                {
                    "title": "BACK",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "back"}]}
                },
            ]
        },
        "dialog_sub_menu_toggle": {
            "type": "dialog_sub_menu",
            "actions": [
                'replace',
                {"title": "Select", "type": "symbol", "symbol": "ok"},
                {"title": "Toggle",  "type": "symbol", "symbol": "toggle"},
                {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
            ]
        },
        "dialog_sub_menu_info": {
            "type": "dialog_sub_menu",
            "actions": [
                'replace',
                {"title": "Select", "type": "symbol", "symbol": "ok"},
                {"title": "Info", "type": "symbol", "symbol": "info"},
                {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
            ]
        },
    },
    "items": {
        "test_menu": {
            "type": "dialog_sub_menu",
            "header": "Test Menu",
            "text": [
                "This is @Test Text@ aka @'DEBUG'@ to see how ~themes~ look",
                " ",
                "Other key contributors:",
                " ·@TEST@ ~test.com/test~ - Test cores",
                " ·@my bigger test@ ~patreon.com/test~ - Test software",
                " ·@theypsilon@ ~my_url.com/theypsilon~ - The test menu itself!",
                " ",
                "Test out!"
            ],
            "entries": [
                {
                    "title": "# BLACK",
                    "description": "yesno ~formatter~: {main_updater:yesno}",
                    "actions": {"ok": [
                        {
                            "ui": "menu",
                            "header": "Testing black screen!",
                            "text": [
                                "No need to change any of this. This is not meant to be updated",
                                " ",
                                " ·@theypsilon@ ~my_url.com/theypsilon~ - That's black sub theme",
                            ],
                            "alert_level": "black",
                            "preselected_action": "Yes",
                            "entries": [
                                {"title": "# FIRST", "description": "First", "actions": {"ok": []}},
                                {"title": "# SECOND", "description": "Second", "actions": {"ok": []}},
                            ],
                            "actions": [
                                {"title": "Yes", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                                {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                            ],
                        },
                    ]}
                },
                {
                    "title": "# RED",
                    "description": "enabled @formatter@: {main_updater:enabled}",
                    "actions": {"ok": [
                        {
                            "ui": "menu",
                            "header": "Testing red screen!",
                            "text": [
                                "No need to change any of this. This is not meant to be updated",
                                " ",
                                " ·@theypsilon@ ~my_url.com/theypsilon~ - That's red sub theme",
                            ],
                            "alert_level": "red",
                            "preselected_action": "Yes",
                            "entries": [
                                {"title": "# FIRST", "description": "First", "actions": {"ok": []}},
                                {"title": "# SECOND", "description": "Second", "actions": {"ok": []}},
                            ],
                            "actions": [
                                {"title": "Yes", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                                {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                            ],
                        },
                    ]}
                },
                {
                    "title": "Go to MAIN MENU!",
                    "description": "yesno_reverse formatter: {main_updater:yesno_reverse}",
                    "actions": {"ok": [{"type": "navigate", "target": "main_menu_login"}]}
                },
            ]
        },
        "main_menu_login": _main_menu(retroaccount_logged_in=False),
        "main_menu_account": _main_menu(retroaccount_logged_in=True),
        "retroaccount_account_menu": {
            "type": "dialog_sub_menu",
            "header": "RetroAccount",
            "variables": {
                "retroaccount_domain": {"default": "https://retroaccount.com"},
                "retroaccount_update_all_extras": {"default": "Checking..."},
                "retroaccount_update_all_extras_support": {"default": ""},
                "retroaccount_jtbeta_access": {"default": "Checking..."},
                "retroaccount_jtbeta_access_support": {"default": ""},
                "retroaccount_device_verified": {"default": "false", "values": ["false", "true"]},
                "retroaccount_device_verification_description": {"default": "FPGA ID not linked"},
                "retroaccount_device_verification_message": {"default": "Linking FPGA ID..."},
                "retroaccount_verified_chip_id_message": {"default": ""},
            },
            "entries": [
                {
                    "title": "# Update All Extras",
                    "description": "{retroaccount_update_all_extras}",
                    "actions": {"ok": [{
                        "ui": "message", "header": "Update All Extras", "text": [
                            "Access the Extended Timeline, Patrons Menu, custom UI themes, and more!",
                            "",
                            "{retroaccount_update_all_extras_support}",
                        ],
                    }]}
                },
                {
                    "title": "# JOTEGO Patreon Access",
                    "description": "{retroaccount_jtbeta_access}",
                    "actions": {"ok": [{
                        "ui": "message", "header": "JOTEGO Patreon Access", "text": [
                            "Get access to JOTEGO beta and release candidate core versions weeks or even months before public release!",
                            "With this benefit, jtbeta.zip is installed automatically, so you don't have to reinstall it by hand with every new release.",
                            "Other Patreon attachments, such as the KAI MRAs, are also installed automatically."
                            "\n",
                            "{retroaccount_jtbeta_access_support}",
                        ],
                    }]}
                },
                {
                    "title": "# Link FPGA ID",
                    "description": "{retroaccount_device_verification_description}",
                    "actions": {"ok": [{
                        "type": "condition",
                        "variable": "retroaccount_device_verified",
                        "true": [{
                            "ui": "message",
                            "header": "FPGA ID Linked",
                            "text": [
                                "This device's FPGA ID is linked to RetroAccount.",
                                "{retroaccount_verified_chip_id_message}",
                            ],
                        }],
                        "false": [{
                            "ui": "confirm",
                            "header": "Link FPGA ID",
                            "text": [
                                "Optional. Some benefits require linking this device's FPGA ID.",
                                "",
                                "What happens next:",
                                "Update All loads a small linker core to read the FPGA ID.",
                                "Then Update All links the ID with RetroAccount.",
                                "The process usually takes around 10 seconds.",
                            ],
                            "preselected_action": "Back",
                            "actions": [
                                {"title": "Continue", "type": "fixed", "fixed": [
                                    {"type": "extract_chip_id"},
                                    {"type": "navigate", "target": "retroaccount_device_verification_status"},
                                ]},
                                {"title": "Back", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                            ],
                        }],
                    }]}
                },
                {
                    "title": "# Manage Your Account",
                    "description": "More options at {retroaccount_domain}",
                    "actions": {"ok": [{
                        "ui": "message",
                        "header": "Manage Your Account",
                        "text": [
                            "{device_label:device_label_message}",
                            "",
                            "Visit ~{retroaccount_domain}~ to manage your account and explore available features.",
                        ],
                    }]}
                },
                {
                    "title": "# Logout Device",
                    "description": "Log out from this device",
                    "actions": {"ok": [{
                        "ui": "confirm",
                        "header": "Logout Device",
                        "alert_level": "red",
                        "text": [
                            "If you log out, you'll lose access to your benefits.",
                            "",
                            "Are you sure you want to log out from this device?"
                        ],
                        "preselected_action": "No",
                        "actions": [
                            {"title": "Yes", "type": "fixed", "fixed": [
                                {"type": "retroaccount_device_logout"},
                                {"type": "apply_theme"},
                                {"type": "navigate", "target": "main_menu_login"},
                            ]},
                            {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
                        ],
                    }]}
                }
            ],
            "on_idle": [{"type": "retroaccount_check_state"}]
        },
        "retroaccount_device_verification_result": {
            "ui": "message",
            "header": "Link FPGA ID",
            "variables": {
                "retroaccount_device_verified": {"default": "false", "values": ["false", "true"]},
                "retroaccount_device_verification_description": {"default": "FPGA ID not linked"},
                "retroaccount_device_verification_message": {"default": "Linking FPGA ID..."},
                "retroaccount_verified_chip_id_message": {"default": ""},
            },
            "text": [
                "{retroaccount_device_verification_message}",
                "{retroaccount_verified_chip_id_message}",
            ],
            "on_idle": [{"type": "retroaccount_attach_chip_id_to_device"}],
        },
        "retroaccount_device_verification_status": {
            "ui": "message",
            "header": "Link FPGA ID",
            "variables": {
                "retroaccount_device_verified": {"default": "false", "values": ["false", "true"]},
                "retroaccount_device_verification_description": {"default": "FPGA ID not linked"},
                "retroaccount_device_verification_message": {"default": "Linking FPGA ID..."},
                "retroaccount_verified_chip_id_message": {"default": ""},
            },
            "text": [
                "{retroaccount_device_verification_message}",
                "{retroaccount_verified_chip_id_message}",
            ],
        },
        "main_distribution_menu": {
            "type": "dialog_sub_menu",
            "header": "Main Distribution Settings",
            "entries": [
                {
                    "title": "# Distribution Enabled",
                    "description": "{main_updater:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "main_updater"}]}
                },
                {
                    "title": "# Cores versions",
                    "description": "{encc_forks:encc_forks_description}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "encc_forks"}]}
                },
            ]
        },
        "jtcores_menu": {
            "type": "dialog_sub_menu",
            "header": "JTCORES Settings",
            "entries": [
                {
                    "title": "# JTCORES Enabled",
                    "description": "{jotego_updater:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "jotego_updater"}]}
                },
                {
                    "title": "# Install Private Releases",
                    "description": "{download_beta_cores:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "download_beta_cores"}]}
                },
            ]
        },
        "arcade_roms_database_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade ROMs Database Settings",
            "variables": {
                "hbmame_filter": {"group": "arcade_roms", "default": "false", "values": ["false", "true"]}
            },
            "entries": [
                {
                    "title": "# Arcade ROMs Database Enabled",
                    "description": "{arcade_roms_db_downloader:yesno}",
                    "actions": {"ok": [_roms_copyright_notice('arcade_roms_db_downloader')]}
                },
                {
                    "title": "# Include HBMAME ROMs",
                    "description": "{hbmame_filter:yesno_reverse}",
                    "actions": {"ok": [
                        {
                            "type": "condition",
                            "variable": "hbmame_filter",
                            "true": [{"type": "rotate_variable", "target": "hbmame_filter"}],
                            "false": [
                                {
                                    "ui": "confirm",
                                    "header": "Filtering out HBMAME ROMs!",
                                    "text": [
                                        "Do you really want to exclude HBMAME ROMs from the installation process?",
                                        " ",
                                        "This means that some alternative MRAs will not work correctly."
                                    ],
                                    "alert_level": "black",
                                    "preselected_action": "No",
                                    "actions": [
                                        {"title": "Yes", "type": "fixed", "fixed": [{"type": "rotate_variable", "target": "hbmame_filter"}, {"type": "navigate", "target": "back"}]},
                                        {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
                                    ],
                                },
                            ]
                        }
                    ]}
                },
            ]
        },
        "names_txt_menu": {
            "type": "dialog_sub_menu",
            "header": "Names TXT Settings",
            "variables": {
                "names_region": {"group": "names_ini", "default": "US", "values": ["US", "EU", "JP"]},
                "names_char_code": {"group": "names_ini", "default": "CHAR18", "values": ["CHAR18", "CHAR28"]},
                "names_sort_code": {"group": "names_ini", "default": "Common", "values": ["Common", "Manufacturer"]},
                "arcade_names_txt": {"group": "db", "default": "true", "values": ["true", "false"]},

                "names_txt_file_warning": {"default": "false", "values": ["false", "true"]},
                "names_char_code_warning": {"default": "false", "values": ["false", "true"]},
            },
            "text": [
                "Installs names.txt file containing curated names for your cores.",
                "You can also contribute to the naming of the cores at:",
                "~https://github.com/ThreepwoodLeBrush/Names_MiSTer~"
            ],
            "entries": [
                {
                    "title": "# Names TXT",
                    "description": "{names_txt_updater:yesno}",
                    "actions": {"ok": _try_toggle_update_names_txt()}
                },
                {
                    "title": "# Arcade Names TXT",
                    "description": "{arcade_names_txt:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_names_txt"}]}
                },
                {
                    "title": "# Region",
                    "description": "{names_region}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "names_region"}]}
                },
                {
                    "title": "# Char Code",
                    "description": "{names_char_code}",
                    "actions": {"ok": [
                        {"type": "rotate_variable", "target": "names_char_code"},
                        {"type": "calculate_names_char_code_warning"},
                        {
                            "type": "condition",
                            "variable": "names_char_code_warning",
                            "true": [{
                                "ui": "message",
                                "text": ["It's recommended to set rbf_hide_datecode=1 on MiSTer.ini when using CHAR28"],
                            }],
                            "false": []
                        }
                    ]}
                },
                {
                    "title": "# Sort Code",
                    "description": "{names_sort_code}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "names_sort_code"}]}
                },
                {
                    "title": "# Remove \"names.txt\"",
                    "description": "Back to standard core names based on RBF files",
                    "actions": {"ok": [
                        {"type": "calculate_file_exists", "target": "names.txt"},
                        {
                            "type": "condition",
                            "variable": "file_exists",
                            "true": [{
                                "ui": "confirm",
                                "header": "Are you sure?",
                                "text": ["If you have done changes to names.txt, they will be lost"],
                                "preselected_action": "No",
                                "actions": [
                                    {"title": "Yes", "type": "fixed", "fixed": [
                                        {"type": "remove_file", "target": "names.txt"},
                                        {"ui": "message", "text": ["names.txt Removed"]}
                                    ]},
                                    {"title": "No", "type": "fixed", "fixed": [
                                        {"ui": "message", "text": ["Operation Canceled"]}
                                    ]}
                                ],
                            }],
                            "false": [{"ui": "message", "text": ["names.txt doesn't exist"]}]
                        }
                    ]}
                },
            ]
        },
        "other_cores_menu": {
            "type": "dialog_sub_menu_info",
            "header": "Other Cores",
            "variables": {
                "coin_op_collection_downloader": {"group": ["ua_ini", "db"], "default": "true", "values": ["false", "true"]},
                "arcade_offset_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "llapi_updater": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "unofficial_updater": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "agg23_db": {"group": "db", "default": "false", "values": ["false", "true"]},
                "MikeS11/YC_Builds-MiSTer": {"group": "db", "default": "false", "values": ["false", "true"]},
                "ajgowans/alt-cores": {"group": "db", "default": "false", "values": ["false", "true"]},
                "TheJesusFish/Dual-Ram-Console-Cores": {"group": "db", "default": "false", "values": ["false", "true"]},
                "MiSTerOrganize/MiSTer_Frontier": {"group": "db", "default": "false", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Coin-Op Collection",
                    "description": "{coin_op_collection_downloader:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "coin_op_collection_downloader"}],
                        "toggle": [{"type": "rotate_variable", "target": "coin_op_collection_downloader"}],
                    }
                },
                {
                    "title": "# Arcade Offset",
                    "description": "{arcade_offset_downloader:enabled} Maintainer: Toya",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "arcade_offset_downloader"}],
                        "info": [{
                            "ui": "message",
                            "header": "Arcade Offset folder",
                            "text": ["Hacks for popular arcade games maintained by Toya"],
                        }]
                    }
                },
                {
                    "title": "# LLAPI Forks Folder",
                    "description": "{llapi_updater:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "llapi_updater"}],
                        "info": [{
                            "ui": "message",
                            "header": "LLAPI Forks Folder",
                            "text": ["Cores for BlisSTer and other addons using the Low-Latency API"],
                        }]
                    }
                },
                {
                    "title": "# Unofficial Distribution",
                    "description": "{unofficial_updater:enabled} Maintainer: theypsilon",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "unofficial_updater"}],
                        "info": [{
                            "ui": "message",
                            "header": "theypsilon Unofficial Distribution",
                            "text": [
                                "Some unofficial and early-access cores:",
                                "- zx48 (ZX Spectrum) from Kyp",
                                "- Nemesis from GX400 Friends"
                            ],
                        }]
                    }
                },
                {
                    "title": "# Y/C Builds",
                    "description": "{MikeS11/YC_Builds-MiSTer:enabled} Maintainer: MikeS11",
                    "actions": {
                        "ok": [{
                            "type": "condition",
                            "variable": "MikeS11/YC_Builds-MiSTer",
                            "true": [{"type": "rotate_variable", "target": "MikeS11/YC_Builds-MiSTer"}],
                            "false": [{
                                "ui": "confirm",
                                "header": "You need a compatible cable!",
                                "preselected_action": "No",
                                "text": [
                                    "The Y/C Builds need a modified VGA cable. And if you don't have it, the cores won't display correctly.",
                                    " ",
                                    "Do you have a modified cable compatible with the Y/C Builds?",
                                ],
                                "actions": [
                                    {"title": "Yes", "type": "fixed", "fixed": [{"type": "rotate_variable", "target": "MikeS11/YC_Builds-MiSTer"}, {"type": "navigate", "target": "back"}]},
                                    {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
                                ],
                            }]
                        }],
                        "info": [{
                            "ui": "message",
                            "header": "Y/C Builds",
                            "text": [
                                "Forks with Y/C outputs for cores that don't",
                                "support these outputs yet officially."
                            ],
                        }]
                    }
                },
                {
                    "title": "# agg23's MiSTer Cores",
                    "description": "{agg23_db:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "agg23_db"}],
                        "info": [{
                            "ui": "message",
                            "header": "agg23's MiSTer Cores",
                            "text": ["Cores made by agg23, including Tamagotchi and Game & Watch."],
                        }]
                    }
                },
                {
                    "title": "# Alt Cores",
                    "description": "{ajgowans/alt-cores:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "ajgowans/alt-cores"}],
                        "info": [{
                            "ui": "message",
                            "header": "Alt Cores",
                            "text": [
                                "Modified versions of some cores. Folder: Other"
                            ],
                        }]
                    }
                },
                {
                    "title": "# Dual RAM Console Cores",
                    "description": "{TheJesusFish/Dual-Ram-Console-Cores:enabled} Maintainer: TheJesusFish",
                    "actions": {
                        "ok": [{
                            "type": "condition",
                            "variable": "TheJesusFish/Dual-Ram-Console-Cores",
                            "true": [{"type": "rotate_variable", "target": "TheJesusFish/Dual-Ram-Console-Cores"}],
                            "false": [{
                                "ui": "confirm",
                                "alert_level": "black",
                                "header": "Dual SDRAM required!",
                                "preselected_action": "No",
                                "text": [
                                    "Only users who have two SDRAMs in their MiSTer should enable this option.",
                                    " ",
                                    "Do you have dual SDRAM modules installed?",
                                ],
                                "actions": [
                                    {"title": "Yes", "type": "fixed", "fixed": [{"type": "rotate_variable", "target": "TheJesusFish/Dual-Ram-Console-Cores"}, {"type": "navigate", "target": "back"}]},
                                    {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
                                ],
                            }]
                        }],
                        "info": [{
                            "ui": "message",
                            "header": "Dual RAM Console Cores",
                            "text": ["Console cores with dual SDRAM support."],
                        }]
                    }
                },
                {
                    "title": "# MiSTer Frontier",
                    "description": "{MiSTerOrganize/MiSTer_Frontier:enabled} Hybrid FPGA+ARM cores",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "MiSTerOrganize/MiSTer_Frontier"}],
                        "info": [{
                            "ui": "message",
                            "header": "MiSTer Frontier",
                            "text": [
                                "Software-based gaming platforms on MiSTer:",
                                "fantasy consoles, game engines, and retro",
                                "graphics systems as hybrid FPGA+ARM cores.",
                                " ",
                                "ARM runs the emulator/engine, FPGA drives",
                                "video and audio directly to hardware for",
                                "native CRT-friendly, zero-lag output.",
                            ],
                        }]
                    }
                },
            ]
        },
        "tools_and_scripts_menu": {
            "type": "dialog_sub_menu",
            "header": "Tools & Scripts",
            "variables": {
                "mistersam_files_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "mrext/all": {"group": "db", "default": "false", "values": ["false", "true"]},
                "anime0t4ku_mister_scripts": {"group": "db", "default": "false", "values": ["false", "true"]},
                "tty2oled_files_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "i2c2oled_files_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "retrospy/retrospy-MiSTer": {"group": "db", "default": "false", "values": ["false", "true"]},
                "ZaparooProject/Zaparoo_MiSTer": {"group": "db", "default": "false", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Zaparoo",
                    "description": "{ZaparooProject/Zaparoo_MiSTer:enabled} NFC Launcher & Zaparoo Frontend",
                    "actions": {"ok": [{"type": "navigate", "target": "zaparoo_menu"}]}
                },
                {
                    "title": "# Arcade Organizer",
                    "description": "{arcade_organizer:enabled} Creates folder for easy navigation",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "arcade_organizer_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "arcade_organizer"}],
                    }
                },
                {
                    "title": "# Names TXT",
                    "description": "{names_txt_updater:enabled} Better core names in the menus",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "names_txt_menu"}],
                        "toggle": _try_toggle_update_names_txt(),
                    }
                },
                {
                    "title": "# MiSTer Extensions (wizzo)",
                    "description": "{mrext/all:enabled}",
                    "actions": {"ok": _try_toggle_mrext_with_zaparoo_prompt()}
                },
                {
                    "title": "# MiSTer Super Attract Mode",
                    "description": "{mistersam_files_downloader:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "mistersam_files_downloader"}]}
                },
                {
                    "title": "# Anime0t4ku MiSTer Scripts",
                    "description": "{anime0t4ku_mister_scripts:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "anime0t4ku_mister_scripts"}]}
                },
                {
                    "title": "# tty2oled Add-on script",
                    "description": "{tty2oled_files_downloader:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "tty2oled_files_downloader"}]}
                },
                {
                    "title": "# i2c2oled Add-on script",
                    "description": "{i2c2oled_files_downloader:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "i2c2oled_files_downloader"}]}
                },
                {
                    "title": "# RetroSpy utility",
                    "description": "{retrospy/retrospy-MiSTer:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "retrospy/retrospy-MiSTer"}]}
                }
            ]
        },
        "zaparoo_menu": {
            "type": "dialog_sub_menu",
            "header": "Zaparoo Settings",
            "entries": [
                {
                    "title": "# Zaparoo Database",
                    "description": "{ZaparooProject/Zaparoo_MiSTer:enabled}",
                    "actions": {"ok": _try_toggle_zaparoo_database_with_install_prompts()}
                },
                {
                    "title": "# Keep Zaparoo Frontend active",
                    "description": "{zaparoo_frontend_default:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "zaparoo_frontend_default"}]}
                },
            ]
        },
        "extra_content_menu": {
            "type": "dialog_sub_menu_toggle",
            "header": "Extra Content",
            "formatters": {
                "rannysnice_wallpapers_filter": {"ar16-9": "16x9", "ar4-3": "4x3", "all": "all"},
                "ajgowans_manuals_dbs_general_selector_description": {"false": "Many DBs. ", "true": "All DBs enabled. "},
            },
            "variables": {
                "Ranny-Snice/Ranny-Snice-Wallpapers": {"group": "db", "default": "false", "values": ["false", "true"]},
                "uberyoji_mister_boot_roms_mgl": {"group": "db", "default": "false", "values": ["false", "true"]},
                "Dinierto/MiSTer-GBA-Borders": {"group": "db", "default": "false", "values": ["false", "true"]},
                "rannysnice_wallpapers_filter": {"group": "rannysnice_wallpapers", "default": "ar16-9", "values": ["ar16-9", "ar4-3", "all"]},
            },
            "entries": [
                {
                    "title": "# BIOS Database",
                    "description": "{bios_getter:enabled} BIOS files for your systems",
                    "actions": {
                        "ok": [_roms_copyright_notice('bios_getter')],
                        "toggle": [_roms_copyright_notice('bios_getter')],
                    }
                },
                {
                    "title": "# Arcade ROMs Database",
                    "description": "{arcade_roms_db_downloader:enabled} ROMs for Arcade Cores",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "arcade_roms_database_menu"}],
                        "toggle": [_roms_copyright_notice('arcade_roms_db_downloader')],
                    }
                },
                {
                    "title": "# Game Manuals (EN) DBs",
                    "description": "{ajgowans_manuals_dbs_general_selector:ajgowans_manuals_dbs_general_selector_description}By Moondandy",
                    "actions": {
                        "ok": [_manuals_early_access_notice("game_manuals_en_db_menu")],
                    }
                },
                {
                    "title": "# Dinierto GBA Borders",
                    "description": "{Dinierto/MiSTer-GBA-Borders:enabled} Borders for the GBA Core",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "Dinierto/MiSTer-GBA-Borders"}],
                        "toggle": [{"type": "rotate_variable", "target": "Dinierto/MiSTer-GBA-Borders"}],
                    }
                },
                {
                    "title": "# Ranny Snice Wallpapers",
                    "description": "{Ranny-Snice/Ranny-Snice-Wallpapers:enabled} Wallpapers for {rannysnice_wallpapers_filter} screens",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "rannysnice_wallpapers_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "Ranny-Snice/Ranny-Snice-Wallpapers"}],
                    }
                },
                {
                    "title": "# Anime0t4ku Wallpapers",
                    "description": "",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "anime0t4ku_wallpapers_menu"}],
                    }
                },
                {
                    "title": "# Uberyoji Boot ROMs",
                    "description": "{uberyoji_mister_boot_roms_mgl:enabled} Boot ROMs for popular consoles",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "uberyoji_mister_boot_roms_mgl"}],
                        "toggle": [{"type": "rotate_variable", "target": "uberyoji_mister_boot_roms_mgl"}],
                    }
                },
            ]
        },
        "game_manuals_en_db_menu": {
            "type": "dialog_sub_menu_toggle",
            "header": "Game Manuals (EN) DBs",
            "text": ["Game Manuals (EN) DBs"],
            "formatters": {
                "ajgowans_manuals_dbs_general_selector_title": {
                    "false": "Select All",
                    "true": "Select None",
                },
                "select_all_toggle": {
                    "false": "",
                    "true": "All Selected. ",
                }
            },
            "variables": {
                "ajgowans_manuals_dbs_general_selector": {"group": "store", "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-3do": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-arcadia2001": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-atari2600": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-atari5200": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-atari7800": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-atarilynx": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-atarixegs": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-avision": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-ballyastrocade": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-bbcbridge": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-cdi": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-channelf": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-colecovision": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-creativision": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-fds": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-gameandwatch": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-gameboy": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-gamegear": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-gba": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-gbc": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-intellivision": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-jaguar": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-jaguarcd": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-lcdhandhelds": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-megadrive": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-n64": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-neogeoaes": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-neogeocd": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-nes": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-ngp": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-ngpc": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-odyssey2": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-pokemonmini": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-psx": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-pyuutajr": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-sega32x": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-segacd": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-segasaturn": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-segasg1000": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-sms": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-snes": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-supervision": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-turbografx16": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-turbografxcd": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-vc4000": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-vectrex": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
                "ajgowans/manualsdb-wonderswanc": {"group": ["separate_db", "manuals"], "default": "false", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": " {ajgowans_manuals_dbs_general_selector:ajgowans_manuals_dbs_general_selector_title}",
                    "description": "{ajgowans_manuals_dbs_general_selector:select_all_toggle}8010 files | 21.9GB total",
                    "actions": {
                        "ok": _try_select_all_ajgowans_manuals_dbs(),
                    }
                },
                {},
                {
                    "title": "# 3DO",
                    "description": "{ajgowans/manualsdb-3do:enabled} 133 | 310MB",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-3do"}]}
                },
                {
                    "title": "# Arcadia 2001",
                    "description": "{ajgowans/manualsdb-arcadia2001:enabled} 47",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-arcadia2001"}]}
                },
                {
                    "title": "# Atari 2600",
                    "description": "{ajgowans/manualsdb-atari2600:enabled} 490 | 445MB",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-atari2600"}]}
                },
                {
                    "title": "# Atari 5200",
                    "description": "{ajgowans/manualsdb-atari5200:enabled} 77",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-atari5200"}]}
                },
                {
                    "title": "# Atari 7800",
                    "description": "{ajgowans/manualsdb-atari7800:enabled} 61",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-atari7800"}]}
                },
                {
                    "title": "# Atari Lynx",
                    "description": "{ajgowans/manualsdb-atarilynx:enabled} 74",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-atarilynx"}]}
                },
                {
                    "title": "# Atari XEGS",
                    "description": "{ajgowans/manualsdb-atarixegs:enabled} 31",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-atarixegs"}]}
                },
                {
                    "title": "# AVision",
                    "description": "{ajgowans/manualsdb-avision:enabled} 5",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-avision"}]}
                },
                {
                    "title": "# Bally Astrocade",
                    "description": "{ajgowans/manualsdb-ballyastrocade:enabled} 41",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-ballyastrocade"}]}
                },
                {
                    "title": "# BBC Bridge",
                    "description": "{ajgowans/manualsdb-bbcbridge:enabled} 3",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-bbcbridge"}]}
                },
                {
                    "title": "# CD-i",
                    "description": "{ajgowans/manualsdb-cdi:enabled} 65",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-cdi"}]}
                },
                {
                    "title": "# Channel F",
                    "description": "{ajgowans/manualsdb-channelf:enabled} 30",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-channelf"}]}
                },
                {
                    "title": "# ColecoVision",
                    "description": "{ajgowans/manualsdb-colecovision:enabled} 138",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-colecovision"}]}
                },
                {
                    "title": "# CreatiVision",
                    "description": "{ajgowans/manualsdb-creativision:enabled} 19",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-creativision"}]}
                },
                {
                    "title": "# FDS",
                    "description": "{ajgowans/manualsdb-fds:enabled} 3",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-fds"}]}
                },
                {
                    "title": "# Game & Watch",
                    "description": "{ajgowans/manualsdb-gameandwatch:enabled} 19",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-gameandwatch"}]}
                },
                {
                    "title": "# Game Boy",
                    "description": "{ajgowans/manualsdb-gameboy:enabled} 441 | 1.2GB",
                    "actions": {"ok": _try_toggle_big_manual_db("ajgowans/manualsdb-gameboy", "Game Boy Manuals", "441", "1.2 GB")}
                },
                {
                    "title": "# Game Gear",
                    "description": "{ajgowans/manualsdb-gamegear:enabled} 202 | 600MB",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-gamegear"}]}
                },
                {
                    "title": "# GBA",
                    "description": "{ajgowans/manualsdb-gba:enabled} 742 | 3.0GB",
                    "actions": {"ok": _try_toggle_big_manual_db("ajgowans/manualsdb-gba", "GBA Manuals", "742", "3.0 GB")}
                },
                {
                    "title": "# Game Boy Color",
                    "description": "{ajgowans/manualsdb-gbc:enabled} 308 | 1.1GB",
                    "actions": {"ok": _try_toggle_big_manual_db("ajgowans/manualsdb-gbc", "Game Boy Color Manuals", "308", "1.1 GB")}
                },
                {
                    "title": "# Intellivision",
                    "description": "{ajgowans/manualsdb-intellivision:enabled} 148",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-intellivision"}]}
                },
                {
                    "title": "# Jaguar",
                    "description": "{ajgowans/manualsdb-jaguar:enabled} 60",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-jaguar"}]}
                },
                {
                    "title": "# Jaguar CD",
                    "description": "{ajgowans/manualsdb-jaguarcd:enabled} 16",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-jaguarcd"}]}
                },
                {
                    "title": "# LCD Handhelds",
                    "description": "{ajgowans/manualsdb-lcdhandhelds:enabled} 2",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-lcdhandhelds"}]}
                },
                {
                    "title": "# Mega Drive",
                    "description": "{ajgowans/manualsdb-megadrive:enabled} 635 | 1.7GB",
                    "actions": {"ok": _try_toggle_big_manual_db("ajgowans/manualsdb-megadrive", "Mega Drive Manuals", "635", "1.7 GB")}
                },
                {
                    "title": "# N64",
                    "description": "{ajgowans/manualsdb-n64:enabled} 293 | 856MB",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-n64"}]}
                },
                {
                    "title": "# Neo Geo AES",
                    "description": "{ajgowans/manualsdb-neogeoaes:enabled} 42",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-neogeoaes"}]}
                },
                {
                    "title": "# Neo Geo CD",
                    "description": "{ajgowans/manualsdb-neogeocd:enabled} 35",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-neogeocd"}]}
                },
                {
                    "title": "# NES",
                    "description": "{ajgowans/manualsdb-nes:enabled} 759 | 960MB",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-nes"}]}
                },
                {
                    "title": "# Neo Geo Pocket",
                    "description": "{ajgowans/manualsdb-ngp:enabled} 3",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-ngp"}]}
                },
                {
                    "title": "# Neo Geo Pocket Color",
                    "description": "{ajgowans/manualsdb-ngpc:enabled} 28",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-ngpc"}]}
                },
                {
                    "title": "# Odyssey 2",
                    "description": "{ajgowans/manualsdb-odyssey2:enabled} 79",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-odyssey2"}]}
                },
                {
                    "title": "# Pokemon Mini",
                    "description": "{ajgowans/manualsdb-pokemonmini:enabled} 7",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-pokemonmini"}]}
                },
                {
                    "title": "# PSX",
                    "description": "{ajgowans/manualsdb-psx:enabled} 1295 | 6.1GB",
                    "actions": {"ok": _try_toggle_big_manual_db("ajgowans/manualsdb-psx", "PSX Manuals", "1295", "6.1 GB")}
                },
                {
                    "title": "# Pyuuta Jr",
                    "description": "{ajgowans/manualsdb-pyuutajr:enabled} 9",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-pyuutajr"}]}
                },
                {
                    "title": "# Sega 32X",
                    "description": "{ajgowans/manualsdb-sega32x:enabled} 32",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-sega32x"}]}
                },
                {
                    "title": "# Sega CD",
                    "description": "{ajgowans/manualsdb-segacd:enabled} 149",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-segacd"}]}
                },
                {
                    "title": "# Sega Saturn",
                    "description": "{ajgowans/manualsdb-segasaturn:enabled} 256 | 1.4GB",
                    "actions": {"ok": _try_toggle_big_manual_db("ajgowans/manualsdb-segasaturn", "Sega Saturn Manuals", "256", "1.4 GB")}
                },
                {
                    "title": "# Sega SG-1000",
                    "description": "{ajgowans/manualsdb-segasg1000:enabled} 12",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-segasg1000"}]}
                },
                {
                    "title": "# SMS",
                    "description": "{ajgowans/manualsdb-sms:enabled} 202 | 540MB",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-sms"}]}
                },
                {
                    "title": "# SNES",
                    "description": "{ajgowans/manualsdb-snes:enabled} 766 | 1.9GB",
                    "actions": {"ok": _try_toggle_big_manual_db("ajgowans/manualsdb-snes", "SNES Manuals", "766", "1.9 GB")}
                },
                {
                    "title": "# Supervision",
                    "description": "{ajgowans/manualsdb-supervision:enabled} 53",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-supervision"}]}
                },
                {
                    "title": "# TurboGrafx-16",
                    "description": "{ajgowans/manualsdb-turbografx16:enabled} 77",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-turbografx16"}]}
                },
                {
                    "title": "# TurboGrafx CD",
                    "description": "{ajgowans/manualsdb-turbografxcd:enabled} 44",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-turbografxcd"}]}
                },
                {
                    "title": "# VC 4000",
                    "description": "{ajgowans/manualsdb-vc4000:enabled} 47",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-vc4000"}]}
                },
                {
                    "title": "# Vectrex",
                    "description": "{ajgowans/manualsdb-vectrex:enabled} 31",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-vectrex"}]}
                },
                {
                    "title": "# WonderSwan Color",
                    "description": "{ajgowans/manualsdb-wonderswanc:enabled} 1",
                    "actions": {"ok": [{"type": "select_all_ajgowans_manuals_dbs", "action": "unapply"}, {"type": "rotate_variable", "target": "ajgowans/manualsdb-wonderswanc"}]}
                },
            ]
        },
        "analogue_pocket_menu": {
            "type": "dialog_sub_menu_toggle",
            "header": "Analogue Pocket",
            "variables": {
                "pocket_firmware_version": {"default": "2.5"},
                "pocket_firmware_update": {"group": ["store", "pocket"], "default": "false", "values": ["false", "true"]},
                "pocket_firmware_update_result_header": {"default": "Update Complete!"},
                "pocket_firmware_update_result_txt": {"default": "OK."},
                "pocket_backup": {"group": ["store", "pocket"], "default": "false", "values": ["false", "true"]},
                "pocket_backup_result_header": {"default": "Update Complete!"},
                "pocket_backup_result_txt": {"default": "OK."},
            },
            "entries": [
                {
                    "title": "# Firmware Update",
                    "description": "{pocket_firmware_update:enabled} Installs firmware {pocket_firmware_version} on your Pocket",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "pocket_firmware_update_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "pocket_firmware_update"}]
                    }
                },
                {
                    "title": "# Pocket Backup",
                    "description": "{pocket_backup:enabled} Backup saves & other important files",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "pocket_backup_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "pocket_backup"}]
                    }
                }
            ]
        },
        "pocket_firmware_update_menu": {
            "type": "dialog_sub_menu",
            "header": "Pocket Firmware Update",
            "entries": [
                {
                    "title": "# Run now",
                    "description": "",
                    "actions": {
                        "ok": [
                            {"type": "pocket_firmware_update"},
                            {
                                "ui": "message",
                                "header": "{pocket_firmware_update_result_header}",
                                "text": ["{pocket_firmware_update_result_txt}"]
                            }
                        ]
                    }
                },
                {
                    "title": "# Run always with Update All",
                    "description": "{pocket_firmware_update:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "pocket_firmware_update"}]
                    }
                }
            ]
        },
        "pocket_backup_menu": {
            "type": "dialog_sub_menu",
            "header": "Pocket Backup",
            "entries": [
                {
                    "title": "# Run now",
                    "description": "",
                    "actions": {
                        "ok": [
                            {"type": "pocket_backup"},
                            {
                                "ui": "message",
                                "header": "{pocket_backup_result_header}",
                                "text": ["{pocket_backup_result_txt}"]
                            }
                        ]
                    }
                },
                {
                    "title": "# Run always with Update All",
                    "description": "{pocket_backup:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "pocket_backup"}]
                    }
                }
            ]
        },
        "system_options_menu": {
            "type": "dialog_sub_menu",
            "header": "System Options",
            "variables": {
                "autoreboot": {"group": ["ua_ini", "store"], "default": "true", "values": ["false", "true"]},
                "countdown_time": {"group": ["ua_ini", "store"], "default": "15", "values": ["15", "4", "60"]},
                "log_viewer": {"group": "store", "default": "true", "values": ["false", "true"]},
                "overscan": {"group": "store", "default": "medium", "values": ["none", "low", "medium", "high", "maximum"]},
                "monochrome_ui": {"group": "store", "default": "false", "values": ["false", "true"]},
# @TODO (mirror)                "mirror": {"group": "store", "default": "off", "values": ["off", "mysticalrealm"]},
            },
            "entries": [
                {
                    "title": "# Autoreboot (if needed)",
                    "description": "{autoreboot:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "autoreboot"}]}
                },
                {
                    "title": "# Countdown Timer",
                    "description": "{countdown_time}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "countdown_time"}]}
                },
                {
                    "title": "# Log Viewer",
                    "description": "Scrollable Screen: {log_viewer:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "log_viewer"}]}
                },
                {
                    "title": "# Overscan",
                    "description": "{overscan:overscan}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "overscan"}, {"type": "apply_overscan"}]}
                },
                {
                    "title": "# CRT Video Mode",
                    "description": "Select different resolutions",
                    "actions": {"ok": [_crt_warning("system_video_mode_menu")]}
                },
                {
                    "title": "# CRT Screen Position",
                    "description": "Adjust ←↑↓→ the image.",
                    "actions": {"ok": [_crt_warning("system_video_adjust_menu")]}
                },
                {
                    "title": "# Accessibility: Monochrome UI",
                    "description": "{monochrome_ui:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "monochrome_ui"}, {"type": "apply_theme"}]}
                },
                # {
                #     "title": "# Mirror",
                #     "description": "{mirror}",
                #     "actions": {"ok": [{"type": "rotate_variable", "target": "mirror"}]}
                # }
            ]
        },
        "system_video_mode_menu": {
            "type": "dialog_sub_menu",
            "header": "Select CRT Resolution",
            "text": [
                "IMPORTANT: Choose the option that matches your CRT equipment.",
            ],
            "entries": [
                {
                    "title": "# NTSC 60Hz",
                    "description": "America, JP, PH, MN, KR, TW, EH",
                    "actions": {"ok": [{"type": "navigate", "target": "system_video_mode_menu_ntsc"}]}
                },
                {
                    "title": "# PAL 50Hz",
                    "description": "Europe, Asia, Africa, BR, AR, AU, PY, NZ, UY",
                    "actions": {"ok": [{"type": "navigate", "target": "system_video_mode_menu_pal"}]}
                },
            ]
        },
        "system_video_mode_menu_ntsc": {
            "ui": "mister_video_mode",
            "header": "Select NTSC CRT Resolution",
            "text": [
                "Try a video mode:",
            ],
            "resolutions": [
                {"name": "1 720x240", "video_mode": "720,24,65,71,240,4,3,15,13820"},
                {"name": "2 640x240", "video_mode": "640,30,60,70,240,4,4,14,12587"},
                {"name": "3 512x240", "video_mode": "512,32,72,64,240,8,10,4,10690"},
                {"name": "4 352x240", "video_mode": "352,32,24,64,240,8,10,4,7427"},
                {"name": "5 336x240", "video_mode": "336,16,64,32,240,8,10,4,7043"},
                {"name": "6 320x240 a", "video_mode": "320,13,31,52,240,2,3,16,6515"},
                {"name": "7 320x240 b", "video_mode": "320,8,32,24,240,4,3,16,6048"},
                {"name": "8 304x240", "video_mode": "304,16,56,32,240,8,10,4,6414"},
            ],
        },
        "system_video_mode_menu_pal": {
            "ui": "mister_video_mode",
            "header": "Select PAL CRT Resolution",
            "text": [
                "Try a video mode:",
            ],
            "resolutions": [
                {"name": "1 640x288", "video_mode": "640,32,64,96,288,1,3,17,13100"},
                {"name": "2 640x240", "video_mode": "640,30,60,70,288,6,4,14,12587"},
                {"name": "3 512x288", "video_mode": "512,32,56,72,288,1,3,20,10680"},
                {"name": "4 384x288", "video_mode": "384,16,40,56,288,1,3,17,7850"},
                {"name": "5 352x288", "video_mode": "352,16,40,56,288,1,3,20,7400"},
                {"name": "6 320x288", "video_mode": "320,13,31,52,288,4,3,18,6510"},
            ],
        },
        "system_video_adjust_menu": {
            "ui": "mister_video_adjust",
            "header": "Adjust CRT Screen Position",
            "text": [
                "Press ←↑↓→ to move the image.",
                "ESC to restore.",
            ],
        },
        "rannysnice_wallpapers_menu": {
            "type": "dialog_sub_menu",
            "header": "Ranny Snice Wallpapers Settings",
            "entries": [
                {
                    "title": "# Wallpapers Enabled",
                    "description": "{Ranny-Snice/Ranny-Snice-Wallpapers:yesno}",
                    "actions":  {"ok": [{"type": "rotate_variable", "target": "Ranny-Snice/Ranny-Snice-Wallpapers"}]}
                },
                {
                    "title": "# Aspect Ratio",
                    "description": "{rannysnice_wallpapers_filter}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "rannysnice_wallpapers_filter"}]}
                },
            ]
        },
        "anime0t4ku_wallpapers_menu": {
            "type": "dialog_sub_menu",
            "variables": {
                "anime0t4ku_wallpapers": {"group": "db", "default": "false", "values": ["false", "true"]},
                "pcn_challenge_wallpapers": {"group": "db", "default": "false", "values": ["false", "true"]},
            },
            "header": "Anime0t4ku Wallpapers Settings",
            "entries": [
                {
                    "title": "# Unrestricted Anime0t4ku 16:9 Wallpapers",
                    "description": "{anime0t4ku_wallpapers:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "anime0t4ku_wallpapers"}]}
                },
                {
                    "title": "# PCN Challenge 16:9 Wallpapers",
                    "description": "{pcn_challenge_wallpapers:enabled}",
                    "actions": {
                        "ok": [{
                            "ui": "confirm",
                            "header": "PCN Challenge Wallpapers",
                            "text": [
                                "Anime0t4ku creates these wallpapers during Pixel Cherry Ninja livestreams.",
                                "They are made live based on suggestions from the chat, often within time limits or specific creative challenges.",
                            ],
                            "actions": [
                                {"title": "Enable", "type": "fixed", "fixed": [{"type": "set_variable", "value": "true", "target": "pcn_challenge_wallpapers"}, {"type": "navigate", "target": "back"}]},
                                {"title": "Disable", "type": "fixed", "fixed": [{"type": "set_variable", "value": "false", "target": "pcn_challenge_wallpapers"}, {"type": "navigate", "target": "back"}]}
                            ],
                        }],
                    }
                },
            ]
        },
        "patrons_menu": {
            "ui": "menu",
            "header": "Patrons Menu",
            "hotkeys": [
                {
                    "keys": [27],
                    "action": [{
                        "type": "condition",
                        "variable": "firmware_needs_reboot",
                        "true": [{
                            "ui": "message",
                            "header": "The Firmware has been changed",
                            "text": ["Please reboot NOW to execute it!"]
                        }],
                        "false": [{"type": "navigate", "target": "back"}]
                    }]
                },
            ],
            "actions": [
                {
                    "title": "Select",
                    "type": "symbol",
                    "symbol": "ok"
                },
                {
                    "title": "Back",
                    "type": "fixed",
                    "fixed": [{
                        "type": "condition",
                        "variable": "firmware_needs_reboot",
                        "true": [{
                            "ui": "message",
                            "header": "The Firmware has been changed",
                            "text": ["Please reboot NOW to execute it!"]
                        }],
                        "false": [{"type": "navigate", "target": "back"}]
                    }]
                }
            ],
            "variables": {
                "ui_theme": {"group": "store", "default": "Blue Installer", "values": ["Blue Installer", "Cyan Night", "Japan", "Aquamarine", "Clean Wall", "Bloody Amber", "Mainframe", "Aurora", "Neon Noir", "Mono"]},
                "firmware_needs_reboot": {"default": "false", "values": ["false", "true"]},
                "timeline_after_logs": {"group": "store", "default": "true", "values": ["true", "false"]},
                "use_settings_screen_theme_in_log_viewer": {"group": "store", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Change Theme",
                    "description": "{ui_theme}",
                    "actions": {"ok": [
                        {"type": "rotate_variable", "target": "ui_theme"},
                        {"type": "disable_monochrome_ui"},
                        {"type": "apply_theme"}
                    ]}
                },
                {
                    "title": "# Apply Theme in Log Viewer",
                    "description": "{use_settings_screen_theme_in_log_viewer:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "use_settings_screen_theme_in_log_viewer"}]}
                },
                {
                    "title": "# Timeline in Log Viewer",
                    "description": "{timeline_after_logs:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "timeline_after_logs"}]}
                },
                {
                    "title": "# Advanced Options",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "patrons_advanced_menu"}]}
                },
                {
                    "title": "# BACK",
                    "description": "",
                    "actions": {"ok": [
                        {
                            "type": "condition",
                            "variable": "firmware_needs_reboot",
                            "true": [{
                                "ui": "message",
                                "header": "The Firmware has been changed",
                                "text": ["Please reboot NOW to execute it!"]
                            }],
                            "false": [{"type": "navigate", "target": "back"}]
                        },
                    ]}
                },
            ]
        },
        "patrons_advanced_menu": {
            "ui": "menu",
            "header": "Patrons Menu Advanced Options",
            "hotkeys": [
                {
                    "keys": [27],
                    "action": [{
                        "type": "condition",
                        "variable": "firmware_needs_reboot",
                        "true": [{
                            "ui": "message",
                            "header": "The Firmware has been changed",
                            "text": ["Please reboot NOW to execute it!"]
                        }],
                        "false": [{"type": "navigate", "target": "back"}]
                    }]
                },
            ],
            "actions": [
                {
                    "title": "Select",
                    "type": "symbol",
                    "symbol": "ok"
                },
                {
                    "title": "Back",
                    "type": "fixed",
                    "fixed": [{
                        "type": "condition",
                        "variable": "firmware_needs_reboot",
                        "true": [{
                            "ui": "message",
                            "header": "The Firmware has been changed",
                            "text": ["Please reboot NOW to execute it!"]
                        }],
                        "false": [{"type": "navigate", "target": "back"}]
                    }]
                }
            ],
            "formatters": {
                "spinner_option": {"true": "Revert Unstable Spinner Firmware", "false": "Test Experimental Spinner Firmware"},
                "spinner_desc": {"true": "Restore the original MiSTer binary", "false": "For the Taito EGRET II Mini"}
            },
            "variables": {
                "is_test_spinner_firmware_applied": {"default": "false", "values": ["false", "true"]},
                "firmware_needs_reboot": {"default": "false", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# {is_test_spinner_firmware_applied:spinner_option}",
                    "description": "{is_test_spinner_firmware_applied:spinner_desc}",
                    "actions": {"ok": [
                        {"type": "calculate_is_test_spinner_firmware_applied"},
                        {
                            "type": "condition",
                            "variable": "is_test_spinner_firmware_applied",
                            "true": [{"type": "test_unstable_spinner_firmware"}],
                            "false": [{
                                "ui": "confirm",
                                "header": "WARNING",
                                "alert_level": "red",
                                "preselected_action": "No",
                                "text": [
                                    "This will replace the original firmware with an unstable test version that only works with Arkanoid. All other cores using the mouse WILL work erratically.",
                                    " ",
                                    "You have to revert to the original firmware after you are done testing Arkanoid.",
                                    " ",
                                    "DON'T REPORT ISSUES IN ANY CORE WHILE USING THIS FIRMWARE!"
                                ],
                                "actions": [
                                    {"title": "Yes", "type": "fixed",
                                     "fixed": [{"type": "test_unstable_spinner_firmware"},
                                               {"type": "navigate", "target": "back"}]},
                                    {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
                                ],
                            }]
                        }
                    ]}
                },
                {
                    "title": "# BACK",
                    "description": "",
                    "actions": {"ok": [
                        {
                            "type": "condition",
                            "variable": "firmware_needs_reboot",
                            "true": [{
                                "ui": "message",
                                "header": "The Firmware has been changed",
                                "text": ["Please reboot NOW to execute it!"]
                            }],
                            "false": [{"type": "navigate", "target": "back"}]
                        },
                    ]}
                },
            ]
        },
        "arcade_organizer_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Settings",
            "variables": {
                "arcade_organizer_orgdir": {"rename": "orgdir", "group": "ao_ini", "default": "/media/fat/_Arcade/_Organized", "values": ["/media/fat/_Arcade/_Organized", "/media/fat/_Arcade", "/media/fat/_Arcade Organized"]},
                "arcade_organizer_topdir": {"rename": "topdir", "group": "ao_ini", "default": "", "values": ["", "platform", "core", "year"]},
                "arcade_organizer_skipalts": {"rename": "skipalts", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "formatters": {
                'orgdir_description': {
                    "/media/fat/_Arcade/_Organized": "On 'Organized' folder under 'Arcade'",
                    "/media/fat/_Arcade": "Directly on 'Arcade' folder",
                    "/media/fat/_Arcade Organized": "On new folder 'Arcade Organized'",
                },
                'capitalize': lambda string_value: string_value.capitalize(),
            },
            "entries": [
                {
                    "title": "# Arcade Organizer Enabled",
                    "description": "{arcade_organizer:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer"}]}
                },
                {
                    "title": "# Arcade Organizer Folders",
                    "description": "{arcade_organizer_orgdir:orgdir_description}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_orgdir"}]}
                },
                {
                    "title": "# Top additional folders",
                    "description": "{arcade_organizer_topdir:capitalize}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_topdir"}]}
                },
                {
                    "title": "# Skip MRA-Alternatives",
                    "description": "{arcade_organizer_skipalts:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_skipalts"}]}
                },
                {
                    "title": "# Alphabetic",
                    "description": "Options for 0-9 and A-Z folders",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_alphabetic_menu"}]}
                },
                {
                    "title": "# Region",
                    "description": "Options for Regions (World, Japan, USA...)",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_region_menu"}]}
                },
                {
                    "title": "# Collections",
                    "description": "Options for Platform, Core, Category, Year...",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_collections_menu"}]}
                },
                {
                    "title": "# Video & Input",
                    "description": "Options for Rotation, Resolution, Inputs...",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_video_input_menu"}]}
                },
                {
                    "title": "# Extra Software",
                    "description": "Options for Homebrew, Bootleg, Hacks...",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_extra_software_menu"}]}
                },
                {
                    "title": "# Advanced Submenu",
                    "description": "Advanced Options",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_advanced_menu"}]}
                },
            ]
        },
        "arcade_organizer_alphabetic_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Alphabetic Options",
            "variables": {
                "arcade_organizer_az_dir": {"rename": "az_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Alphabetic folders",
                    "description": "{arcade_organizer_az_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_az_dir"}]}
                },
            ]
        },
        "arcade_organizer_region_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Region Options",
            "variables": {
                "arcade_organizer_region_dir": {"rename": "region_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_region_main": {"rename": "region_main", "group": "ao_ini", "default": "DEV PREFERRED", "values": ["DEV PREFERRED", "Japan", "World", "USA", "Asia", "Europe", "Hispanic", "Spain", "Argentina", "Italy", "Brazil", "France", "Germany"]},
                "arcade_organizer_region_others": {"rename": "region_others", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
            },
            "formatters": {
                "arcade_organizer_region_main_formatter": {"DEV PREFERRED": "Region chosen by the MRA maintainer"}
            },
            "entries": [
                {
                    "title": "# Region folders",
                    "description": "{arcade_organizer_region_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_region_dir"}]}
                },
                {
                    "title": "# Main region",
                    "description": "{arcade_organizer_region_main:arcade_organizer_region_main_formatter}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_region_main"}]}
                },
                {
                    "title": "# MRAs with other regions",
                    "description": "{arcade_organizer_region_others:bool_flag_presence_text=Region}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_region_others"}]}
                },
            ]
        },
        "arcade_organizer_collections_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Collections Options",
            "variables": {
                "arcade_organizer_platform_dir": {"rename": "platform_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_core_dir": {"rename": "core_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_category_dir": {"rename": "category_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_manufacturer_dir": {"rename": "manufacturer_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_series_dir": {"rename": "series_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_best_of_dir": {"rename": "best_of_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Platform folders",
                    "description": "{arcade_organizer_platform_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_platform_dir"}]}
                },
                {
                    "title": "# MiSTer Core folders",
                    "description": "{arcade_organizer_core_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_core_dir"}]}
                },
                {
                    "title": "# Year options",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_year_options_menu"}]}
                },
                {
                    "title": "# Category folders",
                    "description": "{arcade_organizer_category_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_category_dir"}]}
                },
                {
                    "title": "# Manufacturer folders",
                    "description": "{arcade_organizer_manufacturer_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_manufacturer_dir"}]}
                },
                {
                    "title": "# Series folders",
                    "description": "{arcade_organizer_series_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_series_dir"}]}
                },
                {
                    "title": "# Best-of folders",
                    "description": "{arcade_organizer_best_of_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_best_of_dir"}]}
                },
            ]
        },
        "arcade_organizer_year_options_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Year Options",
            "variables": {
                "arcade_organizer_year_dir": {"rename": "year_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_decades_dir": {"rename": "decades_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Year folders",
                    "description": "{arcade_organizer_year_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_year_dir"}]}
                },
                {
                    "title": "# Decade folders",
                    "description": "{arcade_organizer_decades_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_decades_dir"}]}
                },
            ]
        },
        "arcade_organizer_video_input_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Video & Inputs Options",
            "variables": {
                "arcade_organizer_move_inputs": {"rename": "move_inputs", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_num_buttons": {"rename": "num_buttons", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_special_controls": {"rename": "special_controls", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_num_controllers": {"rename": "num_controllers", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_cocktail_dir": {"rename": "cocktail_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_num_monitors": {"rename": "num_monitors", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Resolution options",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_resolution_menu"}]}
                },
                {
                    "title": "# Rotation options",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_rotation_menu"}]}
                },
                {
                    "title": "# Move Inputs folders",
                    "description": "{arcade_organizer_move_inputs:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_move_inputs"}]}
                },
                {
                    "title": "# Num Buttons folders",
                    "description": "{arcade_organizer_num_buttons:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_num_buttons"}]}
                },
                {
                    "title": "# Special Inputs folders",
                    "description": "{arcade_organizer_special_controls:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_special_controls"}]}
                },
                {
                    "title": "# Num Controllers folders",
                    "description": "{arcade_organizer_num_controllers:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_num_controllers"}]}
                },
                {
                    "title": "# Cocktail folders",
                    "description": "{arcade_organizer_cocktail_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_cocktail_dir"}]}
                },
                {
                    "title": "# Num Monitors folders",
                    "description": "{arcade_organizer_num_monitors:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_num_monitors"}]}
                },
            ]
        },
        "arcade_organizer_resolution_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Resolution Options",
            "variables": {
                "arcade_organizer_resolution_dir": {"rename": "resolution_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_resolution_15khz": {"rename": "resolution_15khz", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_resolution_24khz": {"rename": "resolution_24khz", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_resolution_31khz": {"rename": "resolution_31khz", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Resolution folders",
                    "description": "{arcade_organizer_resolution_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_dir"}]}
                },
                {
                    "title": "# 15 kHz Scan Rate",
                    "description": "{arcade_organizer_resolution_15khz:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_15khz"}]}
                },
                {
                    "title": "# 24 kHz Scan Rate",
                    "description": "{arcade_organizer_resolution_24khz:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_24khz"}]}
                },
                {
                    "title": "# 31 kHz Scan Rate",
                    "description": "{arcade_organizer_resolution_31khz:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_31khz"}]}
                },
            ]
        },
        "arcade_organizer_rotation_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Rotation Options",
            "variables": {
                "arcade_organizer_rotation_dir": {"rename": "rotation_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_rotation_0": {"rename": "rotation_0", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_rotation_90": {"rename": "rotation_90", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_rotation_270": {"rename": "rotation_270", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_rotation_180": {"rename": "rotation_180", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_flip": {"rename": "flip", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "# Rotation folders",
                    "description": "{arcade_organizer_rotation_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_dir"}]}
                },
                {
                    "title": "# Horizontal",
                    "description": "{arcade_organizer_rotation_0:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_0"}]}
                },
                {
                    "title": "# Vertical Clockwise",
                    "description": "{arcade_organizer_rotation_90:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_90"}]}
                },
                {
                    "title": "# Vertical Counter-Clockwise",
                    "description": "{arcade_organizer_rotation_270:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_270"}]}
                },
                {
                    "title": "# Horizontal (reversed)",
                    "description": "{arcade_organizer_rotation_180:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_180"}]}
                },
                {
                    "title": "# Cores with Flip in opposite Rotations",
                    "description": "{arcade_organizer_flip:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_flip"}]}
                },
            ]
        },
        "arcade_organizer_extra_software_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Extra Software Options",
            "variables": {
                "arcade_organizer_homebrew": {"rename": "homebrew", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
                "arcade_organizer_bootleg": {"rename": "bootleg", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
                "arcade_organizer_enhancements": {"rename": "enhancements", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
                "arcade_organizer_translations": {"rename": "translations", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
            },
            "entries": [
                {
                    "title": "# Homebrew",
                    "description": "{arcade_organizer_homebrew:bool_flag_presence_text=Homebrew}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_homebrew"}]}
                },
                {
                    "title": "# Bootleg",
                    "description": "{arcade_organizer_bootleg:bool_flag_presence_text=Bootleg}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_bootleg"}]}
                },
                {
                    "title": "# Enhancements",
                    "description": "{arcade_organizer_enhancements:bool_flag_presence_text=Enhancements}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_enhancements"}]}
                },
                {
                    "title": "# Translations",
                    "description": "{arcade_organizer_translations:bool_flag_presence_text=Translations}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_translations"}]}
                },
            ]
        },
        "arcade_organizer_advanced_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer Advanced Options",
            "variables": {
                "arcade_organizer_prepend_year": {"rename": "prepend_year", "group": "ao_ini", "default": "false", "values": ["false", "true"]},
                "arcade_organizer_verbose": {"rename": "verbose", "group": "ao_ini", "default": "false", "values": ["false", "true"]},
                "arcade_organizer_folders_list": {"default": ""}
            },
            "entries": [
                {
                    "title": "# Chronological sort below",
                    "description": "{arcade_organizer_prepend_year:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_prepend_year"}]}
                },
                {
                    "title": "# Verbose script output",
                    "description": "{arcade_organizer_verbose:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_verbose"}]}
                },
                {
                    "title": "# Clean Folders",
                    "description": "Deletes the Arcade Organizer folders",
                    "actions": {"ok": [
                        {"type": "calculate_arcade_organizer_folders"},
                        {
                            "type": "condition",
                            "variable": "has_arcade_organizer_folders",
                            "true": [
                                {
                                    "ui": "confirm",
                                    "header": "ARE YOU SURE?",
                                    "text": [
                                        "WARNING! You will lose ALL the data contained in the folders:",
                                        "{arcade_organizer_folders_list}"
                                    ],
                                    "alert_level": "black",
                                    "preselected_action": "No",
                                    "actions": [
                                        {"title": "Yes", "type": "fixed", "fixed": [
                                            {"type": "clean_arcade_organizer_folders"},
                                            {"ui": "message", "text": ["Organized folder Cleared"]}
                                        ]},
                                        {"title": "No", "type": "fixed", "fixed": [{"ui": "message", "text": ["Operation Canceled"]}]}
                                    ],
                                }
                            ],
                            "false": [{"ui": "message", "text": ["Operation Canceled"]}]
                        },
                    ]}
                },
            ]
        },
    }
}


def _retroaccount_account_entry(): return {
    "title": "# Account",
    "description": "From RetroAccount. {retroaccount_checking}",
    "actions": {
        "ok": [{"type": "navigate", "target": "retroaccount_account_menu"}],
    }
}


def _retroaccount_login_entry(): return {
    "title": "# Login",
    "description": "Login to RetroAccount",
    "actions": {"ok": [{
        "ui": "device_login",
        "header": "Device Login",
        "success_effects": [
            {"type": "set_variable", "target": "retroaccount_open_account_after_login", "value": "true"},
            {"type": "apply_theme"},
            {"type": "navigate", "target": "main_menu_account"},
        ],
        "failure_effects": [{"type": "navigate", "target": "back"}],
    }]}
}

def _main_menu(retroaccount_logged_in): return {
    "ui": "menu",
    "header": "Update All {update_all_version} Settings",
    "variables": {
        "retroaccount_checking": {"default": ""},
        "retroaccount_open_account_after_login": {"default": "false", "values": ["false", "true"]},
    },
    "hotkeys": [{"keys": [27], "action": _try_abort()}],
    "actions": [
        {"title": "Select", "type": "symbol", "symbol": "ok"},
        {"title": "Toggle",  "type": "symbol", "symbol": "toggle"},
        {"title": "Abort", "type": "fixed", "fixed": _try_abort()}
    ],
    "entries": [
        {
            "title": "# Main Distribution",
            "description": "{main_updater:enabled} Main cores from {encc_forks}",
            "actions": {
                "ok": [{"type": "navigate", "target": "main_distribution_menu"}],
                "toggle": [{"type": "rotate_variable", "target": "main_updater"}],
            }
        },
        {
            "title": "# JTCORES for MiSTer",
            "description": "{jotego_updater:enabled} Cores by Jotego Team ({download_beta_cores})",
            "actions": {
                "ok": [{"type": "navigate", "target": "jtcores_menu"}],
                "toggle": [{"type": "rotate_variable", "target": "jotego_updater"}],
            }
        },
        {},  # separator
        {
            "title": "# Other Cores",
            "description": "Coin-Op Collection, LLAPI, Y/C, more...",
            "actions": {
                "ok": [{"type": "navigate", "target": "other_cores_menu"}],
            }
        },
        {
            "title": "# Tools & Scripts",
            "description": "Zaparoo, Names TXT, Scripts...",
            "actions": {
                "ok": [{"type": "navigate", "target": "tools_and_scripts_menu"}],
            }
        },
        {
            "title": "# Extra Content",
            "description": "ROMs, BIOS & Wallpapers",
            "actions": {
                "ok": [{"type": "navigate", "target": "extra_content_menu"}],
            }
        },
        {
            "title": "# Analogue Pocket",
            "description": "Firmware Update & Backups",
            "actions": {"ok": [{"type": "navigate", "target": "analogue_pocket_menu"}]}
        },
        {},  # separator
        _retroaccount_account_entry() if retroaccount_logged_in else _retroaccount_login_entry(),
        {
            "title": "# Patrons Menu",
            "description": "Timeline, Themes, etc... 2026.02.13",
            "actions": {"ok": [
                {"type": "calculate_has_right_available_code"},
                {
                    "type": "condition",
                    "variable": "has_right_available_code",
                    "true": [{"type": "navigate", "target": "patrons_menu"}],
                    "false": [{
                        "ui": "message",
                        "header": "Patrons Menu locked",
                        "text": [
                            "Requires the @Update All Extras@ patron benefit.",
                            " ",
                            "Support ~patreon.com/theypsilon~ and then sign in from the @Login@ menu to unlock it.",
                            " ",
                            "Thank you for your support!",
                        ],
                        "effects": [{
                            "ui": "message",
                            "header": "Support MiSTer",
                            "text": [
                                "Consider supporting @Alexey Melnikov@ aka @'Sorgelig'@ for his invaluable work as the main maintainer of the MiSTer Project: ~patreon.com/FPGAMiSTer~",
                                " ",
                                "Other key contributors:",
                                " ·@Ace@ ~ko-fi.com/ace9921~ - Arcade cores",
                                " ·@Artemio@ ~patreon.com/aurbina~ - Testing tools",
                                " ·@Coin-Op@ ~patreon.com/atrac17~ - Arcade cores",
                                " ·@furrtek@ ~patreon.com/furrtek~ - Reverse engineering hardware",
                                " ·@JimmyStones@ ~ko-fi.com/jimmystones~ - Arcade cores",
                                " ·@JOTEGO@ ~patreon.com/jotego~ - Arcade & Console cores",
                                " ·@1FPGA@ ~patreon.com/1fpga~ - Firmware rewrite",
                                " ·@Pierco@ ~ko-fi.com/pierco~ - Arcade cores",
                                " ·@Srg320@ ~patreon.com/srg320~ - Console cores",
                                " ·@theypsilon@ ~patreon.com/theypsilon~ - Updaters & Other Tools",
                                " ·@wizzo@ ~patreon.com/wizzo~ - Tools & scripts",
                                " ",
                                "Your favorite open-source projects require your support to keep evolving!"
                            ]
                        }],
                    }]
                }
            ]}
        },
        {
            "title": "# System Options",
            "description": "",
            "actions": {"ok": [{"type": "navigate", "target": "system_options_menu"}]}
        },
        {},  # separator
        {
            "title": "SAVE",
            "description": "Writes all changes to the INI file/s",
            "actions": {"ok": [
                {"type": "calculate_needs_save"},
                {
                    "type": "condition",
                    "variable": "needs_save",
                    "true": [{
                        "ui": "confirm",
                        "header": "Are you sure?",
                        "text": [
                            "Following files will be overwritten with your changes:",
                            "{needs_save_file_list}"
                        ],
                        "preselected_action": "No",
                        "actions": [
                            {
                                "title": "Yes",
                                "type": "fixed",
                                "fixed": [{"type": "save"}, {"type": "navigate", "target": "back"}]
                            },
                            {
                                "title": "No",
                                "type": "fixed",
                                "fixed": [{"type": "navigate", "target": "back"}]
                            }
                        ],
                    }],
                    "false": [{"ui": "message", "text": ["No changes to save"]}]
                }
            ]}
        },
        {
            "title": "EXIT and RUN UPDATE ALL",
            "description": "",
            "actions": {"ok": [
                {"type": "calculate_needs_save"},
                {
                    "type": "condition",
                    "variable": "needs_save",
                    "true": [{
                        "ui": "confirm",
                        "header": "INI file/s were not saved",
                        "text": [
                            "Do you really want to run Update All without saving your changes?",
                            "(current changes will apply only for this run)",
                        ],
                        "actions": [
                            {
                                "title": "Yes",
                                "type": "fixed",
                                "fixed": [
                                    {"type": "prepare_exit_dont_save_and_run"},
                                    {"type": "navigate", "target": "exit_and_run"}
                                ]
                            },
                            {
                                "title": "No",
                                "type": "fixed",
                                "fixed": [{"type": "navigate", "target": "back"}]
                            }
                        ],
                    }],
                    "false": [{"type": "navigate", "target": "exit_and_run"}]
                },
                {"type": "navigate", "target": "exit_and_run"}
            ]}
        }
    ],
    "on_idle": [
        {"type": "retroaccount_check_state"},
        {
            "type": "condition",
            "variable": "retroaccount_open_account_after_login",
            "true": [
                {"type": "set_variable", "target": "retroaccount_open_account_after_login", "value": "false"},
                {"type": "navigate", "target": "retroaccount_account_menu"},
            ],
            "false": [],
        },
    ]
}


def _try_access_patrons_menu(): return [
    {"type": "calculate_has_right_available_code"},
    {
        "type": "condition",
        "variable": "has_right_available_code",
        "true": [{"type": "navigate", "target": "patrons_menu"}],
        "false": [{
            "ui": "message",
            "header": "Update All Extras not enabled!",
            "text": [
                "This menu contains exclusive content for patrons only.",
                " ",
                "Support ~patreon.com/theypsilon~ and then log in via the @Login@ menu entry to unlock premium options.",
                " ",
                "Thank you so much for your support!",
            ],
            "effects": [{
                "ui": "message",
                "header": "Support MiSTer",
                "text": [
                    "Consider supporting @Alexey Melnikov@ aka @'Sorgelig'@ for his invaluable work as the main maintainer of the MiSTer Project: ~patreon.com/FPGAMiSTer~",
                    " ",
                    "Other key contributors:",
                    " ·@Ace@ ~ko-fi.com/ace9921~ - Arcade cores",
                    " ·@Artemio@ ~patreon.com/aurbina~ - Testing tools",
                    " ·@atrac17@ ~patreon.com/atrac17~ - MRAs & Modelines",
                    " ·@Blackwine@ ~patreon.com/blackwine~ - Arcade cores",
                    " ·@FPGAZumSpass@ ~patreon.com/FPGAZumSpass~ - Console & Computer cores",
                    " ·@d0pefish@ ~ko-fi.com/d0pefish~ - mt32pi author",
                    " ·@JOTEGO@ ~patreon.com/jotego~ - Arcade & Console cores",
                    " ·@MiSTer-X@ ~patreon.com/MrX_8B~ - Arcade cores",
                    " ·@Nullobject@ ~patreon.com/nullobject~ - Arcade cores",
                    " ·@Srg320@ ~patreon.com/srg320~ - Console cores",
                    " ·@theypsilon@ ~patreon.com/theypsilon~ - Downloader, Update All & Other Tools",
                    " ",
                    "Your favorite open-source projects require your support to keep evolving!"
                ]
            }],
        }]
    }
]


def _try_abort(): return [
    {"type": "calculate_needs_save"},
    {
        "type": "condition",
        "variable": "needs_save",
        "true": [{
            "ui": "confirm",
            "header": "INI file/s were not saved",
            "text": ["Do you really want to abort Update All without saving your changes?"],
            "actions": [
                {"title": "Yes", "type": "fixed", "fixed": [{"type": "prepare_exit_without_save"}, {"type": "navigate", "target": "abort"}]},
                {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
            ],
        }],
        "false": [{"ui": "message", "text": ["Pressed ESC/Abort", "Closing Update All..."], "hotkeys": [{"keys": [27], "action": [{"type": "prepare_exit_without_save"}, {"type": "navigate", "target": "abort"}]}], "effects": [{"type": "prepare_exit_without_save"}, {"type": "navigate", "target": "abort"}]}]
    }
]


def _try_toggle_update_names_txt(): return [
    {
        "type": "condition",
        "variable": "names_txt_updater",
        "true": [{"type": "rotate_variable", "target": "names_txt_updater"}],
        "false": [
            {"type": "calculate_names_txt_file_warning"},
            {
                "type": "condition",
                "variable": "names_txt_file_warning",
                "true": [{
                    "ui": "message",
                    "text": ["WARNING! Your current names.txt file will be overwritten after updating"],
                    "alert_level": "black",
                    "effects": [{"type": "rotate_variable", "target": "names_txt_updater"}, {"type": "navigate", "target": "back"}],
                }],
                "false": [{"type": "rotate_variable", "target": "names_txt_updater"}]
            }
        ]
    }
]


def _roms_copyright_notice(variable): return {
    "type": "condition",
    "variable": variable,
    "false": [{
        "ui": "confirm",
        "header": "COPYRIGHT NOTICE",
        "text": [
            "This database may contain links to copyrighted ROMs, potentially",
            "illegal in your region. Activating this option signifies your",
            "responsibility for any processing and downloading of files within.",
            " ",
            "The author and contributors of this script disclaim all liability",
            "for any legal infringements arising from the use of these links.",
            " ",
            "Users must ensure compliance with local laws and regulations.",
            " ",
            " ",
            "Do you accept these terms and take full responsibility for legal",
            "compliance in your use of this software?"
        ],
        "alert_level": "black",
        "preselected_action": "No",
        "actions": [
            {"title": "Yes", "type": "fixed", "fixed": [{"type": "rotate_variable", "target": variable}, {"type": "navigate", "target": "back"}]},
            {"title": "No", "type": "fixed", "fixed": [{"ui": "message", "text": ["Operation Canceled"]}, {"type": "navigate", "target": "back"}]}
        ],
    }],
    "true": [{"type": "rotate_variable", "target": variable}]
}

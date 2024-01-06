# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

def settings_screen_model(): return {
    "formatters": {
        "yesno": {"false": "No", "true": "Yes"},
        "yesno_reverse": {"false": "Yes", "true": "No"},
        "enabled": {"false": "[ ]", "true": "[*]"},
        "encc_forks": {"false": "MiSTer-devel", "true": "MiSTer-DB9"},
        "encc_forks_description": {"false": "Official Cores from MiSTer-devel", "true": "DB9 / SNAC8 forks with ENCC"},
        "download_beta_cores": {"false": "jtcores", "true": "jtpremium"},
        "bool_flag_presence_text": {
            "0": "Ignore them entirely",
            "1": "Place them only on its {0} folder",
            "2": "Place them everywhere",
        }
    },
    "variables": {
        # Global variables
        "update_all_version": {"default": "2.1"},
        "main_updater": {"group": ["ua_ini", "db"], "default": "true", "values": ["false", "true"]},
        "encc_forks": {"group": "ua_ini", "default": "false", "values": ["false", "true"]},
        "jotego_updater": {"group": ["ua_ini", "db"], "default": "true", "values": ["false", "true"]},
        "download_beta_cores": {"group": "jt_ini", "default": "false", "values": ["false", "true"]},
        "bios_getter": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
        "arcade_roms_db_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
        "names_txt_updater": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
        "arcade_organizer": {"group": ["ua_ini", "ao_ini"], "default": "true", "values": ["false", "true"]},

        # Internal variables
        "file_exists": {"default": "false", "values": ["false", "true"]},
        "needs_save": {"default": "false", "values": ["false", "true"]},
        "needs_save_file_list": {"default": ""},
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
                    "title": "1 BLACK",
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
                                {"title": "1 FIRST", "description": "First", "actions": {"ok": []}},
                                {"title": "2 SECOND", "description": "Second", "actions": {"ok": []}},
                            ],
                            "actions": [
                                {"title": "Yes", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                                {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]},
                            ],
                        },
                    ]}
                },
                {
                    "title": "2 RED",
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
                                {"title": "1 FIRST", "description": "First", "actions": {"ok": []}},
                                {"title": "2 SECOND", "description": "Second", "actions": {"ok": []}},
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
                    "actions": {"ok": [{"type": "navigate", "target": "main_menu"}]}
                },
            ]
        },
        "main_menu": {
            "ui": "menu",
            "header": "Update All {update_all_version} Settings",
            "variables": {
                "coin_op_collection_downloader": {"group": ["ua_ini", "db"], "default": "true", "values": ["false", "true"]},
            },
            "hotkeys": [{"keys": [27], "action": _try_abort()}],
            "actions": [
                {"title": "Select", "type": "symbol", "symbol": "ok"},
                {"title": "Toggle",  "type": "symbol", "symbol": "toggle"},
                {"title": "Abort", "type": "fixed", "fixed": _try_abort()}
            ],
            "entries": [
                {
                    "title": "1 Main Distribution",
                    "description": "{main_updater:enabled} Main MiSTer cores from {encc_forks}",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "main_distribution_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "main_updater"}],
                    }
                },
                {
                    "title": "2 JTCORES for MiSTer",
                    "description": "{jotego_updater:enabled} Cores by Jotego Team ({download_beta_cores})",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "jtcores_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "jotego_updater"}],
                    }
                },
                {
                    "title": "3 Coin-Op Collection",
                    "description": "{coin_op_collection_downloader:enabled} Cores by Coin-Op Collection Org",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "coin_op_collection_downloader"}],
                        "toggle": [{"type": "rotate_variable", "target": "coin_op_collection_downloader"}],
                    }
                },
                {},  # separator
                {
                    "title": "4 Other Cores",
                    "description": "LLAPI, Unofficials, Y/C Builds...",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "other_cores_menu"}],
                    }
                },
                {
                    "title": "5 Tools & Scripts",
                    "description": "Names TXT, Arcade Organizer, Scripts...",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "tools_and_scripts_menu"}],
                    }
                },
                {
                    "title": "6 Extra Content",
                    "description": "ROMs, BIOS & Wallpapers",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "extra_content_menu"}],
                    }
                },
                {},  # separator
                {
                    "title": "7 Analogue Pocket",
                    "description": "Firmware Update & Backups",
                    "actions": {"ok": [{"type": "navigate", "target": "analogue_pocket_menu"}]}
                },
                {
                    "title": "8 Patrons Menu",
                    "description": "Taito Spinner, Themes, etc... [2022.12.07]",
                    "actions": {"ok": [
                        {"type": "calculate_has_right_available_code"},
                        {
                            "type": "condition",
                            "variable": "has_right_available_code",
                            "true": [{"type": "navigate", "target": "patrons_menu"}],
                            "false": [{
                                "ui": "message",
                                "header": "Patreon Key not found!",
                                "text": [
                                    "This menu contains exclusive content for patrons only.",
                                    " ",
                                    "Get your @'Patreon Key'@ file from ~patreon.com/theypsilon~ and put it on the @Scripts@ folder to unlock early access and experimental options.",
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
                                        " ·@atrac17@ ~patreon.com/atrac17~ - Arcade cores",
                                        " ·@d0pefish@ ~ko-fi.com/d0pefish~ - mt32pi author",
                                        " ·@FPGAZumSpass@ ~patreon.com/FPGAZumSpass~ - Console & Computer cores",
                                        " ·@furrtek@ ~patreon.com/furrtek~ - Reverse engineering hardware",
                                        " ·@GoLEm FPGA@ ~patreon.com/golem_fpga~ - Firmware rewrite",
                                        " ·@JOTEGO@ ~patreon.com/jotego~ - Arcade & Console cores",
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
                    "title": "9 System Options",
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
            ]
        },
        "main_distribution_menu": {
            "type": "dialog_sub_menu",
            "header": "Main Distribution Settings",
            "entries": [
                {
                    "title": "1 Distribution Enabled",
                    "description": "{main_updater:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "main_updater"}]}
                },
                {
                    "title": "2 Cores versions",
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
                    "title": "1 JTCORES Enabled",
                    "description": "{jotego_updater:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "jotego_updater"}]}
                },
                {
                    "title": "2 Install Premium Cores",
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
                    "title": "1 Arcade ROMs Database Enabled",
                    "description": "{arcade_roms_db_downloader:yesno}",
                    "actions": {"ok": [_roms_copyright_notice('arcade_roms_db_downloader')]}
                },
                {
                    "title": "2 Include HBMAME ROMs",
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
                    "title": "1 Names TXT",
                    "description": "{names_txt_updater:yesno}",
                    "actions": {"ok": _try_toggle_update_names_txt()}
                },
                {
                    "title": "2 Arcade Names TXT",
                    "description": "{arcade_names_txt:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_names_txt"}]}
                },
                {
                    "title": "3 Region",
                    "description": "{names_region}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "names_region"}]}
                },
                {
                    "title": "4 Char Code",
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
                    "title": "5 Sort Code",
                    "description": "{names_sort_code}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "names_sort_code"}]}
                },
                {
                    "title": "6 Remove \"names.txt\"",
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
                "arcade_offset_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "llapi_updater": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "unofficial_updater": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "agg23_db": {"group": "db", "default": "false", "values": ["false", "true"]},
                "MikeS11/YC_Builds-MiSTer": {"group": "db", "default": "false", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "1 Arcade Offset folder (atrac17)",
                    "description": "{arcade_offset_downloader:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "arcade_offset_downloader"}],
                        "info": [{
                            "ui": "message",
                            "header": "Arcade Offset folder",
                            "text": ["Hacks for popular arcade games maintained by atrac17"],
                        }]
                    }
                },
                {
                    "title": "2 LLAPI Forks Folder",
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
                    "title": "3 theypsilon Unofficial Distribution",
                    "description": "{unofficial_updater:enabled}",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "unofficial_updater"}],
                        "info": [{
                            "ui": "message",
                            "header": "theypsilon Unofficial Distribution",
                            "text": [
                                "Some unofficial and early-access cores, such as:",
                                "- zx48 (ZX Spectrum) from Kyp",
                                "- Nemesis from GX400 Friends",
                                "- Teenage Mutant Ninja Turtles from Wicker Waka"
                            ],
                        }]
                    }
                },
                {
                    "title": "4 Y/C Builds from MikeS11",
                    "description": "{MikeS11/YC_Builds-MiSTer:enabled}",
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
                    "title": "5 agg23's MiSTer Cores",
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
            ]
        },
        "tools_and_scripts_menu": {
            "type": "dialog_sub_menu",
            "header": "Tools & Scripts",
            "variables": {
                "mistersam_files_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "mrext/all": {"group": "db", "default": "false", "values": ["false", "true"]},
                "tty2oled_files_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "i2c2oled_files_downloader": {"group": ["ua_ini", "db"], "default": "false", "values": ["false", "true"]},
                "retrospy/retrospy-MiSTer": {"group": "db", "default": "false", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "1 Arcade Organizer",
                    "description": "{arcade_organizer:enabled} Creates folder for easy navigation",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "arcade_organizer_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "arcade_organizer"}],
                    }
                },
                {
                    "title": "2 Names TXT",
                    "description": "{names_txt_updater:enabled} Better core names in the menus",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "names_txt_menu"}],
                        "toggle": _try_toggle_update_names_txt(),
                    }
                },
                {
                    "title": "3 MiSTer Extensions (wizzo)",
                    "description": "{mrext/all:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "mrext/all"}]}
                },
                {
                    "title": "4 MiSTer Super Attract Mode",
                    "description": "{mistersam_files_downloader:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "mistersam_files_downloader"}]}
                },
                {
                    "title": "5 tty2oled Add-on script",
                    "description": "{tty2oled_files_downloader:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "tty2oled_files_downloader"}]}
                },
                {
                    "title": "6 i2c2oled Add-on script",
                    "description": "{i2c2oled_files_downloader:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "i2c2oled_files_downloader"}]}
                },
                {
                    "title": "7 RetroSpy utility",
                    "description": "{retrospy/retrospy-MiSTer:enabled}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "retrospy/retrospy-MiSTer"}]}
                }
            ]
        },
        "extra_content_menu": {
            "type": "dialog_sub_menu_toggle",
            "header": "Extra Content",
            "formatters": {
                "rannysnice_wallpapers_filter": {"ar16-9": "16x9", "ar4-3": "4x3", "all": "all"},
            },
            "variables": {
                "Ranny-Snice/Ranny-Snice-Wallpapers": {"group": "db", "default": "false", "values": ["false", "true"]},
                "uberyoji_mister_boot_roms_mgl": {"group": "db", "default": "false", "values": ["false", "true"]},
                "RGarciaLago/Wallpaper_Collection": {"group": "db", "default": "false", "values": ["false", "true"]},
                "rannysnice_wallpapers_filter": {"group": "rannysnice_wallpapers", "default": "ar16-9", "values": ["ar16-9", "ar4-3", "all"]},
            },
            "entries": [
                {
                    "title": "1 BIOS Database",
                    "description": "{bios_getter:enabled} BIOS files for your systems",
                    "actions": {
                        "ok": [_roms_copyright_notice('bios_getter')],
                        "toggle": [_roms_copyright_notice('bios_getter')],
                    }
                },
                {
                    "title": "2 Arcade ROMs Database",
                    "description": "{arcade_roms_db_downloader:enabled} ROMs for Arcade Cores",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "arcade_roms_database_menu"}],
                        "toggle": [_roms_copyright_notice('arcade_roms_db_downloader')],
                    }
                },
                {
                    "title": "3 Ranny Snice Wallpapers",
                    "description": "{Ranny-Snice/Ranny-Snice-Wallpapers:enabled} Wallpapers for {rannysnice_wallpapers_filter} screens",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "rannysnice_wallpapers_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "Ranny-Snice/Ranny-Snice-Wallpapers"}],
                    }
                },
                {
                    "title": "4 Uberjoyi Boot ROMs",
                    "description": "{uberyoji_mister_boot_roms_mgl:enabled} Boot ROMs for popular consoles",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "uberyoji_mister_boot_roms_mgl"}],
                        "toggle": [{"type": "rotate_variable", "target": "uberyoji_mister_boot_roms_mgl"}],
                    }
                },
                {
                    "title": "5 RGarciaLago Wallpaper Col.",
                    "description": "{RGarciaLago/Wallpaper_Collection:enabled} Wallpapers from different authors",
                    "actions": {
                        "ok": [{"type": "rotate_variable", "target": "RGarciaLago/Wallpaper_Collection"}],
                        "toggle": [{"type": "rotate_variable", "target": "RGarciaLago/Wallpaper_Collection"}],
                    }
                },
            ]
        },
        "analogue_pocket_menu": {
            "type": "dialog_sub_menu_toggle",
            "header": "Analogue Pocket",
            "variables": {
                "pocket_firmware_version": {"default": "1.0"},
                "pocket_firmware_update": {"group": ["store", "pocket"], "default": "false", "values": ["false", "true"]},
                "pocket_firmware_update_result_header": {"default": "Update Complete!"},
                "pocket_firmware_update_result_txt": {"default": "OK."},
                "pocket_backup": {"group": ["store", "pocket"], "default": "false", "values": ["false", "true"]},
                "pocket_backup_result_header": {"default": "Update Complete!"},
                "pocket_backup_result_txt": {"default": "OK."},
            },
            "entries": [
                {
                    "title": "1 Firmware Update",
                    "description": "{pocket_firmware_update:enabled} Installs firmware {pocket_firmware_version} on your Pocket",
                    "actions": {
                        "ok": [{"type": "navigate", "target": "pocket_firmware_update_menu"}],
                        "toggle": [{"type": "rotate_variable", "target": "pocket_firmware_update"}]
                    }
                },
                {
                    "title": "2 Pocket Backup",
                    "description": "{pocket_backup:enabled} Backup saves & other important files.",
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
                    "title": "1 Run now",
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
                    "title": "2 Run always with Update All",
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
                    "title": "1 Run now",
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
                    "title": "2 Run always with Update All",
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
                "wait_time_for_reading": {"group": ["ua_ini", "store"], "default": "2", "values": ["2", "0", "30"]},
                "countdown_time": {"group": ["ua_ini", "store"], "default": "15", "values": ["15", "4", "60"]},
            },
            "entries": [
                {
                    "title": "1 Autoreboot (if needed)",
                    "description": "{autoreboot:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "autoreboot"}]}
                },
                {
                    "title": "2 Pause (between updaters)",
                    "description": "{wait_time_for_reading}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "wait_time_for_reading"}]}
                },
                {
                    "title": "3 Countdown Timer",
                    "description": "{countdown_time}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "countdown_time"}]}
                },
            ]
        },
        "rannysnice_wallpapers_menu": {
            "type": "dialog_sub_menu",
            "header": "Ranny Snice Wallpapers Settings",
            "entries": [
                {
                    "title": "1 Wallpapers Enabled",
                    "description": "{Ranny-Snice/Ranny-Snice-Wallpapers:yesno}",
                    "actions":  {"ok": [{"type": "rotate_variable", "target": "Ranny-Snice/Ranny-Snice-Wallpapers"}]}
                },
                {
                    "title": "2 Aspect Ratio",
                    "description": "{rannysnice_wallpapers_filter}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "rannysnice_wallpapers_filter"}]}
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
            "formatters": {
                "spinner_option": {"true": "Revert Unstable Spinner Firmware", "false": "Test Unstable Spinner Firmware"},
                "spinner_desc": {"true": "Restore the original MiSTer binary", "false": "For the Taito EGRET II Mini"}
            },
            "variables": {
                "is_test_spinner_firmware_applied": {"default": "false", "values": ["false", "true"]},
                "ui_theme": {"group": "store", "default": "Blue Installer", "values": ["Blue Installer", "Cyan Night", "Japan", "Aquamarine", "Clean Wall"]},
                "firmware_needs_reboot": {"default": "false", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "1 Play Bad Apple Database",
                    "description": "",
                    "actions": {
                        "ok": [{
                            "ui": "confirm",
                            "header": "This will take time",
                            "preselected_action": "No",
                            "text": [
                                "The Bad Apple Database is an animation that takes around 4 minutes to finish.",
                                " ",
                                "You can't interrupt it by pressing any button. You'd have to reboot your MiSTer if you don't want to wait for the animation to end.",
                                " ",
                                "Do you really want to play it now?"
                            ],
                            "actions": [
                                {"title": "Yes", "type": "fixed", "fixed": [{"type": "play_bad_apple"}, {"type": "navigate", "target": "back"}]},
                                {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
                            ],
                        }],
                    }
                },
                {
                    "title": "2 {is_test_spinner_firmware_applied:spinner_option}",
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
                    "title": "3 Settings Screen Theme",
                    "description": "{ui_theme}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "ui_theme"}, {"type": "apply_theme"}]}
                },
                {
                    "title": "BACK",
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
            "header": "Arcade Organizer 2.0 Settings",
            "variables": {
                "arcade_organizer_orgdir": {"rename": "orgdir", "group": "ao_ini", "default": "/media/fat/_Arcade/_Organized", "values": ["/media/fat/_Arcade/_Organized", "/media/fat/_Arcade", "/media/fat/_Arcade Organized"]},
                "arcade_organizer_mad_db_description": {"rename": "mad_db_description", "group": "ao_ini", "default": "https://raw.githubusercontent.com/Toryalai1/MiSTer_ArcadeDatabase/db/mad_db.json.zip", "values": ["https://raw.githubusercontent.com/Toryalai1/MiSTer_ArcadeDatabase/db/mad_db.json.zip", "https://raw.githubusercontent.com/theypsilon/MAD_Database_MiSTer/db/mad_db.json.zip"]},
                "arcade_organizer_topdir": {"rename": "topdir", "group": "ao_ini", "default": "", "values": ["", "platform", "core", "year"]},
                "arcade_organizer_skipalts": {"rename": "skipalts", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_prepend_year": {"rename": "prepend_year", "group": "ao_ini", "default": "false", "values": ["false", "true"]},
                "arcade_organizer_verbose": {"rename": "verbose", "group": "ao_ini", "default": "false", "values": ["false", "true"]},
            },
            "formatters": {
                "mad_db_name_formatter": {
                    "https://raw.githubusercontent.com/Toryalai1/MiSTer_ArcadeDatabase/db/mad_db.json.zip": "Toryalai1/MiSTer_ArcadeDatabase",
                    "https://raw.githubusercontent.com/theypsilon/MAD_Database_MiSTer/db/mad_db.json.zip": "theypsilon/Incomplete_MAD_DB_Generator",
                },
                'orgdir_description': {
                    "/media/fat/_Arcade/_Organized": "On the 'Organized' sub folder under 'Arcade'",
                    "/media/fat/_Arcade": "Directly on 'Arcade' folder",
                    "/media/fat/_Arcade Organized": "On new folder 'Arcade Organized'",
                },
                'capitalize': lambda string_value: string_value.capitalize(),
            },
            "entries": [
                {
                    "title": "1 Arcade Organizer Enabled",
                    "description": "{arcade_organizer:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer"}]}
                },
                {
                    "title": "2 Arcade Organizer Folders",
                    "description": "{arcade_organizer_orgdir:orgdir_description}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_orgdir"}]}
                },
                {
                    "title": "3 Selected Database",
                    "description": "{arcade_organizer_mad_db_description:mad_db_name_formatter}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_mad_db_description"}]}
                },
                {
                    "title": "4 Top additional folders",
                    "description": "{arcade_organizer_topdir:capitalize}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_topdir"}]}
                },
                {
                    "title": "5 Skip MRA-Alternatives",
                    "description": "{arcade_organizer_skipalts:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_skipalts"}]}
                },
                {
                    "title": "6 Chronological sort below",
                    "description": "{arcade_organizer_prepend_year:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_prepend_year"}]}
                },
                {
                    "title": "7 Verbose script output",
                    "description": "{arcade_organizer_verbose:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_verbose"}]}
                },
                {
                    "title": "8 Alphabetic",
                    "description": "Options for 0-9 and A-Z folders",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_alphabetic_menu"}]}
                },
                {
                    "title": "9 Region",
                    "description": "Options for Regions (World, Japan, USA...)",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_region_menu"}]}
                },
                {
                    "title": "0 Collections",
                    "description": "Options for Platform, Core, Category, Year...",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_collections_menu"}]}
                },
                {
                    "title": "A Video & Input",
                    "description": "Options for Rotation, Resolution, Inputs...",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_video_input_menu"}]}
                },
                {
                    "title": "S Extra Software",
                    "description": "Options for Homebrew, Bootleg, Hacks...",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_extra_software_menu"}]}
                },
                {
                    "title": "D Advanced Submenu",
                    "description": "Advanced Options",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_advanced_menu"}]}
                },
            ]
        },
        "arcade_organizer_alphabetic_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Alphabetic Options",
            "variables": {
                "arcade_organizer_az_dir": {"rename": "az_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "1 Alphabetic folders",
                    "description": "{arcade_organizer_az_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_az_dir"}]}
                },
            ]
        },
        "arcade_organizer_region_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Region Options",
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
                    "title": "1 Region folders",
                    "description": "{arcade_organizer_region_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_region_dir"}]}
                },
                {
                    "title": "2 Main region",
                    "description": "{arcade_organizer_region_main:arcade_organizer_region_main_formatter}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_region_main"}]}
                },
                {
                    "title": "3 MRAs with other regions",
                    "description": "{arcade_organizer_region_others:bool_flag_presence_text=Region}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_region_others"}]}
                },
            ]
        },
        "arcade_organizer_collections_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Collections Options",
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
                    "title": "1 Platform folders",
                    "description": "{arcade_organizer_platform_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_platform_dir"}]}
                },
                {
                    "title": "2 MiSTer Core folders",
                    "description": "{arcade_organizer_core_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_core_dir"}]}
                },
                {
                    "title": "3 Year options",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_year_options_menu"}]}
                },
                {
                    "title": "4 Category folders",
                    "description": "{arcade_organizer_category_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_category_dir"}]}
                },
                {
                    "title": "5 Manufacturer folders",
                    "description": "{arcade_organizer_manufacturer_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_manufacturer_dir"}]}
                },
                {
                    "title": "6 Series folders",
                    "description": "{arcade_organizer_series_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_series_dir"}]}
                },
                {
                    "title": "7 Best-of folders",
                    "description": "{arcade_organizer_best_of_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_best_of_dir"}]}
                },
            ]
        },
        "arcade_organizer_year_options_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Year Options",
            "variables": {
                "arcade_organizer_year_dir": {"rename": "year_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_decades_dir": {"rename": "decades_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "1 Year folders",
                    "description": "{arcade_organizer_year_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_year_dir"}]}
                },
                {
                    "title": "2 Decade folders",
                    "description": "{arcade_organizer_decades_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_decades_dir"}]}
                },
            ]
        },
        "arcade_organizer_video_input_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Video & Inputs Options",
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
                    "title": "1 Resolution options",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_resolution_menu"}]}
                },
                {
                    "title": "2 Rotation options",
                    "description": "",
                    "actions": {"ok": [{"type": "navigate", "target": "arcade_organizer_rotation_menu"}]}
                },
                {
                    "title": "3 Move Inputs folders",
                    "description": "{arcade_organizer_move_inputs:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_move_inputs"}]}
                },
                {
                    "title": "4 Num Buttons folders",
                    "description": "{arcade_organizer_num_buttons:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_num_buttons"}]}
                },
                {
                    "title": "5 Special Inputs folders",
                    "description": "{arcade_organizer_special_controls:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_special_controls"}]}
                },
                {
                    "title": "6 Num Controllers folders",
                    "description": "{arcade_organizer_num_controllers:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_num_controllers"}]}
                },
                {
                    "title": "7 Cocktail folders",
                    "description": "{arcade_organizer_cocktail_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_cocktail_dir"}]}
                },
                {
                    "title": "8 Num Monitors folders",
                    "description": "{arcade_organizer_num_monitors:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_num_monitors"}]}
                },
            ]
        },
        "arcade_organizer_resolution_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Resolution Options",
            "variables": {
                "arcade_organizer_resolution_dir": {"rename": "resolution_dir", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_resolution_15khz": {"rename": "resolution_15khz", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_resolution_24khz": {"rename": "resolution_24khz", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
                "arcade_organizer_resolution_31khz": {"rename": "resolution_31khz", "group": "ao_ini", "default": "true", "values": ["false", "true"]},
            },
            "entries": [
                {
                    "title": "1 Resolution folders",
                    "description": "{arcade_organizer_resolution_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_dir"}]}
                },
                {
                    "title": "2 15 kHz Scan Rate",
                    "description": "{arcade_organizer_resolution_15khz:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_15khz"}]}
                },
                {
                    "title": "3 24 kHz Scan Rate",
                    "description": "{arcade_organizer_resolution_24khz:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_24khz"}]}
                },
                {
                    "title": "4 31 kHz Scan Rate",
                    "description": "{arcade_organizer_resolution_31khz:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_resolution_31khz"}]}
                },
            ]
        },
        "arcade_organizer_rotation_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Rotation Options",
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
                    "title": "1 Rotation folders",
                    "description": "{arcade_organizer_rotation_dir:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_dir"}]}
                },
                {
                    "title": "2 Horizontal",
                    "description": "{arcade_organizer_rotation_0:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_0"}]}
                },
                {
                    "title": "3 Vertical Clockwise",
                    "description": "{arcade_organizer_rotation_90:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_90"}]}
                },
                {
                    "title": "4 Vertical Counter-Clockwise",
                    "description": "{arcade_organizer_rotation_270:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_270"}]}
                },
                {
                    "title": "5 Horizontal (reversed)",
                    "description": "{arcade_organizer_rotation_180:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_rotation_180"}]}
                },
                {
                    "title": "6 Cores with Flip in opposite Rotations",
                    "description": "{arcade_organizer_flip:yesno}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_flip"}]}
                },
            ]
        },
        "arcade_organizer_extra_software_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Extra Software Options",
            "variables": {
                "arcade_organizer_homebrew": {"rename": "homebrew", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
                "arcade_organizer_bootleg": {"rename": "bootleg", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
                "arcade_organizer_enhancements": {"rename": "enhancements", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
                "arcade_organizer_translations": {"rename": "translations", "group": "ao_ini", "default": "1", "values": ["1", "0", "2"]},
            },
            "entries": [
                {
                    "title": "1 Homebrew",
                    "description": "{arcade_organizer_homebrew:bool_flag_presence_text=Homebrew}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_homebrew"}]}
                },
                {
                    "title": "2 Bootleg",
                    "description": "{arcade_organizer_bootleg:bool_flag_presence_text=Bootleg}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_bootleg"}]}
                },
                {
                    "title": "3 Enhancements",
                    "description": "{arcade_organizer_enhancements:bool_flag_presence_text=Enhancements}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_enhancements"}]}
                },
                {
                    "title": "4 Translations",
                    "description": "{arcade_organizer_translations:bool_flag_presence_text=Translations}",
                    "actions": {"ok": [{"type": "rotate_variable", "target": "arcade_organizer_translations"}]}
                },
            ]
        },
        "arcade_organizer_advanced_menu": {
            "type": "dialog_sub_menu",
            "header": "Arcade Organizer 2.0 Advanced Options",
            "variables": {
                "arcade_organizer_folders_list": {"default": ""}
            },
            "entries": [
                {
                    "title": "1 Clean Folders",
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


def _try_access_patrons_menu(): return [
    {"type": "calculate_has_right_available_code"},
    {
        "type": "condition",
        "variable": "has_right_available_code",
        "true": [{"type": "navigate", "target": "patrons_menu"}],
        "false": [{
            "ui": "message",
            "header": "Patreon Key not found!",
            "text": [
                "This menu contains exclusive content for patrons only.",
                " ",
                "Get your @'Patreon Key'@ file from ~patreon.com/theypsilon~ and put it on the @Scripts@ folder to unlock early access and experimental options.",
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
                {"title": "Yes", "type": "fixed", "fixed": [{"type": "navigate", "target": "abort"}]},
                {"title": "No", "type": "fixed", "fixed": [{"type": "navigate", "target": "back"}]}
            ],
        }],
        "false": [{"ui": "message", "text": ["Pressed ESC/Abort", "Closing Update All..."], "effects": [{"type": "navigate", "target": "abort"}]}]
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

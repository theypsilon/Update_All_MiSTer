# Arcade Organizer PC Launcher (for Windows, Mac, and Linux)

This launcher runs the [Arcade Organizer](arcade_organizer.md) on a PC without needing a MiSTer. It organizes your arcade MRA files into categorized folders (by genre, year, manufacturer, etc.) directly on the SD card or any local copy of your MiSTer file tree.

The launcher uses the directory where it is placed as the base path. It reads MRA files from `_Arcade/` and creates the organized folders inside `_Arcade/_Organized/`, both relative to the launcher location.

Typically, you would place it in the root of your MiSTer SD card, so that you can do the following workflow:
- Eject the SD from MiSTer and insert it into your PC.
- Use the PC to **run the launcher**.
- After completion, eject the SD card from the PC to put it back on MiSTer.
- Turn on your MiSTer.
- Enjoy your organized arcade folders.

## Get the launcher

Download [`arcade_organizer_pc_launcher.py`](https://github.com/theypsilon/Update_All_MiSTer/blob/master/src/arcade_organizer_pc_launcher.py) and place it at the root of your MiSTer file tree (e.g. the SD card root).

## How to run the launcher on Windows?

First, you need to install Python version 3.9 or higher. The easiest way to do it is through the Microsoft Store. Just click on this [link](https://www.microsoft.com/store/productId/9PJPW5LDXLZ5), press the button to get it, and that's all.

Now that the Python installation is completed, you should see that the `arcade_organizer_pc_launcher.py` file has the Python icon. Then just double-click on it, and a window will open with the Arcade Organizer running in it.

On Windows, symlinks require elevated privileges, so the launcher automatically uses file copies instead of symlinks (`NO_SYMLINKS=true`).

### Troubleshooting

* **Microsoft Store showed an error when I attempted to install Python**

Just reboot your computer and try again later.

* **Double-clicking on the file doesn't execute it, but it opens something else**

This happens most probably because you have another program assigned to this file format. The solution is to open the context menu of the launcher file with the mouse right-click. Then navigate to the "Open with" entry, and select Python over there.

* **It runs but shows an error about the Python binary not being found**

You didn't install Python through the Microsoft Store, right? When you use alternative ways to install Python, you need to make sure that the installed programs are getting included in the system path.

* **It runs but closes very quick and I can't read anything**

This probably means Python is not properly installed in your system or it's an old version. If you wanna read a more detailed error message, try to run the launcher from the command prompt ("cmd.exe"), by typing `python3 arcade_organizer_pc_launcher.py` in the same directory.

* **I have Python installed but I don't know which version I have**

Open the command prompt, and type `python3 --version` to find out.

## How to run the launcher on Linux or Mac?

1. Make sure you have installed Python version 3.9 or higher.
2. Open the terminal, and in the same folder where you have placed the launcher execute the following command:
```sh
python3 arcade_organizer_pc_launcher.py
```

## Configuration

The launcher looks for an INI file in this order:
1. `INI_FILE` environment variable (if set)
2. `arcade_organizer_pc_launcher.ini` (same name as the script, with `.ini` extension)
3. `Scripts/update_arcade-organizer.ini` (default location)

If no INI file is found, default settings are used. Key INI options include:

| Option | Default | Description |
|--------|---------|-------------|
| `ORGDIR` | `{base_path}/_Arcade/_Organized` | Where organized folders are created |
| `MRADIR` | `{base_path}/_Arcade/` | Where to find MRA files |
| `SKIPALTS` | `true` | Skip alternative MRAs in main folders |
| `NO_SYMLINKS` | `false` (forced `true` on Windows) | Use file copies instead of symlinks |
| `VERBOSE` | `false` | Show detailed output |

See the [Arcade Organizer documentation](arcade_organizer.md) for all available INI options.

## Environment variables

| Variable | Description |
|----------|-------------|
| `UPDATE_ALL_SOURCE` | URL or local file path to `update_all.pyz` (for development/testing) |
| `PC_LAUNCHER_NO_WAIT` | Set to `1` to skip the "Press Enter" prompt at the end |
| `INI_FILE` | Override the INI file path |

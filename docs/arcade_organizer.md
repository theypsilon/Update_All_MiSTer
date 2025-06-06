# Arcade Organizer

A tool to automate organizing MiSTer's \_Arcade directory based on your MRA files.

The AO does not duplicate any cores or mra files; only soft symlinks are used.

_Note: These sylinks only work on MiSTer. If you mount your SD card outside of MiSTer, these symlinks will not work._

The AO looks at what MRA files you have, and the information in them, to organize MiSTer's `\_Arcade` directory. 

If the XLM tags for _Year, Manufacturer, and Category_ are included in the MRA file, it will create an `\_Organized` Directory in `\_Arcade` and will create the following sub-directories with soft sysmlinks to organize it:

```
_Organized
├── _1 A-E
├── _1 F-K
├── _1 L-Q
├── _1 R-T
├── _1 U-Z
├── _2 Year
├── _3 Manufacturer
└── _4 Category
```

## Features

**You can browse by:**

* Region
* Rotation (0-90-180-270 ± flip)
* Resolution (15-24-31kHz)
* Platform
* Series
* Move Inputs (8-way, 4-way, 2-way)
* Special Controls (spinner, wheel, etc)
* Number of Players
* Number of Buttons
* Decades
* Best-of Lists
* Homebrew
* Bootleg.

**"Top Additional Directories" toggle:**

Allows you to include the extra folders that you choose in the top level of the organized directory: Platform, Core, Year

**"Chronological Sorting at the Botom" toggle:**

By enabling this, every directory will include an additional chronologically sorted index at the bottom of the list.

**_Clean Folders_ sub-option:**

Can be run to delete all the Arcade Organizer folders

**Arcade Database support:**

The AO uses information from the [Arcade Database](https://github.com/MiSTer-devel/ArcadeDatabase_MiSTer) to organize the MRAs. Please report any miscategorization you see in your `\_Organized` folder there if it is due to incorrect metadata.

## Instructions

Run [Update All](../README.md), and press Up on the keyboard to enter the Settings Screen. Then access the arcade organizer suboptions within the *Other Tools & Scripts* menu, which will look like this:

![screnshot of arcade organizer options in update all menu](https://i.imgur.com/3NWiUqi.png)

You can optionally toggle to activate/deactivate specific folders. Deactivating unwanted folders will boost the speed of the process.

## FAQ

**Q: Will this tool over write files I already have?**

A: NO, The AO will not clober files you already have.


**Q: What If I get new MRA/Core files?**

A: You need to re-run Update All to have them included in the Organized files.

**Q: Can I run the Arcade Organizer without Update All?**

This tool is now integrated into Update All, and its code lives in the same codebase. You may run the [archived version of the Arcade Organizer](https://github.com/theypsilon/_arcade-organizer), but be aware that the version there will no longer be updated and any bugs you find will remain unresolved. By contrast, the Arcade Organizer included in Update All will continue to receive improvements and fixes.

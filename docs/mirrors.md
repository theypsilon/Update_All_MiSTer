# Update All mirrors

An Update All mirror rehosts Downloader databases and the files referenced by them. It can also serve the Update All program for a first-run download.

The mirror definition in [`databases.py`](../src/update_all/databases.py) maps database URLs to the mirror. Users normally select that mirror from the Settings Screen. An `update_all.mirror` file provides the same configuration before the first run.

## Use a mirror

### From the Settings Screen

Run `update_all.sh` and press **UP** during the countdown. Open **System Options → Mirror**, choose the mirror, and select **SAVE**. Update All will remember the selection for later runs.

### Before the first run

Place the regular `update_all.sh` launcher in `/media/fat/Scripts`, then create `/media/fat/Scripts/update_all.mirror` next to it:

```json
{
  "mirror_id": "example",
  "mirror_tool_url": "https://mirror.example/theypsilon/Update_All_MiSTer/master/dont_download2.sh"
}
```

- `mirror_id` must exactly match an ID supported in `databases.py`. It selects the mirrored database URLs.
- `mirror_tool_url` must be a direct HTTPS URL to a current, executable copy of `dont_download2.sh` or `update_all.pyz`.

The launcher reads this file before downloading Update All, allowing a new installation to use the mirror from its first download. Mirror operators can distribute `update_all.sh` and `update_all.mirror` together.

An optional `extra_ntp_servers` value may contain comma-separated NTP hostnames for regions where the launcher's default time servers are unavailable. Because a mirror may serve executable code, only use one you trust.

## Host mirror content

### Choose what to mirror

Build the content list in this order:

1. Mirror every database declared by `AllDBs` in [`databases.py`](../src/update_all/databases.py). This is the primary source.
2. Check the database table in the [MultiDatabases MiSTer README](https://github.com/theypsilon/MultiDatabases_MiSTer#readme) and mirror only entries that are not already present in `databases.py`.

Some MultiDatabases entries are already declared in `databases.py`. When an entry appears in both places, use the `databases.py` definition and do not add the README entry a second time.

Synchronize database manifests and downloadable files with GitHub at least once every 24 hours so the mirror does not become stale.

### Rewrite download URLs

Rehosting only the database JSON is not enough: its file entries may still point to GitHub. When publishing a mirrored database, recursively rewrite URLs from `raw.githubusercontent.com`, `github.com`, and `www.github.com` to the equivalent paths on your mirror.

File URLs are either explicit `url` values or `base_files_url` plus the file path, so handle both forms; see Downloader's [custom database format](https://github.com/MiSTer-devel/Downloader_MiSTer/blob/main/docs/custom-databases.md).

URL discovery has at most two levels: first the database, then any remote summaries referenced by its archives. See Downloader's [`summary_file` documentation](https://github.com/MiSTer-devel/Downloader_MiSTer/blob/main/docs/custom-databases-archives.md#summary_file).

Serve the exact original file bytes behind those rewritten URLs so the sizes and hashes recorded in the database continue to validate. Leave URLs on origins you do not mirror unchanged rather than producing dead mirror links.

For first-run support, also host a current runnable Update All file for `mirror_tool_url` and synchronize it at least once every 24 hours.

## Add the mirror with a PR

In `src/update_all/databases.py`:

1. Add a stable, lowercase mirror ID constant and include it in `all_mirrors()`.
2. Add an `AllDBs` subclass. Call `super().__init__()`, then rewrite each `Database.db_url` that your mirror serves.
3. Add a matching branch to `all_dbs()` before the `Unknown mirror` error.

The shape of the change is:

```python
MIRROR_EXAMPLE = 'example'

class AllDBsExampleMirror(AllDBs):
    def __init__(self):
        super().__init__()
        for db in self.all_dbs_list():
            db.db_url = rewrite_for_example_mirror(db.db_url)

def all_dbs(mirror: Optional[str]) -> AllDBs:
    # Existing cases...
    if mirror == MIRROR_EXAMPLE:
        return AllDBsExampleMirror()
    raise ValueError(f'Unknown mirror: {mirror}')
```

Follow the existing mirror classes for concrete rewrite examples. Keep every database's `db_id` and `title` unchanged.

Then register the mirror in `src/update_all/settings_screen_model.py`:

1. Add its friendly name to the `mirror` formatter.
2. Add its ID to the System Options `mirror` variable's `values`.
3. Extend the Mirror entry's actions so users can select it.

Add database tests that verify the new ID and URL rewrites without changing database IDs or titles. Add Settings Screen tests for selecting, displaying, and saving the mirror. Run:

```bash
cd src
python3 -m unittest \
  test.unit.test_databases \
  test.unit.test_settings_screen_model \
  test.unit.test_settings_screen_routines
```

In the PR description, include the public mirror base URL, its synchronization schedule, and a ready-to-copy `update_all.mirror` example. Wait until a released Update All build recognizes the new `mirror_id` before distributing that file broadly.

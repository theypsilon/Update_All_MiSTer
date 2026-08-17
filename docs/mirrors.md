# Update All mirrors

A complete mirror covers two stages:

1. The Update All program itself, including the first-run download.
2. The Downloader databases and the files referenced by those databases.

The `update_all.mirror` file handles the first stage. The mirror definition in [`databases.py`](../src/update_all/databases.py) handles the second.

## Use a mirror

Place the regular `update_all.sh` launcher in `/media/fat/Scripts`, then create `/media/fat/Scripts/update_all.mirror` next to it:

```json
{
  "mirror_tool_url": "https://mirror.example/theypsilon/Update_All_MiSTer/master/dont_download2.sh",
  "mirror_id": "example"
}
```

- `mirror_tool_url` must be a direct HTTPS URL to a current, executable copy of `dont_download2.sh` or `update_all.pyz`.
- `mirror_id` must exactly match an ID supported in `databases.py`.

The launcher reads this file before downloading Update All. On a new installation, where no cached `update_all.pyz` exists yet, even that first download comes from `mirror_tool_url`. It then passes `mirror_id` to Update All so the database URLs use the same mirror.

Mirror operators can distribute `update_all.sh` and `update_all.mirror` together, making the setup available to any user. Because a mirror serves executable code, only use one you trust.

An optional `extra_ntp_servers` value may contain comma-separated NTP hostnames for regions where the launcher's default time servers are unavailable.

## Host a mirror

### Choose what to mirror

Build the content list in this order:

1. Mirror every database declared by `AllDBs` in [`databases.py`](../src/update_all/databases.py). This is the primary source.
2. Check the database table in the [MultiDatabases MiSTer README](https://github.com/theypsilon/MultiDatabases_MiSTer#readme) and mirror only entries that are not already present in `databases.py`.

Some MultiDatabases entries are already declared in `databases.py`. When an entry appears in both places, use the `databases.py` definition and do not add the README entry a second time.

Also mirror a current runnable Update All build for `mirror_tool_url`. Synchronize the mirror with GitHub at least once every 24 hours so builds, database manifests, and downloadable files do not become stale.

### Rewrite download URLs

Rehosting only the database JSON is not enough: its file entries may still point to GitHub. When publishing a mirrored database, recursively rewrite URLs from `raw.githubusercontent.com`, `github.com`, and `www.github.com` to the equivalent paths on your mirror. Apply the same rule to zipped database JSON files.

Serve the exact original file bytes behind those rewritten URLs so the sizes and hashes recorded in the database continue to validate. Leave URLs on origins you do not mirror unchanged rather than producing dead mirror links.

### Add the mirror with a PR

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

Add unit coverage in `src/test/unit/test_databases.py` that verifies the new ID is returned by `all_mirrors()` and that every expected URL is rewritten without changing its database ID or title. Run:

```bash
cd src
python3 -m unittest test.unit.test_databases
```

In the PR description, include the public mirror base URL, its synchronization schedule, and a ready-to-copy `update_all.mirror` example. Wait until a released Update All build recognizes the new `mirror_id` before distributing that file broadly.

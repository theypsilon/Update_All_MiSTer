#!/usr/bin/env python3
# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

import sys
import os
import json
import zipfile
import tempfile
import subprocess
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

# Add src directory to path to import databases
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from update_all.databases import AllDBs, all_dbs_list

# Mirror configuration
SOURCE_DOMAIN = 'raw.githubusercontent.com'
MIRROR_DOMAIN = 'mirror1.undefinedproxy.com'
MIRROR_BRANCH = 'mirror-1'


def main():
    """Main entry point for mirror generation."""
    print("🪞 Starting mirror generation...")

    # Get all databases from AllDBs class
    databases = all_dbs_list()
    print(f"📊 Found {len(databases)} database(s)")

    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Working directory: {temp_path}")

        # Process each database
        processed_files = []
        for db in databases:
            print(f"\n🔄 Processing: {db.title}")
            print(f"   DB ID: {db.db_id}")
            print(f"   URL: {db.db_url}")

            try:
                file_paths = process_database(db, temp_path)
                processed_files.extend(file_paths)
                print(f"   ✅ Successfully processed {len(file_paths)} file(s)")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        if not processed_files:
            print("\n⚠️  No files were processed. Exiting.")
            return 1

        print(f"\n📦 Total files processed: {len(processed_files)}")

        # Commit to orphan branch and force-push
        print(f"\n🌿 Creating orphan branch '{MIRROR_BRANCH}'...")
        commit_and_push(temp_path, processed_files)

    print("\n✨ Mirror generation complete!")
    return 0


def parse_github_url(url):
    """Parse GitHub raw URL to extract full path after domain.

    Expected format: https://raw.githubusercontent.com/<full_path>
    Returns: full_path or None if not a valid GitHub raw URL
    """
    prefix = 'https://raw.githubusercontent.com/'
    if not url.startswith(prefix):
        return None

    # Extract everything after https://raw.githubusercontent.com/
    return url[len(prefix):]


def process_database(db, temp_path):
    """Process a single database: download, transform URLs, and save."""
    url = db.db_url

    # Parse URL to get full path - skip if not a GitHub URL
    full_path = parse_github_url(url)
    if not full_path:
        print(f"   ⏭️  Skipping non-GitHub URL")
        return []

    is_zipped = url.endswith('.zip')

    # Download the file
    print(f"   ⬇️  Downloading...")
    content = download_url(url)

    # Extract directory and filename from full path
    path_parts = full_path.split('/')
    filename = path_parts[-1]
    rel_dir = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else ''
    print(f"   📁 Using path: {full_path}")

    # Create subdirectory structure
    db_dir = temp_path / rel_dir if rel_dir else temp_path
    db_dir.mkdir(parents=True, exist_ok=True)

    # Handle zipped files
    if is_zipped:
        print(f"   📦 Extracting ZIP archive...")
        json_data = extract_json_from_zip(content)
        json_filename = filename.replace('.zip', '')
    else:
        json_data = json.loads(content)
        json_filename = filename

    # Replace URLs in JSON
    print(f"   🔁 Replacing URLs ({SOURCE_DOMAIN} → {MIRROR_DOMAIN})...")
    modified_json = replace_urls_in_json(json_data, SOURCE_DOMAIN, MIRROR_DOMAIN)

    # Save the modified JSON in the org/repo/branch subdirectory
    output_path = db_dir / json_filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(modified_json, f, indent=2, ensure_ascii=False)

    # If original was zipped, zip it again
    if is_zipped:
        print(f"   📦 Creating ZIP archive...")
        zip_path = db_dir / filename
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_path, json_filename)
        output_path.unlink()  # Remove the unzipped file
        result_path = f"{rel_dir}/{filename}" if rel_dir else filename
        return [result_path]

    result_path = f"{rel_dir}/{json_filename}" if rel_dir else json_filename
    return [result_path]


def download_url(url):
    """Download content from URL."""
    try:
        with urlopen(url, timeout=30) as response:
            return response.read()
    except URLError as e:
        raise Exception(f"Failed to download {url}: {e}")


def extract_json_from_zip(zip_content):
    """Extract JSON from ZIP archive."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
        tmp_zip.write(zip_content)
        tmp_zip_path = tmp_zip.name

    try:
        with zipfile.ZipFile(tmp_zip_path, 'r') as zf:
            # Find the first JSON file in the archive
            json_files = [f for f in zf.namelist() if f.endswith('.json')]
            if not json_files:
                raise Exception("No JSON file found in ZIP archive")

            with zf.open(json_files[0]) as json_file:
                return json.load(json_file)
    finally:
        os.unlink(tmp_zip_path)


def replace_urls_in_json(obj, source_domain, target_domain):
    """Recursively replace URLs in JSON object."""
    if isinstance(obj, dict):
        return {k: replace_urls_in_json(v, source_domain, target_domain) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_urls_in_json(item, source_domain, target_domain) for item in obj]
    elif isinstance(obj, str):
        return obj.replace(source_domain, target_domain)
    else:
        return obj


def commit_and_push(temp_path, file_paths):
    """Create orphan branch, commit files, and force-push."""
    repo_root = Path(__file__).parent.parent

    # Create orphan branch (no history)
    run_git(['checkout', '--orphan', MIRROR_BRANCH])

    # Remove all files from index
    run_git(['rm', '-rf', '.'], check=False)

    # Copy processed files to repo root with directory structure
    for file_path in file_paths:
        source = temp_path / file_path
        dest = repo_root / file_path

        # Create parent directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        dest.write_bytes(source.read_bytes())
        print(f"   📄 Added: {file_path}")

    # Add and commit
    run_git(['add'] + file_paths)
    run_git(['commit', '-m', 'Mirror: Update database files'])

    # Force-push to remote
    print(f"   ⬆️  Force-pushing to origin/{MIRROR_BRANCH}...")
    run_git(['push', '-f', 'origin', MIRROR_BRANCH])


def run_git(args, check=True):
    """Run git command."""
    result = subprocess.run(['git'] + args, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise Exception(f"Git command failed: {result.stderr}")
    return result


if __name__ == '__main__':
    sys.exit(main())
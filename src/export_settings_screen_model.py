#!/usr/bin/env python3
# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

from update_all.settings_screen_model import settings_screen_model


def json_default(value: Any) -> str:
    if not callable(value):
        raise TypeError(f'Object of type {value.__class__.__name__} is not JSON serializable')
    return getattr(value, '__name__', repr(value))


def count_nodes(value: Any) -> int:
    children = value.values() if isinstance(value, dict) else value if isinstance(value, list) else []
    return 1 + sum(count_nodes(child) for child in children)


def output_zip_entry_name(output_file: str) -> str:
    path = Path(output_file)
    stem = path.name[:-4]
    return stem if stem.endswith('.json') else f'{stem}.json'


def main() -> int:
    parser = argparse.ArgumentParser(description='Write the Settings Screen model as JSON and print a short summary.')
    parser.add_argument('output_file', help='Path where the model is written as JSON.')
    parser.add_argument('--pretty', action='store_true', help='Write the output file as pretty JSON instead of compact JSON.')
    args = parser.parse_args()

    print('Generating Settings Screen model...')
    model = settings_screen_model()

    top_entries = ', '.join(model.keys())
    print(f'Settings Screen model summary: {count_nodes(model)} nodes, {len(model)} top entries ({top_entries}).')
    if isinstance(model.get('items'), dict):
        print(f'{len(model["items"])} item entries: ' + ', '.join(model['items'].keys()))

    json_kwargs = {'indent': 2} if args.pretty else {'separators': (',', ':')}
    output = json.dumps(model, default=json_default, sort_keys=True, **json_kwargs)
    if args.pretty:
        output += '\n'

    if args.output_file.endswith('.zip'):
        entry_name = output_zip_entry_name(args.output_file)
        print(f'Writing {"pretty" if args.pretty else "compact"} JSON to {args.output_file} as {entry_name}...')
        with zipfile.ZipFile(args.output_file, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zip_file:
            zip_file.writestr(entry_name, output)
    else:
        print(f'Writing {"pretty" if args.pretty else "compact"} JSON to {args.output_file}...')
        with open(args.output_file, 'w') as f:
            f.write(output)

    print('Done.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

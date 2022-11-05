# Copyright (c) 2022 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from enum import Enum
from typing import Callable, Any, TypeVar, Dict


class Key(Enum):
    NONE = 0

    # Directions
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

    # Special
    ENTER = 5


def expand_type(data, base_types):
    if 'type' not in data and 'ui' in data:
        data['type'] = 'ui'

    if 'type' not in data:
        return

    while data['type'] in base_types:
        base_type = base_types[data['type']]

        for key, content in base_type.items():
            if type(content) in (str, int, float, bool):
                data[key] = base_type[key]
            elif isinstance(content, list):
                data[key] = [*data.get(key, []), *base_type.get(key, [])]
            elif isinstance(content, dict):
                data[key] = {**data.get(key, []), **base_type.get(key, [])}
            else:
                raise ValueError(f'Can not inherit field {key} with content of type: {str(type(content))}')


def gather_variable_declarations(model, group = None):
    group = {} if group is None else {group}
    result = {}
    search_in_model(result, model.get('base_types', {}), model, lambda r, v: _add_variables_descriptions(r, v, group))
    return result


def _add_variables_descriptions(result, item, group):
    if 'variables' not in item:
        return

    for variable, description in  item['variables'].items():
        if len(group) > 0:
            if 'group' not in description:
                continue
            description_group = description['group'] if isinstance(description['group'], list) else [description['group']]
            if group.isdisjoint(description_group):
                continue

        result[variable] = description


TResult = TypeVar('TResult')
def search_in_model(result: TResult, base_types: Dict[str, Any], item, cb: Callable[[TResult, Any], None]) -> None:
    expand_type(item, base_types)
    cb(result, item)

    if 'actions' in item:
        if isinstance(item['actions'], dict):
            for action_chain in item['actions'].values():
                for action in action_chain:
                    search_in_model(result, base_types, action, cb)

        elif isinstance(item['actions'], list):
            for action in item['actions']:
                search_in_model(result, base_types, action, cb)

    if 'entries' in item:
        for entry in item['entries']:
            search_in_model(result, base_types, entry, cb)

    if 'effects' in item:
        for effect in item['effects']:
            search_in_model(result, base_types, effect, cb)

    if 'items' in item:
        for item in item['items'].values():
            search_in_model(result, base_types, item, cb)

    if 'type' not in item:
        return

    node_type = item['type']
    if node_type == 'fixed':
        for fixed in item['fixed']:
            search_in_model(result, base_types, fixed, cb)

    elif node_type == 'condition':
        for true in item['true']:
            search_in_model(result, base_types, true, cb)

        for false in item['false']:
            search_in_model(result, base_types, false, cb)


def dynamic_convert_string(value):
    if type(value) == str:
        lower_value = value.lower()
        if lower_value == 'true':
            value = True
        elif lower_value == 'false':
            value = False
        elif value.isdigit():
            value = int(value)

    return value

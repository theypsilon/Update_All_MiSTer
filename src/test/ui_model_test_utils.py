# Copyright (c) 2022-2023 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from typing import Dict, Any, List, Tuple, Set

from update_all.ui_model_utilities import search_in_model


def basic_types(): return 'menu', 'confirm', 'message'
def special_navigate_targets(): return 'back', 'abort', 'exit_and_run'


# Second wave
def ensure_node_is_correct(item):
    if 'actions' in item:
        _ensure_field_least_length_1(item['actions'], item)

    if 'entries' in item:
        _ensure_field_least_length_1(item['entries'], item)

    if 'effects' in item:
        _ensure_field_least_length_1(item['effects'], item)

    if 'items' in item:
        _ensure_field_least_length_1(item['items'], item)

    if 'type' not in item:
        return item

    node_type = item['type']
    if node_type == 'fixed':
        _ensure_field_least_length_1(item['fixed'], item)

    elif node_type == 'condition':
        _ensure_field_least_length_1(item['true'] + item['false'], item)

    return item


def _ensure_field_least_length_1(collection, ctx):
    if len(collection) == 0:
        raise Exception(f'_ensure_field_least_length_1 did not pass.', ctx)


def gather_all_nodes(model):
    result = []
    search_in_model(result, model.get('base_types', {}), model, lambda r, item: r.append(item))
    return [item for item in result if len(item) > 0]


def gather_section_names(model):
    result = set()
    search_in_model(result, model.get('base_types', {}), model, _add_section_name)
    return result


def _add_section_name(result, item):
    if 'items' in item:
        for item in item['items']:
            result.add(item)


def gather_navigate_targets(model):
    result = set()
    search_in_model(result, model.get('base_types', {}), model, _add_navigate_targets)
    return result


def _add_navigate_targets(result, item):
    if 'type' not in item or item['type'] != 'navigate':
        return

    result.add(item['target'])


def gather_formatter_declarations(model):
    result = set()
    search_in_model(result, model.get('base_types', {}), model, _add_formatter_declarations)
    return result


def _add_formatter_declarations(result, item):
    if 'formatters' not in item:
        return

    for formatter in item['formatters']:
        result.add(formatter)


def gather_target_formatters(model):
    result = set()
    search_in_model(result, model.get('base_types', {}), model, _add_target_formatters)
    return result


def _add_target_formatters(result, item):
    if 'header' in item:
        result.update(extract_interpolations_from_text(item['header'])[1])

    if 'texts' in item:
        for text in item['texts']:
            result.update(extract_interpolations_from_text(text)[1])

    if 'title' in item:
        result.update(extract_interpolations_from_text(item['title'])[1])

    if 'description' in item:
        result.update(extract_interpolations_from_text(item['description'])[1])


def gather_used_effects(model):
    result = []
    search_in_model(result, model.get('base_types', {}), model, _add_used_effects)
    return result


def _add_used_effects(result: List[str], item: Dict[str, Any]):
    if 'type' not in item:
        return

    if item['type'] not in ['ui', 'rotate_variable', 'fixed', 'symbol', 'navigate', 'condition']:
        result.append(item['type'])


def gather_target_variables(model) -> Set[str]:
    result = set()
    search_in_model(result, model.get('base_types', {}), model, _add_target_variables)
    return result


def _add_target_variables(result: Set[str], item: Dict[str, Any]) -> None:
    if 'header' in item:
        result.update(extract_interpolations_from_text(item['header'])[0])

    if 'type' not in item:
        return

    node_type = item['type']
    if node_type == 'rotate_variable':
        result.add(item['target'])

    elif node_type == 'condition':
        result.add(item['variable'])


def extract_interpolations_from_text(text: str) -> Tuple[Set[str], Set[str]]:
    variables = set()
    formatters = set()

    reading_state = 0
    reading_value = ''
    reading_modifier = ''

    for character in text:
        if reading_state == 0:
            if character == '{':
                reading_state = 1
                reading_value = ''

        elif reading_state == 1:
            if character == '}':
                reading_state = 0
                variables.add(reading_value)
            elif character == ':':
                reading_state = 2
                reading_modifier = ''
                variables.add(reading_value)
            else:
                reading_value += character

        elif reading_state == 2:
            if character == '=':
                reading_state = 3
                formatters.add(reading_modifier)
            elif character == '}':
                reading_state = 0
                formatters.add(reading_modifier)
            else:
                reading_modifier += character

        elif reading_state == 3:
            if character == '}':
                reading_state = 0

        else:
            raise NotImplementedError(reading_state)

    for v in variables:
        _ensure_field_least_length_1(v, text)

    for f in formatters:
        _ensure_field_least_length_1(f, text)

    return variables, formatters


def expand_model_base_types(model):
    result = {}
    search_in_model(result, model.get('base_types', {}), model, _add_expanded_node)
    return result


def _add_expanded_node(_result, _item):
    pass

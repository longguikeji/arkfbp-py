# pylint: disable=missing-module-docstring
import json


def list_duplicate_removal(raw_list):
    """
    duplicate removal for list.
    """
    transitional_list = list(set(raw_list))
    transitional_list.sort(key=raw_list.index)
    return transitional_list


def json_load(file):
    """
    load json data from file.
    """
    with open(file, 'r', encoding='utf8') as _file:
        data = json.load(_file)

    return data

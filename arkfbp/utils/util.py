# pylint: disable=missing-module-docstring
import json
from importlib import import_module


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


def get_class_from_path(path):
    """
    path => models.models.user.User
    return User
    """
    path_list = path.split('.')
    module = import_module('.'.join(path_list[:-1]))
    cls = getattr(module, path_list[-1])
    return cls

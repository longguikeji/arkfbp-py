import json


def convert_def_to_model_lines(definition):
    lines = []
    lines += ['']

    model_name = definition.get('className')
    lines += [f'class {model_name}(models.Model):']
    for field in definition.get('fields'):
        field_name = field.get('name')
        field_func = field.get('field')
        field_props = field.get('properties')
        wrapper = '"%s"'
        prop_string = ', '.join([f'{key}={value if not isinstance(value, str) else wrapper % value}' for
                                 key, value in field_props.items()])
        field_line = f'    {field_name} = models.{field_func}({prop_string})'
        lines += [field_line,]
    lines += ['']
    return lines


def convert_json_model_to_lines(json_model):
    lines = []
    lines += ['from django.db import models']
    models = json_model.get('models')
    for model in models:
        lines += [''  ]
        model_string = convert_def_to_model_lines(model)
        lines += model_string
    return lines


def convert_json_file_to_model_lines(json_file):
    with open(json_file, 'r', encoding='utf8') as _file:
        data = json.load(_file)

        lines = convert_json_model_to_lines(data)
        return lines

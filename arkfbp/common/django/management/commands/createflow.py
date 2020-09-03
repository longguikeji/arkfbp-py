import os

from django.core.management import CommandError

import arkfbp
from django.core.management.templates import TemplateCommand


FLOW_CLASS_MAP = {
    'base': 'Flow',
    'view': 'ViewFlow',
    'hook': 'GlobalHookFlow',
}


class Command(TemplateCommand):
    help = (
        "Creates a Arkfbp Flow for the given flow name"
    )
    missing_args_message = "You must provide an flow name."

    def handle(self, **options):
        app_name = options.pop('name')
        target = options.pop('topdir')
        base_class = options.pop('class')
        flow_base_class_value = FLOW_CLASS_MAP['base']
        if base_class:
            clz = FLOW_CLASS_MAP.get(base_class.lower(), None)
            if not clz:
                raise CommandError('Invalid Flow Class.')
            flow_base_class_value = clz
        options.update(flow_base_class=flow_base_class_value)
        options.update(template=f'file://{arkfbp.__path__[0]}/common/django/conf/flow_template')
        _target = os.path.join(target, app_name)
        if not os.path.exists(_target):
            os.mkdir(_target)
        super().handle('app', app_name, _target, **options)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--topdir', type=str, help='Specifies the file path for the flow.')
        parser.add_argument('--class', type=str, help='Select the class that the flow needs to inherit from.')

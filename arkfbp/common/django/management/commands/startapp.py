import os

import arkfbp
from django.core.management.templates import TemplateCommand


class Command(TemplateCommand):
    help = (
        "Creates a Arkfbp app directory structure for the given app name in "
        "the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide an application name."

    def handle(self, **options):
        app_name = options.pop('name')
        target = options.pop('directory')
        top_dir = options.pop('topdir')
        if top_dir:
            path = os.path.join(top_dir, app_name)
            if not os.path.exists(path):
                os.mkdir(path)
            target = path
        options.update(template=f'file://{arkfbp.__path__[0]}/common/django/conf/app_template')
        super().handle('app', app_name, target, **options)

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--topdir', type=str, help='Specify the parent directory where django app resides.')

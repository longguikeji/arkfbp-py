from django.core.management.templates import TemplateCommand
from django.core.management.utils import get_random_secret_key

import arkfbp


class Command(TemplateCommand):
    help = (
        "Creates a Django project directory structure for the given project "
        "name in the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide a project name."

    def handle(self, **options):
        project_name = options.pop('name')
        target = options.pop('directory')

        # Create a random SECRET_KEY to put it in the main settings.
        options['secret_key'] = get_random_secret_key()
        options.update(template=f'file://{arkfbp.__path__[0]}/common/django/conf/project_template')
        super().handle('project', project_name, target, **options)

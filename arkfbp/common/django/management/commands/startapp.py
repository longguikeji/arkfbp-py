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
        options.update(template=f'file://{arkfbp.__path__[0]}/common/django/conf/app_template')
        super().handle('app', app_name, target, **options)

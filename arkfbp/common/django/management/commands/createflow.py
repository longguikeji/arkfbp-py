import arkfbp
from django.core.management.templates import TemplateCommand


class Command(TemplateCommand):
    help = (
        "Creates a Arkfbp Flow for the given flow name"
    )
    missing_args_message = "You must provide an flow name."

    def handle(self, **options):
        app_name = options.pop('name')
        target = options.pop('directory')
        options.update(template=f'file://{arkfbp.__path__[0]}/common/django/conf/flow_template')
        super().handle('app', app_name, target, **options)

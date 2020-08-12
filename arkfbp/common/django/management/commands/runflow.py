import importlib
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run a Arkfbp Flow for the given flow name"
    # missing_args_message = "You must provide an flow name."

    def handle(self, **options):
        path = options.get('flow')
        input = options.get('input')
        try:
            clz = importlib.import_module(f'{path}.main')
            instance = clz.Main()
            instance.main(input)
        except ModuleNotFoundError:
            self.stdout.write('\nRun failed, Invalid flow.')

    def add_arguments(self, parser):
        parser.add_argument('--flow', type=str, help='Specifies the import path for the target flow name.')
        parser.add_argument('--input', type=str, help='Input data at the beginning of the flow.')

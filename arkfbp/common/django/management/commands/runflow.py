import importlib

from arkfbp.flow.executer import FlowExecuter
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Run a Arkfbp Flow for the given flow name"

    def handle(self, **options):
        path = options.get('flow')
        input = options.get('input')
        http_method = options.get('http_method', None)
        header = options.get('header', None)
        try:
            clz = importlib.import_module(f'{path}.main')
            instance = clz.Main()
            FlowExecuter.cli_start_flow(instance, input, http_method=http_method, header=header)
        except ModuleNotFoundError:
            raise CommandError('Run failed, Invalid flow.')

    def add_arguments(self, parser):
        parser.add_argument('--flow', type=str, help='Specifies the import path for the target flow name.')
        parser.add_argument('--input', type=str, help='Input data at the beginning of the flow.')
        parser.add_argument('--http_method', type=str, help='HTTP method of flow.')
        parser.add_argument('--header', type=str, help='HTTP method of flow.')

import importlib
import os

from arkfbp.flow.executer import FlowExecuter
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Run all Arkfbp Test Flows"

    def handle(self, **options):
        print('cwd is', os.getcwd())

    def add_arguments(self, parser):
        # parser.add_argument('--flow', type=str, help='Specifies the import path for the target flow name.')
        # parser.add_argument('--input', type=str, help='Input data at the beginning of the flow.')
        # parser.add_argument('--http_method', type=str, help='HTTP method of flow.')
        # parser.add_argument('--header', type=str, help='HTTP method of flow.')
        pass

import importlib
import os
import sys

from django.core.management.base import BaseCommand, CommandError

from arkfbp.common.extension.transformer import RemoveNodeTransformer


class Command(BaseCommand):
    help = "For vscode extension to remove a node in flow's main.py"
    leave_locale_alone = True
    requires_system_checks = False

    def handle(self, **options):
        flow = options.get('flow')
        node_id = options.get('id')
        top_dir = options.get('topdir')

        if top_dir:
            sys.path.append(top_dir)

        if not node_id:
            raise CommandError('Run failed, Invalid node id.')

        try:
            clz = importlib.import_module(f'{flow}.main')
            _ = clz.Main()
        except ModuleNotFoundError:
            raise CommandError('Run failed, Invalid flow.')

        filepath = ''
        _ = flow.split('.')
        _.append('main.py')
        for x in _:
            filepath = os.path.join(filepath, x)
        filepath = os.path.join(top_dir, filepath)

        visitor = RemoveNodeTransformer(node_id)
        visitor.execute(filepath)

    def add_arguments(self, parser):
        parser.add_argument('--flow', type=str, help='Specifies the import path for name of flow.')
        parser.add_argument('--id', type=str, help='Specifies the id for node.')
        parser.add_argument('--topdir', type=str, help='Specifies the current top directory.')

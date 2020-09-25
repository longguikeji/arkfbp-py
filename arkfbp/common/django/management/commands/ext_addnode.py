import importlib
import os
import sys

from django.core.management.base import CommandError
from django.core.management.templates import TemplateCommand

from arkfbp.common.extension.transformer import AddNodeTransformer


class Command(TemplateCommand):
    help = "For vscode extension to add a node in flow's main.py"

    def handle(self, **options):
        flow = options.get('flow')
        node_clz = options.get('class')
        node_id = options.get('id')
        next_node_id = options.get('next')
        coord_x = options.get('x')
        coord_y = options.get('y')
        node_clz_alias = options.get('alias')
        top_dir = options.get('topdir')

        if top_dir:
            sys.path.append(top_dir)

        try:
            clz = importlib.import_module(f'{flow}.main')
            _ = clz.Main()
        except ModuleNotFoundError:
            raise CommandError('Run failed, Invalid flow.')

        try:
            _node_clz = node_clz.split('.')
            clz_path = '.'.join(_node_clz[:-1])
            clz = importlib.import_module(clz_path)
            node_id = getattr(clz, _node_clz[-1]).id
        except ModuleNotFoundError:
            raise CommandError('Run failed, Invalid node.')

        filepath = ''
        _ = flow.split('.')
        _.append('main.py')
        for x in _:
            filepath = os.path.join(filepath, x)

        visitor = AddNodeTransformer(node_clz, node_id, coord_x=float(coord_x), coord_y=float(coord_y),
                                     next_node_id=next_node_id,
                                     clz_as=node_clz_alias)
        visitor.execute(filepath)

    def add_arguments(self, parser):
        parser.add_argument('--flow', type=str, help='Specifies the import path for name of flow.')
        parser.add_argument('--class', type=str, help='Specifies the import path for node.')
        parser.add_argument('--id', type=str, help='Specifies the id for node.')
        parser.add_argument('--next', type=str, help='Specifies the next node id for the node.')
        parser.add_argument('--x', type=str, help='Specifies the coord x for node.')
        parser.add_argument('--y', type=str, help='Specifies the coord y for node.')
        parser.add_argument('--alias', type=str, help='Specifies the alias for node class.')
        parser.add_argument('--topdir', type=str, help='Specifies the current top directory.')

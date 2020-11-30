"""
meta config flow
"""
from arkfbp.flow import ViewFlow
from arkfbp.node import StartNode, StopNode

from .nodes.config import ConfigCore


class Main(ViewFlow):
    """
    Main FLow.
    """
    def create_nodes(self):
        """
        These nodes cannot be changed,if you are sure to do that.
        """
        return [{
            'cls': StartNode,
            'id': 'start',
            'next': 'config_meta',
            'x': None,
            'y': None
        }, {
            'cls': ConfigCore,
            'id': 'config_meta',
            'next': 'stop',
            'x': None,
            'y': None
        }, {
            'cls': StopNode,
            'id': 'stop',
            'next': None,
            'x': None,
            'y': None
        }]

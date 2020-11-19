"""
siteapi flow
"""
from arkfbp.flow import ViewFlow
from arkfbp.node import StartNode, StopNode
from .nodes.permission import PermissionCore
from ..admin.nodes.serializer import SerializerCore


class Main(ViewFlow):
    """
    Main FLow.
    """
    def create_nodes(self):
        """
        These nodes cannot be changed,if you are sure to do that,
        you can initialize a new SerializerCore node.
        """
        return [{
            'cls': StartNode,
            'id': 'start',
            'next': 'permission_core',
            'x': None,
            'y': None
        }, {
            'cls': PermissionCore,
            'id': 'permission_core',
            'next': 'serializer_core',
            'x': None,
            'y': None
        }, {
            'cls': SerializerCore,
            'id': 'serializer_core',
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

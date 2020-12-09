"""
siteapi flow
"""
from arkfbp.flow import ViewsetFlow
from arkfbp.node import StartNode, StopNode
from arkfbp.common.django.app.automation.flows.admin.nodes.queryset_node import QuerysetCore

from .nodes.permission import PermissionCore
from ..admin.nodes.serializer import SerializerCore


class Main(ViewsetFlow):
    """
    Main FLow.
    """

    def create_nodes(self):
        """
        These nodes cannot be changed,if you are sure to do that,
        you can initialize a new SerializerCore node.
        """
        return [
            {
                'cls': StartNode,
                'id': 'start',
                'next': 'permission_core',
                'x': None,
                'y': None
            },
            {
                'cls': PermissionCore,
                'id': 'permission_core',
                'next': 'queryset_core',
                'x': None,
                'y': None
            },
            {
                'cls': QuerysetCore,
                'id': 'queryset_core',
                'next': 'serializer_core',
                'x': None,
                'y': None
            },
            {
                'cls': SerializerCore,
                'id': 'serializer_core',
                'next': 'stop',
                'x': None,
                'y': None
            },
            {
                'cls': StopNode,
                'id': 'stop',
                'next': None,
                'x': None,
                'y': None
            }
        ]

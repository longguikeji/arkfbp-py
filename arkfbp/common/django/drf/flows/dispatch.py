"""
siteapi flow
"""
from arkfbp.node import StartNode, StopNode
from common.django.drf.nodes.init_request import InitRequestCore
from common.django.drf.nodes.method_handler import HandlerCore
from common.django.drf.generics import ModelViewSet

from common.django.drf.nodes.renderer import RendererCore


class Main(ModelViewSet):
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
                'next': 'init',
                'x': None,
                'y': None
            },
            {
                'cls': InitRequestCore,
                'id': 'init',
                'next': 'handler_core',
                'x': None,
                'y': None
            },
            {
                'cls': HandlerCore,
                'id': 'handler_core',
                'next': 'renderer_core',
                'x': None,
                'y': None
            },
            {
                'cls': RendererCore,
                'id': 'renderer_core',
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

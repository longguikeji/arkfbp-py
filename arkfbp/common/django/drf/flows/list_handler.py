"""
siteapi flow
"""
from arkfbp.node import StartNode, StopNode
from arkfbp.flow import Flow
from common.django.drf.nodes.get_queryset import QuerysetCore
from common.django.drf.nodes.many_serialize import ManySerializeCore


class ListHandler(Flow):
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
                'next': 'get_queryset',
                'x': None,
                'y': None
            },
            {
                'cls': QuerysetCore,
                'id': 'get_queryset',
                'next': 'serialize',
                'x': None,
                'y': None
            },
            {
                'cls': ManySerializeCore,
                'id': 'serialize',
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

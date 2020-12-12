"""
siteapi flow
"""
from arkfbp.node import StartNode, StopNode
from arkfbp.flow import Flow
from common.django.drf.nodes.intermediate import InterMediateCore


class RetrieveHandler(Flow):
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
                'next': 'inter',
                'x': None,
                'y': None
            },
            {
                'cls': InterMediateCore,
                'id': 'inter',
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

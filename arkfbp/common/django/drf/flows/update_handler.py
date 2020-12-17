"""
siteapi flow
"""
from arkfbp.node import StartNode, StopNode
from arkfbp.flow import Flow
from common.django.drf.nodes.get_object import GetObjectCore
from common.django.drf.nodes.update_obj_serialize import UpdateObjSerializerCore


class UpdateHandler(Flow):
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
                'next': 'get_object',
                'x': None,
                'y': None
            },
            {
                'cls': GetObjectCore,
                'id': 'get_object',
                'next': 'update',
                'x': None,
                'y': None
            },
            {
                'cls': UpdateObjSerializerCore,
                'id': 'update',
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

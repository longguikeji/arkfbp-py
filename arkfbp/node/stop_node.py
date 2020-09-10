from .base import Node


# StopNode metadata
_NODE_NAME = 'stop'
_NODE_KIND = 'stop'


class StopNode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND

    def run(self, *args, **kwargs):
        return self.inputs

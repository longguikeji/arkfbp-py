from .base import Node


# StartNode metadata
_NODE_NAME = 'start'
_NODE_KIND = 'start'


class StartNode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND

    def run(self, *args, **kwargs):
        return self.inputs

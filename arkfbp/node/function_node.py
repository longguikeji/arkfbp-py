from .base import Node


# FunctionNode metadata
_NODE_NAME = 'function'
_NODE_KIND = 'function'


class FunctionNode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND

    def run(self, *args, **kwargs):
        return None

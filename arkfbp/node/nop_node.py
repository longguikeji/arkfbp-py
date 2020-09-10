from .base import Node


# NopNode metadata
_NODE_NAME = 'nop'
_NODE_KIND = 'nop'


class NopNode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND

    def run(self, *args, **kwargs):
        return None

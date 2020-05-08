from .base import Node


class FunctionNode(Node):

    name = 'function'
    kind = 'function'

    def run(self):
        return None
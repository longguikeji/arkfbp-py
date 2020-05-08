from .base import Node


class NopNode(Node):

    name = 'nop'
    kind = 'nop'

    def run(self):
        return None
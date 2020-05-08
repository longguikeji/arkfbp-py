from .base import Node


class StartNode(Node):

    name = 'start'
    kind = 'start'

    def run(self):
        return None
from .base import Node


class StopNode(Node):

    name = 'stop'
    kind = 'stop'

    def run(self):
        return None
from .base import Node


class StopNode(Node):

    name = 'stop'
    kind = 'stop'

    def run(self, *args, **kwargs):
        return self.inputs

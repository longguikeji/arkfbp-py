from .base import Node


class StartNode(Node):

    name = 'start'
    kind = 'start'

    def run(self, *args, **kwargs):
        return self.inputs

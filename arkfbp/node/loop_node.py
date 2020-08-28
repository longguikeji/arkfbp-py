from .base import Node


# LoopNode metadata
_NODE_NAME = 'loop'
_NODE_KIND = 'loop'


class LoopNode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND

    def init_statement(self):
        pass

    def condition_statement(self):
        return False

    def post_statement(self):
        pass

    def process(self):
        pass

    def run(self, *args, **kwargs):
        self.init_statement()

        while bool(self.condition_statement()):
            self.process()
            self.post_statement()

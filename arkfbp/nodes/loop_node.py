from .base import Node

class LoopNode(Node):

    name = "loop"
    kind = "loop"

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

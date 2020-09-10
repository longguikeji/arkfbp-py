from .base import Node


# IFNode metadata
_NODE_NAME = 'if'
_NODE_KIND = 'if'


class IFNode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND

    ret = False

    def run(self, *args, **kwargs):
        self.ret = bool(self.expression())
        if self.ret:
            return self.positive_statement()
        return self.negative_statement()

    def expression(self):
        return True

    def positive_statement(self):
        pass

    def negative_statement(self):
        pass

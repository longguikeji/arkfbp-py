from .base import Node

# IFNode metadata
_NODE_NAME = 'if'
_NODE_KIND = 'if'


class IFNode(Node):
    next_values = ['error_next','positive_next','negative_next']

    name = _NODE_NAME
    kind = _NODE_KIND

    ret = False

    def run(self, *args, **kwargs):
        self.ret = bool(self.expression())
        if self.ret:
            self.next = 'positive_next'
            self.positive_statement()
        else:
            self.next = 'negative_next'
            self.negative_statement()
        return self.ret

    def expression(self):
        return True

    def positive_statement(self):
        pass

    def negative_statement(self):
        pass

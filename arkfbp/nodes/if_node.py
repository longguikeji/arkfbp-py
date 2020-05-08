from .base import Node


class IFNode(Node):

    name = 'if'
    kind = 'if'

    ret = False

    def run(self, *args, **kwargs):
        ret_code = self.expression()
        self.ret = bool(ret_code)

        if ret_code:
            return self.positive_statement()

        return self.negative_statement()

    def expression(self):
        return True

    def positive_statement(self):
        pass

    def negative_statement(self):
        pass
"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework.response import Response


class InterMediateCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        response = Response()
        return response

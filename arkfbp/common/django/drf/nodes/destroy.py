"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework import status
from rest_framework.response import Response


class DestroyCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        obj = self.flow.get_object()
        obj.delete()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        return response

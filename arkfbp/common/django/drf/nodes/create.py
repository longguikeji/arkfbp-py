"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework import status
from rest_framework.response import Response


class CreateCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        serializer_cls = self.flow.get_serializer_class()
        data = self.flow.request.data
        srl = serializer_cls(data=data)
        srl.is_valid(raise_exception=True)
        srl.save()
        return Response(srl.data)

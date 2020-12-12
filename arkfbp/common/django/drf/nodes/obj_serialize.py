"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework.response import Response


class ObjSerializeCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        obj = self.inputs
        serializer_cls = self.flow.get_serializer_class()
        srl = serializer_cls(obj)
        return Response(srl.data)

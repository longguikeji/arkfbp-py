"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework.response import Response


class ManySerializeCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        queryset = self.inputs
        serializer_cls = self.flow.get_serializer_class()
        srl = serializer_cls(queryset, many=True)
        return Response(srl.data)
